"""샘플 FastAPI 엔드포인트."""
from fastmsa.api import get, post
from fastmsa.repo import SqlAlchemyRepository

from ..domain.models import User
from ..schema.sample import UserCreateSchema, UserReadSchema


@post("/users")
def create_user(data: UserCreateSchema):
    """사용자를 추가합니다."""
    user = User(**data.dict())  # type: ignore
    with SqlAlchemyRepository(User) as users:
        users.add(user)
        users.session.commit()


@get("/users", response_model=list[UserReadSchema])
def read_users():
    """모든 사용자 정보를 조회합니다."""
    with SqlAlchemyRepository(User) as users:
        return users.all()
