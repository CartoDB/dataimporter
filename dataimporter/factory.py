# -*- coding: utf-8 -*-
"""
    dataimporter
    ~~~~~~~~~~~~
    A data importer utility for CARTO
    :copyright: (c) 2017 by CARTO Solutions TEAM.
    :license: TBD, see LICENSE for more details.
"""

# import os
from celery import Celery
from flask import Flask, g
from flask_wtf.csrf import CsrfProtect
from werkzeug.utils import find_modules, import_string
# from dataimporter.blueprints.dataimporter import init_db


def create_app(config=None, blueprints=True):
    app = Flask(__name__)

    app.config.update(dict(
        SECRET_KEY=b'_5#y2L"F4Q8z\n\xec]/',
        USERNAME='admin',
        PASSWORD='default',
        UPLOAD_FOLDER='/app/uploads',
        ALLOWED_EXTENSIONS=['csv'],
        CELERY_BROKER_URL='redis://localhost:6379/0',
        CELERY_RESULT_BACKEND='redis://localhost:6379/0'
    ))
    app.config.update(config or {})
    app.config.from_envvar('FLASKR_SETTINGS', silent=True)
    CsrfProtect(app)

    if blueprints:
        register_blueprints(app)
    # register_cli(app)
    # register_teardowns(app)

    return app


def register_blueprints(app):
    """Register all blueprint modules
    Reference: Armin Ronacher, "Flask for Fun and for Profit" PyBay 2016.
    """
    for name in find_modules('dataimporter.blueprints.dataimporter'):
        mod = import_string(name)
        if hasattr(mod, 'bp'):
            app.register_blueprint(mod.bp)
    return None


def create_celery(app):
    celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'], backend=app.config['CELERY_RESULT_BACKEND'])
    celery.conf.update(app.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery


# def register_cli(app):
#     @app.cli.command('initdb')
#     def initdb_command():
#         """Creates the database tables."""
#         init_db()
#         print('Initialized the database.')


# def register_teardowns(app):
#     @app.teardown_appcontext
#     def close_db(error):
#         """Closes the database again at the end of the request."""
#         if hasattr(g, 'sqlite_db'):
#             g.sqlite_db.close()