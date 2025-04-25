import grpc
import json
from datetime import datetime
from collections import OrderedDict
from flask import Blueprint, request, jsonify, current_app, g, Response
from functools import wraps
from utils.auth import token_required
from utils.schemas import (
    PostCreate,
    PostUpdate,
    PostResponse,
    MetaResponse,
    ListQuery,
    validate_post_id,
    simplify_validation_errors,
    InvalidPostID,
    ValidationError,
    CommentCreate
)
from proto import post_pb2, post_pb2_grpc

posts_bp = Blueprint('posts', __name__)


def get_grpc_stub():
    if "grpc_stub" not in g:
        channel = grpc.insecure_channel(
            f"{current_app.config['POST_SERVICE_HOST']}:{current_app.config['POST_SERVICE_PORT']}"
        )
        g.grpc_stub = post_pb2_grpc.PostServiceStub(channel)
    return g.grpc_stub


def handle_grpc_error(error: grpc.RpcError):
    error_message = error.details()
    if error.code() == grpc.StatusCode.OUT_OF_RANGE:
        return jsonify({"message": error_message}), 400
    error_map = {
        grpc.StatusCode.NOT_FOUND: (404, error_message),
        grpc.StatusCode.PERMISSION_DENIED: (403, error_message),
        grpc.StatusCode.INVALID_ARGUMENT: (400, error_message),
        grpc.StatusCode.UNAUTHENTICATED: (401, error_message),
        grpc.StatusCode.INTERNAL: (500, "Internal server error")
    }
    status_code, message = error_map.get(error.code(), (500, "Internal server error"))
    return jsonify({"message": message}), status_code


@posts_bp.errorhandler(InvalidPostID)
def handle_invalid_post_id(error):
    return jsonify({"message": str(error)}), 400


