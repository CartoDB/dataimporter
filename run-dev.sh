#!/bin/bash

#pip uninstall .
pip install -e .
export FLASK_APP="app" FLASK_DEBUG=1
flask run
