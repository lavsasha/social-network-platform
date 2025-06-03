from functools import wraps
import pytest
from unittest.mock import Mock, patch
from flask import Flask, request, jsonify
import json
import grpc
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def mock_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        return f(TEST_USER_ID, *args, **kwargs)

    return decorated


with patch('api_gateway.utils.auth.token_required', mock_token_required):
    from api_gateway.routes.statistics import statistics_bp, get_statistic_stub
    from proto import statistic_pb2, post_pb2


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['STATISTIC_SERVICE_HOST'] = 'localhost'
    app.config['STATISTIC_SERVICE_PORT'] = '50052'
    app.config['POST_SERVICE_HOST'] = 'localhost'
    app.config['POST_SERVICE_PORT'] = '50051'
    app.config['USER_SERVICE_URL'] = 'http://user-service'
    app.register_blueprint(statistics_bp)
    return app


@pytest.fixture
def client(app):
    return app.test_client()


TEST_USER_ID = "test_user_1"
TEST_POST_ID = "test_post_1"
TEST_TOKEN = "test_token"


@pytest.fixture
def mock_services():
    with patch('api_gateway.routes.statistics.get_post_stub') as mock_post_stub, \
            patch('api_gateway.routes.statistics.get_statistic_stub') as mock_stat_stub:
        yield mock_post_stub, mock_stat_stub


