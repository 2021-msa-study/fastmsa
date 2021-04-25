"""E2E 테스트 모듈입니다."""
import contextlib
import threading
import time

import uvicorn
from fastapi import FastAPI
from uvicorn.config import Config
from werkzeug.serving import make_server

from fastmsa.core import FastMSA


class FastApiServer(uvicorn.Server):
    def __init__(self, app: FastAPI, port=5000):
        super().__init__(Config(app, host="127.0.0.1", port=port, log_level="info"))

    def install_signal_handlers(self):
        pass

    @contextlib.contextmanager
    def run_in_thread(self):
        thread = threading.Thread(target=self.run)
        thread.start()
        try:
            while not self.started:
                time.sleep(1e-3)
            yield
        finally:
            self.should_exit = True
            thread.join()
