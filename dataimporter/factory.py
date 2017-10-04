# -*- coding: utf-8 -*-
"""
    dataimporter
    ~~~~~~~~~~~~
    A data importer utility for CARTO
    :copyright: (c) 2017 by CARTO Solutions TEAM.
    :license: TBD, see LICENSE for more details.
"""

# import os
from flask import Flask, g
from flask_wtf.csrf import CsrfProtect
from werkzeug.utils import find_modules, import_string
# from dataimporter.blueprints.dataimporter import init_db


def create_app(config=None):
    app = Flask(__name__)

    app.config.update(dict(
        SECRET_KEY=b'_5#y2L"F4Q8z\n\xec]/',
        USERNAME='admin',
        PASSWORD='default',
        UPLOAD_FOLDER='/tmp',
        ALLOWED_EXTENSIONS=['csv']
    ))
    app.config.update(config or {})
    app.config.from_envvar('FLASKR_SETTINGS', silent=True)
    CsrfProtect(app)

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