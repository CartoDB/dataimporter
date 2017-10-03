from flask import Blueprint, request, session, g, redirect, url_for, abort, \
     render_template, flash, current_app
from werkzeug.utils import secure_filename


# create our blueprint :)
bp = Blueprint('dataimporter', __name__)


@bp.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['the_file']
        f.save('/tmp/' + secure_filename(f.filename))

@bp.route('/')
def hello_world():
    current_app.logger.warn('warn message')
    flash('fuck you')
    return redirect(url_for('dataimporter.hello'))

@bp.route('/projects/')
def projects():
    return 'The project page'

@bp.route('/about')
def about():
    return 'The about page'

@bp.route('/hello/')
@bp.route('/hello/<name>')
def hello(name=None):
    if name == 'motherfucker':
        return server_error('{name} is not allowed'.format(name=name))
    return render_template('hello.html', name=name)

@bp.app_errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@bp.app_errorhandler(500)
def server_error(error):
    return render_template('500.html', error=error), 500

@bp.route('/error')
def error():
    abort(401)
