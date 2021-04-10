"""Aggregate models."""
from dataclasses import dataclass

from .models import Item
from fastmsa.domain import Aggregate


@dataclass
class Product(Aggregate[Item]):
    """Sample aggregate model."""

    id: str
    items: list[Item]
    version_number: int = 0