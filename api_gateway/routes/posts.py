import grpc
import json
from collections import OrderedDict
from flask import Blueprint, request, jsonify, current_app, g, Response
from utils.auth import token_required
from utils.schemas import (
    PostCreate,
    PostUpdate,
    PostResponse,
    MetaResponse,
    ListPostsQuery,
    validate_post_id,
    simplify_validation_errors,
    InvalidPostID,
    ValidationError
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


@posts_bp.route('/posts', methods=['POST'])
@token_required
def create_post(user_id: str):
    try:
        data = PostCreate(**request.get_json())
    except ValidationError as e:
        return jsonify(simplify_validation_errors(e)), 400

    try:
        grpc_request = post_pb2.CreatePostRequest(
            title=data.title,
            description=data.description or "",
            creator_id=user_id,
            is_private=data.is_private,
            tags=data.tags
        )
        stub = get_grpc_stub()
        response = stub.CreatePost(grpc_request)
        return jsonify({
            "post_id": response.post_id,
            "created_at": response.created_at
        }), 201
    except grpc.RpcError as e:
        return handle_grpc_error(e)


@posts_bp.route('/posts/<post_id>', methods=['GET'])
@token_required
def get_post(user_id: str, post_id: str):
    try:
        post_id = validate_post_id(post_id)
        grpc_request = post_pb2.GetPostRequest(
            post_id=str(post_id),
            user_id=user_id
        )
        stub = get_grpc_stub()
        response = stub.GetPost(grpc_request)

        if not response.HasField('post'):
            return json.dumps({"message": "Post not found"}), 404, {'Content-Type': 'application/json'}

        response_data = OrderedDict([
            ("post_id", int(response.post.post_id)),
            ("title", response.post.title),
            ("description", response.post.description),
            ("creator_id", response.post.creator_id),
            ("created_at", response.post.created_at),
            ("updated_at", response.post.updated_at),
            ("is_private", response.post.is_private),
            ("tags", list(response.post.tags))
        ])

        return json.dumps(response_data, ensure_ascii=False), 200, {'Content-Type': 'application/json'}

    except InvalidPostID as e:
        return json.dumps({"message": str(e)}), 400, {'Content-Type': 'application/json'}
    except grpc.RpcError as e:
        error_response = handle_grpc_error(e)
        return json.dumps({"message": error_response[0].json["message"]}), error_response[1], {
            'Content-Type': 'application/json'}


@posts_bp.route('/posts/<post_id>', methods=['PUT'])
@token_required
def update_post(user_id: str, post_id: str):
    try:
        post_id = validate_post_id(post_id)
        data = PostUpdate(**request.get_json())
    except (ValidationError, InvalidPostID) as e:
        if isinstance(e, ValidationError):
            return jsonify(simplify_validation_errors(e)), 400
        return jsonify({"message": str(e)}), 400

    try:
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

        stub = get_grpc_stub()
        response = stub.UpdatePost(grpc_request)
        return jsonify({"updated_at": response.updated_at}), 200
    except grpc.RpcError as e:
        return handle_grpc_error(e)


@posts_bp.route('/posts/<post_id>', methods=['DELETE'])
@token_required
def delete_post(user_id: str, post_id: str):
    try:
        post_id = validate_post_id(post_id)
        grpc_request = post_pb2.DeletePostRequest(
            post_id=str(post_id),
            user_id=user_id
        )
        stub = get_grpc_stub()
        response = stub.DeletePost(grpc_request)
        return jsonify({"message": "Post deleted successfully."}), 200
    except InvalidPostID as e:
        return jsonify({"message": str(e)}), 400
    except grpc.RpcError as e:
        return handle_grpc_error(e)


@posts_bp.route('/posts', methods=['GET'])
@token_required
def list_posts(user_id: str):
    try:
        query = ListPostsQuery(
            page=request.args.get('page', 1, type=int),
            per_page=request.args.get('per_page', 10, type=int)
        )
    except ValidationError as e:
        return jsonify(simplify_validation_errors(e)), 400

    try:
        grpc_request = post_pb2.ListPostsRequest(
            user_id=user_id,
            page=query.page,
            per_page=query.per_page
        )
        stub = get_grpc_stub()
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

        response_data = OrderedDict([
            ("posts", posts),
            ("meta", meta)
        ])

        return Response(
            json.dumps(response_data, ensure_ascii=False, sort_keys=False),
            mimetype='application/json'
        ), 200

    except grpc.RpcError as e:
        return handle_grpc_error(e)
