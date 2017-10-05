#!/bin/bash

#env/bin/celery worker -A dataimporter.blueprints.dataimporter.tasks.import_worker.celery --loglevel=info
pip install -e .
honcho start
