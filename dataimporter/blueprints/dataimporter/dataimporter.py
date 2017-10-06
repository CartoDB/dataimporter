from io import TextIOWrapper
import os
from flask import Blueprint, request, session, g, redirect, url_for, abort, \
     render_template, flash, current_app, send_from_directory, jsonify
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from werkzeug.utils import secure_filename
from wtforms import StringField, IntegerField, BooleanField
from wtforms.validators import DataRequired

from .tasks.import_worker import long_task
from .tasks.import_worker import insert_task


# create our blueprint :)
bp = Blueprint('dataimporter', __name__, static_folder='static', template_folder='templates', static_url_path='/static/dataimporter')

class ImportForm(FlaskForm):
    base_url = StringField("CARTO base URL", validators=[DataRequired()], description="Example: https://aromeu.carto.com/", default="https://aromeu.carto.com/")
    api_key = StringField("CARTO API key", validators=[DataRequired()], description='Found on the "Your API keys" section of your user profile', default="424dec8b179567aace6ef7b229c9afa1d78d68e7")
    table_name = StringField("CARTO dataset name", validators=[DataRequired()], description="Name of the target dataset in CARTO (it has to exist)", default="sample_1")
    delimiter = StringField("CSV character delimiter", validators=[DataRequired()], description="Character used as delimiter in the CSV file, tipycally a comma", default=",")
    columns = StringField("Columns of the CSV file", validators=[DataRequired()], description="Comma separated list of columns of the CSV file that will be transferred to CARTO", default="mes,provincia,total_suministros,clientes_telegestion,telegestion,porcentaje,created_at,updated_at")
    date_columns = StringField("Date columns of the CSV file", description="Comma separated list of columns of the CSV file that represent a date or timestamp and have a different format than the CARTO date format (%Y-%m-%d %H:%M:%S+00), so that they need to be transformed. If this field is set, then either `date_format` or `datetime_format` must be properly set to indicate the format of the `date_columns` in the CSV file")
    x_column = StringField("X column", description="Name of the column that contains the x coordinate", default="")
    y_column = StringField("Y column", description="Name of the column that contains the y coordinate", default="")
    srid = IntegerField("SRID", description="The SRID of the coordinates in the CSV file", default=4326)
    chunk_size = IntegerField("Chunk size", validators=[DataRequired()], description="Number of items to be grouped on a single INSERT or DELETE request. POST requests can deal with several MBs of data (i.e. characters), so this number can go quite high if you wish", default=10000)
    max_attempts = IntegerField("Max. attempts", validators=[DataRequired()], description="Number of attempts before giving up on a API request to CARTO", default=3)
    file_encoding = StringField("CSV file encoding", validators=[DataRequired()], description="Encoding of the file. By default it's `utf-8`, if your file contains accents or it's in spanish it may be `ISO-8859-1`", default="utf-8")
    force_no_geometry = BooleanField("CSV without geometry", description="Check this if your destination table does not have a geometry column", default="false")
    force_the_geom = StringField("The geometry column name", description="Indicate the name of the geometry column in the CSV file in case it's an hexstring value that has to be inserted directly into PostGIS", default="the_geom")
    date_format = StringField("Date format", description="Format of the `date_columns` expressed in the `datetime` Python module supported formats")
    datetime_format = StringField("DateTime format", description="Format of the `date_columns` in case they are timestamps expressed in the `datetime` Python module supported formats")
    float_comma_separator = StringField("Number comma separator", description="Character used as comma separator in float columns", default=".")
    float_thousand_separator = StringField("Number thousands separator", description="Character used as thousand separator in float columns")
    csv_file = FileField("Upload .csv file", validators=[FileRequired(), FileAllowed(["csv"], ".csv files only!")], description=".csv to be imported")


def allowed_file(filename, current_app):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@bp.route('/import/', methods=['GET', 'POST'])
def upload_file():
    form = ImportForm()
    task_id = ''
    if form.validate_on_submit():
        kwargs = prepare_args(form)
        file = request.files['csv_file']
        if file and allowed_file(file.filename, current_app):
            local_filename = os.path.join(current_app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
            file.save(local_filename)
        task = insert_task.apply_async(args=[local_filename, form.csv_file.data.filename], kwargs=kwargs)
        task_id = task.id
        return jsonify({}), 202, {'Location': url_for('dataimporter.import_status', taskid=task_id)}
    return render_template("import.html", form=form)

def prepare_args(dict):
    args = {}
    for key in dict._fields:
        if key != 'csv_file':
            args[key] = dict._fields[key].data
    return args

@bp.route('/')
def hello_world():
    current_app.logger.warn('warn message')
    flash('.............')
    return redirect(url_for('.hello'))

@bp.route('/projects', methods=['GET'])
def projects():
    task = long_task.apply_async()
    return jsonify({}), 202, {'Location': url_for('dataimporter.project_status',
                                                  taskid=task.id)}

@bp.route('/import/<taskid>', methods=['GET'])
def import_status(taskid):
    task = insert_task.AsyncResult(taskid)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'current': task.info['current'],
            'total': task.info['total'],
            'status': task.info['status']
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info['current'],
            'total': task.info['total'],
            'status': task.info['status']
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)

@bp.app_errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@bp.app_errorhandler(500)
def server_error(error):
    return render_template('500.html', error=error), 500
