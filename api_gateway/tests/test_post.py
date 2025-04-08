import pytest
import json
from datetime import datetime, timedelta
import jwt
from ..app import app
import sys

sys.path.append("/app/proto")
from proto import post_pb2, post_pb2_grpc

POST_TEST_USER_LOGIN = "bob_grey"
POST_TEST_USER_PASSWORD = "Bob4Grey#2005"
POST_TEST_USER_EMAIL = "bob.grey@example.com"
POST_CREATED_ID = None
POST_TOKEN = None


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.mark.dependency()
def test_register_for_posts(client):
    response = client.post('/api/v1/register', json={
        "login": POST_TEST_USER_LOGIN,
        "password": POST_TEST_USER_PASSWORD,
        "email": POST_TEST_USER_EMAIL,
        "first_name": "Bob",
        "last_name": "Grey"
    })
    assert response.status_code in [200, 201], f"Unexpected status code: {response.status_code}"
    assert response.json == {"message": "User registered successfully."}


@pytest.mark.dependency(depends=["test_register_for_posts"])
def test_login_for_posts(client):
    global POST_TOKEN
    response = client.post('/api/v1/login', json={
        "login": POST_TEST_USER_LOGIN,
        "password": POST_TEST_USER_PASSWORD
    })
    assert response.status_code == 200, f"Unexpected status code: {response.status_code}"
    data = response.get_json()
    assert "token" in data, "Response must contain a token"
    POST_TOKEN = data["token"]
    assert data["message"] == "User successfully authenticated!"


@pytest.mark.dependency(depends=["test_login_for_posts"])
def test_create_post(client):
    global POST_CREATED_ID
    response = client.post(
        '/api/v1/posts',
        headers={"Authorization": POST_TOKEN},
        json={
            "title": "My First Post",
            "description": "Hello from test!",
            "is_private": False,
            "tags": ["test", "hello"]
        }
    )
    assert response.status_code == 201, f"Unexpected status code: {response.status_code}"
    data = response.get_json()
    assert "post_id" in data, "Response must contain post_id"
    assert "created_at" in data, "Response must contain created_at"
    POST_CREATED_ID = data["post_id"]


@pytest.mark.dependency(depends=["test_create_post"])
def test_get_post(client):
    response = client.get(
        f'/api/v1/posts/{POST_CREATED_ID}',
        headers={"Authorization": POST_TOKEN}
    )
    assert response.status_code == 200, f"Unexpected status code: {response.status_code}"
    data = response.get_json()
    assert data["post_id"] == int(POST_CREATED_ID)
    assert data["title"] == "My First Post"
    assert data["description"] == "Hello from test!"
    assert data["is_private"] is False
    assert data["tags"] == ["test", "hello"]


@pytest.mark.dependency(depends=["test_create_post"])
def test_update_post(client):
    response = client.put(
        f'/api/v1/posts/{POST_CREATED_ID}',
        headers={"Authorization": POST_TOKEN},
        json={
            "title": "Updated Title",
            "description": "Updated description",
            "is_private": True
        }
    )
    assert response.status_code == 200, f"Unexpected status code: {response.status_code}"
    data = response.get_json()
    assert "updated_at" in data, "Response must contain updated_at"
    get_response = client.get(
        f'/api/v1/posts/{POST_CREATED_ID}',
        headers={"Authorization": POST_TOKEN}
    )
    assert get_response.status_code == 200
    updated_data = get_response.get_json()
    assert updated_data["title"] == "Updated Title"
    assert updated_data["description"] == "Updated description"
    assert updated_data["is_private"] is True


@pytest.mark.dependency(depends=["test_login_for_posts"])
def test_list_posts(client):
    response = client.get(
        '/api/v1/posts?page=1&per_page=5',
        headers={"Authorization": POST_TOKEN}
    )
    assert response.status_code == 200, f"Unexpected status code: {response.status_code}"
    data = response.get_json()
    assert "posts" in data, "Response must contain 'posts' key"
    assert "meta" in data, "Response must contain 'meta' key"
    meta = data["meta"]
    assert "total" in meta
    assert "per_page" in meta
    assert "current_page" in meta


@pytest.mark.dependency(depends=["test_update_post"])
def test_delete_post(client):
    response = client.delete(
        f'/api/v1/posts/{POST_CREATED_ID}',
        headers={"Authorization": POST_TOKEN}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "message" in data and data["message"] == "Post deleted successfully."

    get_response = client.get(
        f'/api/v1/posts/{POST_CREATED_ID}',
        headers={"Authorization": POST_TOKEN}
    )
    assert get_response.status_code == 404


def test_protected_endpoint_no_token(client):
    response = client.get('/api/v1/posts')
    assert response.status_code == 401, f"Unexpected status code: {response.status_code}"
    data = response.get_json()
    assert "error" in data or "message" in data


def test_protected_endpoint_invalid_token(client):
    response = client.get(
        '/api/v1/posts',
        headers={"Authorization": "some.invalid.token"}
    )
    assert response.status_code == 401, f"Unexpected status code: {response.status_code}"
    data = response.get_json()
    assert "error" in data or "message" in data


@pytest.mark.dependency(depends=["test_login_for_posts"])
def test_create_post_with_missing_title(client):
    response = client.post(
        '/api/v1/posts',
        headers={"Authorization": POST_TOKEN},
        json={
            "description": "Some desc",
            "is_private": False
        }
    )
    assert response.status_code == 400, f"Unexpected status code: {response.status_code}"
    data = response.get_json()
    assert data.get("field") == "title" or "title" in data.get("message", "")


@pytest.mark.dependency(depends=["test_create_post"])
def test_post_pagination_boundaries(client):
    response = client.get(
        '/api/v1/posts?page=0&per_page=0',
        headers={"Authorization": POST_TOKEN}
    )
    assert response.status_code == 400

    response = client.get(
        '/api/v1/posts?page=1&per_page=101',
        headers={"Authorization": POST_TOKEN}
    )
    assert response.status_code == 400
