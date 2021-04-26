"""Domain models."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class User:
    """Sample user model."""

    id: str = field(metadata=dict(title="아이디", description="8자 이상"))
    name: str = field(metadata=dict(title="이름", description="한글 이름"))
    email: str = field(metadata=dict(title="이메일"))


@dataclass
class Item:
    """Sample item model."""

    id: int
    uuid: str
    product_id: str
    created: datetime
