import pytest
import grpc
from unittest.mock import MagicMock, patch
from datetime import datetime
from proto import post_pb2
from api.post_grpc_service import PostServiceServicer
from db.post_db import PostDB, PostDBError, NotFoundError, InvalidArgumentError, OutOfRangeError, AccessDeniedError


class DummyContext:
    def __init__(self):
        self.code = None
        self.details = None

    def set_code(self, code):
        self.code = code

    def set_details(self, details):
        self.details = details


@pytest.fixture
def dummy_context():
    return DummyContext()


@pytest.fixture
def servicer_with_mock_kafka():
    mock_db = MagicMock()
    mock_kafka = MagicMock()
    with patch('api.post_grpc_service.kafka_producer', mock_kafka):
        servicer = PostServiceServicer(mock_db)
        yield servicer, mock_db, mock_kafka


def test_view_post_sends_kafka_event(servicer_with_mock_kafka):
    servicer, mock_db, mock_kafka = servicer_with_mock_kafka
    mock_db.increment_views_count.return_value = post_pb2.ViewPostResponse(success=True)

    request = post_pb2.ViewPostRequest(
        post_id="123",
        user_id="user456"
    )

    response = servicer.ViewPost(request, None)
    assert response.success is True
    mock_kafka.send_post_viewed_event.assert_called_once_with("user456", "123")


def test_like_post_sends_kafka_event(servicer_with_mock_kafka):
    servicer, mock_db, mock_kafka = servicer_with_mock_kafka
    mock_db.increment_likes_count.return_value = post_pb2.LikePostResponse(success=True)

    request = post_pb2.LikePostRequest(
        post_id="123",
        user_id="user456"
    )

    response = servicer.LikePost(request, None)
    assert response.success is True
    mock_kafka.send_post_liked_event.assert_called_once_with("user456", "123")


def test_comment_post_sends_kafka_event(servicer_with_mock_kafka):
    servicer, mock_db, mock_kafka = servicer_with_mock_kafka
    mock_db.create_comment.return_value = post_pb2.CommentPostResponse(
        comment_id="789",
        created_at=datetime.utcnow().isoformat()
    )

    request = post_pb2.CommentPostRequest(
        post_id="123",
        user_id="user456",
        comment="Test comment"
    )

    response = servicer.CommentPost(request, None)
    assert response.comment_id == "789"
    mock_kafka.send_post_commented_event.assert_called_once_with(
        user_id="user456",
        post_id="123",
        comment_id="789",
        text="Test comment"
    )


def test_view_post_not_found(servicer_with_mock_kafka, dummy_context):
    servicer, mock_db, mock_kafka = servicer_with_mock_kafka
    mock_db.increment_views_count.side_effect = NotFoundError("Post not found")

    request = post_pb2.ViewPostRequest(post_id="999", user_id="user1")
    response = servicer.ViewPost(request, dummy_context)

    assert dummy_context.code == grpc.StatusCode.NOT_FOUND
    mock_kafka.send_post_viewed_event.assert_not_called()


def test_like_post_db_error(servicer_with_mock_kafka, dummy_context):
    servicer, mock_db, mock_kafka = servicer_with_mock_kafka
    mock_db.increment_likes_count.side_effect = PostDBError("DB error")

    request = post_pb2.LikePostRequest(post_id="123", user_id="user1")
    response = servicer.LikePost(request, dummy_context)

    assert dummy_context.code == grpc.StatusCode.INTERNAL
    mock_kafka.send_post_liked_event.assert_not_called()


def test_comment_post_empty_text(servicer_with_mock_kafka, dummy_context):
    servicer, mock_db, mock_kafka = servicer_with_mock_kafka

    request = post_pb2.CommentPostRequest(post_id="123", user_id="user1", comment="")
    response = servicer.CommentPost(request, dummy_context)

    assert dummy_context.code == grpc.StatusCode.INVALID_ARGUMENT
    mock_kafka.send_post_commented_event.assert_not_called()
