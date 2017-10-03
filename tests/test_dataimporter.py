from flask import url_for

def test_app_fixture(app):
    assert app is not None

def test_app(client):
    assert client.get(url_for('dataimporter.hello')).status_code == 200
    assert client.get(url_for('dataimporter.error')).status_code == 401
    assert client.get('/asd').status_code == 404
    res = client.get('/hello/motherfucker')
    assert res.status_code == 500
    assert b'motherfucker' in res.data

