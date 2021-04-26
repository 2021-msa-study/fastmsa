"""샘플 스키마."""
from fastmsa.schema import Field, schema_from

from ..domain.models import User


@schema_from(User, excludes=["email"], orm_mode=True)
class UserReadSchema:
    """읽기용 스키마 예제.

    `schema_from` 데코레이터의 `excludes` 옵션으로 `email` 필드를 제외했으며,
    `orm_mode=True` 옵션을 주어 SqlAlchemy 모델 데이터틀 자동으로 객체 직렬화
    하도록 했습니다. `orm_mode` 옵션을 주지 않으면 DB 조회 결과를 직접
    `UserReadSchema` 객체로 직렬화해서 리턴해야 합니다.
    """


@schema_from(User)
class UserCreateSchema:  # noqa
    """쓰기용 스키마 예제.

    아래처럼 `= Field(...)` 를 주어 필드에 대한 설명이나 최대 길이 등을 정보를
    추가할 수 있습니다. 추가 가능한 정보들은 :func:`pydantic.fields.Field` 를 참고하세요.
    """

    id: str = Field(..., description="ID는 8자 이상으로 입력해야 합니다.")
