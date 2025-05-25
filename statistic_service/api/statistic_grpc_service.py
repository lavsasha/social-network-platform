import grpc
from proto import statistic_pb2, statistic_pb2_grpc
from statistic_service.db.statistic_db import StatisticDB


class StatisticServiceServicer(statistic_pb2_grpc.StatisticServiceServicer):
    def __init__(self, db: StatisticDB):
        self.db = db

    def GetPostStats(self, request, context):
        session = self.db.get_session()
        try:
            self.db.aggregate_events(session, request.post_id, request.user_id)
            stats = self.db.get_post_stats(session, request.post_id)
            session.commit()

            return statistic_pb2.PostStatsResponse(
                views_count=int(stats["views_count"]),
                likes_count=int(stats["likes_count"]),
                comments_count=int(stats["comments_count"])
            )
        except Exception as e:
            session.rollback()
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Post stats operation failed: {e}")
            return statistic_pb2.PostStatsResponse()
        finally:
            session.close()

    def GetPostDynamic(self, request, context):
        session = self.db.get_session()
        try:
            self.db.aggregate_events(session, request.post_id, request.user_id)

            metric_map = {
                statistic_pb2.PostDynamicRequest.VIEWS: 'views',
                statistic_pb2.PostDynamicRequest.LIKES: 'likes',
                statistic_pb2.PostDynamicRequest.COMMENTS: 'comments'
            }

            dynamic = self.db.get_post_dynamic(
                session,
                post_id=request.post_id,
                metric=metric_map[request.metric]
            )

            session.commit()

            return statistic_pb2.PostDynamicResponse(
                stats=[statistic_pb2.DailyStat(
                    date=item['date'],
                    count=item['count']
                ) for item in dynamic]
            )
        except Exception as e:
            session.rollback()
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"get_post_dynamic failed: {e}")
            return statistic_pb2.PostDynamicResponse()
        finally:
            session.close()

    def GetTopPosts(self, request, context):
        session = self.db.get_session()
        try:
            metric_map = {
                statistic_pb2.TopPostsRequest.VIEWS: 'views',
                statistic_pb2.TopPostsRequest.LIKES: 'likes',
                statistic_pb2.TopPostsRequest.COMMENTS: 'comments'
            }
            top_posts = self.db.get_top_posts(
                session,
                metric=metric_map[request.metric]
            )

            return statistic_pb2.TopPostsResponse(
                posts=[statistic_pb2.TopPost(
                    post_id=item['post_id'],
                    count=item['count']
                ) for item in top_posts]
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"get_top_posts failed: {e}")
            return statistic_pb2.TopPostsResponse()
        finally:
            session.close()

    def GetTopUsers(self, request, context):
        session = self.db.get_session()
        try:
            metric_map = {
                statistic_pb2.TopUsersRequest.VIEWS: 'views',
                statistic_pb2.TopUsersRequest.LIKES: 'likes',
                statistic_pb2.TopUsersRequest.COMMENTS: 'comments'
            }
            top_users = self.db.get_top_users(
                session,
                metric=metric_map[request.metric]
            )

            return statistic_pb2.TopUsersResponse(
                users=[statistic_pb2.TopUser(
                    user_id=item['user_id'],
                    count=item['count']
                ) for item in top_users]
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"get_top_users failed: {e}")
            return statistic_pb2.TopUsersResponse()
        finally:
            session.close()

    def GetPostIds(self, request, context):
        session = self.db.get_session()
        try:
            post_ids = self.db.get_unique_post_ids(session)
            return statistic_pb2.GetPostIdsResponse(post_ids=post_ids)
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"get_post_ids failed: {e}")
            return statistic_pb2.GetPostIdsResponse()
        finally:
            session.close()
