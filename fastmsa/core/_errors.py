class FastMSAError(Exception):
    """``FastMSA`` 와 관련된 모든 에러의 기본 클래스."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

    ...
