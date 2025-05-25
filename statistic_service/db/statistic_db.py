import grpc
from datetime import datetime
from sqlalchemy import create_engine, func, desc, and_, or_, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.postgresql import insert
from .clickhouse_models import (
    Base, Event, PostStats, PostDailyStats, UserStats, EventType
)
from sqlalchemy import case
from sqlalchemy import text
import logging


class StatisticDB:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)

    def get_session(self):
        return self.Session()

    def aggregate_events(self, session, post_id=None, user_id=None):
        logger = logging.getLogger("StatisticDB.aggregate_events")
        logger.info(f"→ aggregate_events(post_id={post_id}, user_id={user_id})")
        try:
            total_query = session.query(
                Event.post_id,
                func.count(func.if_(Event.event_type == EventType.VIEW, 1, None)).label("views"),
                func.count(func.if_(Event.event_type == EventType.LIKE, 1, None)).label("likes"),
                func.count(func.if_(Event.event_type == EventType.COMMENT, 1, None)).label("comments")
            )
            if post_id:
                total_query = total_query.filter(Event.post_id == post_id)

            total_query = total_query.group_by(Event.post_id)
            total_stats = total_query.all()
            logger.info(f"   total_stats rows: {len(total_stats)}")

            for stat in total_stats:
                stats_dict = {
                    'post_id': stat.post_id,
                    'views': stat.views,
                    'likes': stat.likes,
                    'comments': stat.comments
                }
                self._update_post_stats(session, stats_dict)
                if user_id:
                    self._update_user_stats(session, user_id, stats_dict)

            daily_query = session.query(
                Event.post_id,
                Event.event_date,
                func.count(func.if_(Event.event_type == EventType.VIEW, 1, None)).label("views"),
                func.count(func.if_(Event.event_type == EventType.LIKE, 1, None)).label("likes"),
                func.count(func.if_(Event.event_type == EventType.COMMENT, 1, None)).label("comments")
            )
            if post_id:
                daily_query = daily_query.filter(Event.post_id == post_id)

            daily_query = daily_query.group_by(Event.post_id, Event.event_date)
            print(str(daily_query.statement.compile(compile_kwargs={"literal_binds": True})))
            daily_stats = daily_query.all()
            logger.info(f"   daily_stats rows: {len(daily_stats)}")

            for stat in daily_stats:
                stats_dict = {
                    'post_id': stat.post_id,
                    'event_date': stat.event_date,
                    'views': stat.views,
                    'likes': stat.likes,
                    'comments': stat.comments
                }
                self._update_daily_stats(session, stats_dict)

            if post_id:
                stmt = text("ALTER TABLE events DELETE WHERE post_id = :post_id")
                session.execute(stmt, {"post_id": post_id})
                logger.info(f"   issued DELETE for post_id={post_id}")
            else:
                session.execute(text("ALTER TABLE events DELETE WHERE 1"))
                logger.info("   issued DELETE for all events")

            session.commit()
            logger.info("← aggregate_events ok")
            return True

        except Exception:
            logger.exception("!!! aggregate_events failure")
            session.rollback()
            raise

    def _update_daily_stats(self, session, stats):
        existing = session.query(PostDailyStats).filter(
            PostDailyStats.post_id == stats['post_id'],
            PostDailyStats.date == stats['event_date']
        ).first()

        if existing:
            existing.views_count += stats['views']
            existing.likes_count += stats['likes']
            existing.comments_count += stats['comments']
        else:
            new_stat = PostDailyStats(
                post_id=stats['post_id'],
                date=stats['event_date'],
                views_count=stats['views'],
                likes_count=stats['likes'],
                comments_count=stats['comments']
            )
            session.add(new_stat)

    def _update_post_stats(self, session, stats):
        existing = session.query(PostStats).filter(
            PostStats.post_id == stats['post_id']
        ).first()

        if existing:
            existing.views_count += stats['views']
            existing.likes_count += stats['likes']
            existing.comments_count += stats['comments']
            existing.updated_at = datetime.now()
        else:
            new_stat = PostStats(
                post_id=stats['post_id'],
                views_count=stats['views'],
                likes_count=stats['likes'],
                comments_count=stats['comments'],
                updated_at=datetime.now()
            )
            session.add(new_stat)

    def _update_user_stats(self, session, user_id, stats):
        existing = session.query(UserStats).filter(
            UserStats.user_id == user_id
        ).first()

        if existing:
            existing.views_count += stats['views']
            existing.likes_count += stats['likes']
            existing.comments_count += stats['comments']
            existing.updated_at = datetime.now()
        else:
            new_stat = UserStats(
                user_id=user_id,
                views_count=stats['views'],
                likes_count=stats['likes'],
                comments_count=stats['comments'],
                updated_at=datetime.now()
            )
            session.add(new_stat)

    def get_post_stats(self, session, post_id: str) -> dict:
        try:
            stats = session.query(PostStats).filter_by(post_id=post_id).first()

            if not stats:
                return {
                    "views_count": 0,
                    "likes_count": 0,
                    "comments_count": 0,
                    "updated_at": datetime.utcnow().isoformat()
                }

            return {
                "views_count": stats.views_count or 0,
                "likes_count": stats.likes_count or 0,
                "comments_count": stats.comments_count or 0,
                "updated_at": stats.updated_at.isoformat()
            }
        except Exception as e:
            session.rollback()
            raise RuntimeError(f"Database error: {str(e)}")

    def get_post_dynamic(self, session, post_id: str, metric: str):
        try:
            stats = session.query(
                PostDailyStats.date,
                getattr(PostDailyStats, f"{metric}_count")
            ).filter(
                PostDailyStats.post_id == post_id
            ).order_by(
                PostDailyStats.date
            ).all()

            return [{'date': stat.date.isoformat(), 'count': getattr(stat, f"{metric}_count")}
                    for stat in stats]
        except SQLAlchemyError as e:
            raise

    def get_top_posts(self, session, metric: str, limit: int = 10):
        try:
            column = getattr(PostStats, f"{metric}_count")

            top = session.query(
                PostStats.post_id,
                column
            ).order_by(
                desc(column)
            ).limit(limit).all()

            return [{'post_id': post_id, 'count': count} for post_id, count in top]
        except SQLAlchemyError as e:
            raise

    def get_top_users(self, session, metric: str, limit: int = 10):
        try:
            column = getattr(UserStats, f"{metric}_count")

            top = session.query(
                UserStats.user_id,
                column
            ).order_by(
                desc(column)
            ).limit(limit).all()

            return [{'user_id': user_id, 'count': count} for user_id, count in top]
        except SQLAlchemyError as e:
            raise

    def close(self):
        if self.engine:
            self.engine.dispose()
