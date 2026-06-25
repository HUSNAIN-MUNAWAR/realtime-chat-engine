from app.security.jwt import create_access_token, decode_token
from app.security.passwords import hash_password, verify_password

def test_password_hash_roundtrip():
    hashed = hash_password("StrongPass123!")
    assert hashed != "StrongPass123!"
    assert verify_password("StrongPass123!", hashed)

def test_jwt_roundtrip():
    token = create_access_token("user-1", "admin")
    payload = decode_token(token)
    assert payload["sub"] == "user-1"
    assert payload["role"] == "admin"
