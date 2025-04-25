import pytest
from unittest.mock import MagicMock, patch
import grpc
from datetime import datetime
from proto import post_pb2, post_pb2_grpc
from db.post_db import PostDB, PostDBError, NotFoundError, InvalidArgumentError, OutOfRangeError, AccessDeniedError

mock_kafka_producer = MagicMock()
with patch.dict('sys.modules', {'broker.kafka_producer': mock_kafka_producer}):
    from api.post_grpc_service import PostServiceServicer


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
def servicer():
    mock_db = MagicMock(spec=PostDB)
    return PostServiceServicer(mock_db), mock_db


def test_delete_post_success(servicer, dummy_context):
    service, mock_db = servicer
    mock_db.delete_post.return_value = post_pb2.DeletePostResponse(success=True)
    request = post_pb2.DeletePostRequest(
        post_id="1",
        user_id="user123"
    )
    response = service.DeletePost(request, dummy_context)
    assert response.success is True
    assert dummy_context.code is None


def test_delete_post_not_found(servicer, dummy_context):
    service, mock_db = servicer
    mock_db.delete_post.side_effect = NotFoundError("Post not found")
    request = post_pb2.DeletePostRequest(
        post_id="1",
        user_id="user123"
    )
    response = service.DeletePost(request, dummy_context)
    assert isinstance(response, post_pb2.DeletePostResponse)
    assert dummy_context.code == grpc.StatusCode.NOT_FOUND
    assert "Post not found" in dummy_context.details


def test_update_post_success(servicer, dummy_context):
    service, mock_db = servicer
    mock_db.update_post.return_value = post_pb2.UpdatePostResponse(
        updated_at=datetime.utcnow().isoformat()
    )
    request = post_pb2.UpdatePostRequest(
        post_id="1",
        user_id="user123",
        title="Updated Post",
        description="Updated Description",
        is_private=True,
        tags=["update"]
    )
    response = service.UpdatePost(request, dummy_context)
    assert hasattr(response, "updated_at")
    assert dummy_context.code is None


def test_update_post_not_found(servicer, dummy_context):
    service, mock_db = servicer
    mock_db.update_post.side_effect = NotFoundError("Post not found")
    request = post_pb2.UpdatePostRequest(
        post_id="1",
        user_id="user123",
        title="Updated Post",
        description="Updated Description",
        is_private=True,
        tags=["update"]
    )
    response = service.UpdatePost(request, dummy_context)
    assert isinstance(response, post_pb2.UpdatePostResponse)
    assert dummy_context.code == grpc.StatusCode.NOT_FOUND
    assert "Post not found" in dummy_context.details


def test_get_post_success(servicer, dummy_context):
    service, mock_db = servicer
    mock_db.get_post.return_value = post_pb2.GetPostResponse(
        post=post_pb2.Post(
            post_id="1",
            title="Test Post",
            description="Test Description",
            creator_id="user123",
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
            is_private=False,
            tags=["test"]
        )
    )
    request = post_pb2.GetPostRequest(
        post_id="1",
        user_id="user123"
    )
    response = service.GetPost(request, dummy_context)
    assert response.HasField("post")
    assert response.post.title == "Test Post"
    assert dummy_context.code is None


def test_get_post_not_found(servicer, dummy_context):
    service, mock_db = servicer
    mock_db.get_post.side_effect = NotFoundError("Post not found")
    request = post_pb2.GetPostRequest(
        post_id="1",
        user_id="user123"
    )
    response = service.GetPost(request, dummy_context)
    assert isinstance(response, post_pb2.GetPostResponse)
    assert dummy_context.code == grpc.StatusCode.NOT_FOUND
    assert "Post not found" in dummy_context.details


def test_list_posts_success(servicer, dummy_context):
    service, mock_db = servicer
    mock_response = post_pb2.ListPostsResponse(
        posts=[post_pb2.Post(
            post_id=str(i),
            title=f"Post {i}",
            creator_id="user123",
            created_at=datetime.utcnow().isoformat(),
            is_private=False
        ) for i in range(1, 6)],
        total=10,
        page=1,
        per_page=5,
        last_page=2,
        from_=1,
        to_=5
    )
    mock_db.list_posts.return_value = mock_response
    request = post_pb2.ListPostsRequest(
        user_id="user123",
        page=1,
        per_page=5
    )
    response = service.ListPosts(request, dummy_context)
    assert response.total == 10
    assert response.page == 1
    assert len(response.posts) == 5
    assert dummy_context.code is None