@pytest.mark.dependency()
def test_get_post_stats_success(client, mock_services):
    mock_post_stub, mock_stat_stub = mock_services

    mock_post_response = Mock()
    mock_post_response.post = Mock()
    mock_post_response.post.creator_id = TEST_USER_ID
    mock_post_stub.return_value.GetPost.return_value = mock_post_response

    mock_stat_response = statistic_pb2.PostStatsResponse(
        views_count=100,
        likes_count=50,
        comments_count=30
    )
    mock_stat_stub.return_value.GetPostStats.return_value = mock_stat_response

    response = client.get(
        f'/posts/{TEST_POST_ID}/stats',
        headers={'Authorization': TEST_TOKEN}
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["views_count"] == 100
    assert data["likes_count"] == 50
    assert data["comments_count"] == 30


@pytest.mark.dependency(depends=["test_get_post_stats_success"])
def test_get_post_stats_not_found(client, mock_services):
    mock_post_stub, mock_stat_stub = mock_services
    rpc_error = grpc.RpcError()
    rpc_error.code = lambda: grpc.StatusCode.NOT_FOUND
    rpc_error.details = lambda: "Post not found"

    mock_post_stub.return_value.GetPost.side_effect = rpc_error

    response = client.get(
        f'/posts/{TEST_POST_ID}/stats',
        headers={'Authorization': TEST_TOKEN}
    )

    assert response.status_code == 404
    data = json.loads(response.data)
    assert "message" in data
    assert data["message"] == "Post not found"


@pytest.mark.dependency()
def test_get_post_dynamic_success(client, mock_services):
    mock_post_stub, mock_stat_stub = mock_services

    mock_post_response = Mock()
    mock_post_response.post = Mock()
    mock_post_response.post.creator_id = TEST_USER_ID
    mock_post_stub.return_value.GetPost.return_value = mock_post_response

    mock_stat_response = statistic_pb2.PostDynamicResponse(
        stats=[
            statistic_pb2.DailyStat(date="2025-05-20", count=10),
            statistic_pb2.DailyStat(date="2025-05-21", count=20)
        ]
    )
    mock_stat_stub.return_value.GetPostDynamic.return_value = mock_stat_response

    response = client.get(
        f'/posts/{TEST_POST_ID}/dynamic?metric=views',
        headers={'Authorization': TEST_TOKEN}
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 2
    assert data[0]["date"] == "2025-05-20"
    assert data[0]["count"] == 10


@pytest.mark.dependency(depends=["test_get_post_dynamic_success"])
def test_get_post_dynamic_forbidden(client, mock_services):
    mock_post_stub, mock_stat_stub = mock_services

    mock_post_response = Mock()
    mock_post_response.post = Mock()
    mock_post_response.post.creator_id = "another_user"
    mock_post_stub.return_value.GetPost.return_value = mock_post_response

    response = client.get(
        f'/posts/{TEST_POST_ID}/dynamic?metric=views',
        headers={'Authorization': TEST_TOKEN}
    )

    assert response.status_code == 403
    data = json.loads(response.data)
    assert "message" in data
    assert data["message"] == "Only post creator can view post dynamics"


@pytest.mark.dependency()
def test_get_top_posts_success(client, mock_services):
    _, mock_stat_stub = mock_services

    mock_stat_response = statistic_pb2.TopPostsResponse(
        posts=[
            statistic_pb2.TopPost(post_id="post2", count=100),
            statistic_pb2.TopPost(post_id="post1", count=90)
        ]
    )
    mock_stat_stub.return_value.GetTopPosts.return_value = mock_stat_response

    response = client.get(
        '/posts/top?metric=views',
        headers={'Authorization': TEST_TOKEN}
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 2
    assert data[0]["post_id"] == "post2"
    assert data[0]["count"] == 100


@pytest.mark.dependency(depends=["test_get_top_posts_success"])
def test_get_top_posts_invalid_metric(client):
    response = client.get(
        '/posts/top?metric=invalid',
        headers={'Authorization': TEST_TOKEN}
    )

    assert response.status_code == 400
    data = json.loads(response.data)
    assert "message" in data
    assert data["message"] == "Invalid metric"


@pytest.mark.dependency()
def test_get_top_users_success(client, mock_services):
    _, mock_stat_stub = mock_services

    mock_stat_response = statistic_pb2.TopUsersResponse(
        users=[
            statistic_pb2.TopUser(user_id="user1", count=200),
            statistic_pb2.TopUser(user_id="user2", count=150)
        ]
    )
    mock_stat_stub.return_value.GetTopUsers.return_value = mock_stat_response

    response = client.get(
        '/users/top?metric=views',
        headers={'Authorization': TEST_TOKEN}
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 2
    assert data[0]["user_id"] == "user1"
    assert data[0]["count"] == 200


@pytest.mark.dependency(depends=["test_get_top_users_success"])
def test_get_top_users_invalid_metric(client):
    response = client.get(
        '/users/top?metric=invalid',
        headers={'Authorization': TEST_TOKEN}
    )

    assert response.status_code == 400
    data = json.loads(response.data)
    assert "message" in data
    assert data["message"] == "Invalid metric"


@pytest.mark.dependency(depends=["test_get_post_stats_success"])
def test_get_post_stats_unauthorized(client):
    response = client.get(f'/posts/{TEST_POST_ID}/stats')
    assert response.status_code == 401
    data = json.loads(response.data)
    assert "message" in data
    assert data["message"] == "Token is missing"


@pytest.mark.dependency(depends=["test_get_post_dynamic_success"])
def test_get_post_dynamic_unauthorized(client):
    response = client.get(f'/posts/{TEST_POST_ID}/dynamic')
    assert response.status_code == 401
    data = json.loads(response.data)
    assert "message" in data
    assert data["message"] == "Token is missing"


@pytest.mark.dependency(depends=["test_get_top_posts_success"])
def test_get_top_posts_unauthorized(client):
    response = client.get('/posts/top')
    assert response.status_code == 401
    data = json.loads(response.data)
    assert "message" in data
    assert data["message"] == "Token is missing"


@pytest.mark.dependency(depends=["test_get_top_users_success"])
def test_get_top_users_unauthorized(client):
    response = client.get('/users/top')
    assert response.status_code == 401
    data = json.loads(response.data)
    assert "message" in data
    assert data["message"] == "Token is missing"


@pytest.mark.dependency(depends=["test_get_post_stats_success"])
def test_get_post_stats_internal_error(client, mock_services):
    mock_post_stub, _ = mock_services

    mock_post_stub.return_value.GetPost.side_effect = Exception("Internal error")

    response = client.get(
        f'/posts/{TEST_POST_ID}/stats',
        headers={'Authorization': TEST_TOKEN}
    )

    assert response.status_code == 500
    data = json.loads(response.data)
    assert "message" in data
    assert data["message"] == "Internal server error"


@pytest.mark.dependency(depends=["test_get_post_dynamic_success"])
def test_get_post_dynamic_internal_error(client, mock_services):
    mock_post_stub, _ = mock_services

    mock_post_stub.return_value.GetPost.side_effect = Exception("Internal error")

    response = client.get(
        f'/posts/{TEST_POST_ID}/dynamic',
        headers={'Authorization': TEST_TOKEN}
    )

    assert response.status_code == 500
    data = json.loads(response.data)
    assert "message" in data
    assert data["message"] == "Internal server error"
