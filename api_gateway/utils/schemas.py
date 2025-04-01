from pydantic import BaseModel, Field, field_validator, ConfigDict, ValidationError
from typing import List, Optional, Dict, Any
import re
from datetime import datetime
from collections import OrderedDict


class InvalidPostID(Exception):
    pass


class PostBase(BaseModel):
    description: Optional[str] = Field(None, max_length=1000)
    is_private: Optional[bool] = None
    tags: Optional[List[str]] = Field(None)

    @field_validator('tags')
    def validate_tags(cls, v):
        if v is not None and len(v) > 10:
            raise ValueError("Maximum 10 tags allowed")
        return v

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        populate_by_name=True
    )


class PostCreate(PostBase):
    title: str = Field(..., min_length=1, max_length=100)


class PostUpdate(PostBase):
    title: Optional[str] = Field(None, min_length=1, max_length=100)


class PostResponse(PostBase):
    post_id: int
    title: str
    description: str
    creator_id: str
    created_at: str
    updated_at: str
    is_private: bool
    tags: List[str]

    def dict(self, **kwargs) -> Dict[str, Any]:
        return OrderedDict([
            ("post_id", self.post_id),
            ("title", self.title),
            ("description", self.description),
            ("creator_id", self.creator_id),
            ("created_at", self.created_at),
            ("updated_at", self.updated_at),
            ("is_private", self.is_private),
            ("tags", self.tags)
        ])


class MetaResponse(BaseModel):
    total: int
    per_page: int
    current_page: int
    last_page: int
    from_: int = Field(..., alias="from")
    to_: int

    model_config = ConfigDict(populate_by_name=True)

    def dict(self, **kwargs) -> Dict[str, Any]:
        return OrderedDict([
            ("total", self.total),
            ("per_page", self.per_page),
            ("current_page", self.current_page),
            ("last_page", self.last_page),
            ("from_", self.from_),
            ("to_", self.to_)
        ])


class ListPostsQuery(BaseModel):
    page: int = Field(1, gt=0)
    per_page: int = Field(10, gt=0, le=100)


class ListPostsResponse(BaseModel):
    posts: List[PostResponse]
    meta: MetaResponse

    def dict(self, **kwargs) -> Dict[str, Any]:
        return OrderedDict([
            ("posts", [post.dict() for post in self.posts]),
            ("meta", self.meta.dict())
        ])


def validate_post_id(post_id: str) -> int:
    if not re.match(r'^\d+$', post_id):
        raise InvalidPostID("Post ID must be a positive integer")
    return int(post_id)


def simplify_validation_errors(exc: ValidationError):
    error = exc.errors()[0]
    field = ".".join(str(loc) for loc in error['loc'])
    msg = error['msg']

    if error['type'] == 'missing':
        msg = f"Field '{field}' is required"
    elif error['type'] == 'string_type':
        msg = f"Field '{field}' must be a string"
    elif error['type'] == 'bool_type':
        msg = f"Field '{field}' must be a boolean"

    return {"field": field, "message": msg}
