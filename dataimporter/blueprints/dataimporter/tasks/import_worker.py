import random
import time
from itertools import chain
from time import sleep
from ....factory import create_app, create_celery

from etl.etl import InsertJob

app = create_app(blueprints=False)
celery = create_celery(app)

@celery.task(bind=True)
def long_task(self):
    """Background task that runs a long function with progress reports."""
    verb = ['Starting up', 'Booting', 'Repairing', 'Loading', 'Checking']
    adjective = ['master', 'radiant', 'silent', 'harmonic', 'fast']
    noun = ['solar array', 'particle reshaper', 'cosmic ray', 'orbiter', 'bit']
    message = ''
    total = random.randint(10, 50)
    for i in range(total):
        if not message or random.random() < 0.25:
            message = '{0} {1} {2}...'.format(random.choice(verb),
                                              random.choice(adjective),
                                              random.choice(noun))
        self.update_state(state='PROGRESS',
                          meta={'current': i, 'total': total,
                                'status': message})
        time.sleep(1)
    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 42}

class ImportWorker(object):
    def __init__(self, *args, **kwargs):
        self.total = 0
        self.csv_file_name = args[1]
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


@celery.task(bind=True)
def insert_task(self, *args, **kwargs):
    kwargs['task'] = self
    import_worker = ImportWorker(*args, **kwargs)
    import_worker.run()
    return {'current': 100, 'total': 100, 'status': 'Task completed!',
            'result': 'completed'}
