"""Stable error codes for M8R-05C projection layer."""
from __future__ import annotations


class ProjectionError(ValueError):
    """Raised when a deterministic projection cannot be completed.

    Attributes
    ----------
    code : str
        Machine-readable, stable error code.  Never include secrets,
        tokens, credentials, or absolute local paths in the code string.
    """

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)
