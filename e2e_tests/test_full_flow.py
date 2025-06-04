import pytest
import requests
import time
import uuid


@pytest.fixture(scope="function")
def test_user():
    uid = str(uuid.uuid4())[:8]
    return {
        "login": f"e2e_user_{uid}",
        "password": "E2eTest123!",
        "email": f"e2e_user_{uid}@example.com",
        "first_name": "EndToEnd",
        "last_name": "Test"
    }


@pytest.fixture(scope="function")
def registered_user(test_user):
    requests.post('http://api_gateway:8080/api/v1/register', json=test_user)
    return test_user


@pytest.fixture(scope="function")
def auth_token(registered_user):
    login_response = requests.post(
        'http://api_gateway:8080/api/v1/login',
        json={"login": registered_user["login"], "password": registered_user["password"]}
    )
    return login_response.json()["token"]


def test_full_flow_post_creation_view_and_stats(auth_token):
    post_data = {
        "title": "E2E Test Post",
        "description": "Post for end-to-end testing",
        "is_private": False
    }
    post_response = requests.post(
        'http://api_gateway:8080/api/v1/posts',
        headers={"Authorization": auth_token},
        json=post_data
    )
    post_id = post_response.json()["post_id"]

    for _ in range(3):
        requests.post(
            f'http://api_gateway:8080/api/v1/posts/{post_id}/view',
            headers={"Authorization": auth_token}
        )

    time.sleep(5)

    stats_response = requests.get(
        f'http://api_gateway:8080/api/v1/posts/{post_id}/stats',
        headers={"Authorization": auth_token}
    )
    stats = stats_response.json()
    assert stats["views_count"] == 3


def test_post_likes_and_comments_flow(auth_token):
    post_response = requests.post(
        'http://api_gateway:8080/api/v1/posts',
        headers={"Authorization": auth_token},
        json={
            "title": "Likes and Comments Test",
            "description": "Testing likes and comments flow",
            "is_private": False
        }
    )
    post_id = post_response.json()["post_id"]

    for _ in range(2):
        requests.post(
            f'http://api_gateway:8080/api/v1/posts/{post_id}/like',
            headers={"Authorization": auth_token}
        )

    comment_text = "This is a test comment for E2E testing"
    requests.post(
        f'http://api_gateway:8080/api/v1/posts/{post_id}/comment',
        headers={"Authorization": auth_token},
        json={"text": comment_text}
    )

    comments_response = requests.get(
        f'http://api_gateway:8080/api/v1/posts/{post_id}/comments',
        headers={"Authorization": auth_token}
    )

    comments = comments_response.json()["comments"]
    assert any(comment["text"] == comment_text for comment in comments)

    stats_response = requests.get(
        f'http://api_gateway:8080/api/v1/posts/{post_id}/stats',
        headers={"Authorization": auth_token}
    )
    stats = stats_response.json()
    assert stats["likes_count"] == 2
    assert stats["comments_count"] == 1


def test_user_profile_and_post_dynamics(auth_token):
    update_data = {
        "first_name": "UpdatedFirstName",
        "profile": {
            "city": "Test City",
            "about_me": "E2E Test User"
        }
    }
    requests.put(
        'http://api_gateway:8080/api/v1/profile',
        headers={"Authorization": auth_token},
        json=update_data
    )

    profile_response = requests.get(
        'http://api_gateway:8080/api/v1/profile',
        headers={"Authorization": auth_token}
    )
    profile = profile_response.json()

    assert profile["first_name"] == "UpdatedFirstName"
    assert profile["profile"]["city"] == "Test City"
    assert profile["profile"]["about_me"] == "E2E Test User"

    post_ids = []
    for i in range(2):
        post_response = requests.post(
            'http://api_gateway:8080/api/v1/posts',
            headers={"Authorization": auth_token},
            json={
                "title": f"Dynamics Test Post {i + 1}",
                "description": f"Post {i + 1} for dynamics testing",
                "is_private": False
            }
        )
        post_ids.append(post_response.json()["post_id"])

    for _ in range(5):
        requests.post(
            f'http://api_gateway:8080/api/v1/posts/{post_ids[0]}/view',
            headers={"Authorization": auth_token}
        )

    requests.post(
        f'http://api_gateway:8080/api/v1/posts/{post_ids[0]}/like',
        headers={"Authorization": auth_token}
    )

    for _ in range(2):
        requests.post(
            f'http://api_gateway:8080/api/v1/posts/{post_ids[1]}/view',
            headers={"Authorization": auth_token}
        )

    for _ in range(3):
        requests.post(
            f'http://api_gateway:8080/api/v1/posts/{post_ids[1]}/like',
            headers={"Authorization": auth_token}
        )

    time.sleep(2)

    dynamics_response = requests.get(
        f'http://api_gateway:8080/api/v1/posts/{post_ids[0]}/dynamic?metric=views',
        headers={"Authorization": auth_token}
    )
    dynamics = dynamics_response.json()
    assert any(d["count"] == 5 for d in dynamics)

    requests.get(
        f'http://api_gateway:8080/api/v1/posts/{post_ids[1]}/stats',
        headers={"Authorization": auth_token}
    )

    top_posts_views_response = requests.get(
        'http://api_gateway:8080/api/v1/posts/top?metric=views',
        headers={"Authorization": auth_token}
    )
    top_posts = top_posts_views_response.json()
    assert int(top_posts[0]["post_id"]) == int(post_ids[0])

    top_posts_likes_response = requests.get(
        'http://api_gateway:8080/api/v1/posts/top?metric=likes',
        headers={"Authorization": auth_token}
    )
    top_posts = top_posts_likes_response.json()
    assert int(top_posts[0]["post_id"]) == int(post_ids[1])
