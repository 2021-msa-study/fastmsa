from fastmsa.api import get
from fastmsa.repo import SqlAlchemyRepository

from ..domain.models import User


@get("/users")
def read_users():
    with SqlAlchemyRepository(User) as users:
        return users.all()
