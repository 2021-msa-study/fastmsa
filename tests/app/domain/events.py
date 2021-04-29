from dataclasses import dataclass

from fastmsa.core import Event


@dataclass
class OutOfStock(Event, Exception):
    sku: str


@dataclass
class Allocated(Event):
    orderid: str
    sku: str
    qty: int
    batchref: str
