import pytest

from src.backend.security.jwt_crit import (
    InvalidCriticalHeaderError,
    validate_jwt_critical_headers,
)


def test_accepts_header_without_crit() -> None:
    validate_jwt_critical_headers({"alg": "HS256"})


def test_rejects_unknown_critical_extension() -> None:
    with pytest.raises(InvalidCriticalHeaderError, match="Unsupported critical extension: x-custom-policy"):
        validate_jwt_critical_headers(
            {
                "alg": "HS256",
                "crit": ["x-custom-policy"],
                "x-custom-policy": "require-mfa",
            }
        )


def test_rejects_missing_critical_member() -> None:
    with pytest.raises(InvalidCriticalHeaderError, match="Critical extension b64 not in header"):
        validate_jwt_critical_headers(
            {
                "alg": "HS256",
                "crit": ["b64"],
            }
        )


@pytest.mark.parametrize("crit", ["b64", b"b64", 123, []])
def test_rejects_invalid_crit_shape(crit) -> None:
    with pytest.raises(InvalidCriticalHeaderError, match="crit must be a non-empty array"):
        validate_jwt_critical_headers({"alg": "HS256", "crit": crit})


def test_accepts_supported_extension_when_present() -> None:
    validate_jwt_critical_headers(
        {
            "alg": "HS256",
            "crit": ["b64"],
            "b64": False,
        }
    )
