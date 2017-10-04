from io import TextIOWrapper
from flask import Blueprint, request, session, g, redirect, url_for, abort, \
     render_template, flash, current_app, send_from_directory
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from werkzeug.utils import secure_filename
from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired

from etl.etl import InsertJob


# create our blueprint :)
bp = Blueprint('dataimporter', __name__, static_folder='static', template_folder='templates', static_url_path='/static/dataimporter')

class ImportForm(FlaskForm):
    carto_api_endpoint = StringField("CARTO base URL", validators=[DataRequired()], description="Example: https://aromeu.carto.com/")
    carto_api_key = StringField("CARTO API key", validators=[DataRequired()], description='Found on the "Your API keys" section of your user profile')
    the_csv = FileField("Upload .csv file", validators=[FileRequired(), FileAllowed(["csv"], ".csv files only!")], description=".csv to be imported")

class ImportWorker(object):
    def __init__(self, csv_stream, csv_file_name, api_endpoint, api_key, x_column="lon",
                 y_column="lat", srid=4326, file_encoding=None,
                 force_no_geometry=None, force_the_geom=None, float_comma_separator=None, float_thousand_separator=None):
        self.csv_file_name = csv_file_name
        self.api_endpoint = api_endpoint
        self.api_key = api_key
        self.x_column = x_column
        self.y_column = y_column
        self.srid = srid
        self.file_encoding = file_encoding
        self.force_no_geometry = force_no_geometry
        self.force_the_geom = force_the_geom
        self.float_comma_separator = float_comma_separator
        self.float_thousand_separator = float_thousand_separator

        text_stream = TextIOWrapper(csv_stream, encoding=self.file_encoding)
        self.job = InsertJob(text_stream, base_url=api_endpoint, api_key=api_key, x_column=x_column, y_column=y_column, srid=srid, file_encoding="utf-8", force_no_geometry=force_no_geometry, force_the_geom=force_the_geom, float_comma_separator=float_comma_separator, float_thousand_separator=float_thousand_separator, table_name="sample01", columns="a,lat,lon,b,c,d,e,f,g,h,j,k,l,m,n,o", delimiter="|")

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
        importer = ImportWorker(form.the_csv.data.stream, form.the_csv.data.filename, form.carto_api_endpoint.data, form.carto_api_key.data, file_encoding="ISO-8859-1")
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
    flash('fuck you')
    return redirect(url_for('.hello'))

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
