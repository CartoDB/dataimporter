from io import TextIOWrapper
from flask import Blueprint, request, session, g, redirect, url_for, abort, \
     render_template, flash, current_app, send_from_directory, jsonify
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from werkzeug.utils import secure_filename
from wtforms import StringField, IntegerField, BooleanField
from wtforms.validators import DataRequired

from etl.etl import InsertJob
from .tasks.import_worker import long_task


# create our blueprint :)
bp = Blueprint('dataimporter', __name__, static_folder='static', template_folder='templates', static_url_path='/static/dataimporter')

class ImportForm(FlaskForm):
    carto_base_url = StringField("CARTO base URL", validators=[DataRequired()], description="Example: https://aromeu.carto.com/", default="https://aromeu.carto.com/")
    carto_api_key = StringField("CARTO API key", validators=[DataRequired()], description='Found on the "Your API keys" section of your user profile', default="c4faca161957ce0bcee88d91f58d3f68a3462b57")
    carto_table_name = StringField("CARTO dataset name", validators=[DataRequired()], description="Name of the target dataset in CARTO (it has to exist)", default="sample_1")
    carto_delimiter = StringField("CSV character delimiter", validators=[DataRequired()], description="Character used as delimiter in the CSV file, tipycally a comma", default=",")
    carto_columns = StringField("Columns of the CSV file", validators=[DataRequired()], description="Comma separated list of columns of the CSV file that will be transferred to CARTO", default="mes,provincia,total_suministros,clientes_telegestion,telegestion,porcentaje,created_at,updated_at,the_geom")
    carto_date_columns = StringField("Date columns of the CSV file", description="Comma separated list of columns of the CSV file that represent a date or timestamp and have a different format than the CARTO date format (%Y-%m-%d %H:%M:%S+00), so that they need to be transformed. If this field is set, then either `date_format` or `datetime_format` must be properly set to indicate the format of the `date_columns` in the CSV file")
    carto_x_column = StringField("X column", description="Name of the column that contains the x coordinate", default="")
    carto_y_column = StringField("Y column", description="Name of the column that contains the y coordinate", default="")
    carto_srid = IntegerField("SRID", description="The SRID of the coordinates in the CSV file", default=4326)
    etl_chunk_size = IntegerField("Chunk size", validators=[DataRequired()], description="Number of items to be grouped on a single INSERT or DELETE request. POST requests can deal with several MBs of data (i.e. characters), so this number can go quite high if you wish", default=10000)
    etl_max_attempts = IntegerField("Max. attempts", validators=[DataRequired()], description="Number of attempts before giving up on a API request to CARTO", default=3)
    etl_file_encoding = StringField("CSV file encoding", validators=[DataRequired()], description="Encoding of the file. By default it's `utf-8`, if your file contains accents or it's in spanish it may be `ISO-8859-1`", default="utf-8")
    etl_force_no_geometry = BooleanField("CSV without geometry", description="Check this if your destination table does not have a geometry column", default="false")
    etl_force_the_geom = StringField("The geometry column name", description="Indicate the name of the geometry column in the CSV file in case it's an hexstring value that has to be inserted directly into PostGIS", default="the_geom")
    etl_date_format = StringField("Date format", description="Format of the `date_columns` expressed in the `datetime` Python module supported formats")
    etl_datetime_format = StringField("DateTime format", description="Format of the `date_columns` in case they are timestamps expressed in the `datetime` Python module supported formats")
    etl_float_comma_separator = StringField("Number comma separator", description="Character used as comma separator in float columns", default=".")
    etl_float_thousand_separator = StringField("Number thousands separator", description="Character used as thousand separator in float columns")
    the_csv = FileField("Upload .csv file", validators=[FileRequired(), FileAllowed(["csv"], ".csv files only!")], description=".csv to be imported")

