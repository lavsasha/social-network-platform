import pytest
from datetime import datetime, date
from sqlalchemy import inspect
from clickhouse_sqlalchemy import types as ch_types
from statistic_service.db.clickhouse_models import Event, PostStats, PostDailyStats, UserStats, EventType


@pytest.fixture
def sample_event():
    return Event(
        post_id="post123",
        event_type=EventType.VIEW,
        event_date=date.today()
    )


@pytest.fixture
def sample_post_stats():
    return PostStats(
        post_id="post123",
        views_count=100,
        likes_count=10,
        comments_count=5,
        updated_at=datetime.now()
    )


@pytest.fixture
def sample_post_daily_stats():
    return PostDailyStats(
        post_id="post123",
        date=date.today(),
        views_count=50,
        likes_count=5,
        comments_count=2
    )


@pytest.fixture
def sample_user_stats():
    return UserStats(
        user_id="user123",
        views_count=200,
        likes_count=20,
        comments_count=10,
        updated_at=datetime.now()
    )


def test_event_model(sample_event):
    assert sample_event.post_id == "post123"
    assert sample_event.event_type == EventType.VIEW
    assert sample_event.event_date == date.today()


def test_event_column_definitions():
    columns = inspect(Event).columns
    assert isinstance(columns['event_id'].type, ch_types.UUID)
    assert columns['event_id'].primary_key is True
    assert isinstance(columns['post_id'].type, ch_types.String)
    assert isinstance(columns['event_type'].type, ch_types.Enum8)
    assert isinstance(columns['event_date'].type, ch_types.Date)


def test_post_stats_model(sample_post_stats):
    assert sample_post_stats.post_id == "post123"
    assert sample_post_stats.views_count == 100
    assert sample_post_stats.likes_count == 10
    assert sample_post_stats.comments_count == 5
    assert isinstance(sample_post_stats.updated_at, datetime)


def test_post_stats_column_definitions():
    columns = inspect(PostStats).columns
    assert isinstance(columns['post_id'].type, ch_types.String)
    assert columns['post_id'].primary_key is True
    assert isinstance(columns['views_count'].type, ch_types.UInt64)
    assert columns['views_count'].default.arg == 0
    assert isinstance(columns['likes_count'].type, ch_types.UInt64)
    assert columns['likes_count'].default.arg == 0
    assert isinstance(columns['comments_count'].type, ch_types.UInt64)
    assert columns['comments_count'].default.arg == 0
    assert isinstance(columns['updated_at'].type, ch_types.DateTime)


def test_post_daily_stats_model(sample_post_daily_stats):
    assert sample_post_daily_stats.post_id == "post123"
    assert sample_post_daily_stats.date == date.today()
    assert sample_post_daily_stats.views_count == 50
    assert sample_post_daily_stats.likes_count == 5
    assert sample_post_daily_stats.comments_count == 2


def test_post_daily_stats_column_definitions():
    columns = inspect(PostDailyStats).columns
    assert isinstance(columns['post_id'].type, ch_types.String)
    assert isinstance(columns['date'].type, ch_types.Date)
    assert isinstance(columns['views_count'].type, ch_types.UInt64)
    assert columns['views_count'].default.arg == 0
    assert isinstance(columns['likes_count'].type, ch_types.UInt64)
    assert columns['likes_count'].default.arg == 0
    assert isinstance(columns['comments_count'].type, ch_types.UInt64)
    assert columns['comments_count'].default.arg == 0


def test_user_stats_model(sample_user_stats):
    assert sample_user_stats.user_id == "user123"
    assert sample_user_stats.views_count == 200
    assert sample_user_stats.likes_count == 20
    assert sample_user_stats.comments_count == 10
    assert isinstance(sample_user_stats.updated_at, datetime)


def test_user_stats_column_definitions():
    columns = inspect(UserStats).columns
    assert isinstance(columns['user_id'].type, ch_types.String)
    assert columns['user_id'].primary_key is True
    assert isinstance(columns['views_count'].type, ch_types.UInt64)
    assert columns['views_count'].default.arg == 0
    assert isinstance(columns['likes_count'].type, ch_types.UInt64)
    assert columns['likes_count'].default.arg == 0
    assert isinstance(columns['comments_count'].type, ch_types.UInt64)
    assert columns['comments_count'].default.arg == 0
    assert isinstance(columns['updated_at'].type, ch_types.DateTime)
