"""Integrazione riproducibile di Umbrella nel sorgente Chromium."""

from .engine import (
    GnListAdd,
    InsertAfter,
    InsertBefore,
    IntegrationError,
    RegexReplace,
    Replace,
    ReplaceFile,
    Result,
    apply_operations,
    describe_operations,
)

__all__ = [
    "GnListAdd",
    "InsertAfter",
    "InsertBefore",
    "IntegrationError",
    "RegexReplace",
    "Replace",
    "ReplaceFile",
    "Result",
    "apply_operations",
    "describe_operations",
]
