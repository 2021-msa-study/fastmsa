from dataclasses import dataclass

from fastmsa.domain import Event


@dataclass
class OutOfStock(Event):
    sku: str
