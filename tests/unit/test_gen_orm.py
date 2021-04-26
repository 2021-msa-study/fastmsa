"""ORM 매핑 코드 자동 생성 기능을 테스트합니다."""
from dataclasses import dataclass
from inspect import getmembers
from types import CodeType
from typing import Optional

import jinja2


class Batch:
    """테스트 클래스.

    이 클래스 코드의 바이트코드를 보면 `self.qty = qty` 처럼 속성에 할당하는 연산은
    `STORE_ATTR` OP로 실행되어 `co_names` 에 추가 되고 `x`, `y` 등의 변수는
    `STORE_FAST` OP로 도행되어 `co_varnames` 에 추가됩니다.
    """

    def __init__(self, ref: str, qty: int, test=1):
        self.ref = ref
        self.qty = qty
        x = 1
        y = 2
        z = x + y


def test_instance_class_attrs():
    """매핑 코드 생성 테스트.
    Example:

        ``Batch`` 도메인 클래스가 다음처럼 정의되었을 경우::

            class Batch:
                def __init__(self, ref:str, sku: str, qty: int):
                    self.ref = ref
                    self.qty = qty

        이런 초기화 코드가 생성되어야 합니다::

            batch = Table(
                "batch",
                metadata,
                Column("id", Integer, primary_key=True, autoincrement=True),
                Column("ref", String(255),
                Column("qty", Integer),
                extend_existing=True,
            )
    """

    members = getmembers(Batch)
    attrs = list[str]()
    annot = dict[str, type]()

    for name, member in members:
        if "__init__" == name:
            annot = member.__annotations__
            code: CodeType = member.__code__
            attrs = list(code.co_names)

    assert 2 == len(attrs)
    assert int == annot["qty"]


@dataclass
class AttrDef:
    name: str
    type: type
    size: int = 255
    primary_key: Optional[bool] = None
    autoincrement: Optional[bool] = None
    _sql_type: Optional[str] = None

    @property
    def sql_type(self) -> str:
        if self.type == int:
            return "Integer"
        elif self.type == float:
            return "Float"

        return f"String({self.size})"


@dataclass
class ModelDef:
    name: str
    attrs: list[AttrDef]


def test_template():
    model_def = ModelDef(
        name="Batch",
        attrs=[
            AttrDef(name="id", type=int, primary_key=True, autoincrement=True),
            AttrDef(name="ref", type=str),
            AttrDef(name="qty", type=int),
        ],
    )

    tpl = jinja2.Template(
        """
    batch = Table(
        "{{model.name}}",
        metadata,
        {%- for attr in model.attrs %}
        {%- if attr.primary_key %}
        Column("{{attr.name}}", {{attr.sql_type}}, primary_key=True{{attr.autoincrement and ", autoincrement=True" or ""}}),
        {%- else %}
        Column("{{attr.name}}", {{attr.sql_type}}),
        {%- endif %}
        {%- endfor %}
    )
    """
    )

    output = tpl.render(model=model_def).strip()
    expected = """
        batch = Table(
        "Batch",
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("ref", String(255)),
        Column("qty", Integer),
    )
    """.strip()
    assert expected == output
