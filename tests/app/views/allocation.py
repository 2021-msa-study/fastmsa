from fastmsa.uow import SqlAlchemyUnitOfWork


def get_allocations_by(orderid: str, uow: SqlAlchemyUnitOfWork):
    with uow:
        results = uow.session.execute(
            """
            SELECT sku, batchref FROM allocations_view WHERE orderid = :orderid
            """,
            dict(orderid=orderid),
        )
    return [dict(r) for r in results]
