"""Machine-readable failures for the M8R-05B-03 boundary."""


class OrchestrationError(ValueError):
    def __init__(self, code: str, message: str | None = None):
        super().__init__(message or code)
        self.code = code
