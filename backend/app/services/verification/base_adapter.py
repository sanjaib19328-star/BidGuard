from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from app.models.enums import DataSourceType, NameMatchVerdict, VerificationResultStatus

# Sensitive keys that must be stripped before any external payload is persisted
SENSITIVE_KEY_PATTERNS = {"token", "secret", "password", "authorization", "auth", "api_key", "apikey", "bearer", "private_key"}


def sanitize_payload(data: Any) -> Any:
    """Recursively sanitize payloads so credentials, tokens, or auth headers can never enter the database."""
    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            k_lower = str(k).lower()
            if any(secret_term in k_lower for secret_term in SENSITIVE_KEY_PATTERNS):
                cleaned[k] = "[REDACTED_CREDENTIAL]"
            else:
                cleaned[k] = sanitize_payload(v)
        return cleaned
    elif isinstance(data, list):
        return [sanitize_payload(item) for item in data]
    return data


@dataclass
class AdapterResult:
    source_type: DataSourceType
    status: VerificationResultStatus
    sanitized_response: Optional[Dict[str, Any]]
    matched_fields: Optional[Dict[str, Any]]
    name_match_score: Optional[float]
    name_match_verdict: Optional[NameMatchVerdict]
    discrepancies: Optional[List[Dict[str, Any]]]
    officer_action_required: bool
    recommended_action: Optional[str]


class BaseVerificationAdapter(ABC):
    """Abstract interface for all government/open-data verification connectors."""

    @abstractmethod
    async def verify(
        self,
        identifier: str,
        bidder_legal_name: Optional[str] = None,
        auth_config: Optional[Dict[str, Any]] = None,
        is_sandbox: bool = True,
    ) -> AdapterResult:
        """Execute verification. If not sandbox and credentials missing, return AUTH_REQUIRED."""
        pass
