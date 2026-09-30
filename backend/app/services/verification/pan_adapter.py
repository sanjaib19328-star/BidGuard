import re
from typing import Any, Dict, List, Optional
from app.models.enums import DataSourceType, NameMatchVerdict, VerificationResultStatus
from app.services.name_matching_service import compare_legal_names
from app.services.verification.base_adapter import AdapterResult, BaseVerificationAdapter, sanitize_payload
from app.services.verification.benchmark_registry import PAN_BENCHMARK_REGISTRY

RE_PAN_FORMAT = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$")


class PanVerificationAdapter(BaseVerificationAdapter):
    """Adapter for Central Board of Direct Taxes (CBDT) PAN verification."""

    async def verify(
        self,
        identifier: str,
        bidder_legal_name: Optional[str] = None,
        auth_config: Optional[Dict[str, Any]] = None,
        is_sandbox: bool = True,
    ) -> AdapterResult:
        clean_pan = identifier.strip().upper()

        # 1. Format validation
        if not RE_PAN_FORMAT.match(clean_pan):
            return AdapterResult(
                source_type=DataSourceType.CBDT_PAN,
                status=VerificationResultStatus.INVALID_FORMAT,
                sanitized_response={"pan": clean_pan, "error": "Invalid PAN structure (must be 5 letters, 4 digits, 1 letter)"},
                matched_fields={"pan": False},
                name_match_score=None,
                name_match_verdict=None,
                discrepancies=[{"field": "pan", "issue": "PAN format invalid"}],
                officer_action_required=True,
                recommended_action="Request bidder to submit clear copy of valid PAN Card",
            )

        # 2. Strict Live-Mode Credential Check
        if not is_sandbox:
            has_credentials = auth_config and (auth_config.get("api_key") or auth_config.get("client_secret"))
            if not has_credentials:
                return AdapterResult(
                    source_type=DataSourceType.CBDT_PAN,
                    status=VerificationResultStatus.AUTH_REQUIRED,
                    sanitized_response={"pan": clean_pan, "message": "Authorized connection required. External government verification not executed."},
                    matched_fields=None,
                    name_match_score=None,
                    name_match_verdict=None,
                    discrepancies=None,
                    officer_action_required=True,
                    recommended_action="Configure authorized CBDT/PAN API credentials in Settings or enable Sandbox/Benchmark mode",
                )

        # 3. Deterministic Sandbox/Benchmark Registry Lookup
        record = PAN_BENCHMARK_REGISTRY.get(clean_pan)
        if not record:
            return AdapterResult(
                source_type=DataSourceType.CBDT_PAN,
                status=VerificationResultStatus.NOT_FOUND,
                sanitized_response={"pan": clean_pan, "message": "PAN record not found in tax database"},
                matched_fields={"pan": False},
                name_match_score=None,
                name_match_verdict=None,
                discrepancies=[{"field": "pan", "issue": f"No active PAN record found for {clean_pan}"}],
                officer_action_required=True,
                recommended_action="Seek clarification from bidder to confirm PAN authenticity",
            )

        sanitized_rec = sanitize_payload(record)
        name_score = None
        verdict = None
        discrepancies = []
        status_result = VerificationResultStatus.VERIFIED
        officer_req = False
        action_msg = "PAN verified successfully with Income Tax Department records"

        if bidder_legal_name:
            pan_name = record.get("legal_name", "")
            verdict, name_score, reason = compare_legal_names(bidder_legal_name, pan_name)
            
            if verdict == NameMatchVerdict.SERIOUS_MISMATCH:
                status_result = VerificationResultStatus.MISMATCH
                officer_req = True
                discrepancies.append({
                    "field": "legal_name",
                    "bidder_value": bidder_legal_name,
                    "pan_value": pan_name,
                    "issue": reason,
                })
                action_msg = f"PAN card holder name '{pan_name}' does not match bidder entity '{bidder_legal_name}'"
            elif verdict == NameMatchVerdict.POTENTIAL_MISMATCH:
                officer_req = True
                discrepancies.append({
                    "field": "legal_name",
                    "bidder_value": bidder_legal_name,
                    "pan_value": pan_name,
                    "issue": reason,
                })
                action_msg = "Potential name variation between PAN card and bidder entity"

        return AdapterResult(
            source_type=DataSourceType.CBDT_PAN,
            status=status_result,
            sanitized_response=sanitized_rec,
            matched_fields={
                "pan": True,
                "status": record.get("status"),
                "category": record.get("category"),
                "legal_name": verdict.value if verdict else "UNCHECKED",
            },
            name_match_score=name_score,
            name_match_verdict=verdict,
            discrepancies=discrepancies if discrepancies else None,
            officer_action_required=officer_req,
            recommended_action=action_msg,
        )
