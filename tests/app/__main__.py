"""App 실행용 모듈.

`python -m app` 과 같은 명령으로 실행하기 위한 메인 모듈입니다.
"""
from .apps.flask import init_app

app = init_app()
app.run(use_reloader=True)
