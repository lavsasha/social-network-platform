import pytest
from unittest.mock import Mock
import grpc
import sys
import os

PROTO_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'proto'))
sys.path.insert(0, PROTO_PATH)

from proto import statistic_pb2, statistic_pb2_grpc
from statistic_service.api.statistic_grpc_service import StatisticServiceServicer
from statistic_service.db.statistic_db import StatisticDB

TEST_POST_ID = "test_post_1"
TEST_USER_ID = "test_user_1"
TEST_POST_IDS = ["post1", "post2", "post3"]
TEST_DAILY_STATS = [
    {"date": "2023-01-01", "count": 10},
    {"date": "2023-01-02", "count": 20}
]


@pytest.fixture
def mock_db():
    db = Mock(spec=StatisticDB)
    db.get_session.return_value = Mock()
    db.get_post_stats.return_value = {
        "views_count": 100,
        "likes_count": 50,
        "comments_count": 30
    }
    db.get_post_dynamic.return_value = TEST_DAILY_STATS
    db.get_top_posts.return_value = [
        {"post_id": "post1", "count": 100},
        {"post_id": "post2", "count": 90}
    ]
    db.get_top_users.return_value = [
        {"user_id": "user1", "count": 200},
        {"user_id": "user2", "count": 150}
    ]
    db.get_unique_post_ids.return_value = TEST_POST_IDS
    return db


@pytest.fixture
def statistic_service(mock_db):
    return StatisticServiceServicer(mock_db)


class TestGetPostStats:
    def test_success(self, statistic_service, mock_db):
        request = statistic_pb2.PostStatsRequest(
            post_id=TEST_POST_ID,
            user_id=TEST_USER_ID
        )
        context = Mock()

        response = statistic_service.GetPostStats(request, context)

        assert response.views_count == 100
        assert response.likes_count == 50
        assert response.comments_count == 30
        mock_db.aggregate_events.assert_called_once()
        mock_db.get_post_stats.assert_called_once()

    def test_db_error(self, statistic_service, mock_db):
        mock_db.aggregate_events.side_effect = Exception("DB error")
        request = statistic_pb2.PostStatsRequest(
            post_id=TEST_POST_ID,
            user_id=TEST_USER_ID
        )
        context = Mock()

        response = statistic_service.GetPostStats(request, context)

        assert response == statistic_pb2.PostStatsResponse()
        context.set_code.assert_called_with(grpc.StatusCode.INTERNAL)


class TestGetPostDynamic:
    def test_success(self, statistic_service, mock_db):
        request = statistic_pb2.PostDynamicRequest(
            post_id=TEST_POST_ID,
            user_id=TEST_USER_ID,
            metric=statistic_pb2.PostDynamicRequest.VIEWS
        )
        context = Mock()

        response = statistic_service.GetPostDynamic(request, context)

        assert len(response.stats) == 2
        assert response.stats[0].date == "2023-01-01"
        assert response.stats[0].count == 10
        mock_db.aggregate_events.assert_called_once()
        mock_db.get_post_dynamic.assert_called_once()

    def test_invalid_metric(self, statistic_service, mock_db):
        request = statistic_pb2.PostDynamicRequest(
            post_id=TEST_POST_ID,
            user_id=TEST_USER_ID,
            metric=999
        )
        context = Mock()
        mock_db.get_post_dynamic.side_effect = KeyError("Invalid metric")

        response = statistic_service.GetPostDynamic(request, context)

        assert response == statistic_pb2.PostDynamicResponse()
        context.set_code.assert_called_with(grpc.StatusCode.INTERNAL)


class TestGetTopPosts:
    def test_success(self, statistic_service, mock_db):
        request = statistic_pb2.TopPostsRequest(
            metric=statistic_pb2.TopPostsRequest.VIEWS,
            user_id=TEST_USER_ID
        )
        context = Mock()

        response = statistic_service.GetTopPosts(request, context)

        assert len(response.posts) == 2
        assert response.posts[0].post_id == "post1"
        assert response.posts[0].count == 100
        mock_db.get_top_posts.assert_called_once()

    def test_db_error(self, statistic_service, mock_db):
        mock_db.get_top_posts.side_effect = Exception("DB error")
        request = statistic_pb2.TopPostsRequest(
            metric=statistic_pb2.TopPostsRequest.VIEWS,
            user_id=TEST_USER_ID
        )
        context = Mock()

        response = statistic_service.GetTopPosts(request, context)

        assert response == statistic_pb2.TopPostsResponse()
        context.set_code.assert_called_with(grpc.StatusCode.INTERNAL)


class TestGetTopUsers:
    def test_success(self, statistic_service, mock_db):
        request = statistic_pb2.TopUsersRequest(
            metric=statistic_pb2.TopUsersRequest.VIEWS,
            user_id=TEST_USER_ID
        )
        context = Mock()

        response = statistic_service.GetTopUsers(request, context)

        assert len(response.users) == 2
        assert response.users[0].user_id == "user1"
        assert response.users[0].count == 200
        mock_db.get_top_users.assert_called_once()

    def test_db_error(self, statistic_service, mock_db):
        mock_db.get_top_users.side_effect = Exception("DB error")
        request = statistic_pb2.TopUsersRequest(
            metric=statistic_pb2.TopUsersRequest.VIEWS,
            user_id=TEST_USER_ID
        )
        context = Mock()

        response = statistic_service.GetTopUsers(request, context)

        assert response == statistic_pb2.TopUsersResponse()
        context.set_code.assert_called_with(grpc.StatusCode.INTERNAL)


class TestGetPostIds:
    def test_success(self, statistic_service, mock_db):
        request = statistic_pb2.GetPostIdsRequest()
        context = Mock()

        response = statistic_service.GetPostIds(request, context)

        assert response.post_ids == TEST_POST_IDS
        mock_db.get_unique_post_ids.assert_called_once()

    def test_db_error(self, statistic_service, mock_db):
        mock_db.get_unique_post_ids.side_effect = Exception("DB error")
        request = statistic_pb2.GetPostIdsRequest()
        context = Mock()

        response = statistic_service.GetPostIds(request, context)

        assert response == statistic_pb2.GetPostIdsResponse()
        context.set_code.assert_called_with(grpc.StatusCode.INTERNAL)
