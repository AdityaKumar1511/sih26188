"""
Database / Supabase Integration Module
Handles cross-checking extracted identity credentials against the mock government identity registry.
Includes in-memory mock fallback for offline or zero-configuration development.
"""

import os
import re
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "") or os.getenv("SUPABASE_ANON_KEY", "")

supabase_client = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client, Client
        supabase_client: Optional[Client] = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client initialized successfully.")
    except Exception as e:
        logger.warning(f"Could not connect to Supabase: {e}. Fallback to mock registry.")
        supabase_client = None
else:
    logger.info("SUPABASE_URL or SUPABASE_KEY not provided. Using in-memory mock registry.")


# ==============================================================================
# IN-MEMORY FALLBACK REGISTRY (Pre-seeded valid and test government records)
# ==============================================================================

MOCK_REGISTRY = [
    {
        "doc_type": "AADHAAR",
        "id_number": "548921049811",
        "full_name": "RAJESH KUMAR SHARMA",
        "dob": "1988-08-14",
        "gender": "MALE",
        "status": "ACTIVE",
        "issuer": "UIDAI"
    },
    {
        "doc_type": "AADHAAR",
        "id_number": "984277102391",
        "full_name": "ANANYA VERMA",
        "dob": "1992-11-22",
        "gender": "FEMALE",
        "status": "ACTIVE",
        "issuer": "UIDAI"
    },
    {
        "doc_type": "PAN",
        "id_number": "ABCPM1234F",
        "full_name": "VIKRAM SINGH MEHTA",
        "father_name": "HARISH CHANDRA MEHTA",
        "dob": "1982-05-12",
        "status": "ACTIVE",
        "issuer": "INCOME_TAX_DEPT"
    },
    {
        "doc_type": "PAN",
        "id_number": "BKZPR8491K",
        "full_name": "PRIYA SHARMA",
        "father_name": "RAMESH SHARMA",
        "dob": "1995-03-24",
        "status": "ACTIVE",
        "issuer": "INCOME_TAX_DEPT"
    }
]


def normalize_id(id_str: str) -> str:
    """Removes spaces, dashes, and normalizes uppercase."""
    return re.sub(r'[\s\-]', '', str(id_str).strip()).upper()


async def cross_check_record(
    doc_type: str,
    id_number: str,
    extracted_name: Optional[str] = None,
    extracted_dob: Optional[str] = None
) -> Dict[str, Any]:
    """
    Cross-checks the document against Supabase government_id_registry table.
    Returns:
    - exists_in_db: bool
    - status: 'ACTIVE' | 'REVOKED' | 'NOT_FOUND'
    - name_matched: bool | None
    - record_details: dict | None
    """
    clean_id = normalize_id(id_number)
    clean_doc_type = doc_type.strip().upper()

    # 1. Try Supabase Query with strict timeout protection
    if supabase_client is not None:
        try:
            import asyncio
            def _query_supabase():
                return supabase_client.table("government_id_registry") \
                    .select("*") \
                    .eq("doc_type", clean_doc_type) \
                    .eq("id_number", clean_id) \
                    .execute()

            response = await asyncio.wait_for(asyncio.to_thread(_query_supabase), timeout=2.0)

            if response.data and len(response.data) > 0:
                record = response.data[0]
                db_name = record.get("full_name", "").upper()
                name_match = None
                if extracted_name:
                    # Partial / Levenshtein substring match
                    clean_extracted_name = extracted_name.strip().upper()
                    name_match = (clean_extracted_name in db_name) or (db_name in clean_extracted_name)

                return {
                    "exists_in_db": True,
                    "status": record.get("status", "ACTIVE"),
                    "name_matched": name_match,
                    "db_record": {
                        "registered_name": record.get("full_name"),
                        "registered_dob": record.get("dob"),
                        "status": record.get("status"),
                        "issuer": record.get("issuer")
                    },
                    "source": "supabase"
                }
        except Exception as e:
            logger.warning(f"Supabase lookup timed out or failed: {e}. Falling back to in-memory registry.")

    # 2. Fallback in-memory query
    matched = next((
        r for r in MOCK_REGISTRY
        if r["doc_type"] == clean_doc_type and normalize_id(r["id_number"]) == clean_id
    ), None)

    if matched:
        db_name = matched["full_name"].upper()
        name_match = None
        if extracted_name:
            clean_extracted = extracted_name.strip().upper()
            name_match = (clean_extracted in db_name) or (db_name in clean_extracted)

        return {
            "exists_in_db": True,
            "status": matched["status"],
            "name_matched": name_match,
            "db_record": {
                "registered_name": matched["full_name"],
                "registered_dob": matched["dob"],
                "status": matched["status"],
                "issuer": matched["issuer"]
            },
            "source": "in-memory-mock"
        }

    return {
        "exists_in_db": False,
        "status": "NOT_FOUND",
        "name_matched": False,
        "db_record": None,
        "source": "supabase" if supabase_client else "in-memory-mock"
    }
