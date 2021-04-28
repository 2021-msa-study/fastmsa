from dataclasses import dataclass
from datetime import date
from typing import Optional

from fastmsa.core import Event


@dataclass
class OutOfStock(Event, Exception):
    sku: str


@dataclass
class BatchCreated(Event):
    ref: str
    sku: str
    qty: int
    eta: Optional[date] = None


@dataclass
class AllocationRequired(Event):
    orderid: str
    sku: str
    qty: int


@dataclass
class BatchQuantityChanged(Event):
    ref: str
    qty: int