def test_list_posts_invalid_argument(servicer, dummy_context):
    service, mock_db = servicer
    mock_db.list_posts.side_effect = InvalidArgumentError("Invalid pagination parameters")
    request = post_pb2.ListPostsRequest(
        user_id="user123",
        page=0,
        per_page=5
    )
    response = service.ListPosts(request, dummy_context)
    assert isinstance(response, post_pb2.ListPostsResponse)
    assert dummy_context.code == grpc.StatusCode.INVALID_ARGUMENT
    assert "Invalid pagination parameters" in dummy_context.details


def test_list_posts_internal_error(servicer, dummy_context):
    service, mock_db = servicer
    mock_db.list_posts.side_effect = PostDBError("Unexpected error")
    request = post_pb2.ListPostsRequest(
        user_id="user123",
        page=1,
        per_page=5
    )
    response = service.ListPosts(request, dummy_context)
    assert isinstance(response, post_pb2.ListPostsResponse)
    assert dummy_context.code == grpc.StatusCode.INTERNAL
    assert "Unexpected error" in dummy_context.details


def test_list_private_posts_for_owner(servicer, dummy_context):
    service, mock_db = servicer
    mock_response = post_pb2.ListPostsResponse(
        posts=[post_pb2.Post(
            post_id="1",
            title="My Private Post",
            is_private=True,
            creator_id="user123"
        )],
        total=1,
        page=1,
        per_page=10
    )
    mock_db.list_posts.return_value = mock_response
    request = post_pb2.ListPostsRequest(
        user_id="user123"
    )
    response = service.ListPosts(request, dummy_context)
    assert len(response.posts) == 1
    assert response.posts[0].is_private


def test_get_comments_success(servicer, dummy_context):
    service, mock_db = servicer

    mock_response = post_pb2.GetCommentsResponse(
        comments=[
            post_pb2.Comment(
                comment_id="1",
                text="Test comment",
                user_id="user123",
                created_at="2023-01-01T00:00:00"
            )
        ],
        meta=post_pb2.Meta(
            total=1,
            page=1,
            per_page=10,
            last_page=1
        )
    )
    mock_db.get_comments.return_value = mock_response

    request = post_pb2.GetCommentsRequest(
        post_id="123",
        user_id="user123",
        page=1,
        per_page=10
    )
    response = service.GetComments(request, dummy_context)

    assert len(response.comments) == 1
    assert response.comments[0].text == "Test comment"
    assert response.meta.total == 1
    assert dummy_context.code is None


def test_get_comments_not_found(servicer, dummy_context):
    service, mock_db = servicer
    mock_db.get_comments.side_effect = NotFoundError("Post not found")

    request = post_pb2.GetCommentsRequest(
        post_id="123",
        user_id="user123"
    )
    response = service.GetComments(request, dummy_context)

    assert isinstance(response, post_pb2.GetCommentsResponse)
    assert dummy_context.code == grpc.StatusCode.NOT_FOUND
    assert "Post not found" in dummy_context.details


def test_get_comments_pagination_error(servicer, dummy_context):
    service, mock_db = servicer
    mock_db.get_comments.side_effect = OutOfRangeError("Invalid page")

    request = post_pb2.GetCommentsRequest(
        post_id="123",
        user_id="user123",
        page=999,
        per_page=10
    )
    response = service.GetComments(request, dummy_context)

    assert isinstance(response, post_pb2.GetCommentsResponse)
    assert dummy_context.code == grpc.StatusCode.OUT_OF_RANGE
    assert "Invalid page" in dummy_context.details


def test_get_comments_access_denied(servicer, dummy_context):
    service, mock_db = servicer
    mock_db.get_comments.side_effect = AccessDeniedError("Access denied")

    request = post_pb2.GetCommentsRequest(
        post_id="123",
        user_id="user123"
    )
    response = service.GetComments(request, dummy_context)

    assert isinstance(response, post_pb2.GetCommentsResponse)
    assert dummy_context.code == grpc.StatusCode.PERMISSION_DENIED
    assert "Access denied" in dummy_context.details


def test_get_comments_pagination_params(servicer, dummy_context):
    service, mock_db = servicer

    request = post_pb2.GetCommentsRequest(
        post_id="123",
        user_id="user123",
        page=2,
        per_page=5
    )

    service.GetComments(request, dummy_context)
    mock_db.get_comments.assert_called_with("123", "user123", 2, 5)


def test_get_comments_invalid_arguments(servicer, dummy_context):
    service, mock_db = servicer
    mock_db.get_comments.side_effect = InvalidArgumentError("Invalid arguments")

    request = post_pb2.GetCommentsRequest(
        post_id="123",
        user_id="user123",
        page=0,
        per_page=0
    )

    response = service.GetComments(request, dummy_context)
    assert dummy_context.code == grpc.StatusCode.INVALID_ARGUMENT
