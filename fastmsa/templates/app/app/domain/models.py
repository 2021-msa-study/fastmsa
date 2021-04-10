"""Domain models."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    """Sample user model."""

    id: str
    name: str
    email: str


@dataclass
class Item:
    """Sample item model."""

    id: int
    uuid: str
    product_id: str
    created: datetime
