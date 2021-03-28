"""테스트 기본 설정 및 헬퍼 함수를 정의합니다."""
from __future__ import annotations
from typing import Callable, Any, Optional
from types import ModuleType
import os
import sys
import uuid
import types
import inspect
import traceback

FAIL = '\033[91m'
VIOLET = '\033[95m'
ENDC = '\033[0m'
BOLD = '\033[1m'

_AnyFunc = Callable[..., Any]


def random_suffix() -> str:
    """랜덤 ID뒤에 붙일 UUID 기반의 6자리 임의의 ID를 생성합니다."""
    return uuid.uuid4().hex[:6]


def random_sku(name: str = '') -> str:
    """임의의 SKU를 생성합니다."""
    return f'sku-{name}-{random_suffix()}'


def random_batchref(num: int = 1) -> str:
    """임의의 Batch reference를 생성합니다."""
    return f'batch-{num}-{random_suffix()}'


def random_orderid(name: str = '') -> str:
    """임의의 order_id 를 생성합니다."""
    return f'order-{name}-{random_suffix()}'


class mytest:  #pylint: disable=invalid-name
    """pytest 를 흉내내는 간단한 Jupyter Notebook용 테스트 러너 입니다."""
    fixtures: dict[str, _AnyFunc] = {}
    tests: dict[_AnyFunc, _AnyFunc] = {}

    @classmethod
    def fixture(cls, func: _AnyFunc) -> _AnyFunc:
        """함수 객체를 픽스쳐 레지스트리에 등록하는 함수 데코레이터."""
        cls.fixtures[func.__name__] = func
        return func

    @classmethod
    def run(cls, func: _AnyFunc) -> Any:
        """이전에 실행한 유닛 테스트를 다시 실행합니다.

        Example:
            ::

                @test
                def test_example()
                    ...

                mytest.run(test_example)
        """
        assert func in cls.tests, \
               f'{func} should be registered with `@unit` decorator first'
        cls.tests[func]()

    @classmethod
    def test(cls, func: _AnyFunc) -> _AnyFunc:
        """유닛 테스트를 등록하는 함수 데코레이터.

        함수 정의와 동시에 테스트 함수를 실행합니다. 함수 실행이 실패해도 예외
        메세지가 출력될 뿐 실행이 중단되지 않습니다.

        파라메터가 정의된 함수의 경우 파라메터 이름들을 픽스쳐 레지스트리에서 찾아
        재귀적으로 픽스쳐 함수를 실행한 결과를 인자 값으로 주입하여 테스트 함수를
        실행합니다.

        테스트 실행시 예외가 발생하면 예외 메세지를 출력합니다.

        함수 객체는 내부 테스트 레지스트리에 보관되며 :meth:`mytest.run` 으로 다시
        실행할 수 있습니다.
        """
        def unit() -> _AnyFunc:
            cleanups = []

            def unwrap(func: _AnyFunc) -> Any:
                argvals = []
                fixnames: list[str] = inspect.getfullargspec(func).args

                for fixname in fixnames:
                    assert fixname in cls.fixtures, \
                           f'name "{fixname}" should be registered first with @mytest.fixture'

                    fixfunc = cls.fixtures[fixname]
                    fixargs = inspect.getfullargspec(fixfunc).args

                    if not fixargs:  # 인자가 없는 fixture라면
                        val = fixfunc()
                        if isinstance(val, types.GeneratorType):
                            argvals.append(next(val))
                            cleanups.append(val)
                        else:
                            argvals.append(val)
                    else:  # 인자가 있을경우 재귀적으로 반복합니다.
                        argvals.append(unwrap(fixfunc))

                val = func(*argvals)
                if isinstance(val, types.GeneratorType):
                    cleanups.append(val)
                    return next(val)
                return val

            try:
                unwrap(func)
                print(f'✅ {VIOLET}{func.__name__}{ENDC}', flush=True)
            except:  #pylint: disable=bare-except
                print(f'❌ {FAIL}{func.__name__}{ENDC}', flush=True)
                traceback.print_exc(limit=-1)
                sys.stderr.flush()
            finally:  # 함수 실행이 실패해도 함수 정의는 그대로 리턴하도록
                for gen in cleanups:
                    try:
                        next(gen)
                    except StopIteration:
                        pass
                return func  # pylint: disable=lost-exception

        cls.tests[func] = unit
        return unit()
