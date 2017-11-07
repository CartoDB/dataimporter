CARTO Dataimporter
==================

A web application to upload CSV files bigger than 1M rows or 1GB to a CARTO account

Features
--------

- UI to upload CSV files to CARTO without limits
- Concurrent uploads + upload progress
- Advanced options (chunks, dates, numbers, encoding, etc.)

How it's done
-------------

1. Web application made with [Flask](http://flask.pocoo.org/)
2. Job manager made with [Celery](http://www.celeryproject.org/) and Redis
3. UI made with [WTForms](https://wtforms.readthedocs.io/en/latest/), jQuery, Bootstrap
4. CSV processing made with [carto-etl](https://github.com/CartoDB/carto-etl)
5. SQL API queries made with [carto-python](https://github.com/CartoDB/carto-python)

Test bed
--------

https://dataimporter.carto.io/

Development
-----------

```
virtualenv env
source env/bin/activate
pip install -r requirements-dev.txt
./run-dev.sh
```

Run with Docker
---------------

https://hub.docker.com/r/carto/dataimporter/

`docker run --name dataimporter -p 5000:5000 -p 6379:6379 -v ~/:/app/uploads carto/dataimporter`

Go to: http://localhost:5000
