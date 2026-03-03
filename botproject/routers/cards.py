"""
Card Router
API endpoints for credit and debit card operations
"""
import logging
from typing import List
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from typing import Optional
from models.card import (
    BankListItem,
    BankWithCards,
    BinLookupWithUserRequest,
    AddUserCardRequest,
)
from services.card_service import card_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cards", tags=["Cards"])


# ==================== UTILITY ====================

def ensure_initialized():
    """Ensure card service is initialized"""
    if not card_service._initialized:
        card_service.initialize()


# ==================== ROOT ENDPOINT ====================

@router.get("/")
def cards_info():
    """Card API information and available endpoints"""
    return {
        "message": "Card API - Credit & Debit Cards",
        "version": "2.1.0",
        "endpoints": {
            "GET /cards/credit/banks": "Get all banks with credit card counts",
            "GET /cards/credit/banks-with-cards": "Get all banks with their credit cards",
            "GET /cards/credit/banks/{bank_name}/cards": "Get all credit cards from a specific bank",
            "GET /cards/credit/cards": "Get all credit cards (paginated)",
            "GET /cards/credit/search": "Search credit cards by name",
            "GET /cards/debit/banks": "Get all banks with debit card counts",
            "GET /cards/debit/banks-with-cards": "Get all banks with their debit cards",
            "GET /cards/debit/banks/{bank_name}/cards": "Get all debit cards from a specific bank",
            "GET /cards/debit/cards": "Get all debit cards (paginated)",
            "GET /cards/debit/search": "Search debit cards by name",
            "GET /cards/all/banks": "Get all banks from both collections",
            "GET /cards/all/search": "Search across both credit and debit cards",
            "POST /cards/bin/lookup": "Lookup card by BIN (first 6 digits) and find matching cards",
            "POST /cards/bin/lookup-with-user": "Lookup BIN with user/member details",
            "POST /cards/user/add": "Add a card to user's collection (self/family)",
            "GET /cards/user/{user_id}": "Get user's saved cards",
            "DELETE /cards/user/{user_id}/card/{card_id}": "Remove a card from user's collection",
            "GET /cards/benefits/{card_id}": "Get insurance benefits for a card"
        },
        "card_types": ["credit", "debit"]
    }


# ==================== CREDIT CARD ENDPOINTS ====================

@router.get("/credit/banks", response_model=List[BankListItem])
def get_credit_banks():
    """Get list of all banks with credit card counts"""
    try:
        ensure_initialized()
        banks = card_service.get_banks("credit")
        return [BankListItem(**bank) for bank in banks]
    except Exception as e:
        logger.error(f"Error retrieving credit banks: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving banks: {str(e)}")


@router.get("/credit/banks-with-cards", response_model=List[BankWithCards])
def get_credit_banks_with_cards():
    """Get all banks with their complete credit card details"""
    try:
        ensure_initialized()
        banks = card_service.get_banks_with_cards("credit")
        return [BankWithCards(**bank) for bank in banks]
    except Exception as e:
        logger.error(f"Error retrieving credit banks with cards: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving banks with cards: {str(e)}")


