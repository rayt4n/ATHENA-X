"""Supabase JWT verifier.

Verifies access tokens issued by Supabase Auth. Used by FastAPI dependencies
to protect user-facing endpoints.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import time

import httpx
import jwt
from jwt import PyJWKClient

from athena_x_runtime_logger import get_logger

log = get_logger("runtime.auth")


@dataclass(frozen=True)
class AuthUser:
    """Authenticated user extracted from JWT."""
    id: str
    email: str | None
    role: str
    raw_claims: dict[str, Any]


class JWTVerifier:
    """Verifies Supabase JWT access tokens.

    Fetches the JWKS (JSON Web Key Set) from Supabase Auth on first use,
    caches it, and uses it to verify token signatures.
    """

    def __init__(self, supabase_url: str, supabase_anon_key: str,
                 jwks_cache_ttl_seconds: int = 3600):
        self._supabase_url = supabase_url.rstrip("/")
        self._anon_key = supabase_anon_key
        self._jwks_url = f"{self._supabase_url}/auth/v1/.well-known/jwks.json"
        self._jwks_cache_ttl = jwks_cache_ttl_seconds
        # PyJWKClient lazily fetches keys on first verification
        self._jwks_client = PyJWKClient(self._jwks_url)

    def verify(self, token: str) -> AuthUser:
        """Verify a JWT and return the authenticated user.

        Raises:
            jwt.InvalidTokenError: if the token is invalid, expired, or malformed.
        """
        # Supabase JWTs are signed with the JWT secret, but newer versions use
        # asymmetric keys (RS256). PyJWKClient handles both.
        signing_key = self._jwks_client.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256", "HS256"],
            audience="authenticated",
            options={"verify_aud": False},  # Supabase doesn't always set aud
        )

        return AuthUser(
            id=claims.get("sub", ""),
            email=claims.get("email"),
            role=claims.get("role", "authenticated"),
            raw_claims=claims,
        )

    async def verify_async(self, token: str) -> AuthUser:
        """Async variant — runs sync verify in a thread."""
        import asyncio
        return await asyncio.to_thread(self.verify, token)


# FastAPI dependency factory
def create_auth_dependency(verifier: JWTVerifier):
    """Create a FastAPI dependency that verifies the Authorization header.

    Usage:
        verifier = JWTVerifier(supabase_url, anon_key)
        authenticate = create_auth_dependency(verifier)

        @app.get("/protected")
        async def protected(user: AuthUser = Depends(authenticate)):
            return {"user_id": user.id}
    """
    from fastapi import Depends, HTTPException, Request, status

    async def authenticate(request: Request) -> AuthUser:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid Authorization header",
            )
        token = auth_header[7:]
        try:
            return await verifier.verify_async(token)
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {e}",
            )

    return authenticate
