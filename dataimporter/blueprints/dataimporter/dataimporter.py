from flask import Blueprint, request, url_for, render_template, current_app, jsonify
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from werkzeug.utils import secure_filename
from wtforms import StringField, IntegerField, BooleanField
from wtforms.validators import DataRequired

from .tasks.import_worker import insert_task, create_file_name, get_running_tasks


# create our blueprint :)
bp = Blueprint('dataimporter', __name__, static_folder='static', template_folder='templates', static_url_path='/static/dataimporter')

class ImportForm(FlaskForm):
    base_url = StringField("CARTO base URL", validators=[DataRequired()],render_kw={"placeholder": "https://username.carto.com"})
    api_key = StringField("CARTO API key", validators=[DataRequired()], default="")
    table_name = StringField("CARTO dataset name", validators=[DataRequired()], description="Name of the target dataset in CARTO (it has to exist)")
    delimiter = StringField("CSV column delimiter", validators=[DataRequired()], default=",")
    columns = StringField("Columns of the CSV file", validators=[DataRequired()], description="Comma separated list of columns of the CSV file that will be transferred to CARTO", render_kw={"placeholder": "column1,column2,column3,column4"})
    date_columns = StringField("Date columns of the CSV file", description="Comma separated list of columns of the CSV file that represent a date or timestamp and have a different format than the CARTO date format (%Y-%m-%d %H:%M:%S+00), so that they need to be transformed. If this field is set, then either `date_format` or `datetime_format` must be properly set to indicate the format of the `date_columns` in the CSV file", render_kw={"placeholder": "date_column1,date_column2"})
    x_column = StringField("X column", description="Column that contains the x coordinate", render_kw={"placeholder": "longitude"})
    y_column = StringField("Y column", description="Column that contains the y coordinate", render_kw={"placeholder": "latitude"})
    srid = IntegerField("SRID", default=4326)
    chunk_size = IntegerField("Chunk size", validators=[DataRequired()], description="Number of items to be grouped on a single INSERT request", default=5000)
    max_attempts = IntegerField("Max. attempts", validators=[DataRequired()], description="Number of attempts before giving up on an API request to CARTO", default=3)
    file_encoding = StringField("CSV file encoding", validators=[DataRequired()], default="utf-8")
    force_no_geometry = BooleanField("CSV without geometry", description="Check this if your destination table does not have a geometry column", default=False)
    force_the_geom = StringField("The geometry column name", description="Indicate the name of the geometry column in the CSV file in case it's an hexstring value that has to be inserted directly into PostGIS",render_kw={"placeholder": "the_geom"})
    date_format = StringField("Date format", description="Format of the `date_columns` expressed in the `datetime` Python module supported formats")
    datetime_format = StringField("DateTime format", description="Format of the `date_columns` in case they are timestamps expressed in the `datetime` Python module supported formats")
    float_comma_separator = StringField("Number comma separator", default=".")
    float_thousand_separator = StringField("Number thousands separator")
    csv_file = FileField("Upload .csv file", validators=[FileRequired(), FileAllowed(["csv"], ".csv files only!")], description=".csv to be imported")


def allowed_file(filename, current_app):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@bp.route('/', methods=['GET', 'POST'])
def upload_file():
    form = ImportForm()
    task_id = ''
    if form.validate_on_submit():
        kwargs = prepare_args(form)
        file = request.files['csv_file']
        if file and allowed_file(file.filename, current_app):
            local_filename = create_file_name(current_app, file.filename)
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

@bp.route('/imports/', methods=['GET'])
def imports_list():
    imports = get_running_tasks()
    if imports is not None:
        return jsonify(imports)
    else:
        return jsonify([])

@bp.route('/import/<taskid>', methods=['GET'])
def import_status(taskid):
    task = insert_task.AsyncResult(taskid)
    try:
        if task is not None and task.state is not None and task.info is not None:
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
                    'status': str(task.info)  # this is the exception raised
                }
        else:
            response = {
                'state': 'PENDING',
                'current': 0,
                'total': 1,
                'status': 'wait'  # this is the exception raised
            }
    except Exception:
        response = {
            'state': 'PENDING',
            'current': 0,
            'total': 1,
            'status': 'wait'  # this is the exception raised
        }

    return jsonify(response)

@bp.app_errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@bp.app_errorhandler(500)
def server_error(error):
    return render_template('500.html', error=error), 500
