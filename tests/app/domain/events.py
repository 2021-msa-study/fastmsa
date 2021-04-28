from dataclasses import dataclass

from fastmsa.core import Event


@dataclass
class OutOfStock(Event, Exception):
    sku: str
