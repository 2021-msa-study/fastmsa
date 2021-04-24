from datetime import datetime
from typing import Optional

from fastmsa.schema import BaseModel


class BatchAdd(BaseModel):
    eta: Optional[datetime]
    ref: str
    sku: str
    qty: int


class BatchDelete(BaseModel):
    eta: Optional[datetime]
    refs: list[str]
    sku: str
    qty: int


class BatchAllocate(BaseModel):
    eta: Optional[datetime]
    orderid: str
    ref: str
    sku: str
    qty: int
