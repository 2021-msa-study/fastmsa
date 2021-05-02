class FastMSAError(Exception):
    """``FastMSA`` 와 관련된 모든 에러의 기본 클래스."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

    ...


class FastMSAInitError(FastMSAError):
    """프로젝트 초기화 실패 에러."""

    ...
