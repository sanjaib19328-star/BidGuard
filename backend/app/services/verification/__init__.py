from app.services.verification.base_adapter import (
    AdapterResult,
    BaseVerificationAdapter,
    sanitize_payload,
)
from app.services.verification.gst_adapter import GstVerificationAdapter
from app.services.verification.udyam_adapter import UdyamVerificationAdapter
from app.services.verification.pan_adapter import PanVerificationAdapter

ADAPTERS = {
    "GSTN_PORTAL": GstVerificationAdapter(),
    "UDYAM_MSME": UdyamVerificationAdapter(),
    "CBDT_PAN": PanVerificationAdapter(),
}

__all__ = [
    "BaseVerificationAdapter",
    "AdapterResult",
    "sanitize_payload",
    "GstVerificationAdapter",
    "UdyamVerificationAdapter",
    "PanVerificationAdapter",
    "ADAPTERS",
]
