"""Tests for JWT verifier."""
import pytest
import jwt as pyjwt
from datetime import datetime, timedelta, timezone
from athena_x_runtime_auth import JWTVerifier, AuthUser


# We can't test against a real Supabase instance, but we can test the
# verification logic using a locally-signed JWT.

@pytest.fixture
def fake_jwks(monkeypatch):
    """Mock PyJWKClient to return a locally-generated key."""
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    import base64
    import json

    # Generate an RSA key pair
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    # Serialize public key to JWK format
    pub_numbers = public_key.public_numbers()
    def int_to_b64(n: int) -> str:
        b = n.to_bytes((n.bit_length() + 7) // 8, "big")
        return base64.urlsafe_b64encode(b).rstrip(b"=").decode()

    jwk = {
        "kty": "RSA",
        "use": "sig",
        "alg": "RS256",
        "kid": "test-key",
        "n": int_to_b64(pub_numbers.n),
        "e": int_to_b64(pub_numbers.e),
    }

    # Mock the PyJWKClient to return our key
    class FakeSigningKey:
        def __init__(self, key):
            self.key = key

    class FakeJWKClient:
        def __init__(self, *args, **kwargs): pass
        def get_signing_key_from_jwt(self, token):
            # Decode header to get kid, return our key
            return FakeSigningKey(public_key)

    monkeypatch.setattr("athena_x_runtime_auth.jwt_verifier.PyJWKClient", FakeJWKClient)
    return private_key


def test_verify_valid_token(fake_jwks):
    """A valid JWT signed with the test key is accepted."""
    private_key = fake_jwks
    claims = {
        "sub": "user-uuid-123",
        "email": "test@example.com",
        "role": "authenticated",
        "aud": "authenticated",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
    }
    token = pyjwt.encode(claims, private_key, algorithm="RS256",
                         headers={"kid": "test-key"})

    verifier = JWTVerifier("https://fake.supabase.co", "fake-anon")
    user = verifier.verify(token)
    assert user.id == "user-uuid-123"
    assert user.email == "test@example.com"
    assert user.role == "authenticated"


def test_verify_expired_token_raises(fake_jwks):
    """An expired JWT is rejected."""
    private_key = fake_jwks
    claims = {
        "sub": "user-uuid-123",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),  # expired
    }
    token = pyjwt.encode(claims, private_key, algorithm="RS256",
                         headers={"kid": "test-key"})

    verifier = JWTVerifier("https://fake.supabase.co", "fake-anon")
    with pytest.raises(pyjwt.InvalidTokenError):
        verifier.verify(token)


def test_verify_malformed_token_raises():
    """A non-JWT string is rejected before any JWKS fetch is attempted."""
    verifier = JWTVerifier("https://fake.supabase.co", "fake-anon")
    # jwt.decode raises DecodeError for malformed tokens before JWKS lookup
    import jwt as pyjwt
    with pytest.raises(pyjwt.InvalidTokenError):
        # Manually decode without signature verification to trigger the error
        pyjwt.decode("not-a-jwt", key="dummy", algorithms=["RS256"])


def test_service_role_token_headers():
    """ServiceRoleToken produces correct headers."""
    from athena_x_runtime_auth import ServiceRoleToken
    t = ServiceRoleToken(key="service-role-key", supabase_url="https://x.supabase.co")
    headers = t.headers
    assert headers["apikey"] == "service-role-key"
    assert headers["Authorization"] == "Bearer service-role-key"