def handle_errors(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValidationError as e:
            return jsonify(simplify_validation_errors(e)), 400
        except InvalidPostID as e:
            return jsonify({"message": str(e)}), 400
        except grpc.RpcError as e:
            return handle_grpc_error(e)
        except Exception:
            return jsonify({"message": "Internal server error"}), 500
    return wrapper


@posts_bp.route('/posts', methods=['POST'])
@token_required
@handle_errors
def create_post(user_id: str):
    data = PostCreate(**request.get_json())
    stub = get_grpc_stub()
    grpc_request = post_pb2.CreatePostRequest(
        title=data.title,
        description=data.description or "",
        creator_id=user_id,
        is_private=data.is_private,
        tags=data.tags
    )
    response = stub.CreatePost(grpc_request)

    return Response(
        json.dumps(OrderedDict([
            ("post_id", int(response.post_id)),
            ("created_at", response.created_at)
        ]), ensure_ascii=False),
        201,
        {'Content-Type': 'application/json'}
    )


@posts_bp.route('/posts/<post_id>', methods=['GET'])
@token_required
@handle_errors
def get_post(user_id: str, post_id: str):
    post_id = validate_post_id(post_id)
    stub = get_grpc_stub()
    grpc_request = post_pb2.GetPostRequest(
        post_id=str(post_id),
        user_id=user_id
    )
    response = stub.GetPost(grpc_request)

    if not response.HasField('post'):
        return jsonify({"message": "Post not found"}), 404

    return Response(
        json.dumps(OrderedDict([
            ("post_id", int(response.post.post_id)),
            ("title", response.post.title),
            ("description", response.post.description),
            ("creator_id", response.post.creator_id),
            ("created_at", response.post.created_at),
            ("updated_at", response.post.updated_at),
            ("is_private", response.post.is_private),
            ("tags", list(response.post.tags))
        ]), ensure_ascii=False),
        200,
        {'Content-Type': 'application/json'}
    )


@posts_bp.route('/posts/<post_id>', methods=['PUT'])
@token_required
@handle_errors
def update_post(user_id: str, post_id: str):
    post_id = validate_post_id(post_id)
    data = PostUpdate(**request.get_json())
    stub = get_grpc_stub()
    update_fields = {}
    if data.title is not None:
        update_fields['title'] = data.title
    if data.description is not None:
        update_fields['description'] = data.description
    if data.is_private is not None:
        update_fields['is_private'] = data.is_private
    if data.tags is not None:
        update_fields['tags'] = data.tags

    grpc_request = post_pb2.UpdatePostRequest(
        post_id=str(post_id),
        user_id=user_id,
        **update_fields
    )
    response = stub.UpdatePost(grpc_request)
    return jsonify({"updated_at": response.updated_at}), 200


@posts_bp.route('/posts/<post_id>', methods=['DELETE'])
@token_required
@handle_errors
def delete_post(user_id: str, post_id: str):
    post_id = validate_post_id(post_id)
    stub = get_grpc_stub()
    grpc_request = post_pb2.DeletePostRequest(
        post_id=str(post_id),
        user_id=user_id
    )
    stub.DeletePost(grpc_request)
    return jsonify({"message": "Post deleted successfully."}), 200


@posts_bp.route('/posts', methods=['GET'])
@token_required
@handle_errors
def list_posts(user_id: str):
    query = ListQuery(
        page=request.args.get('page', 1, type=int),
        per_page=request.args.get('per_page', 10, type=int)
    )
    stub = get_grpc_stub()
    grpc_request = post_pb2.ListPostsRequest(
        user_id=user_id,
        page=query.page,
        per_page=query.per_page
    )
    response = stub.ListPosts(grpc_request)

    meta = MetaResponse(
        total=response.total,
        per_page=response.per_page,
        current_page=response.page,
        last_page=response.last_page,
        from_=response.from_,
        to_=response.to_
    ).dict(by_alias=True)

    posts = [
        PostResponse(
            post_id=int(post.post_id),
            title=post.title,
            description=post.description,
            creator_id=post.creator_id,
            created_at=post.created_at,
            updated_at=post.updated_at,
            is_private=post.is_private,
            tags=list(post.tags)
        ).dict()
        for post in response.posts
    ]

    return Response(
        json.dumps(OrderedDict([
            ("posts", posts),
            ("meta", meta)
        ]), ensure_ascii=False, sort_keys=False),
        200,
        mimetype='application/json'
    )


@posts_bp.route('/posts/<post_id>/view', methods=['POST'])
@token_required
@handle_errors
def view_post(user_id: str, post_id: str):
    post_id = validate_post_id(post_id)
    stub = get_grpc_stub()
    grpc_request = post_pb2.ViewPostRequest(
        post_id=str(post_id),
        user_id=user_id
    )
    response = stub.ViewPost(grpc_request)

    response_data = OrderedDict([
        ("success", response.success),
        ("viewed_at", datetime.utcnow().isoformat())
    ])

    return Response(
        json.dumps(response_data, ensure_ascii=False),
        200,
        mimetype='application/json'
    )


@posts_bp.route('/posts/<post_id>/like', methods=['POST'])
@token_required
@handle_errors
def like_post(user_id: str, post_id: str):
    post_id = validate_post_id(post_id)
    stub = get_grpc_stub()
    grpc_request = post_pb2.LikePostRequest(
        post_id=str(post_id),
        user_id=user_id
    )
    response = stub.LikePost(grpc_request)

    response_data = OrderedDict([
        ("success", response.success),
        ("liked_at", datetime.utcnow().isoformat())
    ])

    return Response(
        json.dumps(response_data, ensure_ascii=False),
        200,
        mimetype='application/json'
    )


@posts_bp.route('/posts/<post_id>/comment', methods=['POST'])
@token_required
@handle_errors
def comment_post(user_id: str, post_id: str):
    post_id = validate_post_id(post_id)
    data = CommentCreate(**request.get_json())
    stub = get_grpc_stub()
    grpc_request = post_pb2.CommentPostRequest(
        post_id=str(post_id),
        user_id=user_id,
        comment=data.text
    )
    response = stub.CommentPost(grpc_request)

    return jsonify({
        "comment_id": int(response.comment_id),
        "created_at": response.created_at
    }), 201


@posts_bp.route('/posts/<post_id>/comments', methods=['GET'])
@token_required
@handle_errors
def get_comments(user_id: str, post_id: str):
    post_id = validate_post_id(post_id)
    query = ListQuery(
        page=request.args.get('page', 1, type=int),
        per_page=request.args.get('per_page', 10, type=int)
    )
    stub = get_grpc_stub()
    grpc_request = post_pb2.GetCommentsRequest(
        post_id=str(post_id),
        user_id=user_id,
        page=query.page,
        per_page=query.per_page
    )
    response = stub.GetComments(grpc_request)

    comments = [
        OrderedDict([
            ("comment_id", int(comment.comment_id)),
            ("text", comment.text),
            ("user_id", comment.user_id),
            ("created_at", comment.created_at)
        ])
        for comment in response.comments
    ]

    meta = OrderedDict([
        ("total", response.meta.total),
        ("page", response.meta.page),
        ("per_page", response.meta.per_page),
        ("last_page", response.meta.last_page)
    ])

    return Response(
        json.dumps(OrderedDict([
            ("comments", comments),
            ("meta", meta)
        ]), ensure_ascii=False, sort_keys=False),
        200,
        mimetype='application/json'
    )
