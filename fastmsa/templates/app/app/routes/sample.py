from fastmsa.api import get, post
from fastmsa.repo import SqlAlchemyRepository
from fastmsa.schema import from_dataclass

from ..domain.models import User


@from_dataclass(User, excludes=["email"])
class UserSchema:
    ...


@post("/users/")
def write_users(user: UserSchema):
    with SqlAlchemyRepository(User) as users:
        users.add(data)


@get("/users", response_model=UserSchema)
def read_users():
    with SqlAlchemyRepository(User) as users:
        return users.all()
