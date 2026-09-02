"""
Seed script to populate mock Supabase registry records via Python SDK.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("[!] SUPABASE_URL or SUPABASE_KEY not found in environment.")
    print("    Skipping remote database seed. The FastAPI backend will automatically")
    print("    use the in-memory mock registry.")
    sys.exit(0)

try:
    from supabase import create_client
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    SEED_RECORDS = [
        {
            "doc_type": "AADHAAR",
            "id_number": "548921049811",
            "full_name": "RAJESH KUMAR SHARMA",
            "father_name": "RAMESH CHANDRA SHARMA",
            "dob": "1988-08-14",
            "gender": "MALE",
            "address": "H-42, Sector 62, Noida, Gautam Buddha Nagar, Uttar Pradesh 201301",
            "issuer": "UIDAI",
            "status": "ACTIVE"
        },
        {
            "doc_type": "AADHAAR",
            "id_number": "984277102391",
            "full_name": "ANANYA VERMA",
            "father_name": "SURESH VERMA",
            "dob": "1992-11-22",
            "gender": "FEMALE",
            "address": "Flat 402, Green Glen Layout, Bellandur, Bengaluru, Karnataka 560103",
            "issuer": "UIDAI",
            "status": "ACTIVE"
        },
        {
            "doc_type": "PAN",
            "id_number": "ABCPM1234F",
            "full_name": "VIKRAM SINGH MEHTA",
            "father_name": "HARISH CHANDRA MEHTA",
            "dob": "1982-05-12",
            "gender": "MALE",
            "address": "Plot 12, Civil Lines, Jaipur, Rajasthan 302006",
            "issuer": "INCOME_TAX_DEPT",
            "status": "ACTIVE"
        },
        {
            "doc_type": "PAN",
            "id_number": "BKZPS8491K",
            "full_name": "PRIYA SHARMA",
            "father_name": "RAMESH SHARMA",
            "dob": "1995-03-24",
            "gender": "FEMALE",
            "address": "B-104, Sunrise Towers, Andheri East, Mumbai, Maharashtra 400069",
            "issuer": "INCOME_TAX_DEPT",
            "status": "ACTIVE"
        },
        {
            "doc_type": "AADHAAR",
            "id_number": "334455667788",
            "full_name": "FRAUD TEST USER",
            "father_name": "UNKNOWN",
            "dob": "1990-01-01",
            "gender": "MALE",
            "address": "De-listed Address",
            "issuer": "UIDAI",
            "status": "REVOKED"
        }
    ]

    print("[*] Seeding records into Supabase table 'government_id_registry'...")
    for rec in SEED_RECORDS:
        res = supabase.table("government_id_registry").upsert(rec, on_conflict="doc_type,id_number").execute()
        print(f" [+] Upserted: {rec['doc_type']} - {rec['id_number']} ({rec['full_name']})")

    print("[PASS] Supabase database seed completed successfully!")

except Exception as err:
    print(f"[ERROR] Error during Supabase seeding: {err}")
