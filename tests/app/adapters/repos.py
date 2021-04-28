
from fastmsa.repo import AbstractRepository

from ..domain.aggregates import Product


class AbstractProductRepository(AbstractRepository[Product]):
    def _get_by_batchref(self, batchref):
        raise NotImplementedError


class SqlAlchemyProductRepository(AbstractProductRepository):
    def _get_by_batchref(self, batchref):
        return next(
            (p for p in self.all() for b in p.items if b.reference == batchref), None
        )
