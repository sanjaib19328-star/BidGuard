"""Deterministic benchmark government registry records for sandbox verification.

These records mirror official public records for the CPCL Pressure Vessel tender reference data.
"""
from typing import Any, Dict, Optional

GST_BENCHMARK_REGISTRY: Dict[str, Dict[str, Any]] = {
    "33AAACA1234A1Z5": {
        "gstin": "33AAACA1234A1Z5",
        "legal_name": "Apex Heavy Engineering Private Limited",
        "trade_name": "Apex Heavy Engineering",
        "status": "ACTIVE",
        "registration_date": "2017-07-01",
        "taxpayer_type": "Regular",
        "state_code": "33",
        "state_name": "Tamil Nadu",
        "address": "Plot 42, Heavy Industrial Estate, Ambattur, Chennai, Tamil Nadu - 600058",
        "constitution_of_business": "Private Limited Company",
    },
    "27AAACB5678B1Z8": {
        "gstin": "27AAACB5678B1Z8",
        "legal_name": "Bharat Fabricators Private Limited",
        "trade_name": "Bharat Fabricators",
        "status": "ACTIVE",
        "registration_date": "2018-09-14",
        "taxpayer_type": "Regular",
        "state_code": "27",
        "state_name": "Maharashtra",
        "address": "Plot 18, MIDC Bhosari, Pune, Maharashtra - 411026",
        "constitution_of_business": "Private Limited Company",
    },
    "33AAACC9988C1Z2": {
        "gstin": "33AAACC9988C1Z2",
        "legal_name": "Chennai Pressure Systems Private Limited",
        "trade_name": "CPS Heavy Equipment",
        "status": "ACTIVE",
        "registration_date": "2019-02-10",
        "taxpayer_type": "Regular",
        "state_code": "33",
        "state_name": "Tamil Nadu",
        "address": "Guindy Industrial Estate, Chennai, Tamil Nadu - 600032",
        "constitution_of_business": "Private Limited Company",
    },
    "24AAACD4433D1Z9": {
        "gstin": "24AAACD4433D1Z9",
        "legal_name": "Delta Vessels Corporation",
        "trade_name": "Delta Vessels",
        "status": "ACTIVE",
        "registration_date": "2016-04-20",
        "taxpayer_type": "Regular",
        "state_code": "24",
        "state_name": "Gujarat",
        "address": "GIDC Industrial Area, Vadodara, Gujarat - 390010",
        "constitution_of_business": "Corporation",
    },
    "19AAACE7766E1Z4": {
        "gstin": "19AAACE7766E1Z4",
        "legal_name": "Eastern Process Equipments Ltd",
        "trade_name": "Eastern Process",
        "status": "ACTIVE",
        "registration_date": "2015-11-05",
        "taxpayer_type": "Regular",
        "state_code": "19",
        "state_name": "West Bengal",
        "address": "Salt Lake Sector V, Kolkata, West Bengal - 700091",
        "constitution_of_business": "Public Limited Company",
    },
}

UDYAM_BENCHMARK_REGISTRY: Dict[str, Dict[str, Any]] = {
    "UDYAM-TN-02-0012345": {
        "udyam_registration_number": "UDYAM-TN-02-0012345",
        "legal_name": "Apex Heavy Engineering Private Limited",
        "enterprise_type": "Small",
        "major_activity": "Manufacturing",
        "nic_code": "2512",
        "nic_description": "Manufacture of tanks, reservoirs and containers of metal",
        "status": "ACTIVE",
        "registration_date": "2020-08-12",
        "state_name": "Tamil Nadu",
    },
    "UDYAM-MH-18-0054321": {
        "udyam_registration_number": "UDYAM-MH-18-0054321",
        "legal_name": "Bharat Fabricators Private Limited",
        "enterprise_type": "Medium",
        "major_activity": "Manufacturing",
        "nic_code": "2512",
        "nic_description": "Manufacture of tanks, reservoirs and containers of metal",
        "status": "ACTIVE",
        "registration_date": "2021-01-20",
        "state_name": "Maharashtra",
    },
    "UDYAM-TN-03-0099881": {
        "udyam_registration_number": "UDYAM-TN-03-0099881",
        "legal_name": "Chennai Pressure Systems LLP", # Mismatch against GST Private Limited
        "enterprise_type": "Micro",
        "major_activity": "Manufacturing",
        "nic_code": "2512",
        "nic_description": "Manufacture of metal pressure tanks",
        "status": "ACTIVE",
        "registration_date": "2021-06-15",
        "state_name": "Tamil Nadu",
    },
}

PAN_BENCHMARK_REGISTRY: Dict[str, Dict[str, Any]] = {
    "AAACA1234A": {
        "pan": "AAACA1234A",
        "legal_name": "Apex Heavy Engineering Private Limited",
        "status": "ACTIVE",
        "category": "Company",
        "masked_aadhaar": None,
    },
    "AAACB5678B": {
        "pan": "AAACB5678B",
        "legal_name": "Bharat Fabricators Private Limited",
        "status": "ACTIVE",
        "category": "Company",
    },
    "AAACC9988C": {
        "pan": "AAACC9988C",
        "legal_name": "Chennai Pressure Systems Private Limited",
        "status": "ACTIVE",
        "category": "Company",
    },
    "AAACD4433D": {
        "pan": "AAACD4433D",
        "legal_name": "Delta Vessels Corporation",
        "status": "ACTIVE",
        "category": "Company",
    },
}
