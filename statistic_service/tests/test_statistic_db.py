import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime
from statistic_service.db.statistic_db import StatisticDB


@pytest.fixture
def db():
    return StatisticDB("clickhouse://mock")


class TestStatisticDB:
    def test_aggregate_events(self, db):
        mock_session = MagicMock()

        mock_total_stat = MagicMock()
        mock_total_stat.post_id = "post1"
        mock_total_stat.views = 10
        mock_total_stat.likes = 5
        mock_total_stat.comments = 3

        mock_daily_stat = MagicMock()
        mock_daily_stat.post_id = "post1"
        mock_daily_stat.event_date = datetime.now().date()
        mock_daily_stat.views = 10
        mock_daily_stat.likes = 5
        mock_daily_stat.comments = 3

        mock_session.query().filter().group_by().all.return_value = [mock_total_stat]
        mock_session.query().group_by().all.return_value = [mock_daily_stat]

        db.aggregate_events(mock_session, "post1", "user1")

        assert mock_session.commit.called
        assert mock_session.execute.called

    def test_get_post_stats(self, db):
        mock_session = MagicMock()
        mock_stats = Mock()
        mock_stats.views_count = 100
        mock_stats.likes_count = 50
        mock_stats.comments_count = 30

        mock_session.query().filter_by().first.return_value = mock_stats

        result = db.get_post_stats(mock_session, "post1")

        assert result["views_count"] == 100
        assert result["likes_count"] == 50
        assert result["comments_count"] == 30

    def test_get_post_dynamic(self, db):
        mock_session = MagicMock()
        mock_date = datetime.now().date()

        mock_stat = MagicMock()
        mock_stat.date = mock_date
        mock_stat.views_count = 10

        mock_session.query().filter().order_by().all.return_value = [mock_stat]

        result = db.get_post_dynamic(mock_session, "post1", "views")

        assert len(result) == 1
        assert result[0]["date"] == mock_date.isoformat()
        assert result[0]["count"] == 10

    def test_get_top_posts(self, db):
        mock_session = MagicMock()
        mock_session.query().order_by().limit().all.return_value = [
            ("post1", 100),
            ("post2", 90)
        ]

        result = db.get_top_posts(mock_session, "views")

        assert len(result) == 2
        assert result[0]["post_id"] == "post1"
        assert result[0]["count"] == 100

    def test_get_top_users(self, db):
        mock_session = MagicMock()
        mock_session.query().order_by().limit().all.return_value = [
            ("user1", 200),
            ("user2", 150)
        ]

        result = db.get_top_users(mock_session, "views")

        assert len(result) == 2
        assert result[0]["user_id"] == "user1"
        assert result[0]["count"] == 200

    def test_get_unique_post_ids(self, db):
        mock_session = MagicMock()
        mock_session.query().all.return_value = [
            ("post1",),
            ("post2",)
        ]

        result = db.get_unique_post_ids(mock_session)
        assert result == ["post1", "post2"]
