from fastmsa.repo import SqlAlchemyRepository

from ..domain.aggregates import Product


class SqlAlchemyProductRepository(SqlAlchemyRepository[Product]):
    def __repr__(self):
        return self.__class__.__name__

    def _get_by_batchref(self, batchref):
        return next(
            (p for p in self.all() for b in p.items if b.reference == batchref), None
        )
