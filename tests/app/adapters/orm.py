"""ORM 어댑터 모듈"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Column, DateTime, ForeignKey, Integer, MetaData, String, Table
from sqlalchemy.orm import mapper, relationship

from tests.app.domain.aggregates import Product
from tests.app.domain.models import Batch, OrderLine


def init_mappers(metadata: MetaData) -> MetaData:
    """도메인 객체들을 SqlAlchemy ORM 매퍼에 등록합니다."""

    order_line = Table(
        "order_line",
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("sku", String(255)),
        Column("qty", Integer, nullable=False),
        Column("orderid", String(255)),
        extend_existing=True,
    )

    @dataclass
    class Allocation:
        orderline_id: int
        batch_id: int

    allocation = Table(
        "allocation",
        metadata,
        Column("orderline_id", Integer, ForeignKey("order_line.id"), primary_key=True),
        Column("batch_id", Integer, ForeignKey("batch.id"), primary_key=True),
        extend_existing=True,
    )

    batch = Table(
        "batch",
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("reference", String(255), unique=True),
        Column("_purchased_quantity", Integer),
        Column("sku", ForeignKey("product.sku")),  # 외래키 관계 추가),
        Column("eta", DateTime, nullable=True),
        extend_existing=True,
    )

    # Aggregate 매핑 추가
    product = Table(
        "product",
        metadata,
        Column("sku", String(255), primary_key=True),
        Column("version_number", Integer, nullable=False, server_default="0"),
        extend_existing=True,
    )

    mapper(Product, product, properties={"items": relationship(Batch)})
    mapper(Allocation, allocation)

    mapper(
        Batch,
        batch,
        properties={
            "_allocations": relationship(
                OrderLine, secondary=allocation, collection_class=set
            ),
        },
    )

    mapper(OrderLine, order_line)

    allocations_view = Table(
        "allocations_view",
        metadata,
        Column("orderid", String(255)),
        Column("sku", String(255)),
        Column("batchref", String(255)),
    )

    return metadata
