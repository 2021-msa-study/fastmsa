"""E2E 테스트 모듈입니다."""
import threading

from werkzeug.serving import make_server
from flask import Flask

from tests.app import config


class FlaskServerThread(threading.Thread):
    """여러 다른 Flask App 컨텍스트를 교체하고 재시작 가능한 멀티스레드 서버."""
    def __init__(self, app: Flask):
        threading.Thread.__init__(self)
        self.srv = make_server(config.get_api_host(), config.get_api_port(),
                               app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self) -> None:
        """서버를 실행합니다."""
        print('starting server... ', end='')
        self.srv.serve_forever()

    def shutdown(self) -> None:
        """서버를 종료합니다."""
        print('shutting down server...')
        self.srv.shutdown()


class CustomFlask(Flask):
    """동일 endpoint에 라우팅을 덮어쓰도록 허용하는 커스텀 Flask 구현입니다."""
    def add_url_rule(  # type: ignore
            self,
            rule,
            endpoint=None,
            view_func=None,
            provide_automatic_options=None,
            **options):
        """기존 매핑을 제거 후 등록합니다."""
        self.view_functions.pop(view_func.__name__, None)
        Flask.add_url_rule(self,
                           rule,
                           endpoint=endpoint,
                           view_func=view_func,
                           provide_automatic_options=provide_automatic_options,
                           **options)


_FLASK_SERVER: FlaskServerThread


def start_flask_server(app: CustomFlask) -> None:
    """:class:`ServerThread` 를 시작합니다."""
    global _FLASK_SERVER  # pylint: disable=invalid-name, global-statement
    _FLASK_SERVER = FlaskServerThread(app)
    _FLASK_SERVER.start()
    print('started.')


def stop_flask_server() -> None:
    """:class:`ServerThread` 를 종료합니다."""
    server = globals().get('_FLASK_SERVER')
    if server:
        server.shutdown()


def restart_flask_server(app: CustomFlask) -> None:
    """기존에 시작중인 :class:`ServerThread` 를 종료후 재시작 합니다."""
    stop_flask_server()
    start_flask_server(app)
