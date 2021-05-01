"""Aggregate models."""
from dataclasses import dataclass

from fastmsa.core import Aggregate

from .models import Item


@dataclass
class Product(Aggregate[Item]):
    """Sample aggregate model."""

    id: int
    items: list[Item]
    version_number: int = 0
