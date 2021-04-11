"""FastMsa 앱이 설정을 읽고 실행되는 과정을 테스트합니다.
"""
import pytest

from fastmsa.test.unit import FakeConfig
from fastmsa.core import AbstractConfig
from fastmsa import FastMsa


@pytest.fixture
def config():
    return FakeConfig()


def test_msa_validate(config: FakeConfig):
    """앱 유효성 검사 테스트.

    - ORM 매핑에서 누락된 모델이나 Aggregate가 있을 경우.
    """

    msa = FastMsa("testapp", config)


def test_msa_init(config: FakeConfig):
    """FastMsa 앱 초기화 테스트.
    필수 초기화 작업:
    - orm 매핑 초기화
    - routes 로딩
    """
    msa = FastMsa("testapp", config)
    # msa.run()
