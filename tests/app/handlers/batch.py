from fastmsa.event import on_command, on_event
from fastmsa.uow import AbstractUnitOfWork
from tests.app.adapters import email
from tests.app.domain import commands, events
from tests.app.domain.aggregates import Product
from tests.app.domain.models import Batch, OrderLine

ProductUnitOfWork = AbstractUnitOfWork[Product]


class InvalidSku(Exception):
    """배치의 SKU와 다른 SKU를 할당하려 할 때 발생하는 예외입니다."""

    ...


@on_event(events.OutOfStock)
def send_out_of_stock_notification(event: events.OutOfStock):
    """OutOfStock 예외 이벤트 발생시 에러 이메일을 발송합니다."""
    email.send(
        "stock@made.com\n",
        f"Out of stock for {event.sku}",
    )


@on_command(commands.CreateBatch)
def add_batch(e: commands.CreateBatch, uow: ProductUnitOfWork):
    """UOW를 이용해 배치를 추가합니다."""
    with uow:
        product = uow.repo.get(e.sku)

        if not product:
            product = Product(e.sku, items=[])
            uow.repo.add(product)
        product.items.append(Batch(e.ref, e.sku, e.qty, e.eta))
        uow.commit()


@on_command(commands.Allocate)
def allocate(e: commands.Allocate, uow: ProductUnitOfWork):
    """ETA가 가장 빠른 배치를 찾아 :class:`.OrderLine` 을 할당합니다.

    Events:
        InvalidSku: ``SKU`` 가 잘못 지정되어 할당하는한 배치가 없을 경우 발생하는 예외
    """
    line = OrderLine(e.orderid, e.sku, e.qty)
    with uow:
        product = uow.repo.get(line.sku)
        if product is None:
            raise InvalidSku(f"Invalid sku {line.sku}")
        batchref = product.allocate(line)
        uow.commit()
    return batchref


@on_command(commands.ChangeBatchQuantity)
def change_batch_quantity(e: commands.ChangeBatchQuantity, uow: ProductUnitOfWork):
    with uow:
        product = uow.repo.get(by_batchref=e.ref)
        product.change_batch_quantity(ref=e.ref, new_qty=e.qty)
        uow.commit()
