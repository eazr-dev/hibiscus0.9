"""
Card Service
Business logic for credit and debit card operations
Uses production MongoDB with insurance_analysis_db database
"""
import logging
import requests
from typing import List, Dict, Any, Optional
import os
from pymongo import MongoClient
import certifi

logger = logging.getLogger(__name__)

# MongoDB Configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

# Get MongoDB URI based on environment
if ENVIRONMENT == "production":
    MONGODB_URI = os.getenv("MONGODB_URI_PRODUCTION")
    logger.info("🚀 Card Service: Using PRODUCTION MongoDB")
else:
    MONGODB_URI = os.getenv("MONGODB_URI_LOCAL", "mongodb://localhost:27017/")
    logger.info("🔧 Card Service: Using LOCAL MongoDB")

# Card database name - always use "Cards" database
DATABASE_NAME = "Cards"

# Collection names from environment (default: credit_card, debit_card - singular)
CREDIT_CARD_COLLECTION = os.getenv("CREDIT_CARD_COLLECTION", "credit_card")
DEBIT_CARD_COLLECTION = os.getenv("DEBIT_CARD_COLLECTION", "debit_card")

# Bank name normalization mappings
BANK_MAPPINGS = {
    # HDFC variations
    'hdfc': 'hdfc',
    'hdfc bank': 'hdfc',
    'hdfc bank ltd': 'hdfc',
    'hdfc bank limited': 'hdfc',
    'housing development finance corporation': 'hdfc',

    # ICICI variations
    'icici': 'icici',
    'icici bank': 'icici',
    'icici bank ltd': 'icici',
    'icici bank limited': 'icici',
    'industrial credit and investment corporation of india': 'icici',

    # SBI variations
    'sbi': 'sbi',
    'state bank of india': 'sbi',
    'state bank': 'sbi',
    'sbi bank': 'sbi',

    # Axis variations
    'axis': 'axis',
    'axis bank': 'axis',
    'axis bank ltd': 'axis',
    'axis bank limited': 'axis',

    # Kotak variations
    'kotak': 'kotak',
    'kotak mahindra': 'kotak',
    'kotak mahindra bank': 'kotak',
    'kotak bank': 'kotak',

    # IndusInd variations
    'indusind': 'indusind',
    'indusind bank': 'indusind',
    'indusind bank ltd': 'indusind',

    # Yes Bank variations
    'yes': 'yes bank',
    'yes bank': 'yes bank',
    'yes bank ltd': 'yes bank',

    # IDFC variations
    'idfc': 'idfc',
    'idfc bank': 'idfc',
    'idfc first': 'idfc',
    'idfc first bank': 'idfc',

    # RBL variations
    'rbl': 'rbl',
    'rbl bank': 'rbl',
    'ratnakar bank': 'rbl',

    # Standard Chartered variations
    'standard chartered': 'standard chartered',
    'standard chartered bank': 'standard chartered',
    'sc bank': 'standard chartered',
    'scb': 'standard chartered',

    # HSBC variations
    'hsbc': 'hsbc',
    'hsbc bank': 'hsbc',
    'hongkong and shanghai banking corporation': 'hsbc',

    # Citi variations
    'citi': 'citi',
    'citibank': 'citi',
    'citi bank': 'citi',

    # American Express variations
    'amex': 'american express',
    'american express': 'american express',
    'americanexpress': 'american express',

    # PNB variations
    'pnb': 'pnb',
    'punjab national bank': 'pnb',
    'punjab national': 'pnb',

    # Bank of Baroda variations
    'bob': 'bank of baroda',
    'bank of baroda': 'bank of baroda',
    'baroda bank': 'bank of baroda',

    # Canara Bank variations
    'canara': 'canara',
    'canara bank': 'canara',

    # Union Bank variations
    'union': 'union bank',
    'union bank': 'union bank',
    'union bank of india': 'union bank',

    # Bank of India variations
    'boi': 'bank of india',
    'bank of india': 'bank of india',

    # Central Bank variations
    'central': 'central bank',
    'central bank': 'central bank',
    'central bank of india': 'central bank',

    # Indian Bank variations
    'indian bank': 'indian bank',
    'indian': 'indian bank',

    # Federal Bank variations
    'federal': 'federal',
    'federal bank': 'federal',

    # South Indian Bank variations
    'sib': 'south indian bank',
    'south indian bank': 'south indian bank',
    'south indian': 'south indian bank',
}


