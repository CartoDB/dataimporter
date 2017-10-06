import os
from werkzeug.utils import secure_filename

from etl.etl import InsertJob

from ....factory import create_app, create_celery


app = create_app(blueprints=False)
celery = create_celery(app)

class ImportWorker(object):
    def __init__(self, *args, **kwargs):
        self.total = 0
        self.task = kwargs['task']
        kwargs['observer'] = self.observe

        self.job = InsertJob(args[0], **kwargs)

    def run(self):
        self.job.run()

    def observe(self, message):
        method = getattr(self, message['type'], None)
        if callable(method):
            method(message['msg'])

    def total_rows(self, rows):
        self.total = rows
        self.task.update_state(state='PROGRESS',
                          meta={'current': 0, 'total': self.total,
                                'status': 'running'})

    def progress(self, rows):
        self.task.update_state(state='PROGRESS',
                          meta={'current': rows, 'total': self.total,
                                'status': 'running'})

    def error(self, error_message):
        self.task.update_state(state='FAILURE',
                          meta={'current': 0, 'total': self.total, 'status': error_message})

def remove_file(filename):
    try:
        os.remove(filename)
    except OSError:
        pass

def create_file_name(current_app, filename):
    return os.path.join(current_app.config['UPLOAD_FOLDER'], secure_filename(filename))

def get_running_tasks():
    i = celery.control.inspect()
    return i.active()

@celery.task(bind=True)
def insert_task(self, *args, **kwargs):
    kwargs['task'] = self
    import_worker = ImportWorker(*args, **kwargs)
    import_worker.run()
    remove_file(args[0])
    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 'completed'}
