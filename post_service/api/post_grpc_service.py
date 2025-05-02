import grpc
from proto import post_pb2, post_pb2_grpc
from db.post_db import PostDB, PostDBError, AccessDeniedError, NotFoundError, OutOfRangeError, InvalidArgumentError
from sqlalchemy.exc import SQLAlchemyError
from broker.kafka_producer import kafka_producer


class PostServiceServicer(post_pb2_grpc.PostServiceServicer):
    def __init__(self, db: PostDB):
        self.db = db

    def _handle_errors(self, context, exception, error_code, response_type=None):
        context.set_code(error_code)
        context.set_details(str(exception))
        return response_type() if response_type else post_pb2.BaseResponse()

    def CreatePost(self, request, context):
        try:
            return self.db.create_post(request)
        except SQLAlchemyError as e:
            return self._handle_errors(context, e, grpc.StatusCode.INTERNAL, post_pb2.CreatePostResponse)
        except PostDBError as e:
            return self._handle_errors(context, e, grpc.StatusCode.INTERNAL, post_pb2.CreatePostResponse)

    def DeletePost(self, request, context):
        try:
            response = self.db.delete_post(request.post_id, request.user_id)
            return response
        except NotFoundError as e:
            return self._handle_errors(context, e, grpc.StatusCode.NOT_FOUND, post_pb2.DeletePostResponse)
        except SQLAlchemyError as e:
            return self._handle_errors(context, e, grpc.StatusCode.INTERNAL, post_pb2.DeletePostResponse)
        except PostDBError as e:
            return self._handle_errors(context, e, grpc.StatusCode.INTERNAL, post_pb2.DeletePostResponse)

    def UpdatePost(self, request, context):
        try:
            return self.db.update_post(request)
        except NotFoundError as e:
            return self._handle_errors(context, e, grpc.StatusCode.NOT_FOUND, post_pb2.UpdatePostResponse)
        except SQLAlchemyError as e:
            return self._handle_errors(context, e, grpc.StatusCode.INTERNAL, post_pb2.UpdatePostResponse)
        except PostDBError as e:
            return self._handle_errors(context, e, grpc.StatusCode.INTERNAL, post_pb2.UpdatePostResponse)

    def GetPost(self, request, context):
        try:
            return self.db.get_post(request.post_id, request.user_id)
        except NotFoundError as e:
            return self._handle_errors(context, e, grpc.StatusCode.NOT_FOUND, post_pb2.GetPostResponse)
        except InvalidArgumentError as e:
            return self._handle_errors(context, e, grpc.StatusCode.INVALID_ARGUMENT, post_pb2.GetPostResponse)
        except SQLAlchemyError as e:
            return self._handle_errors(context, e, grpc.StatusCode.INTERNAL, post_pb2.GetPostResponse)
        except PostDBError as e:
            return self._handle_errors(context, e, grpc.StatusCode.INTERNAL, post_pb2.GetPostResponse)

    def ListPosts(self, request, context):
        try:
            return self.db.list_posts(
                user_id=request.user_id,
                page=request.page,
                per_page=request.per_page
            )
        except OutOfRangeError as e:
            return self._handle_errors(context, e, grpc.StatusCode.OUT_OF_RANGE, post_pb2.ListPostsResponse)
        except InvalidArgumentError as e:
            return self._handle_errors(context, e, grpc.StatusCode.INVALID_ARGUMENT, post_pb2.ListPostsResponse)
        except SQLAlchemyError as e:
            return self._handle_errors(context, e, grpc.StatusCode.INTERNAL, post_pb2.ListPostsResponse)
        except PostDBError as e:
            return self._handle_errors(context, e, grpc.StatusCode.INTERNAL, post_pb2.ListPostsResponse)

    def ViewPost(self, request, context):
        try:
            result = self.db.increment_views_count(request.post_id, request.user_id)
            kafka_producer.send_post_viewed_event(request.user_id, request.post_id)
            return result
        except NotFoundError as e:
            return self._handle_errors(context, e, grpc.StatusCode.NOT_FOUND, post_pb2.ViewPostResponse)
        except AccessDeniedError as e:
            return self._handle_errors(context, e, grpc.StatusCode.PERMISSION_DENIED, post_pb2.ViewPostResponse)
        except PostDBError as e:
            return self._handle_errors(context, e, grpc.StatusCode.INTERNAL, post_pb2.ViewPostResponse)

    def LikePost(self, request, context):
        try:
            result = self.db.increment_likes_count(request.post_id, request.user_id)
            kafka_producer.send_post_liked_event(request.user_id, request.post_id)
            return result
        except NotFoundError as e:
            return self._handle_errors(context, e, grpc.StatusCode.NOT_FOUND, post_pb2.LikePostResponse)
        except AccessDeniedError as e:
            return self._handle_errors(context, e, grpc.StatusCode.PERMISSION_DENIED, post_pb2.LikePostResponse)
        except PostDBError as e:
            return self._handle_errors(context, e, grpc.StatusCode.INTERNAL, post_pb2.LikePostResponse)

    def CommentPost(self, request, context):
        try:
            if not request.comment.strip():
                raise InvalidArgumentError("Comment text cannot be empty")

            result = self.db.create_comment(request)
            kafka_producer.send_post_commented_event(
                user_id=request.user_id,
                post_id=request.post_id,
                comment_id=result.comment_id,
                text=request.comment[:100]
            )
            return result
        except NotFoundError as e:
            return self._handle_errors(context, e, grpc.StatusCode.NOT_FOUND, post_pb2.CommentPostResponse)
        except AccessDeniedError as e:
            return self._handle_errors(context, e, grpc.StatusCode.PERMISSION_DENIED, post_pb2.CommentPostResponse)
        except InvalidArgumentError as e:
            return self._handle_errors(context, e, grpc.StatusCode.INVALID_ARGUMENT, post_pb2.CommentPostResponse)
        except PostDBError as e:
            return self._handle_errors(context, e, grpc.StatusCode.INTERNAL, post_pb2.CommentPostResponse)

    def GetComments(self, request, context):
        try:
            return self.db.get_comments(
                request.post_id,
                request.user_id,
                request.page,
                request.per_page
            )
        except NotFoundError as e:
            return self._handle_errors(context, e, grpc.StatusCode.NOT_FOUND, post_pb2.GetCommentsResponse)
        except AccessDeniedError as e:
            return self._handle_errors(context, e, grpc.StatusCode.PERMISSION_DENIED, post_pb2.GetCommentsResponse)
        except OutOfRangeError as e:
            return self._handle_errors(context, e, grpc.StatusCode.OUT_OF_RANGE, post_pb2.GetCommentsResponse)
        except InvalidArgumentError as e:
            return self._handle_errors(context, e, grpc.StatusCode.INVALID_ARGUMENT, post_pb2.GetCommentsResponse)
        except PostDBError as e:
            return self._handle_errors(context, e, grpc.StatusCode.INTERNAL, post_pb2.GetCommentsResponse)
