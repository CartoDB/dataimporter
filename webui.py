#!/usr/bin/env python
import ConfigParser
import os

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from flask_wtf.csrf import CsrfProtect
from flask import Flask, send_file, render_template
from werkzeug.utils import secure_filename
from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired
# from dotcarto import DotCartoFile
from dataimporter import readFileImport


class Config(object):
    """
    Looks for config options in a config file or as an environment variable
    """
    def __init__(self, config_file_name):
        self.config_parser = ConfigParser.RawConfigParser()
        self.config_parser.read(config_file_name)

    def get(self, section, option):
        """
        Tries to find an option in a section inside the config file. If it's not found or if there is no
        config file at all, it'll try to get the value from an enviroment variable built from the section
        and options name, by joining the uppercase versions of the names with an underscore. So, if the section is
        "platform" and the option is "secret_key", the environment variable to look up will be PLATFORM_SECRET_KEY
        :param section: Section name
        :param option: Optionname
        :return: Configuration value
        """
        try:
            return self.config_parser.get(section, option)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            return os.environ.get("%s_%s" % (section.upper(), option.upper()), None)


config = Config("dotcarto.conf")

app = Flask(__name__)
if config.get("webui", "debug"):
    app.debug = True
app.secret_key = config.get("webui", "secret_key")
CsrfProtect(app)


class DotCartoForm(FlaskForm):
    carto_api_endpoint = StringField("CARTO username", validators=[DataRequired()], description="Your CARTO username.")
    carto_api_key = StringField("CARTO API key", validators=[DataRequired()], description='Found on the "Your API keys" section of your user profile')
    the_csv = FileField("Upload .csv file", validators=[FileRequired(), FileAllowed(["csv"], ".csv files only!")], description=".csv to be imported")
    row_limit = IntegerField("Account row limit", default=600) # widget=NumberInput()

@app.route("/", methods=["GET", "POST"])
def index():
    form = DotCartoForm()
    importer = None
    if form.validate_on_submit():

        importer = readFileImport(form.the_csv.data.stream, form.the_csv.data.filename, form.carto_api_endpoint.data, form.carto_api_key.data, form.row_limit.data)

    return render_template("index.html", form=form, result=[str(importer)])


# app.run()
