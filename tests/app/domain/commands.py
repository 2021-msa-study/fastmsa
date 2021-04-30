from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from fastmsa.core import Command


@dataclass
class Allocate(Command):
    orderid: str
    sku: str
    qty: int


@dataclass
class CreateBatch(Command):
    ref: str
    sku: str
    qty: int
    eta: Optional[datetime] = None


@dataclass
class ChangeBatchQuantity(Command):
    ref: str
    qty: int
