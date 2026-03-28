from pathlib import Path

from src.backend.auth.session_manager import AuthManager
from src.backend.genesis_core.models.auth import IdentityProfile, TokenSet


def test_auth_manager_creates_parent_directory_on_save(tmp_path: Path) -> None:
    store_path = tmp_path / "runtime" / "auth" / "auth_sessions.json"
    manager = AuthManager(filepath=str(store_path))

    manager.upsert_user(
        user_id="user-123",
        identity=IdentityProfile(provider="mock", sub="sub-123", email="user@example.com"),
        tokens=TokenSet(access_token="token", expires_at=9999999999),
    )

    assert store_path.exists()

    reloaded = AuthManager(filepath=str(store_path))
    session = reloaded.get_user("user-123")

    assert session is not None
    assert session.identity.email == "user@example.com"
