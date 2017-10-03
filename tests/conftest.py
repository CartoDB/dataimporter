import pytest
from dataimporter.factory import create_app

@pytest.fixture
def app():
    app = create_app()
    return app