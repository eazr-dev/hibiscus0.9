"""
Diagnostic script to check why some banks have empty logos.
Run: python scripts/check_missing_logos.py
"""
import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from pymongo import MongoClient
import certifi
import json

def check_logos():
    ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
    MONGODB_URI = os.getenv("MONGODB_URI_PRODUCTION") if ENVIRONMENT == "production" else os.getenv("MONGODB_URI_LOCAL", "mongodb://localhost:27017/")

    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000, tlsCAFile=certifi.where())
    db = client["Cards"]
    credit = db["credit_card"]
    debit = db["debit_card"]

    # Banks that returned empty logos
    empty_logo_banks = [
        "AB Bank", "Bandhan Bank", "Bank Of India", "Bank Of Maharashtra",
        "CSB Bank", "Canara Bank", "Central Bank Of India", "Citi Bank",
        "DBS Bank", "DCB Bank", "Dhanlaxmi Bank", "ESAF Small Finance Bank",
        "Equitas Small Finance Bank", "Indian Bank", "Indian Overseas Bank",
        "Karur Vysya Bank", "LIC", "Punjab National Bank", "SBM Bank",
        "South Indian Bank", "UCO Bank", "Union Bank Of India",
        "Utkarsh Small Finance Bank", "Arunachal Pradesh Rural Bank", "Aryavart Bank"
    ]

    print("=" * 80)
    print("CHECKING BANKS WITH EMPTY LOGOS IN credit_card COLLECTION")
    print("=" * 80)

    for bank in empty_logo_banks:
        # Find one doc for this bank
        doc = credit.find_one({"bank_name": {"$regex": f"^{bank}$", "$options": "i"}})
        if not doc:
            print(f"\n[{bank}] NOT FOUND in credit_card")
            continue

        # Show all fields (keys) of the document
        doc["_id"] = str(doc["_id"])
        print(f"\n[{bank}] Fields: {list(doc.keys())}")
        print(f"  logo field value: {repr(doc.get('logo'))}")
        print(f"  image_url field value: {repr(doc.get('image_url'))}")
        print(f"  bank_logo field value: {repr(doc.get('bank_logo'))}")
        print(f"  icon field value: {repr(doc.get('icon'))}")

        # Check ALL docs for this bank to see if ANY have a logo
        logo_count = credit.count_documents({
            "bank_name": {"$regex": f"^{bank}$", "$options": "i"},
            "logo": {"$nin": [None, "", " "]}
        })
        total_count = credit.count_documents({"bank_name": {"$regex": f"^{bank}$", "$options": "i"}})
        print(f"  Docs with non-empty logo: {logo_count}/{total_count}")

    print("\n" + "=" * 80)
    print("CHECKING IF LOGOS EXIST IN debit_card COLLECTION FOR SAME BANKS")
    print("=" * 80)

    for bank in empty_logo_banks:
        doc = debit.find_one({"bank_name": {"$regex": f"^{bank}$", "$options": "i"}})
        if doc:
            print(f"\n[{bank}] FOUND in debit_card")
            print(f"  logo: {repr(doc.get('logo'))}")
            print(f"  image_url: {repr(doc.get('image_url'))}")
        else:
            print(f"\n[{bank}] NOT in debit_card either")

    client.close()


if __name__ == "__main__":
    check_logos()