@router.get("/credit/banks/{bank_name}/cards")
def get_credit_cards_by_bank(bank_name: str):
    """Get all credit cards from a specific bank"""
    try:
        ensure_initialized()
        result = card_service.get_cards_by_bank("credit", bank_name)

        if not result["cards"]:
            raise HTTPException(
                status_code=404,
                detail=f"No credit cards found for bank: {bank_name}"
            )

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving credit cards for bank {bank_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving cards: {str(e)}")


@router.get("/credit/cards")
def get_all_credit_cards(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return")
):
    """Get all credit cards with pagination"""
    try:
        ensure_initialized()
        return card_service.get_all_cards("credit", skip, limit)
    except Exception as e:
        logger.error(f"Error retrieving all credit cards: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving cards: {str(e)}")


@router.get("/credit/search")
def search_credit_cards(
    q: str = Query(..., min_length=2, description="Search query (min 2 characters)")
):
    """Search for credit cards by bank name or card name"""
    try:
        ensure_initialized()
        return card_service.search_cards("credit", q)
    except Exception as e:
        logger.error(f"Error searching credit cards: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching cards: {str(e)}")


# ==================== DEBIT CARD ENDPOINTS ====================

@router.get("/debit/banks", response_model=List[BankListItem])
def get_debit_banks():
    """Get list of all banks with debit card counts"""
    try:
        ensure_initialized()
        banks = card_service.get_banks("debit")
        return [BankListItem(**bank) for bank in banks]
    except Exception as e:
        logger.error(f"Error retrieving debit banks: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving banks: {str(e)}")


@router.get("/debit/banks-with-cards", response_model=List[BankWithCards])
def get_debit_banks_with_cards():
    """Get all banks with their complete debit card details"""
    try:
        ensure_initialized()
        banks = card_service.get_banks_with_cards("debit")
        return [BankWithCards(**bank) for bank in banks]
    except Exception as e:
        logger.error(f"Error retrieving debit banks with cards: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving banks with cards: {str(e)}")


@router.get("/debit/banks/{bank_name}/cards")
def get_debit_cards_by_bank(bank_name: str):
    """Get all debit cards from a specific bank"""
    try:
        ensure_initialized()
        result = card_service.get_cards_by_bank("debit", bank_name)

        if not result["cards"]:
            raise HTTPException(
                status_code=404,
                detail=f"No debit cards found for bank: {bank_name}"
            )

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving debit cards for bank {bank_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving cards: {str(e)}")


@router.get("/debit/cards")
def get_all_debit_cards(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return")
):
    """Get all debit cards with pagination"""
    try:
        ensure_initialized()
        return card_service.get_all_cards("debit", skip, limit)
    except Exception as e:
        logger.error(f"Error retrieving all debit cards: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving cards: {str(e)}")


@router.get("/debit/search")
def search_debit_cards(
    q: str = Query(..., min_length=2, description="Search query (min 2 characters)")
):
    """Search for debit cards by bank name or card name"""
    try:
        ensure_initialized()
        return card_service.search_cards("debit", q)
    except Exception as e:
        logger.error(f"Error searching debit cards: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching cards: {str(e)}")


# ==================== COMBINED ENDPOINTS ====================

@router.get("/all/banks")
def get_all_banks_combined():
    """Get all banks from both credit and debit collections with name normalization"""
    try:
        ensure_initialized()
        return card_service.get_all_banks_combined()
    except Exception as e:
        logger.error(f"Error retrieving all banks: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving banks: {str(e)}")


@router.get("/all/search")
def search_all_cards(
    q: str = Query(..., min_length=2, description="Search query (min 2 characters)")
):
    """Search across both credit and debit cards"""
    try:
        ensure_initialized()
        return card_service.search_all_cards(q)
    except Exception as e:
        logger.error(f"Error searching all cards: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching cards: {str(e)}")


# ==================== BIN LOOKUP ENDPOINT ====================

@router.post("/bin/lookup")
def lookup_card_bin(request: BinLookupWithUserRequest):
    """
    Lookup card BIN (Bank Identification Number) and find matching cards for self or family

    **How it works:**
    1. Takes the first 6 digits of a card number (BIN)
    2. Calls external API to get card details (bank name, type, scheme)
    3. Searches MongoDB for matching cards from that bank
    4. Returns BIN info + matching cards from database

    **Request Body for Self:**
    ```json
    {
        "bin_number": "459453",
        "user_id": "user_123456",
        "card_for": "self",
        "member_details": {
            "name": "Hitesh Kumar",
            "relationship": "self",
            "gender": "Male"
        }
    }
    ```

    **Request Body for Family:**
    ```json
    {
        "bin_number": "459453",
        "user_id": "user_123456",
        "card_for": "family",
        "member_details": {
            "name": "Priya Kumar",
            "relationship": "Spouse",
            "gender": "Female"
        }
    }
    ```

    **Response includes:**
    - `bin_info`: Card details from BIN lookup (bank, type, scheme, country)
    - `matching_cards`: Cards from database that match the issuer/bank
    - `user_info`: User and member details for card addition
    """
    try:
        ensure_initialized()

        # Validate card_for
        if request.card_for not in ["self", "family"]:
            raise HTTPException(
                status_code=400,
                detail="card_for must be 'self' or 'family'"
            )

        # Get BIN lookup results
        bin_result = card_service.lookup_bin(request.bin_number)

        # Add user info to response
        bin_result["user_info"] = {
            "user_id": request.user_id,
            "card_for": request.card_for,
            "member_details": {
                "name": request.member_details.name,
                "relationship": request.member_details.relationship,
                "gender": request.member_details.gender
            }
        }

        # Return 404 if BIN is invalid or card not found
        if not bin_result.get("success"):
            raise HTTPException(status_code=404, detail=bin_result)

        return bin_result

    except ValueError as e:
        logger.warning(f"BIN lookup validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error looking up BIN: {e}")
        raise HTTPException(status_code=500, detail=f"Error looking up BIN: {str(e)}")


# ==================== USER CARD ENDPOINTS ====================

@router.post("/user/add")
def add_user_card(request: AddUserCardRequest):
    """
    Add a card to user's collection (self or family member)

    **Request Body:**
    ```json
    {
        "user_id": "user_123456",
        "card_for": "self",
        "member_details": {
            "name": "Hitesh Kumar",
            "relationship": "self",
            "gender": "Male"
        },
        "card_id": "674abc123def456",
        "card_name": "Kotak 811 Debit Card",
        "bank_name": "Kotak Mahindra Bank",
        "card_type": "debit",
        "bin_number": "459453",
        "scheme": "VISA",
        "last_four_digits": "1234"
    }
    ```

    **Response:**
    - Card details with insurance benefits
    - Confirmation of card addition
    """
    try:
        ensure_initialized()

        # Validate card_for
        if request.card_for not in ["self", "family"]:
            raise HTTPException(
                status_code=400,
                detail="card_for must be 'self' or 'family'"
            )

        # Prepare data for service
        user_card_data = {
            "user_id": request.user_id,
            "card_for": request.card_for,
            "member_name": request.member_details.name,
            "member_relationship": request.member_details.relationship,
            "member_gender": request.member_details.gender,
            "card_id": request.card_id,
            "card_name": request.card_name,
            "bank_name": request.bank_name,
            "card_type": request.card_type,
            "bin_number": request.bin_number,
            "scheme": request.scheme,
            "last_four_digits": request.last_four_digits
        }

        result = card_service.add_user_card(user_card_data)
        logger.info(f"add_user_card result: {result}")

        # Check if card already exists (duplicate)
        if not result.get("success") and "already added" in result.get("message", ""):
            raise HTTPException(
                status_code=409,
                detail={
                    "success": False,
                    "error_code": "RES_3003",
                    "message": result.get("message")
                }
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding user card: {e}")
        raise HTTPException(status_code=500, detail=f"Error adding card: {str(e)}")


@router.get("/user/{user_id}")
def get_user_cards(
    user_id: str,
    card_for: Optional[str] = Query(None, description="Filter by 'self' or 'family'")
):
    """
    Get all cards saved by a user

    **Path Parameter:**
    - `user_id`: User ID

    **Query Parameter (optional):**
    - `card_for`: Filter by 'self' or 'family'

    **Response:**
    - Cards grouped by self and family
    - Insurance benefits for each card
    """
    try:
        ensure_initialized()

        if card_for and card_for not in ["self", "family"]:
            raise HTTPException(
                status_code=400,
                detail="card_for must be 'self' or 'family'"
            )

        return card_service.get_user_cards(user_id, card_for)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user cards: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving cards: {str(e)}")


@router.delete("/user/{user_id}/card/{card_id}")
def delete_user_card(user_id: str, card_id: str):
    """
    Remove a card from user's collection

    **Path Parameters:**
    - `user_id`: User ID
    - `card_id`: Card document ID to remove
    """
    try:
        ensure_initialized()
        return card_service.delete_user_card(user_id, card_id)
    except Exception as e:
        logger.error(f"Error deleting user card: {e}")
        raise HTTPException(status_code=500, detail=f"Error removing card: {str(e)}")


@router.get("/benefits/{card_id}")
def get_card_benefits(card_id: str):
    """
    Get detailed insurance benefits for a specific card

    **Path Parameter:**
    - `card_id`: Card document ID

    **Response:**
    - Card details with full insurance benefits list
    """
    try:
        ensure_initialized()

        result = card_service.get_card_benefits(card_id)

        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("message"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting card benefits: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving benefits: {str(e)}")
