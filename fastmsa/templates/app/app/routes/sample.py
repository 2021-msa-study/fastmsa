"""샘플 FastAPI 엔드포인트."""
from typing import cast
from fastmsa.api import get, post
from fastmsa.repo import SqlAlchemyRepository
from fastmsa.schema import schema_from, BaseModel, Field

from ..domain.models import User


@schema_from(User, excludes=["email"], orm_mode=True)
class UserReadSchema:  # noqa
    ...


@schema_from(User)
class UserCreateSchema:  # noqa
    id: str = Field(..., description="사용자 ID22")


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