class ImportWorker(object):
    def __init__(self, csv_stream,
                    csv_file_name,
                    base_url,
                    api_key,
                    table_name=None,
                    delimiter=None,
                    columns=None,
                    date_columns=None,
                    x_column=None,
                    y_column=None,
                    srid=None,
                    chunk_size=None,
                    max_attempts=None,
                    file_encoding=None,
                    force_no_geometry=None,
                    force_the_geom=None,
                    date_format=None,
                    datetime_format=None,
                    float_comma_separator=None,
                    float_thousand_separator=None):
        self.csv_file_name = csv_file_name
        self.base_url = base_url
        self.api_key = api_key
        self.table_name = table_name
        self.delimiter = delimiter
        self.columns = columns
        self.date_columns = date_columns
        self.x_column = x_column
        self.y_column = y_column
        self.srid = srid
        self.chunk_size = chunk_size
        self.max_attempts = max_attempts
        self.file_encoding = file_encoding
        self.force_no_geometry = force_no_geometry
        self.force_the_geom = force_the_geom
        self.date_format = date_format
        self.datetime_format = datetime_format
        self.float_comma_separator = float_comma_separator
        self.float_thousand_separator = float_thousand_separator

        text_stream = TextIOWrapper(csv_stream, encoding=self.file_encoding)
        self.job = InsertJob(text_stream,
                        base_url=base_url,
                        api_key=api_key,
                        table_name=self.table_name,
                        delimiter=self.delimiter,
                        columns=self.columns,
                        date_columns=self.date_columns,
                        x_column=self.x_column,
                        y_column=self.y_column,
                        srid=self.srid,
                        chunk_size=self.chunk_size,
                        max_attempts=self.max_attempts,
                        file_encoding=self.file_encoding,
                        force_no_geometry=self.force_no_geometry,
                        force_the_geom=self.force_the_geom,
                        date_format=self.date_format,
                        datetime_format=self.datetime_format,
                        float_comma_separator=float_comma_separator,
                        float_thousand_separator=float_thousand_separator)

    def run(self):
        print("run")
        self.job.run()


def allowed_file(filename, current_app):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@bp.route('/import/', methods=['GET', 'POST'])
def upload_file():
    form = ImportForm()
    importer = None
    if form.validate_on_submit():
        import ipdb; ipdb.set_trace(context=30)
        importer = ImportWorker(form.the_csv.data.stream, form.the_csv.data.filename, form.carto_base_url.data, form.carto_api_key.data,table_name=form.carto_table_name.data,
            delimiter=form.carto_delimiter.data,
            columns=form.carto_columns.data,
            date_columns=form.carto_date_columns.data,
            x_column=form.carto_x_column.data,
            y_column=form.carto_y_column.data,
            srid=form.carto_srid.data,
            chunk_size=form.etl_chunk_size.data,
            max_attempts=form.etl_max_attempts.data,
            file_encoding=form.etl_file_encoding.data,
            force_no_geometry=form.etl_force_no_geometry.data,
            force_the_geom=form.etl_force_the_geom.data,
            date_format=form.etl_date_format.data,
            datetime_format=form.etl_datetime_format.data,
            float_comma_separator=form.etl_float_comma_separator.data,
            float_thousand_separator=form.etl_float_thousand_separator.data)
        importer.run()
    return render_template("import.html", form=form, result=[str(importer)])

    # if request.method == 'POST':
    #     # check if the post request has the file part
    #     if 'file' not in request.files:
    #         flash('No file part')
    #         return redirect(request.url)
    #     file = request.files['file']
    #     # if user does not select file, browser also
    #     # submit a empty part without filename
    #     if file.filename == '':
    #         flash('No selected file')
    #         return redirect(request.url)
    #     if file and allowed_file(file.filename):
    #         filename = secure_filename(file.filename)
    #         file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
    #         return redirect(url_for('uploaded_file',
    #                                 filename=filename))
    # print('get')
    # return render_template('import.html')

@bp.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'],
                               filename)

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

@bp.route('/projects/<taskid>', methods=['GET'])
def project_status(taskid):
    task = long_task.AsyncResult(taskid)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
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
