"""Utilities for strict JWT ``crit`` header validation.

RFC 7515 requires recipients to reject JWS objects that declare critical
extensions they do not understand. Some JWT libraries do not enforce this by
default, so this module provides a small guard that can be called before
claim-level processing.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


class InvalidCriticalHeaderError(ValueError):
    """Raised when a JWT contains an invalid or unsupported ``crit`` header."""


RESERVED_HEADERS: frozenset[str] = frozenset(
    {"alg", "jku", "jwk", "kid", "x5u", "x5c", "x5t", "x5t#S256", "typ", "cty", "crit"}
)


SUPPORTED_CRITICAL_EXTENSIONS: frozenset[str] = frozenset({"b64"})


def validate_jwt_critical_headers(
    headers: Mapping[str, Any],
    *,
    supported_extensions: frozenset[str] = SUPPORTED_CRITICAL_EXTENSIONS,
) -> None:
    """Validate JWT critical headers according to RFC 7515 section 4.1.11.

    Args:
        headers: Decoded JWT/JWS header mapping.
        supported_extensions: Critical extension names the caller understands.

    Raises:
        InvalidCriticalHeaderError: If ``crit`` is malformed, references unknown
            extensions, or references missing header members.
    """

    crit = headers.get("crit")
    if crit is None:
        return

    if isinstance(crit, (str, bytes)) or not isinstance(crit, Sequence):
        raise InvalidCriticalHeaderError("crit must be a non-empty array")

    if not crit:
        raise InvalidCriticalHeaderError("crit must be a non-empty array")

    for ext in crit:
        if not isinstance(ext, str) or not ext.strip():
            raise InvalidCriticalHeaderError("crit entries must be non-empty strings")
        if ext in RESERVED_HEADERS:
            raise InvalidCriticalHeaderError(f"Standard header {ext} is not allowed in crit")
        if ext not in supported_extensions:
            raise InvalidCriticalHeaderError(f"Unsupported critical extension: {ext}")
        if ext not in headers:
            raise InvalidCriticalHeaderError(f"Critical extension {ext} not in header")
