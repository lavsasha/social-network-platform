import grpc
from proto import post_pb2, post_pb2_grpc
from db.post_db import PostDB
from sqlalchemy.exc import SQLAlchemyError


class PostServiceServicer(post_pb2_grpc.PostServiceServicer):
    def __init__(self, db: PostDB):
        self.db = db

    def _handle_errors(self, context, exception, error_code, message=None, response_type=None):
        context.set_code(error_code)
        context.set_details(message or str(exception))
        return response_type() if response_type else post_pb2.BaseResponse()

    def CreatePost(self, request, context):
        try:
            return self.db.create_post(request)
        except SQLAlchemyError as e:
            return self._handle_errors(
                context,
                e,
                grpc.StatusCode.INTERNAL,
                response_type=post_pb2.CreatePostResponse
            )

    def DeletePost(self, request, context):
        try:
            if not self.db.delete_post(request.post_id, request.user_id):
                return self._handle_errors(
                    context,
                    None,
                    grpc.StatusCode.NOT_FOUND,
                    "Post not found or permission denied",
                    response_type=post_pb2.DeletePostResponse
                )
            return post_pb2.DeletePostResponse(success=True)
        except SQLAlchemyError as e:
            return self._handle_errors(
                context,
                e,
                grpc.StatusCode.INTERNAL,
                response_type=post_pb2.DeletePostResponse
            )

    def UpdatePost(self, request, context):
        try:
            response = self.db.update_post(request)
            if not response:
                return self._handle_errors(
                    context,
                    None,
                    grpc.StatusCode.NOT_FOUND,
                    "Post not found or permission denied",
                    response_type=post_pb2.UpdatePostResponse
                )
            return response
        except SQLAlchemyError as e:
            return self._handle_errors(
                context,
                e,
                grpc.StatusCode.INTERNAL,
                response_type=post_pb2.UpdatePostResponse
            )

    def GetPost(self, request, context):
        try:
            response = self.db.get_post(request.post_id, request.user_id)
            if not response or not response.post:
                return self._handle_errors(
                    context,
                    None,
                    grpc.StatusCode.NOT_FOUND,
                    "Post not found",
                    response_type=post_pb2.GetPostResponse
                )
            return response
        except Exception as e:
            return self._handle_errors(
                context,
                e,
                grpc.StatusCode.INTERNAL,
                response_type=post_pb2.GetPostResponse
            )

    def ListPosts(self, request, context):
        try:
            return self.db.list_posts(
                user_id=request.user_id,
                page=request.page,
                per_page=request.per_page
            )
        except ValueError as e:
            if "out of range" in str(e):
                return self._handle_errors(
                    context,
                    e,
                    grpc.StatusCode.OUT_OF_RANGE,
                    response_type=post_pb2.ListPostsResponse
                )
            else:
                return self._handle_errors(
                    context,
                    e,
                    grpc.StatusCode.INVALID_ARGUMENT,
                    response_type=post_pb2.ListPostsResponse
                )
        except SQLAlchemyError as e:
            return self._handle_errors(
                context,
                e,
                grpc.StatusCode.INTERNAL,
                response_type=post_pb2.ListPostsResponse
            )
        except Exception as e:
            return self._handle_errors(
                context,
                e,
                grpc.StatusCode.INTERNAL,
                response_type=post_pb2.ListPostsResponse
            )