def normalize_bank_name(bank_name: str) -> str:
    """
    Normalize bank names to handle variations
    Examples: 'HDFC Bank' -> 'hdfc', 'State Bank of India' -> 'sbi'
    """
    if not bank_name:
        return ""

    name = bank_name.lower().strip()

    # Direct mapping
    if name in BANK_MAPPINGS:
        return BANK_MAPPINGS[name]

    # Remove common suffixes and try again
    suffixes = [' bank', ' bank ltd', ' bank limited', ' ltd', ' limited', ' pvt', ' private']
    cleaned_name = name
    for suffix in suffixes:
        if cleaned_name.endswith(suffix):
            cleaned_name = cleaned_name[:-len(suffix)].strip()
            if cleaned_name in BANK_MAPPINGS:
                return BANK_MAPPINGS[cleaned_name]

    # Try partial matching
    name_without_common_words = name
    for word in ['bank', 'limited', 'ltd', 'pvt', 'private', 'the', 'of', 'india']:
        name_without_common_words = name_without_common_words.replace(word, ' ')

    name_without_common_words = ' '.join(name_without_common_words.split()).strip()

    # Check if cleaned version matches any mapping
    for key, value in BANK_MAPPINGS.items():
        if name_without_common_words == key.replace('bank', '').replace('limited', '').replace('ltd', '').strip():
            return value

    return name_without_common_words if name_without_common_words else name


