import pytest
from pytest_mock import mocker
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
    assert response.json["message"] == "User registered successfully."


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


@pytest.mark.dependency(depends=["test_create_post"])
def test_view_post(client):
    response = client.post(
        f'/api/v1/posts/{POST_CREATED_ID}/view',
        headers={"Authorization": POST_TOKEN}
    )

    assert response.status_code == 200
    data = response.get_json()
    assert "success" in data and isinstance(data["success"], bool)
    assert "viewed_at" in data and isinstance(data["viewed_at"], str)
    try:
        datetime.fromisoformat(data["viewed_at"])
    except ValueError:
        pytest.fail("Invalid viewed_at format")


@pytest.mark.dependency(depends=["test_create_post"])
def test_like_post(client):
    response = client.post(
        f'/api/v1/posts/{POST_CREATED_ID}/like',
        headers={"Authorization": POST_TOKEN}
    )

    assert response.status_code == 200
    data = response.get_json()
    assert "success" in data and isinstance(data["success"], bool)
    assert "liked_at" in data and isinstance(data["liked_at"], str)
    try:
        datetime.fromisoformat(data["liked_at"])
    except ValueError:
        pytest.fail("Invalid liked_at format")


@pytest.mark.dependency(depends=["test_create_post"])
def test_comment_post(client):
    comment_text = "Test comment"

    response = client.post(
        f'/api/v1/posts/{POST_CREATED_ID}/comment',
        headers={"Authorization": POST_TOKEN},
        json={"text": comment_text}
    )

    assert response.status_code == 201
    data = response.get_json()
    assert "comment_id" in data and isinstance(data["comment_id"], int)
    assert "created_at" in data and isinstance(data["created_at"], str)
    try:
        datetime.fromisoformat(data["created_at"])
    except ValueError:
        pytest.fail("Invalid created_at format")


@pytest.mark.dependency(depends=["test_create_post", "test_comment_post"])
def test_get_comments_success(client):
    response = client.get(
        f'/api/v1/posts/{POST_CREATED_ID}/comments?page=1&per_page=10',
        headers={"Authorization": POST_TOKEN}
    )

    assert response.status_code == 200
    data = response.get_json()

    assert "comments" in data and isinstance(data["comments"], list)
    assert "meta" in data and isinstance(data["meta"], dict)

    for comment in data["comments"]:
        assert "comment_id" in comment and isinstance(comment["comment_id"], int)
        assert "text" in comment and isinstance(comment["text"], str)
        assert "user_id" in comment and isinstance(comment["user_id"], str)
        assert "created_at" in comment and isinstance(comment["created_at"], str)
        try:
            datetime.fromisoformat(comment["created_at"])
        except ValueError:
            pytest.fail("Invalid created_at format in comment")

    meta = data["meta"]
    assert "total" in meta and isinstance(meta["total"], int)
    assert "page" in meta and isinstance(meta["page"], int)
    assert "per_page" in meta and isinstance(meta["per_page"], int)
    assert "last_page" in meta and isinstance(meta["last_page"], int)


@pytest.mark.dependency(depends=["test_create_post"])
def test_view_post_not_found(client):
    response = client.post(
        '/api/v1/posts/999999/view',
        headers={"Authorization": POST_TOKEN}
    )
    assert response.status_code == 404
    data = response.get_json()
    assert "message" in data and isinstance(data["message"], str)


@pytest.mark.dependency(depends=["test_create_post"])
def test_like_post_not_found(client):
    response = client.post(
        '/api/v1/posts/999999/like',
        headers={"Authorization": POST_TOKEN}
    )
    assert response.status_code == 404
    data = response.get_json()
    assert "message" in data and isinstance(data["message"], str)


@pytest.mark.dependency(depends=["test_create_post"])
def test_comment_post_empty_text(client):
    response = client.post(
        f'/api/v1/posts/{POST_CREATED_ID}/comment',
        headers={"Authorization": POST_TOKEN},
        json={"text": ""}
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "message" in data and isinstance(data["message"], str)


@pytest.mark.dependency(depends=["test_create_post"])
def test_comment_post_long_text(client):
    long_text = "a" * 1001
    response = client.post(
        f'/api/v1/posts/{POST_CREATED_ID}/comment',
        headers={"Authorization": POST_TOKEN},
        json={"text": long_text}
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "message" in data and isinstance(data["message"], str)


@pytest.mark.dependency(depends=["test_create_post"])
def test_get_comments_not_found(client):
    response = client.get(
        '/api/v1/posts/999999/comments',
        headers={"Authorization": POST_TOKEN}
    )
    assert response.status_code == 404
    data = response.get_json()
    assert "message" in data and isinstance(data["message"], str)


@pytest.mark.dependency(depends=["test_create_post"])
def test_get_comments_invalid_post_id(client):
    response = client.get(
        '/api/v1/posts/invalid/comments',
        headers={"Authorization": POST_TOKEN}
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "message" in data and isinstance(data["message"], str)


@pytest.mark.dependency(depends=["test_create_post"])
def test_get_comments_invalid_pagination(client):
    response = client.get(
        f'/api/v1/posts/{POST_CREATED_ID}/comments?page=0&per_page=0',
        headers={"Authorization": POST_TOKEN}
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "message" in data and isinstance(data["message"], str)


@pytest.mark.dependency(depends=["test_login_for_posts"])
def test_get_comments_unauthorized(client):
    response = client.get(f'/api/v1/posts/1/comments')
    assert response.status_code == 401
    data = response.get_json()
    assert "error" in data and isinstance(data["error"], str)
