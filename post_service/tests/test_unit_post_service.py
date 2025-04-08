import pytest
from unittest.mock import MagicMock, patch
import grpc
from datetime import datetime
from proto import post_pb2, post_pb2_grpc
from api.post_grpc_service import PostServiceServicer
from sqlalchemy.exc import SQLAlchemyError


class DummyContext:
    def __init__(self):
        self.code = None
        self.details = None

    def set_code(self, code):
        self.code = code

    def set_details(self, details):
        self.details = details


def fake_create_post(request):
    response = post_pb2.CreatePostResponse(
        post_id="1",
        created_at=datetime.utcnow().isoformat()
    )
    return response


def fake_delete_post(request):
    return True


def fake_update_post(request):
    response = post_pb2.UpdatePostResponse(
        updated_at=datetime.utcnow().isoformat()
    )
    return response


def fake_get_post(request):
    post = post_pb2.Post(
        post_id="1",
        title="Test Post",
        description="Test Description",
        creator_id=request.user_id,
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat(),
        is_private=False,
        tags=["test"]
    )
    return post_pb2.GetPostResponse(post=post)


def fake_list_posts(user_id, page, per_page):
    posts = [
        post_pb2.Post(
            post_id=str(i),
            title=f"Post {i}",
            creator_id=user_id,
            created_at=datetime.utcnow().isoformat(),
            is_private=False
        )
        for i in range(1, per_page + 1)
    ]
    return post_pb2.ListPostsResponse(
        posts=posts,
        total=10,
        page=page,
        per_page=per_page,
        last_page=2,
        from_=1,
        to_=per_page
    )


@pytest.fixture
def dummy_context():
    return DummyContext()


@pytest.fixture
def servicer():
    mock_db = MagicMock()
    return PostServiceServicer(mock_db), mock_db


def test_create_post_success(servicer, dummy_context):
    service, mock_db = servicer
    mock_db.create_post.return_value = fake_create_post(None)
    request = post_pb2.CreatePostRequest(
        title="Test Post",
        description="Test Description",
        creator_id="user123",
        is_private=False,
        tags=["test"]
    )
    response = service.CreatePost(request, dummy_context)
    assert response.post_id == "1"
    assert dummy_context.code is None


def test_create_post_db_error(servicer, dummy_context):
    service, mock_db = servicer
    mock_db.create_post.side_effect = SQLAlchemyError("DB error")
    request = post_pb2.CreatePostRequest(
        title="Test Post",
        description="Test Description",
        creator_id="user123",
        is_private=False,
        tags=["test"]
    )
    response = service.CreatePost(request, dummy_context)
    assert dummy_context.code == grpc.StatusCode.INTERNAL
    assert dummy_context.details == "DB error"


def test_delete_post_success(servicer, dummy_context):
    service, mock_db = servicer
    mock_db.delete_post.return_value = True
    request = post_pb2.DeletePostRequest(
        post_id="1",
        user_id="user123"
    )
    response = service.DeletePost(request, dummy_context)
    assert response.success is True
    assert dummy_context.code is None


def test_delete_post_not_found(servicer, dummy_context):
    service, mock_db = servicer
    mock_db.delete_post.return_value = False
    request = post_pb2.DeletePostRequest(
        post_id="1",
        user_id="user123"
    )
    response = service.DeletePost(request, dummy_context)
    assert dummy_context.code == grpc.StatusCode.NOT_FOUND
    assert dummy_context.details == "Post not found or permission denied"


def test_update_post_success(servicer, dummy_context):
    service, mock_db = servicer
    mock_db.update_post.return_value = fake_update_post(None)
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
    mock_db.update_post.return_value = None
    request = post_pb2.UpdatePostRequest(
        post_id="1",
        user_id="user123",
        title="Updated Post",
        description="Updated Description",
        is_private=True,
        tags=["update"]
    )
    response = service.UpdatePost(request, dummy_context)
    assert dummy_context.code == grpc.StatusCode.NOT_FOUND
    assert dummy_context.details == "Post not found or permission denied"


def test_get_post_success(servicer, dummy_context):
    service, mock_db = servicer
    mock_db.get_post.return_value = fake_get_post(post_pb2.GetPostRequest(
        post_id="1",
        user_id="user123"
    ))
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
    mock_db.get_post.return_value = None
    request = post_pb2.GetPostRequest(
        post_id="1",
        user_id="user123"
    )
    response = service.GetPost(request, dummy_context)
    assert dummy_context.code == grpc.StatusCode.NOT_FOUND
    assert dummy_context.details == "Post not found"


def test_list_posts_success(servicer, dummy_context):
    service, mock_db = servicer
    mock_db.list_posts.return_value = fake_list_posts("user123", page=1, per_page=5)
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
    mock_db.list_posts.side_effect = ValueError("Invalid pagination parameters")
    request = post_pb2.ListPostsRequest(
        user_id="user123",
        page=0,
        per_page=5
    )
    response = service.ListPosts(request, dummy_context)
    assert dummy_context.code == grpc.StatusCode.INVALID_ARGUMENT
    assert dummy_context.details == "Invalid pagination parameters"


def test_list_posts_internal_error(servicer, dummy_context):
    service, mock_db = servicer
    mock_db.list_posts.side_effect = Exception("Unexpected error")
    request = post_pb2.ListPostsRequest(
        user_id="user123",
        page=1,
        per_page=5
    )
    response = service.ListPosts(request, dummy_context)
    assert dummy_context.code == grpc.StatusCode.INTERNAL
    assert dummy_context.details == "Unexpected error"


def test_list_private_posts_for_owner(servicer, dummy_context):
    service, mock_db = servicer

    def mock_list_posts(user_id, page, per_page):
        posts = [
            post_pb2.Post(
                post_id="1",
                title="My Private Post",
                is_private=True,
                creator_id=user_id
            )
        ]
        return post_pb2.ListPostsResponse(
            posts=posts,
            total=1,
            page=1,
            per_page=10
        )

    mock_db.list_posts.side_effect = mock_list_posts

    request = post_pb2.ListPostsRequest(
        user_id="user123"
    )
    response = service.ListPosts(request, dummy_context)
    assert len(response.posts) == 1
    assert response.posts[0].is_private
