from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ARRAY, Sequence, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Post(Base):
    __tablename__ = 'posts'

    post_id = Column(
        Integer,
        Sequence('posts_post_id_seq', start=1),
        primary_key=True
    )
    title = Column(String(255), nullable=False)
    description = Column(Text)
    creator_id = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow, nullable=False)
    is_private = Column(Boolean, default=False)
    tags = Column(ARRAY(String), nullable=False, default=[])
    views_count = Column(Integer, default=0)
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)

    comments = relationship("Comment", back_populates="post")


class Comment(Base):
    __tablename__ = 'comments'

    comment_id = Column(
        Integer,
        Sequence('comments_id_seq', start=1),
        primary_key=True
    )
    post_id = Column(Integer, ForeignKey('posts.post_id'), nullable=False)
    user_id = Column(String(50), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    post = relationship("Post", back_populates="comments")
