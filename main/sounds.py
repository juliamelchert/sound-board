from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from itsdangerous import NoneAlgorithm
from werkzeug.exceptions import abort

from main.auth import login_required
from main.db import get_db

bp = Blueprint('sounds', __name__)

@bp.route('/')
def index():
    db = get_db()
    if g.user is not None:
        sounds = db.execute(
            'SELECT s.id, title, url, user_id, username'
            ' FROM sound s JOIN user u ON s.user_id = u.id'
            ' WHERE s.user_id = ?',
            (g.user['id'],)
        ).fetchall()

        if sounds == []:
            db.execute(
                'INSERT INTO sound (title, url, user_id)'
                ' VALUES (?, ?, ?)',
                ("default", "www.example.com", g.user['id'])
            )
            db.commit()

        # APPEND SOUNDS to []
    else:
        sounds = []

    return render_template('sounds/index.html', sounds=sounds)


@bp.route('/add', methods=('GET', 'POST'))
@login_required
def add():
    if request.method == 'POST':
        title = request.form['title']
        url = request.form['url']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO sound (title, url, user_id)'
                ' VALUES (?, ?, ?)',
                (title, url, g.user['id'])
            )
            db.commit()
            return redirect(url_for('sounds.index'))

    return render_template('sounds/add.html')


def get_sound(id, check_author=True):
    sound = get_db().execute(
        'SELECT s.id, title, url, user_id, username'
        ' FROM sound s JOIN user u ON s.user_id = u.id'
        ' WHERE s.id = ?',
        (id,)
    ).fetchone()

    if sound is None:
        abort(404, f"Sound id {id} doesn't exist.")

    if check_author and sound['user_id'] != g.user['id']:
        abort(403)

    return sound


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    sound = get_sound(id)

    if request.method == 'POST':
        title = request.form['title']
        url = request.form['url']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE sound SET title = ?, url = ?'
                ' WHERE id = ?',
                (title, url, id)
            )
            db.commit()
            return redirect(url_for('sounds.index'))

    return render_template('sounds/update.html', sound=sound)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_sound(id)
    db = get_db()
    db.execute('DELETE FROM sound WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('sounds.index'))