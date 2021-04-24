"""샘플 FastAPI 엔드포인트."""
from typing import cast
from fastmsa.api import get, post
from fastmsa.repo import SqlAlchemyRepository
from fastmsa.schema import from_dataclass, BaseModel

from ..domain.models import User


@from_dataclass(User, excludes=["email"])
class UserReadSchema:  # noqa
    ...


@from_dataclass(User)
class UserCreateSchema:  # noqa
    ...


@post("/users")
def create_user(user: UserCreateSchema):
    new_user = User(**cast(BaseModel, user).dict())
    with SqlAlchemyRepository(User) as users:
        users.add(new_user)
        users.session.commit()


@get("/users", response_model=list[UserReadSchema])
def read_users():
    with SqlAlchemyRepository(User) as users:
        return users.all()
