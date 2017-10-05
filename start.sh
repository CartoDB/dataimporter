#!/bin/bash

sh run-redis.sh &
celery worker -A dataimporter.blueprints.dataimporter.tasks.import_worker.celery --loglevel=info &
gunicorn app:app --timeout 600
