from typing import Optional, List
import grpc
import time
from datetime import datetime
from sqlalchemy import create_engine, and_, or_, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy import text
from proto import post_pb2
from .models import Base, Post


class PostDB:
    def __init__(self, db_url: str, retries: int = 5, delay: int = 5):
        self.engine = None
        self.Session = None
        for i in range(retries):
            try:
                self.engine = create_engine(db_url)
                self.Session = sessionmaker(bind=self.engine)
                Base.metadata.create_all(self.engine)
                break
            except OperationalError as e:
                if i == retries - 1:
                    raise RuntimeError(f"Failed to connect to database after {retries} attempts") from e
                time.sleep(delay)

    def recreate_tables(self):
        try:
            Base.metadata.drop_all(self.engine)
            with self.engine.connect() as conn:
                from sqlalchemy import text
                conn.execute(text("CREATE SEQUENCE IF NOT EXISTS posts_post_id_seq START 1"))
                conn.commit()

            Base.metadata.create_all(self.engine)

            with self.engine.connect() as conn:
                conn.execute(text("ALTER SEQUENCE posts_post_id_seq RESTART WITH 1"))
                conn.commit()

        except SQLAlchemyError as e:
            raise RuntimeError("Error recreating tables") from e

    def create_post(self, post_data: post_pb2.CreatePostRequest) -> post_pb2.CreatePostResponse:
        session = self.Session()
        try:
            new_post = Post(
                title=post_data.title,
                description=post_data.description,
                creator_id=post_data.creator_id,
                is_private=post_data.is_private,
                tags=post_data.tags,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(new_post)
            session.flush()
            session.commit()

            return post_pb2.CreatePostResponse(
                post_id=str(new_post.post_id),
                created_at=new_post.created_at.isoformat()
            )
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            session.close()

    def get_post(self, post_id: str, user_id: str) -> Optional[post_pb2.GetPostResponse]:
        session = self.Session()
        try:
            post_id_int = int(post_id)
            post = session.query(Post).filter(
                and_(
                    Post.post_id == post_id_int,
                    or_(
                        Post.is_private == False,
                        Post.creator_id == user_id
                    )
                )
            ).first()

            if not post:
                return None

            return post_pb2.GetPostResponse(
                post=post_pb2.Post(
                    post_id=str(post.post_id),
                    title=post.title,
                    description=post.description,
                    creator_id=post.creator_id,
                    created_at=post.created_at.isoformat(),
                    updated_at=post.updated_at.isoformat(),
                    is_private=post.is_private,
                    tags=post.tags
                )
            )
        except ValueError:
            return None
        finally:
            session.close()

    def update_post(self, post_data: post_pb2.UpdatePostRequest) -> Optional[post_pb2.UpdatePostResponse]:
        session = self.Session()
        try:
            post = session.query(Post).filter(
                and_(
                    Post.post_id == int(post_data.post_id),
                    Post.creator_id == post_data.user_id
                )
            ).first()

            if not post:
                return None

            if post_data.title:
                post.title = post_data.title
            if post_data.description:
                post.description = post_data.description
            if post_data.tags:
                post.tags = post_data.tags
            post.is_private = post_data.is_private

            session.commit()

            return post_pb2.UpdatePostResponse(
                updated_at=post.updated_at.isoformat()
            )
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            session.close()

    def delete_post(self, post_id: str, user_id: str) -> bool:
        session = self.Session()
        try:
            result = session.query(Post).filter(
                and_(
                    Post.post_id == int(post_id),
                    Post.creator_id == user_id
                )
            ).delete()

            session.commit()
            return result > 0
        except SQLAlchemyError:
            session.rollback()
            raise
        finally:
            session.close()

    def list_posts(self, user_id: str, page: int, per_page: int) -> post_pb2.ListPostsResponse:
        session = self.Session()
        try:
            total = session.query(func.count(Post.post_id)).filter(
                or_(
                    Post.is_private == False,
                    Post.creator_id == user_id
                )
            ).scalar()

            last_page = (total + per_page - 1) // per_page if total > 0 else 1
            if page > last_page and total > 0:
                raise ValueError(
                    f"Requested page {page} is out of range. Last available page is {last_page}"
                )

            offset = (page - 1) * per_page
            posts = session.query(Post).filter(
                or_(
                    Post.is_private == False,
                    Post.creator_id == user_id
                )
            ).order_by(Post.created_at.asc()
                       ).limit(per_page
                               ).offset(offset
                                        ).all()

            return post_pb2.ListPostsResponse(
                posts=[self._post_to_list_pb(p) for p in posts],
                total=total,
                page=page,
                per_page=per_page,
                last_page=last_page,
                from_=offset + 1 if total > 0 else 0,
                to_=min(offset + per_page, total)
            )
        except SQLAlchemyError as e:
            raise grpc.RpcError(grpc.StatusCode.INTERNAL, f"Database error: {str(e)}")
        finally:
            session.close()

    def _post_to_pb(post: Post) -> post_pb2.GetPostResponse:
        return post_pb2.GetPostResponse(
            post_id=str(post.post_id),
            title=post.title,
            description=post.description,
            creator_id=post.creator_id,
            created_at=post.created_at.isoformat(),
            updated_at=post.updated_at.isoformat(),
            is_private=post.is_private,
            tags=post.tags
        )

    def _post_to_list_pb(self, post: Post) -> post_pb2.Post:
        return post_pb2.Post(
            post_id=str(post.post_id),
            title=post.title,
            description=post.description,
            creator_id=post.creator_id,
            created_at=post.created_at.isoformat(),
            updated_at=post.updated_at.isoformat() if post.updated_at else "",
            is_private=post.is_private,
            tags=post.tags if post.tags else [],
        )

    def close(self):
        if self.engine:
            self.engine.dispose()
