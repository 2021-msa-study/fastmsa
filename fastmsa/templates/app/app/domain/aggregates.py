"""Aggregate models."""
from dataclasses import dataclass, field

from fastmsa.core import Aggregate

from .models import Item


@dataclass
class Product(Aggregate[Item]):
    """Sample aggregate model."""

    id: int
    items: list[Item] = field(default_factory=list)
    version_number: int = 0
