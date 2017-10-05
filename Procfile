redis: sh run-redis.sh
worker: celery worker -A dataimporter.blueprints.dataimporter.tasks.import_worker.celery --loglevel=info
web: gunicorn app:app --timeout 600
