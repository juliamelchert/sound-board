from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from itsdangerous import NoneAlgorithm
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename

from main.auth import login_required
from main.db import get_db

import os

bp = Blueprint('sounds', __name__)

@bp.route('/')
def index():
    db = get_db()
    if g.user is not None:
        sounds = db.execute(
            'SELECT s.id, title, path, user_id, username'
            ' FROM sound s JOIN user u ON s.user_id = u.id'
            ' WHERE s.user_id = ?',
            (g.user['id'],)
        ).fetchall()

    else:
        sounds = []

    print("Including the following sounds:", sounds)
    return render_template('sounds/index.html', sounds=sounds)


@bp.route('/add', methods=('GET', 'POST'))
@login_required
def add():
    if request.method == 'POST':

        # If form submitted without file submitted
        if "file" not in request.files:
            return redirect(request.url)

        # If the file is blank
        file = request.files["file"]
        if file.filename == "":
            return redirect(request.url)

        file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static/user_sounds', secure_filename(file.filename)))

        title = request.form['title']
        path = os.path.join('../../static/user_sounds', secure_filename(file.filename))
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO sound (title, path, user_id)'
                ' VALUES (?, ?, ?)',
                (title, path, g.user['id'])
            )
            db.commit()

            print(f"Uploaded file path '{path}'.")

            return redirect(url_for('sounds.index'))

    return render_template('sounds/add.html')


def get_sound(id, check_author=True):
    sound = get_db().execute(
        'SELECT s.id, title, path, user_id, username'
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
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE sound SET title = ?'
                ' WHERE id = ?',
                (title, id)
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