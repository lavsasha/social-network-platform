from flask import Blueprint, request, Response, current_app, g, jsonify
import grpc
import json
from collections import OrderedDict
from functools import wraps
from proto import statistic_pb2, statistic_pb2_grpc, post_pb2, post_pb2_grpc

try:
    from utils.auth import token_required
except ImportError:
    from ..utils.auth import token_required

statistics_bp = Blueprint('statistics', __name__)


def get_statistic_stub():
    if "statistic_stub" not in g:
        channel = grpc.insecure_channel(
            f"{current_app.config['STATISTIC_SERVICE_HOST']}:{current_app.config['STATISTIC_SERVICE_PORT']}"
        )
        g.statistic_stub = statistic_pb2_grpc.StatisticServiceStub(channel)
    return g.statistic_stub


def get_post_stub():
    if "post_stub" not in g:
        channel = grpc.insecure_channel(
            f"{current_app.config['POST_SERVICE_HOST']}:{current_app.config['POST_SERVICE_PORT']}"
        )
        g.post_stub = post_pb2_grpc.PostServiceStub(channel)
    return g.post_stub


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


def handle_errors(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except grpc.RpcError as e:
            return handle_grpc_error(e)
        except Exception:
            return jsonify({"message": "Internal server error"}), 500

    return wrapper


def get_post_creator_id(post_id: str, user_id: str) -> str:
    stub = get_post_stub()
    grpc_request = post_pb2.GetPostRequest(
        post_id=post_id,
        user_id=user_id
    )
    response = stub.GetPost(grpc_request)
    if not response.HasField('post'):
        raise grpc.RpcError(grpc.StatusCode.NOT_FOUND, "Post not found")
    return response.post.creator_id


@statistics_bp.route('/posts/<post_id>/stats', methods=['GET'])
@token_required
@handle_errors
def get_post_stats(user_id: str, post_id: str):
    creator_id = get_post_creator_id(post_id, user_id)
    stub = get_statistic_stub()
    response = stub.GetPostStats(
        statistic_pb2.PostStatsRequest(post_id=post_id, user_id=creator_id)
    )

    return Response(
        json.dumps(OrderedDict([
            ("views_count", response.views_count),
            ("likes_count", response.likes_count),
            ("comments_count", response.comments_count)
        ]), ensure_ascii=False),
        200,
        mimetype='application/json'
    )


@statistics_bp.route('/posts/<post_id>/dynamic', methods=['GET'])
@token_required
@handle_errors
def get_post_dynamic(user_id: str, post_id: str):
    creator_id = get_post_creator_id(post_id, user_id)
    if creator_id != user_id:
        return jsonify({"message": "Only post creator can view post dynamics"}), 403

    metric = request.args.get('metric', 'views')
    if metric not in ['views', 'likes', 'comments']:
        return jsonify({"message": "Invalid metric"}), 400

    metric_map = {
        'views': statistic_pb2.PostDynamicRequest.VIEWS,
        'likes': statistic_pb2.PostDynamicRequest.LIKES,
        'comments': statistic_pb2.PostDynamicRequest.COMMENTS
    }

    stub = get_statistic_stub()
    response = stub.GetPostDynamic(
        statistic_pb2.PostDynamicRequest(
            post_id=post_id,
            metric=metric_map[metric],
            user_id=creator_id
        )
    )

    stats = [
        OrderedDict([
            ("date", stat.date),
            ("count", stat.count)
        ])
        for stat in response.stats
    ]

    return Response(
        json.dumps(stats, ensure_ascii=False),
        200,
        mimetype='application/json'
    )


@statistics_bp.route('/posts/top', methods=['GET'])
@token_required
@handle_errors
def get_top_posts(user_id: str):
    metric = request.args.get('metric', 'views')
    if metric not in ['views', 'likes', 'comments']:
        return jsonify({"message": "Invalid metric"}), 400

    metric_map = {
        'views': statistic_pb2.TopPostsRequest.VIEWS,
        'likes': statistic_pb2.TopPostsRequest.LIKES,
        'comments': statistic_pb2.TopPostsRequest.COMMENTS
    }

    stub = get_statistic_stub()
    response = stub.GetTopPosts(
        statistic_pb2.TopPostsRequest(metric=metric_map[metric], user_id=user_id)
    )

    posts = [
        OrderedDict([
            ("post_id", post.post_id),
            ("count", post.count)
        ])
        for post in response.posts
    ]

    return Response(
        json.dumps(posts, ensure_ascii=False),
        200,
        mimetype='application/json'
    )


@statistics_bp.route('/users/top', methods=['GET'])
@token_required
@handle_errors
def get_top_users(user_id: str):
    metric = request.args.get('metric', 'views')
    if metric not in ['views', 'likes', 'comments']:
        return jsonify({"message": "Invalid metric"}), 400

    metric_map = {
        'views': statistic_pb2.TopUsersRequest.VIEWS,
        'likes': statistic_pb2.TopUsersRequest.LIKES,
        'comments': statistic_pb2.TopUsersRequest.COMMENTS
    }

    stub = get_statistic_stub()
    response = stub.GetTopUsers(
        statistic_pb2.TopUsersRequest(metric=metric_map[metric], user_id=user_id)
    )

    users = [
        OrderedDict([
            ("user_id", user.user_id),
            ("count", user.count)
        ])
        for user in response.users
    ]

    return Response(
        json.dumps(users, ensure_ascii=False),
        200,
        mimetype='application/json'
    )
