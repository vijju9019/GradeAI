import pytest
from app.core.security import get_password_hash, verify_password, create_access_token, decode_access_token

def test_password_hashing():
    raw = "AcademicSecure2026!"
    hashed = get_password_hash(raw)
    assert hashed != raw
    assert hashed.startswith("pbkdf2_sha256$")
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_jwt_token_creation_and_decoding():
    token = create_access_token(subject=42, role="teacher")
    assert isinstance(token, str)
    payload = decode_access_token(token)
    assert payload is not None
    assert payload.get("sub") == "42"
    assert payload.get("role") == "teacher"

def test_invalid_jwt_token():
    invalid_token = "invalid.bearer.token"
    payload = decode_access_token(invalid_token)
    assert payload is None
