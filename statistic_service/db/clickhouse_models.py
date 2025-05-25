import uuid
from sqlalchemy import Column, PrimaryKeyConstraint
from sqlalchemy.orm import declarative_base
from clickhouse_sqlalchemy import types as ch_types, engines
from enum import Enum

Base = declarative_base()


class EventType(Enum):
    VIEW = 1
    LIKE = 2
    COMMENT = 3


class Event(Base):
    __tablename__ = 'events'

    event_id = Column(ch_types.UUID, primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = Column(ch_types.String)
    event_type = Column(ch_types.Enum8(EventType))
    event_date = Column(ch_types.Date)

    __table_args__ = (
        engines.MergeTree(
            order_by=('event_id', 'post_id'),
            primary_key='event_id'
        ),
    )


class PostStats(Base):
    __tablename__ = 'post_stats'

    post_id = Column(ch_types.String, primary_key=True)
    views_count = Column(ch_types.UInt64, default=0)
    likes_count = Column(ch_types.UInt64, default=0)
    comments_count = Column(ch_types.UInt64, default=0)
    updated_at = Column(ch_types.DateTime)

    __table_args__ = (
        engines.MergeTree(
            order_by=('post_id',),
            primary_key='post_id'
        ),
    )


class PostDailyStats(Base):
    __tablename__ = 'post_daily_stats'

    post_id = Column(ch_types.String)
    date = Column(ch_types.Date)
    views_count = Column(ch_types.UInt64, default=0)
    likes_count = Column(ch_types.UInt64, default=0)
    comments_count = Column(ch_types.UInt64, default=0)

    __table_args__ = (
        PrimaryKeyConstraint('post_id', 'date', name='post_daily_stats_pkey'),
        engines.MergeTree(
            order_by=('post_id', 'date'),
            primary_key=('post_id', 'date')
        ),
    )


class UserStats(Base):
    __tablename__ = 'user_stats'

    user_id = Column(ch_types.String, primary_key=True)
    views_count = Column(ch_types.UInt64, default=0)
    likes_count = Column(ch_types.UInt64, default=0)
    comments_count = Column(ch_types.UInt64, default=0)
    updated_at = Column(ch_types.DateTime)

    __table_args__ = (
        engines.MergeTree(
            order_by=('user_id',),
            primary_key='user_id'
        ),
    )
