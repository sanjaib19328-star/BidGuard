import re
from typing import Any, Dict, List, Optional
from app.models.enums import DataSourceType, NameMatchVerdict, VerificationResultStatus
from app.services.name_matching_service import compare_legal_names
from app.services.verification.base_adapter import AdapterResult, BaseVerificationAdapter, sanitize_payload
from app.services.verification.benchmark_registry import UDYAM_BENCHMARK_REGISTRY

RE_UDYAM_FORMAT = re.compile(r"^UDYAM-[A-Z]{2}-[0-9]{2}-[0-9]{7}$", re.IGNORECASE)


class UdyamVerificationAdapter(BaseVerificationAdapter):
    """Adapter for Ministry of MSME Udyam Registration Portal verification."""

    async def verify(
        self,
        identifier: str,
        bidder_legal_name: Optional[str] = None,
        auth_config: Optional[Dict[str, Any]] = None,
        is_sandbox: bool = True,
    ) -> AdapterResult:
        clean_udyam = identifier.strip().upper()

        # 1. Format validation
        if not RE_UDYAM_FORMAT.match(clean_udyam):
            return AdapterResult(
                source_type=DataSourceType.UDYAM_MSME,
                status=VerificationResultStatus.INVALID_FORMAT,
                sanitized_response={"udyam_registration_number": clean_udyam, "error": "Invalid Udyam format"},
                matched_fields={"udyam_number": False},
                name_match_score=None,
                name_match_verdict=None,
                discrepancies=[{"field": "udyam_registration_number", "issue": "Format must be UDYAM-XX-00-0000000"}],
                officer_action_required=True,
                recommended_action="Request bidder to submit valid official Udyam Registration Certificate",
            )

        # 2. Strict Live-Mode Credential Check
        if not is_sandbox:
            has_credentials = auth_config and (auth_config.get("api_key") or auth_config.get("client_secret"))
            if not has_credentials:
                return AdapterResult(
                    source_type=DataSourceType.UDYAM_MSME,
                    status=VerificationResultStatus.AUTH_REQUIRED,
                    sanitized_response={"udyam_registration_number": clean_udyam, "message": "Authorized connection required. External government verification not executed."},
                    matched_fields=None,
                    name_match_score=None,
                    name_match_verdict=None,
                    discrepancies=None,
                    officer_action_required=True,
                    recommended_action="Configure authorized MSME API credentials in Settings or enable Sandbox/Benchmark mode",
                )

        # 3. Deterministic Sandbox/Benchmark Registry Lookup
        record = UDYAM_BENCHMARK_REGISTRY.get(clean_udyam)
        if not record:
            return AdapterResult(
                source_type=DataSourceType.UDYAM_MSME,
                status=VerificationResultStatus.NOT_FOUND,
                sanitized_response={"udyam_registration_number": clean_udyam, "message": "Udyam registration not found"},
                matched_fields={"udyam_number": False},
                name_match_score=None,
                name_match_verdict=None,
                discrepancies=[{"field": "udyam_registration_number", "issue": f"No Udyam record found for identifier {clean_udyam}"}],
                officer_action_required=True,
                recommended_action="Bidder claimed MSE benefits but Udyam registration is not verified; revoke MSE preference or request proof",
            )

        sanitized_rec = sanitize_payload(record)
        name_score = None
        verdict = None
        discrepancies = []
        status_result = VerificationResultStatus.VERIFIED
        officer_req = False
        action_msg = f"Udyam registration verified as {record.get('enterprise_type')} Enterprise under NIC {record.get('nic_code')}"

        if bidder_legal_name:
            udyam_name = record.get("legal_name", "")
            verdict, name_score, reason = compare_legal_names(bidder_legal_name, udyam_name)
            
            if verdict == NameMatchVerdict.SERIOUS_MISMATCH:
                status_result = VerificationResultStatus.MISMATCH
                officer_req = True
                discrepancies.append({
                    "field": "legal_name",
                    "bidder_value": bidder_legal_name,
                    "udyam_value": udyam_name,
                    "issue": reason,
                })
                action_msg = f"Entity mismatch: Bidder name '{bidder_legal_name}' does not match Udyam certificate enterprise '{udyam_name}'"
            elif verdict == NameMatchVerdict.POTENTIAL_MISMATCH:
                officer_req = True
                discrepancies.append({
                    "field": "legal_name",
                    "bidder_value": bidder_legal_name,
                    "udyam_value": udyam_name,
                    "issue": reason,
                })
                action_msg = "Potential name variation between bidder and Udyam certificate; verify manually"

        return AdapterResult(
            source_type=DataSourceType.UDYAM_MSME,
            status=status_result,
            sanitized_response=sanitized_rec,
            matched_fields={
                "udyam_number": True,
                "enterprise_type": record.get("enterprise_type"),
                "nic_code": record.get("nic_code"),
                "major_activity": record.get("major_activity"),
                "legal_name": verdict.value if verdict else "UNCHECKED",
            },
            name_match_score=name_score,
            name_match_verdict=verdict,
            discrepancies=discrepancies if discrepancies else None,
            officer_action_required=officer_req,
            recommended_action=action_msg,
        )
