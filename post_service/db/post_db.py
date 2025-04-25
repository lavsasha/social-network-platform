from typing import Optional, List, Tuple, Dict
import grpc
import time
from datetime import datetime
from sqlalchemy import create_engine, and_, or_, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy import text
from proto import post_pb2
from .models import Base, Post, Comment


class PostDBError(Exception):
    """Base exception for PostDB errors"""
    pass


class AccessDeniedError(PostDBError):
    """Raised when user doesn't have access to the resource"""
    pass


class NotFoundError(PostDBError):
    """Raised when resource is not found"""
    pass


class OutOfRangeError(PostDBError):
    """Raised when pagination is out of range"""
    pass


class InvalidArgumentError(PostDBError):
    """Raised when invalid arguments are provided"""
    pass


class PostDB:
    def __init__(self, db_url: str, retries: int = 5, delay: int = 5):
        self.engine = None
        self.Session = None
        for i in range(retries):
            try:
                self.engine = create_engine(db_url)
                self.Session = sessionmaker(bind=self.engine)
                self.recreate_tables()
                break
            except OperationalError as e:
                if i == retries - 1:
                    raise RuntimeError(f"Failed to connect to database after {retries} attempts") from e
                time.sleep(delay)

    def recreate_tables(self):
        try:
            Base.metadata.drop_all(self.engine)
            with self.engine.connect() as conn:
                conn.execute(text("CREATE SEQUENCE IF NOT EXISTS posts_post_id_seq START 1"))
                conn.commit()

            Base.metadata.create_all(self.engine)

            with self.engine.connect() as conn:
                conn.execute(text("ALTER SEQUENCE posts_post_id_seq RESTART WITH 1"))
                conn.commit()
        except SQLAlchemyError as e:
            raise PostDBError("Error recreating tables") from e

    def create_post(self, post_data: post_pb2.CreatePostRequest) -> post_pb2.CreatePostResponse:
        session = self.Session()
        try:
            if not post_data.title or not post_data.creator_id:
                raise InvalidArgumentError("Title and creator_id are required")

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
        except SQLAlchemyError as e:
            session.rollback()
            raise PostDBError("Database error while creating post") from e
        finally:
            session.close()

    def get_post(self, post_id: str, user_id: str) -> post_pb2.GetPostResponse:
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
                raise NotFoundError("Post not found or access denied")

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
            raise InvalidArgumentError("Invalid post ID format")
        except SQLAlchemyError as e:
            raise PostDBError("Database error while fetching post") from e
        finally:
            session.close()

    def update_post(self, post_data: post_pb2.UpdatePostRequest) -> post_pb2.UpdatePostResponse:
        session = self.Session()
        try:
            if not post_data.post_id or not post_data.user_id:
                raise InvalidArgumentError("Post ID and user ID are required")

            post = session.query(Post).filter(
                and_(
                    Post.post_id == int(post_data.post_id),
                    Post.creator_id == post_data.user_id
                )
            ).first()

            if not post:
                raise NotFoundError("Post not found or permission denied")

            if post_data.title:
                post.title = post_data.title
            if post_data.description:
                post.description = post_data.description
            if post_data.tags:
                post.tags = post_data.tags
            post.is_private = post_data.is_private
            post.updated_at = datetime.utcnow()

            session.commit()

            return post_pb2.UpdatePostResponse(
                updated_at=post.updated_at.isoformat()
            )
        except ValueError:
            raise InvalidArgumentError("Invalid post ID format")
        except SQLAlchemyError as e:
            session.rollback()
            raise PostDBError("Database error while updating post") from e
        finally:
            session.close()

    def delete_post(self, post_id: str, user_id: str) -> post_pb2.DeletePostResponse:
        session = self.Session()
        try:
            result = session.query(Post).filter(
                and_(
                    Post.post_id == int(post_id),
                    Post.creator_id == user_id
                )
            ).delete()

            session.commit()
            if result == 0:
                raise NotFoundError("Post not found or permission denied")
            return post_pb2.DeletePostResponse(success=True)
        except ValueError:
            raise InvalidArgumentError("Invalid post ID format")
        except SQLAlchemyError as e:
            session.rollback()
            raise PostDBError("Database error while deleting post") from e
        finally:
            session.close()

    def list_posts(self, user_id: str, page: int, per_page: int) -> post_pb2.ListPostsResponse:
        session = self.Session()
        try:
            if page <= 0 or per_page <= 0:
                raise InvalidArgumentError("Page and per_page must be positive integers")

            total = session.query(func.count(Post.post_id)).filter(
                or_(
                    Post.is_private == False,
                    Post.creator_id == user_id
                )
            ).scalar()

            last_page = (total + per_page - 1) // per_page if total > 0 else 1
            if page > last_page and total > 0:
                raise OutOfRangeError(f"Requested page {page} is out of range. Last available page is {last_page}")

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
            raise PostDBError("Database error while listing posts") from e
        finally:
            session.close()

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

    def _check_post_access(self, session, post_id: int, user_id: str) -> Post:
        post = session.query(Post).get(post_id)
        if not post:
            raise NotFoundError("Post not found")
        if post.is_private and post.creator_id != user_id:
            raise AccessDeniedError("Access to post denied")
        return post

    def create_comment(self, comment_data: post_pb2.CommentPostRequest) -> post_pb2.CommentPostResponse:
        session = self.Session()
        try:
            if not comment_data.comment:
                raise InvalidArgumentError("Comment text is required")

            post = self._check_post_access(session, int(comment_data.post_id), comment_data.user_id)

            new_comment = Comment(
                post_id=int(comment_data.post_id),
                user_id=comment_data.user_id,
                text=comment_data.comment,
                created_at=datetime.utcnow()
            )
            session.add(new_comment)
            session.flush()

            post.comments_count += 1
            session.commit()

            return post_pb2.CommentPostResponse(
                comment_id=str(new_comment.comment_id),
                created_at=new_comment.created_at.isoformat()
            )
        except ValueError:
            raise InvalidArgumentError("Invalid post ID format")
        except SQLAlchemyError as e:
            session.rollback()
            raise PostDBError("Database error while creating comment") from e
        finally:
            session.close()

    def get_comments(self, post_id: str, user_id: str, page: int, per_page: int) -> post_pb2.GetCommentsResponse:
        session = self.Session()
        try:
            if page <= 0 or per_page <= 0:
                raise InvalidArgumentError("Page and per_page must be positive integers")

            post = self._check_post_access(session, int(post_id), user_id)

            total = session.query(func.count(Comment.comment_id)).filter(
                Comment.post_id == int(post_id)
            ).scalar()

            if total == 0:
                return post_pb2.GetCommentsResponse(
                    comments=[],
                    meta=post_pb2.Meta(
                        total=0,
                        page=page,
                        per_page=per_page,
                        last_page=1
                    )
                )

            last_page = (total + per_page - 1) // per_page
            if page > last_page:
                raise OutOfRangeError(f"Page {page} is out of range. Last page is {last_page}")

            offset = (page - 1) * per_page
            comments = session.query(Comment).filter(
                Comment.post_id == int(post_id)
            ).order_by(Comment.created_at.desc()
                       ).limit(per_page).offset(offset).all()

            comments_list = [
                post_pb2.Comment(
                    comment_id=str(comment.comment_id),
                    text=comment.text,
                    user_id=comment.user_id,
                    created_at=comment.created_at.isoformat()
                )
                for comment in comments
            ]

            meta_pb = post_pb2.Meta(
                total=total,
                page=page,
                per_page=per_page,
                last_page=last_page
            )

            return post_pb2.GetCommentsResponse(
                comments=comments_list,
                meta=meta_pb
            )
        except ValueError:
            raise InvalidArgumentError("Invalid post ID format")
        except SQLAlchemyError as e:
            raise PostDBError("Database error while fetching comments") from e
        finally:
            session.close()

    def increment_views_count(self, post_id: str, user_id: str) -> post_pb2.ViewPostResponse:
        session = self.Session()
        try:
            post = self._check_post_access(session, int(post_id), user_id)
            post.views_count += 1
            session.commit()
            return post_pb2.ViewPostResponse(success=True)
        except ValueError:
            raise InvalidArgumentError("Invalid post ID format")
        except SQLAlchemyError as e:
            session.rollback()
            raise PostDBError("Database error while incrementing views") from e
        finally:
            session.close()

    def increment_likes_count(self, post_id: str, user_id: str) -> post_pb2.LikePostResponse:
        session = self.Session()
        try:
            post = self._check_post_access(session, int(post_id), user_id)
            post.likes_count += 1
            session.commit()
            return post_pb2.LikePostResponse(success=True)
        except ValueError:
            raise InvalidArgumentError("Invalid post ID format")
        except SQLAlchemyError as e:
            session.rollback()
            raise PostDBError("Database error while incrementing likes") from e
        finally:
            session.close()

    def close(self):
        if self.engine:
            self.engine.dispose()
