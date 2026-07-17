"""Service-role token for backend agents.

Backend agents authenticate to Supabase using the service_role key, which
bypasses RLS. This is intentional — agents write to their designated schemas.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceRoleToken:
    """Service role credentials for backend agents."""
    key: str
    supabase_url: str

    @property
    def headers(self) -> dict[str, str]:
        return {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
        }
