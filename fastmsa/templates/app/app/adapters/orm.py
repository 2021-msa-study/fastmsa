"""ORM 어댑터 모듈"""
from __future__ import annotations

from sqlalchemy import (
    MetaData,
    Table,
    Column,
    ForeignKey,
    Integer,
    String,
    Date,
)
from sqlalchemy.orm import (
    mapper,
    relationship,
)

from ..domain.aggregates import Product
from ..domain.models import Item, User


def init_mappers(metadata: MetaData) -> MetaData:
    """도메인 객체들을 SqlAlchemy ORM 매퍼에 등록합니다."""

    # Domain 매핑
    user = Table(
        "user",
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("name", String(255)),
        Column("email", String(255), unique=True),
        extend_existing=True,
    )

    item = Table(
        "item",
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("uuid", String(36), unique=True),
        Column("product_id", ForeignKey("product.id")),
        Column("created", Date, nullable=True),
        extend_existing=True,
    )

    # Aggregate 매핑
    product = Table(
        "product",
        metadata,
        Column("id", String(255), primary_key=True),
        Column("version_number", Integer, nullable=False, server_default="0"),
        extend_existing=True,
    )

    mapper(User, user)
    mapper(Item, item)
    mapper(Product, product, properties={"items": relationship(Item)})

    return metadata
