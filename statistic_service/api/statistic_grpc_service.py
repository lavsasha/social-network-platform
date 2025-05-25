import grpc
from proto import statistic_pb2, statistic_pb2_grpc
from db.statistic_db import StatisticDB


class StatisticServiceServicer(statistic_pb2_grpc.StatisticServiceServicer):
    def __init__(self, db: StatisticDB):
        self.db = db

    def GetPostStats(self, request, context):
        agg_sess = self.db.get_session()
        try:
            self.db.aggregate_events(agg_sess, request.post_id, request.user_id)
            agg_sess.commit()
        except Exception as e:
            agg_sess.rollback()
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"aggregate_events failed: {e}")
            return statistic_pb2.PostStatsResponse()
        finally:
            agg_sess.close()

        read_sess = self.db.get_session()
        try:
            stats = self.db.get_post_stats(read_sess, request.post_id)
            return statistic_pb2.PostStatsResponse(
                views_count=int(stats["views_count"]),
                likes_count=int(stats["likes_count"]),
                comments_count=int(stats["comments_count"]),
                updated_at=stats["updated_at"]
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"get_post_stats failed: {e}")
            return statistic_pb2.PostStatsResponse()
        finally:
            read_sess.close()

    def GetPostDynamic(self, request, context):
        agg_sess = self.db.get_session()
        try:
            self.db.aggregate_events(agg_sess, request.post_id, request.user_id)
            agg_sess.commit()
        except Exception as e:
            agg_sess.rollback()
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"aggregate_events failed: {e}")
            return statistic_pb2.PostDynamicResponse()
        finally:
            agg_sess.close()

        read_sess = self.db.get_session()
        try:
            metric_map = {
                statistic_pb2.PostDynamicRequest.VIEWS: 'views',
                statistic_pb2.PostDynamicRequest.LIKES: 'likes',
                statistic_pb2.PostDynamicRequest.COMMENTS: 'comments'
            }
            dynamic = self.db.get_post_dynamic(
                read_sess,
                post_id=request.post_id,
                metric=metric_map[request.metric]
            )

            return statistic_pb2.PostDynamicResponse(
                stats=[statistic_pb2.DailyStat(
                    date=item['date'],
                    count=item['count']
                ) for item in dynamic]
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"get_post_dynamic failed: {e}")
            return statistic_pb2.PostDynamicResponse()
        finally:
            read_sess.close()

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