class CardService:
    """
    Service for card-related database operations.
    Uses production MongoDB with insurance_analysis_db database.
    """

    def __init__(self):
        self.client = None
        self.db = None
        self.credit_collection = None
        self.debit_collection = None
        self._initialized = False

    def initialize(self):
        """Initialize card collections with own MongoDB connection"""
        if self._initialized:
            return

        try:
            # Create MongoDB client with production settings
            _card_kwargs = dict(
                maxPoolSize=50,
                minPoolSize=10,
                maxIdleTimeMS=30000,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=10000,
                retryWrites=True,
                retryReads=True,
            )
            # Only enable TLS for Atlas (mongodb+srv) or explicit tls/ssl URIs
            if MONGODB_URI and (
                MONGODB_URI.startswith('mongodb+srv://') or
                'tls=true' in MONGODB_URI or
                'ssl=true' in MONGODB_URI
            ):
                _card_kwargs['tlsCAFile'] = certifi.where()
                logger.info("Card Service: TLS enabled for MongoDB connection")

            self.client = MongoClient(MONGODB_URI, **_card_kwargs)

            # Use insurance_analysis_db database
            self.db = self.client[DATABASE_NAME]

            # Get collection names from environment
            credit_collection_name = CREDIT_CARD_COLLECTION
            debit_collection_name = DEBIT_CARD_COLLECTION

            # Initialize collections
            self.credit_collection = self.db[credit_collection_name]
            self.debit_collection = self.db[debit_collection_name]

            # Log collection stats for debugging
            credit_count = self.credit_collection.count_documents({})
            debit_count = self.debit_collection.count_documents({})

            self._initialized = True
            logger.info(f"✅ Card service connected to MongoDB database: {DATABASE_NAME}")
            logger.info(f"📊 Credit cards collection '{credit_collection_name}': {credit_count} documents")
            logger.info(f"📊 Debit cards collection '{debit_collection_name}': {debit_count} documents")

            if credit_count == 0 and debit_count == 0:
                logger.warning(f"⚠️ No card data found in collections!")
                logger.warning(f"⚠️ Ensure '{credit_collection_name}' and '{debit_collection_name}' collections exist in '{DATABASE_NAME}'")

        except Exception as e:
            logger.error(f"❌ Failed to initialize card service: {e}")
            raise

    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
        self._initialized = False
        logger.info("Card service MongoDB connection closed")

    def _get_collection(self, card_type: str):
        """Get the appropriate collection based on card type"""
        if not self._initialized:
            self.initialize()

        if card_type.lower() == "credit":
            return self.credit_collection
        elif card_type.lower() == "debit":
            return self.debit_collection
        else:
            raise ValueError("Invalid card_type. Must be 'credit' or 'debit'")

    # ==================== BANK OPERATIONS ====================

    def get_banks(self, card_type: str) -> List[Dict[str, Any]]:
        """Get list of all banks with card counts for a specific card type"""
        collection = self._get_collection(card_type)

        pipeline = [
            {
                "$addFields": {
                    "_merged_logo": {"$ifNull": ["$logo", {"$ifNull": ["$Logo", ""]}]}
                }
            },
            {
                "$group": {
                    "_id": "$bank_name",
                    "card_count": {"$sum": 1},
                    "logo": {"$max": "$_merged_logo"}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "bank_name": "$_id",
                    "card_count": 1,
                    "logo": {"$ifNull": ["$logo", ""]},
                    "has_cards": {"$gt": ["$card_count", 0]}
                }
            },
            {
                "$sort": {"bank_name": 1}
            }
        ]

        banks = list(collection.aggregate(pipeline))
        logger.info(f"Retrieved {len(banks)} banks for {card_type} cards")
        return banks

    def get_banks_with_cards(self, card_type: str) -> List[Dict[str, Any]]:
        """Get all banks with their complete card details"""
        collection = self._get_collection(card_type)

        pipeline = [
            {
                "$group": {
                    "_id": "$bank_name",
                    "cards": {
                        "$push": {
                            "id": {"$toString": "$_id"},
                            "card_name": "$card_name",
                            "card_type": "$card_type",
                            "logo": "$logo",
                        }
                    },
                    "card_count": {"$sum": 1}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "bank_name": "$_id",
                    "card_count": 1,
                    "cards": 1
                }
            },
            {
                "$sort": {"bank_name": 1}
            }
        ]

        banks_with_cards = list(collection.aggregate(pipeline))
        logger.info(f"Retrieved {len(banks_with_cards)} banks with {card_type} cards")
        return banks_with_cards

    def get_all_banks_combined(self) -> Dict[str, Any]:
        """Get all banks from both credit and debit collections with normalization"""
        if not self._initialized:
            self.initialize()

        # Get credit card banks
        credit_pipeline = [
            {"$group": {"_id": "$bank_name", "credit_count": {"$sum": 1}}}
        ]

        # Get debit card banks
        debit_pipeline = [
            {"$group": {"_id": "$bank_name", "debit_count": {"$sum": 1}}}
        ]

        credit_banks = {doc["_id"]: doc["credit_count"] for doc in self.credit_collection.aggregate(credit_pipeline)}
        debit_banks = {doc["_id"]: doc["debit_count"] for doc in self.debit_collection.aggregate(debit_pipeline)}

        # Normalize and combine bank names
        normalized_banks = {}

        # Process credit banks
        for bank_name, count in credit_banks.items():
            if bank_name is None:
                continue
            normalized = normalize_bank_name(bank_name)
            if normalized not in normalized_banks:
                normalized_banks[normalized] = {"credit": 0, "debit": 0, "names": set()}
            normalized_banks[normalized]["credit"] += count
            normalized_banks[normalized]["names"].add(bank_name)

        # Process debit banks
        for bank_name, count in debit_banks.items():
            if bank_name is None:
                continue
            normalized = normalize_bank_name(bank_name)
            if normalized not in normalized_banks:
                normalized_banks[normalized] = {"credit": 0, "debit": 0, "names": set()}
            normalized_banks[normalized]["debit"] += count
            normalized_banks[normalized]["names"].add(bank_name)

        # Build results
        results = []
        for normalized, data in normalized_banks.items():
            display_name = min(data["names"], key=len)
            results.append({
                "bank_name": display_name,
                "credit_card_count": data["credit"],
                "debit_card_count": data["debit"],
                "total_card_count": data["credit"] + data["debit"],
                "variations": list(data["names"]) if len(data["names"]) > 1 else []
            })

        results.sort(key=lambda x: x["bank_name"])

        logger.info(f"Retrieved {len(results)} combined banks")
        return {
            "total_banks": len(results),
            "banks": results
        }

    # ==================== CARD OPERATIONS ====================

    def get_cards_by_bank(self, card_type: str, bank_name: str) -> Dict[str, Any]:
        """Get all cards from a specific bank"""
        import re
        collection = self._get_collection(card_type)

        cards = []
        escaped_name = re.escape(bank_name)
        cursor = collection.find({
            "bank_name": {"$regex": f"^{escaped_name}$", "$options": "i"}
        })

        for document in cursor:
            document["id"] = str(document.pop("_id"))
            cards.append(document)

        logger.info(f"Retrieved {len(cards)} {card_type} cards for bank: {bank_name}")

        return {
            "bank_name": bank_name,
            "card_count": len(cards),
            "card_type": card_type,
            "cards": cards
        }

    def get_all_cards(self, card_type: str, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Get all cards with pagination"""
        collection = self._get_collection(card_type)

        cards = []
        cursor = collection.find({}).skip(skip).limit(limit)

        for document in cursor:
            document["id"] = str(document.pop("_id"))
            cards.append(document)

        total_count = collection.count_documents({})

        logger.info(f"Retrieved {len(cards)}/{total_count} {card_type} cards")

        return {
            "total": total_count,
            "skip": skip,
            "limit": limit,
            "card_type": card_type,
            "cards": cards
        }

    def search_cards(self, card_type: str, query: str, limit: int = 50) -> Dict[str, Any]:
        """Search for cards by bank name or card name"""
        collection = self._get_collection(card_type)

        search_query = {
            "$or": [
                {"bank_name": {"$regex": query, "$options": "i"}},
                {"card_name": {"$regex": query, "$options": "i"}}
            ]
        }

        cards = []
        cursor = collection.find(search_query).limit(limit)

        for document in cursor:
            card_data = {
                "card_name": document.get("card_name"),
                "bank_name": document.get("bank_name"),
                "benefits": document.get("insurance_benefits", []),
                "card_url": document.get("card_url", ""),
                "image_url": document.get("image_url", ""),
                "logo": document.get("logo", ""),
                "card_type": card_type
            }
            cards.append(card_data)

        logger.info(f"Search '{query}' found {len(cards)} {card_type} cards")

        return {
            "query": query,
            "card_type": card_type,
            "results_count": len(cards),
            "results": cards
        }

    def search_all_cards(self, query: str, limit_per_type: int = 25) -> Dict[str, Any]:
        """Search across both credit and debit cards"""
        if not self._initialized:
            self.initialize()

        search_query = {
            "$or": [
                {"bank_name": {"$regex": query, "$options": "i"}},
                {"card_name": {"$regex": query, "$options": "i"}}
            ]
        }

        cards = []

        # Search credit cards
        for document in self.credit_collection.find(search_query).limit(limit_per_type):
            card_data = {
                "card_name": document.get("card_name"),
                "bank_name": document.get("bank_name"),
                "card_url": document.get("card_url", ""),
                "image_url": document.get("image_url", ""),
                "logo": document.get("logo", ""),
                "card_type": "credit"
            }
            cards.append(card_data)

        # Search debit cards
        for document in self.debit_collection.find(search_query).limit(limit_per_type):
            card_data = {
                "card_name": document.get("card_name"),
                "bank_name": document.get("bank_name"),
                "benefits": document.get("insurance_benefits", []),
                "card_url": document.get("card_url", ""),
                "image_url": document.get("image_url", ""),
                "logo": document.get("logo", ""),
                "card_type": "debit"
            }
            cards.append(card_data)

        credit_count = sum(1 for c in cards if c["card_type"] == "credit")
        debit_count = sum(1 for c in cards if c["card_type"] == "debit")

        logger.info(f"Search '{query}' found {len(cards)} cards (credit: {credit_count}, debit: {debit_count})")

        return {
            "query": query,
            "results_count": len(cards),
            "credit_count": credit_count,
            "debit_count": debit_count,
            "results": cards
        }

    def lookup_bin(self, bin_number: str) -> Dict[str, Any]:
        """
        Lookup card BIN (first 6 digits) and find matching cards from database

        Args:
            bin_number: First 6 digits of the card number

        Returns:
            BIN information from RapidAPI + matching cards from database
        """
        if not self._initialized:
            self.initialize()

        # Validate BIN number (must be 6 digits)
        if not bin_number or len(bin_number) != 6 or not bin_number.isdigit():
            raise ValueError("BIN number must be exactly 6 digits")

        # Call RapidAPI BIN checker
        url = "https://bin-ip-checker.p.rapidapi.com/"
        querystring = {"bin": bin_number}
        headers = {
            "x-rapidapi-key": os.getenv("RAPIDAPI_KEY", "2d4a5b84cbmsh894dc167ae9013ap1a1535jsnf655878d941e"),
            "x-rapidapi-host": "bin-ip-checker.p.rapidapi.com"
        }

        try:
            response = requests.get(url, headers=headers, params=querystring, timeout=10)
            response.raise_for_status()
            bin_data = response.json()
        except requests.RequestException as e:
            logger.error(f"Error calling BIN API: {e}")
            raise ValueError(f"Failed to lookup BIN: {str(e)}")

        # Check if BIN lookup was successful
        if not bin_data.get("success") or not bin_data.get("BIN", {}).get("valid"):
            return {
                "success": False,
                "message": "Invalid BIN number or card not found",
                "bin_number": bin_number,
                "bin_info": None,
                "matching_cards": []
            }

        bin_info = bin_data.get("BIN", {})
        issuer_name = bin_info.get("issuer", {}).get("name", "")
        card_type = bin_info.get("type", "").lower()  # DEBIT or CREDIT
        scheme = bin_info.get("scheme", "")  # VISA, MASTERCARD, etc.

        logger.info(f"BIN lookup: {bin_number} -> {issuer_name}, {card_type}, {scheme}")

        # Search for matching cards in database based on issuer/bank name
        matching_cards = []
        if issuer_name:
            # Normalize bank name for search (remove common suffixes)
            search_terms = []

            # Add original name
            search_terms.append(issuer_name)

            # Extract key bank name (e.g., "KOTAK MAHINDRA BANK, LTD." -> "KOTAK")
            bank_words = issuer_name.upper().replace(",", "").replace(".", "").split()
            if bank_words:
                search_terms.append(bank_words[0])  # First word (e.g., "KOTAK")
                if len(bank_words) > 1:
                    search_terms.append(f"{bank_words[0]} {bank_words[1]}")  # First two words

            # Search in appropriate collection based on card type
            collection = None
            if card_type == "debit":
                collection = self.debit_collection
            elif card_type == "credit":
                collection = self.credit_collection

            if collection is not None:
                for search_term in search_terms:
                    cursor = collection.find({
                        "bank_name": {"$regex": search_term, "$options": "i"}
                    }).limit(20)

                    for doc in cursor:
                        card_data = {
                            "id": str(doc.get("_id")),
                            "card_name": doc.get("card_name"),
                            "bank_name": doc.get("bank_name"),
                            "card_type": card_type,
                            "card_url": doc.get("card_url", ""),
                            "image_url": doc.get("image_url", ""),
                            "logo": doc.get("logo", ""),
                            "benefits": doc.get("insurance_benefits", [])
                        }
                        # Avoid duplicates
                        if card_data not in matching_cards:
                            matching_cards.append(card_data)

                    if matching_cards:
                        break  # Found matches, no need to try other search terms

            # If no matches found in specific collection, search both
            if not matching_cards:
                for search_term in search_terms:
                    # Search credit cards
                    for doc in self.credit_collection.find({
                        "bank_name": {"$regex": search_term, "$options": "i"}
                    }).limit(10):
                        card_data = {
                            "id": str(doc.get("_id")),
                            "card_name": doc.get("card_name"),
                            "bank_name": doc.get("bank_name"),
                            "card_type": "credit",
                            "card_url": doc.get("card_url", ""),
                            "image_url": doc.get("image_url", ""),
                            "logo": doc.get("logo", ""),
                            "benefits": doc.get("insurance_benefits", [])
                        }
                        if card_data not in matching_cards:
                            matching_cards.append(card_data)

                    # Search debit cards
                    for doc in self.debit_collection.find({
                        "bank_name": {"$regex": search_term, "$options": "i"}
                    }).limit(10):
                        card_data = {
                            "id": str(doc.get("_id")),
                            "card_name": doc.get("card_name"),
                            "bank_name": doc.get("bank_name"),
                            "card_type": "debit",
                            "card_url": doc.get("card_url", ""),
                            "image_url": doc.get("image_url", ""),
                            "logo": doc.get("logo", ""),
                            "benefits": doc.get("insurance_benefits", [])
                        }
                        if card_data not in matching_cards:
                            matching_cards.append(card_data)

                    if matching_cards:
                        break

        logger.info(f"Found {len(matching_cards)} matching cards for BIN {bin_number}")

        return {
            "success": True,
            "bin_number": bin_number,
            "bin_info": {
                "valid": bin_info.get("valid"),
                "scheme": bin_info.get("scheme"),
                "brand": bin_info.get("brand"),
                "type": bin_info.get("type"),
                "level": bin_info.get("level"),
                "is_commercial": bin_info.get("is_commercial"),
                "is_prepaid": bin_info.get("is_prepaid"),
                "currency": bin_info.get("currency"),
                "issuer": bin_info.get("issuer"),
                "country": bin_info.get("country")
            },
            "matching_cards_count": len(matching_cards),
            "matching_cards": matching_cards
        }

    def add_user_card(self, user_card_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a card to user's collection (self or family member)

        Args:
            user_card_data: Dictionary containing user card details

        Returns:
            Added card details with ID
        """
        if not self._initialized:
            self.initialize()

        from datetime import datetime

        # Get or create user_cards collection
        user_cards_collection = self.db["user_cards"]

        # Check if card already exists for this user/member
        # Check by card_id (specific card) + member_name + is_active
        existing_card = user_cards_collection.find_one({
            "user_id": user_card_data.get("user_id"),
            "card_id": user_card_data.get("card_id"),
            "member_name": user_card_data.get("member_name"),
            "is_active": True
        })

        if existing_card:
            existing_card_id = str(existing_card["_id"]) if "_id" in existing_card else ""
            return {
                "success": False,
                "message": "Card already added for this member",
                "card_id": existing_card_id
            }

        # Get card details from database to include insurance benefits
        card_id = user_card_data.get("card_id")
        card_type = user_card_data.get("card_type", "").lower()

        insurance_benefits = []
        logo = ""

        if card_id:
            from bson import ObjectId
            try:
                collection = self.credit_collection if card_type == "credit" else self.debit_collection
                card_doc = collection.find_one({"_id": ObjectId(card_id)})
                if card_doc:
                    insurance_benefits = card_doc.get("insurance_benefits", [])
                    logo = card_doc.get("logo", "")
            except Exception as e:
                logger.warning(f"Could not fetch card details: {e}")

        # Prepare document to insert
        card_document = {
            "user_id": user_card_data.get("user_id"),
            "card_for": user_card_data.get("card_for"),
            "member_name": user_card_data.get("member_name"),
            "member_relationship": user_card_data.get("member_relationship"),
            "member_gender": user_card_data.get("member_gender"),
            "card_id": card_id,
            "card_name": user_card_data.get("card_name"),
            "bank_name": user_card_data.get("bank_name"),
            "card_type": card_type,
            "bin_number": user_card_data.get("bin_number"),
            "scheme": user_card_data.get("scheme"),
            "last_four_digits": user_card_data.get("last_four_digits"),
            "logo": logo,
            "insurance_benefits": insurance_benefits,
            "added_at": datetime.utcnow().isoformat(),
            "is_active": True
        }

        result = user_cards_collection.insert_one(card_document)

        logger.info(f"Added card for user {user_card_data.get('user_id')}, member: {user_card_data.get('member_name')}")

        return {
            "success": True,
            "message": "Card added successfully",
            "card_id": str(result.inserted_id),
            "card_details": {
                "id": str(result.inserted_id),
                "card_name": card_document["card_name"],
                "bank_name": card_document["bank_name"],
                "card_type": card_document["card_type"],
                "card_for": card_document["card_for"],
                "member_name": card_document["member_name"],
                "member_relationship": card_document["member_relationship"],
                "insurance_benefits": insurance_benefits,
                "logo": logo
            }
        }

    def get_user_cards(self, user_id: str, card_for: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all cards for a user, optionally filtered by self/family

        Args:
            user_id: User ID
            card_for: Optional filter - 'self' or 'family'

        Returns:
            User's cards grouped by self and family
        """
        if not self._initialized:
            self.initialize()

        user_cards_collection = self.db["user_cards"]

        # Build query
        query = {"user_id": user_id, "is_active": True}
        if card_for:
            query["card_for"] = card_for

        cards = []
        for doc in user_cards_collection.find(query).sort("added_at", -1):
            cards.append({
                "id": str(doc.get("_id")),
                "card_for": doc.get("card_for"),
                "member_name": doc.get("member_name"),
                "member_relationship": doc.get("member_relationship"),
                "member_gender": doc.get("member_gender"),
                "card_name": doc.get("card_name"),
                "bank_name": doc.get("bank_name"),
                "card_type": doc.get("card_type"),
                "bin_number": doc.get("bin_number"),
                "scheme": doc.get("scheme"),
                "last_four_digits": doc.get("last_four_digits"),
                "logo": doc.get("logo", ""),
                "insurance_benefits": doc.get("insurance_benefits", []),
                "added_at": doc.get("added_at")
            })

        # Group by self and family
        self_cards = [c for c in cards if c["card_for"] == "self"]
        family_cards = [c for c in cards if c["card_for"] == "family"]

        logger.info(f"Retrieved {len(cards)} cards for user {user_id}")

        return {
            "user_id": user_id,
            "total_cards": len(cards),
            "self_cards_count": len(self_cards),
            "family_cards_count": len(family_cards),
            "self_cards": self_cards,
            "family_cards": family_cards
        }

    def delete_user_card(self, user_id: str, card_id: str) -> Dict[str, Any]:
        """
        Delete (deactivate) a card from user's collection

        Args:
            user_id: User ID
            card_id: Card document ID

        Returns:
            Deletion status
        """
        if not self._initialized:
            self.initialize()

        from bson import ObjectId

        user_cards_collection = self.db["user_cards"]

        try:
            result = user_cards_collection.update_one(
                {"_id": ObjectId(card_id), "user_id": user_id},
                {"$set": {"is_active": False}}
            )

            if result.modified_count > 0:
                logger.info(f"Deleted card {card_id} for user {user_id}")
                return {
                    "success": True,
                    "message": "Card removed successfully"
                }
            else:
                return {
                    "success": False,
                    "message": "Card not found or already removed"
                }
        except Exception as e:
            logger.error(f"Error deleting card: {e}")
            return {
                "success": False,
                "message": f"Error removing card: {str(e)}"
            }

    def get_card_benefits(self, card_id: str) -> Dict[str, Any]:
        """
        Get detailed insurance benefits for a specific card
        Searches both credit and debit collections automatically

        Args:
            card_id: Card document ID

        Returns:
            Card details with insurance benefits
        """
        if not self._initialized:
            self.initialize()

        from bson import ObjectId

        try:
            object_id = ObjectId(card_id)

            # Search in credit collection first
            card_doc = self.credit_collection.find_one({"_id": object_id})
            card_type = "credit"

            # If not found in credit, search in debit collection
            if not card_doc:
                card_doc = self.debit_collection.find_one({"_id": object_id})
                card_type = "debit"

            if not card_doc:
                return {
                    "success": False,
                    "message": "Card not found"
                }

            return {
                "success": True,
                "card": {
                    "id": str(card_doc.get("_id")),
                    "card_name": card_doc.get("card_name"),
                    "bank_name": card_doc.get("bank_name"),
                    "card_type": card_type,
                    "logo": card_doc.get("logo", ""),
                    "image_url": card_doc.get("image_url", ""),
                    "card_url": card_doc.get("card_url", ""),
                    "insurance_benefits": card_doc.get("insurance_benefits", [])
                }
            }
        except Exception as e:
            logger.error(f"Error getting card benefits: {e}")
            return {
                "success": False,
                "message": f"Error: {str(e)}"
            }


# Singleton instance
card_service = CardService()
