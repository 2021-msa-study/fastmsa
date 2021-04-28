"""History 예제 서비스(교재 10장).

Usecase 1:
    Given a customer with two orders in their history,
    When the customer places a third order,
    Then they should be flagged as a VIP.

Usecase 2:
    When a customer first becomes a VIP
    Then we should send them an email to congratulate them
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from fastmsa.core import Command, Event
from fastmsa.domain import Aggregate
from fastmsa.event import on_command, on_event
from fastmsa.uow import AbstractUnitOfWork
from tests.app.adapters import email

BasketItems = list[int]

##############################################################################
# Sample Models
##############################################################################
@dataclass
class Order:
    id: str
    qty: int

    @staticmethod
    def from_basket(customer_id: int, items: BasketItems) -> Order:
        raise NotImplementedError


@dataclass
class User:
    id: str
    name: str
    email_address: str
    first_name: str


##############################################################################
# Sample Events and Commands
##############################################################################
@dataclass
class CustomerBecameVIP(Event):
    customer_id: int


@dataclass
class OrderCreated(Event):
    customer_id: int
    order_id: str
    order_amount: int


@dataclass
class CreateOrder(Command):
    customer_id: int
    basket_items: BasketItems


##############################################################################
# Sample Aggregates
##############################################################################
@dataclass
class OrderHistory(Aggregate[Order]):  # Aggregate

    customer_id: int
    items: set[Order]

    def record_order(self, order_id: str, order_amount: int):
        entry = Order(order_id, order_amount)

        if entry in self.items:
            return

        self.items.add(entry)

        if len(self.items) == 3:
            self.messages.append(CustomerBecameVIP(self.customer_id))


@dataclass
class Customer(Aggregate[User], User):
    ...


@dataclass
class CustomerOrder(Aggregate[Order], Order):  # Aggregate
    ...


##############################################################################
# Sample Handlers
##############################################################################
@on_command(CreateOrder)
def create_order_from_basket(cmd: CreateOrder, uow: AbstractUnitOfWork):
    with uow:
        order = Order.from_basket(cmd.customer_id, cmd.basket_items)
        uow[CustomerOrder].add(cast(CustomerOrder, order))
        uow.commit()  # raises OrderCreated


@on_event(OrderCreated)
def update_customer_history(event: OrderCreated, uow: AbstractUnitOfWork):
    with uow:
        history = uow[OrderHistory].get(event.customer_id)
        history.record_order(event.order_id, event.order_amount)
        uow.commit()  # raises CustomerBecameVIP


@on_event(CustomerBecameVIP)
def congratulate_vip_customer(event: CustomerBecameVIP, uow: AbstractUnitOfWork):
    with uow:
        customer = uow[Customer].get(event.customer_id)
        email.send(customer.email_address, f"Congratulations {customer.first_name}!")
