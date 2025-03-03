import sys
import os
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../user-service')))
from user_service.models import db
from ..api_gateway import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()


def test_gateway_routing(client):
    response = client.get('/some-endpoint')
    assert response.status_code == 404


def test_gateway_error_handling(client):
    response = client.get('/nonexistent-endpoint')
    assert response.status_code == 404
    assert response.json == {"message": "Endpoint not found"}


def test_gateway_service_unavailable(client):
    response = client.get('/service-unavailable')
    assert response.status_code == 503
    assert response.json == {"message": "Service unavailable"}
