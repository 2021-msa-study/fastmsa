"""App 실행용 모듈.

`python -m app` 과 같은 명령으로 실행하기 위한 메인 모듈입니다.
"""
from fastmsa import FastMsa
from fastmsa.flask import init_app

from tests.app.config import Config

msa = FastMsa(__name__, Config())
app = init_app(msa)
app.run(use_reloader=True)
