from flask import Blueprint, request, Response, current_app
import grpc
import json
from collections import OrderedDict
from utils.auth import token_required
from proto import statistic_pb2, statistic_pb2_grpc, post_pb2, post_pb2_grpc

statistics_bp = Blueprint('statistics', __name__)


def get_statistic_stub():
    channel = grpc.insecure_channel(
        f"{current_app.config['STATISTIC_SERVICE_HOST']}:{current_app.config['STATISTIC_SERVICE_PORT']}"
    )
    return statistic_pb2_grpc.StatisticServiceStub(channel)


def get_post_stub():
    channel = grpc.insecure_channel(
        f"{current_app.config['POST_SERVICE_HOST']}:{current_app.config['POST_SERVICE_PORT']}"
    )
    return post_pb2_grpc.PostServiceStub(channel)


def get_post_creator_id(post_id: str, user_id: str) -> str:
    try:
        stub = get_post_stub()
        response = stub.GetPost(
            post_pb2.GetPostRequest(post_id=post_id, user_id=user_id)
        )
        return response.post.creator_id
    except grpc.RpcError as e:
        current_app.logger.error(f"Failed to get post creator: {e.details()}")
        raise


@statistics_bp.route('/posts/<post_id>/stats', methods=['GET'])
@token_required
def get_post_stats(user_id: str, post_id: str):
    try:
        creator_id = get_post_creator_id(post_id, user_id)
        stub = get_statistic_stub()
        response = stub.GetPostStats(
            statistic_pb2.PostStatsRequest(post_id=post_id, user_id=creator_id)
        )

        response_data = {
            "views_count": int(response.views_count),
            "likes_count": int(response.likes_count),
            "comments_count": int(response.comments_count),
            "updated_at": response.updated_at
        }

        return Response(
            json.dumps(response_data, ensure_ascii=False),
            200,
            mimetype='application/json'
        )
    except grpc.RpcError as e:
        error_data = {"error": e.details()}
        return Response(
            json.dumps(error_data, ensure_ascii=False),
            grpc_status_to_http(e.code()),
            mimetype='application/json'
        )
    except Exception as e:
        current_app.logger.error(f"Error in get_post_stats: {str(e)}")
        error_data = {"error": "Internal server error"}
        return Response(
            json.dumps(error_data, ensure_ascii=False),
            500,
            mimetype='application/json'
        )


@statistics_bp.route('/posts/<post_id>/dynamic', methods=['GET'])
@token_required
def get_post_dynamic(user_id: str, post_id: str):
    try:
        metric = request.args.get('metric', 'views')
        if metric not in ['views', 'likes', 'comments']:
            error_data = {"error": "Invalid metric"}
            return Response(
                json.dumps(error_data, ensure_ascii=False),
                400,
                mimetype='application/json'
            )

        creator_id = get_post_creator_id(post_id, user_id)
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
    except grpc.RpcError as e:
        error_data = {"error": e.details()}
        return Response(
            json.dumps(error_data, ensure_ascii=False),
            grpc_status_to_http(e.code()),
            mimetype='application/json'
        )
    except Exception as e:
        current_app.logger.error(f"Error in get_post_dynamic: {str(e)}")
        error_data = {"error": "Internal server error"}
        return Response(
            json.dumps(error_data, ensure_ascii=False),
            500,
            mimetype='application/json'
        )


@statistics_bp.route('/posts/top', methods=['GET'])
def get_top_posts():
    try:
        metric = request.args.get('metric', 'views')
        if metric not in ['views', 'likes', 'comments']:
            error_data = {"error": "Invalid metric"}
            return Response(
                json.dumps(error_data, ensure_ascii=False),
                400,
                mimetype='application/json'
            )

        metric_map = {
            'views': statistic_pb2.TopPostsRequest.VIEWS,
            'likes': statistic_pb2.TopPostsRequest.LIKES,
            'comments': statistic_pb2.TopPostsRequest.COMMENTS
        }

        stub = get_statistic_stub()
        response = stub.GetTopPosts(
            statistic_pb2.TopPostsRequest(metric=metric_map[metric])
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
    except grpc.RpcError as e:
        error_data = {"error": e.details()}
        return Response(
            json.dumps(error_data, ensure_ascii=False),
            grpc_status_to_http(e.code()),
            mimetype='application/json'
        )
    except Exception as e:
        current_app.logger.error(f"Error in get_top_posts: {str(e)}")
        error_data = {"error": "Internal server error"}
        return Response(
            json.dumps(error_data, ensure_ascii=False),
            500,
            mimetype='application/json'
        )


@statistics_bp.route('/users/top', methods=['GET'])
def get_top_users():
    try:
        metric = request.args.get('metric', 'views')
        if metric not in ['views', 'likes', 'comments']:
            error_data = {"error": "Invalid metric"}
            return Response(
                json.dumps(error_data, ensure_ascii=False),
                400,
                mimetype='application/json'
            )

        metric_map = {
            'views': statistic_pb2.TopUsersRequest.VIEWS,
            'likes': statistic_pb2.TopUsersRequest.LIKES,
            'comments': statistic_pb2.TopUsersRequest.COMMENTS
        }

        stub = get_statistic_stub()
        response = stub.GetTopUsers(
            statistic_pb2.TopUsersRequest(metric=metric_map[metric])
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
    except grpc.RpcError as e:
        error_data = {"error": e.details()}
        return Response(
            json.dumps(error_data, ensure_ascii=False),
            grpc_status_to_http(e.code()),
            mimetype='application/json'
        )
    except Exception as e:
        current_app.logger.error(f"Error in get_top_users: {str(e)}")
        error_data = {"error": "Internal server error"}
        return Response(
            json.dumps(error_data, ensure_ascii=False),
            500,
            mimetype='application/json'
        )


def grpc_status_to_http(grpc_code):
    mapping = {
        grpc.StatusCode.OK: 200,
        grpc.StatusCode.NOT_FOUND: 404,
        grpc.StatusCode.INVALID_ARGUMENT: 400,
        grpc.StatusCode.UNAUTHENTICATED: 401,
        grpc.StatusCode.PERMISSION_DENIED: 403,
        grpc.StatusCode.UNIMPLEMENTED: 501
    }
    return mapping.get(grpc_code, 500)
