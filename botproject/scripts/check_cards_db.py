"""
Script to check MongoDB Cards database connection and data
Run: python scripts/check_cards_db.py
"""
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

from pymongo import MongoClient
import certifi
import json

def check_cards_database():
    """Check MongoDB connection and Cards database"""

    # Get MongoDB URI
    ENVIRONMENT = os.getenv("ENVIRONMENT", "local")

    if ENVIRONMENT == "production":
        MONGODB_URI = os.getenv("MONGODB_URI_PRODUCTION")
        print(f"🚀 Using PRODUCTION MongoDB")
    else:
        MONGODB_URI = os.getenv("MONGODB_URI_LOCAL", "mongodb://localhost:27017/")
        print(f"🔧 Using LOCAL MongoDB")

    if not MONGODB_URI:
        print("❌ MONGODB_URI not set!")
        return

    # Mask password in URI for display
    display_uri = MONGODB_URI
    if "@" in MONGODB_URI:
        parts = MONGODB_URI.split("@")
        display_uri = parts[0][:20] + "****@" + parts[1]
    print(f"📡 MongoDB URI: {display_uri}")

    try:
        # Connect to MongoDB
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            tlsCAFile=certifi.where()
        )

        # Test connection
        client.admin.command('ping')
        print("✅ MongoDB connection successful!")

        # Check Cards database
        db = client["Cards"]

        print("\n📁 Collections in 'Cards' database:")
        for coll_name in db.list_collection_names():
            count = db[coll_name].count_documents({})
            print(f"   - {coll_name}: {count} documents")

        # Check credit_card collection
        print("\n📄 Sample Credit Card document:")
        credit_sample = db["credit_card"].find_one()
        if credit_sample:
            credit_sample["_id"] = str(credit_sample["_id"])
            print(json.dumps(credit_sample, indent=2, default=str)[:1000])
        else:
            print("   No documents found")

        # Check debit_card collection
        print("\n📄 Sample Debit Card document:")
        debit_sample = db["debit_card"].find_one()
        if debit_sample:
            debit_sample["_id"] = str(debit_sample["_id"])
            print(json.dumps(debit_sample, indent=2, default=str)[:1000])
        else:
            print("   No documents found")

        # Check unique bank names
        print("\n🏦 Unique Bank Names in credit_card:")
        credit_banks = db["credit_card"].distinct("bank_name")
        for bank in credit_banks[:10]:
            print(f"   - {bank}")
        if len(credit_banks) > 10:
            print(f"   ... and {len(credit_banks) - 10} more")

        print("\n🏦 Unique Bank Names in debit_card:")
        debit_banks = db["debit_card"].distinct("bank_name")
        for bank in debit_banks[:10]:
            print(f"   - {bank}")
        if len(debit_banks) > 10:
            print(f"   ... and {len(debit_banks) - 10} more")

        client.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_cards_database()
