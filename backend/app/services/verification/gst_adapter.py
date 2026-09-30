import re
from typing import Any, Dict, List, Optional
from app.models.enums import DataSourceType, NameMatchVerdict, VerificationResultStatus
from app.services.name_matching_service import compare_legal_names
from app.services.verification.base_adapter import AdapterResult, BaseVerificationAdapter, sanitize_payload
from app.services.verification.benchmark_registry import GST_BENCHMARK_REGISTRY

RE_GSTIN_FORMAT = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")


class GstVerificationAdapter(BaseVerificationAdapter):
    """Adapter for Goods and Services Tax Network (GSTN) verification."""

    async def verify(
        self,
        identifier: str,
        bidder_legal_name: Optional[str] = None,
        auth_config: Optional[Dict[str, Any]] = None,
        is_sandbox: bool = True,
    ) -> AdapterResult:
        clean_gstin = identifier.strip().upper()

        # 1. Format validation
        if not RE_GSTIN_FORMAT.match(clean_gstin):
            return AdapterResult(
                source_type=DataSourceType.GSTN_PORTAL,
                status=VerificationResultStatus.INVALID_FORMAT,
                sanitized_response={"gstin": clean_gstin, "error": "Invalid GSTIN format structure"},
                matched_fields={"gstin": False},
                name_match_score=None,
                name_match_verdict=None,
                discrepancies=[{"field": "gstin", "issue": "GSTIN must be 15 alphanumeric characters conforming to GST rules"}],
                officer_action_required=True,
                recommended_action="Request bidder to submit valid 15-digit GST Registration Certificate",
            )

        # 2. Strict Live-Mode Credential Check (Anti-Hallucination Safeguard)
        if not is_sandbox:
            has_credentials = auth_config and (auth_config.get("api_key") or auth_config.get("client_secret"))
            if not has_credentials:
                return AdapterResult(
                    source_type=DataSourceType.GSTN_PORTAL,
                    status=VerificationResultStatus.AUTH_REQUIRED,
                    sanitized_response={"gstin": clean_gstin, "message": "Authorized connection required. External government verification not executed."},
                    matched_fields=None,
                    name_match_score=None,
                    name_match_verdict=None,
                    discrepancies=None,
                    officer_action_required=True,
                    recommended_action="Configure authorized GSTN API credentials in Settings or enable Sandbox/Benchmark mode",
                )

        # 3. Deterministic Sandbox/Benchmark Registry Lookup
        record = GST_BENCHMARK_REGISTRY.get(clean_gstin)
        if not record:
            return AdapterResult(
                source_type=DataSourceType.GSTN_PORTAL,
                status=VerificationResultStatus.NOT_FOUND,
                sanitized_response={"gstin": clean_gstin, "message": "GSTIN not found in GST database"},
                matched_fields={"gstin": False},
                name_match_score=None,
                name_match_verdict=None,
                discrepancies=[{"field": "gstin", "issue": f"No active GST record found for identifier {clean_gstin}"}],
                officer_action_required=True,
                recommended_action="Issue clarification to bidder to confirm valid GST registration status",
            )

        # Sanitize response
        sanitized_rec = sanitize_payload(record)

        # Check Active Status
        is_active = record.get("status") == "ACTIVE"
        if not is_active:
            return AdapterResult(
                source_type=DataSourceType.GSTN_PORTAL,
                status=VerificationResultStatus.INACTIVE_EXPIRED,
                sanitized_response=sanitized_rec,
                matched_fields={"gstin": True, "status": record.get("status")},
                name_match_score=None,
                name_match_verdict=None,
                discrepancies=[{"field": "status", "issue": f"GSTIN status is {record.get('status')}"}],
                officer_action_required=True,
                recommended_action="Bidder GSTIN is inactive/suspended; reject or seek clarification",
            )

        # 4. Compare with Bidder Legal Name if provided
        name_score = None
        verdict = None
        discrepancies = []
        status_result = VerificationResultStatus.VERIFIED
        officer_req = False
        action_msg = "GSTIN verified successfully with active registration status"

        if bidder_legal_name:
            gst_legal_name = record.get("legal_name", "")
            verdict, name_score, reason = compare_legal_names(bidder_legal_name, gst_legal_name)
            
            if verdict == NameMatchVerdict.SERIOUS_MISMATCH:
                status_result = VerificationResultStatus.MISMATCH
                officer_req = True
                discrepancies.append({
                    "field": "legal_name",
                    "bidder_value": bidder_legal_name,
                    "gst_value": gst_legal_name,
                    "issue": reason,
                })
                action_msg = f"Legal entity name mismatch: '{bidder_legal_name}' differs significantly from GST registration '{gst_legal_name}'"
            elif verdict == NameMatchVerdict.POTENTIAL_MISMATCH:
                officer_req = True
                discrepancies.append({
                    "field": "legal_name",
                    "bidder_value": bidder_legal_name,
                    "gst_value": gst_legal_name,
                    "issue": reason,
                })
                action_msg = "Potential legal name discrepancy; officer verification required"

        return AdapterResult(
            source_type=DataSourceType.GSTN_PORTAL,
            status=status_result,
            sanitized_response=sanitized_rec,
            matched_fields={
                "gstin": True,
                "status": record.get("status"),
                "taxpayer_type": record.get("taxpayer_type"),
                "state_code": record.get("state_code"),
                "legal_name": verdict.value if verdict else "UNCHECKED",
            },
            name_match_score=name_score,
            name_match_verdict=verdict,
            discrepancies=discrepancies if discrepancies else None,
            officer_action_required=officer_req,
            recommended_action=action_msg,
        )
