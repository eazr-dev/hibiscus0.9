"""
Card Models
Pydantic models for credit and debit card data
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any


class Card(BaseModel):
    """Individual card model"""
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[str] = Field(None, alias="_id")
    bank_name: str
    card_name: str
    card_type: Optional[str] = None
    benefits: Optional[List[str]] = None
    insurance_benefits: Optional[List[str]] = None
    card_url: Optional[str] = None
    image_url: Optional[str] = None


class CardResponse(BaseModel):
    """Card response with additional metadata"""
    card_name: str
    bank_name: str
    benefits: Optional[List[str]] = None
    card_url: Optional[str] = None
    image_url: Optional[str] = None
    card_type: str  # 'credit' or 'debit'


class BankWithCards(BaseModel):
    """Bank with its associated cards"""
    bank_name: str
    card_count: int
    cards: List[Dict[str, Any]]


class BankListItem(BaseModel):
    """Bank summary item"""
    bank_name: str
    card_count: int
    has_cards: bool
    logo: Optional[str] = ""


class BankCombined(BaseModel):
    """Combined bank info from both collections"""
    bank_name: str
    credit_card_count: int
    debit_card_count: int
    total_card_count: int
    variations: List[str] = []


class CardSearchResult(BaseModel):
    """Search result response"""
    query: str
    card_type: Optional[str] = None
    results_count: int
    credit_count: Optional[int] = None
    debit_count: Optional[int] = None
    results: List[CardResponse]


class CardListResponse(BaseModel):
    """Paginated card list response"""
    total: int
    skip: int
    limit: int
    card_type: str
    cards: List[Dict[str, Any]]


class BankCardsResponse(BaseModel):
    """Response for cards by bank"""
    bank_name: str
    card_count: int
    card_type: str
    cards: List[Dict[str, Any]]


class AllBanksResponse(BaseModel):
    """Response for all banks combined"""
    total_banks: int
    banks: List[BankCombined]


class BinLookupRequest(BaseModel):
    """Request model for BIN lookup"""
    bin_number: str = Field(..., min_length=6, max_length=6, description="First 6 digits of card number (BIN)")


class MemberDetails(BaseModel):
    """Member details for card ownership"""
    name: str = Field(..., min_length=2, max_length=100, description="Full name of card holder")
    relationship: str = Field(..., description="Relationship: self, spouse, son, daughter, father, mother, brother, sister, other")
    gender: str = Field(..., description="Gender: Male, Female, Other")


class BinLookupWithUserRequest(BaseModel):
    """Request model for BIN lookup with user details"""
    bin_number: str = Field(..., min_length=6, max_length=6, description="First 6 digits of card number (BIN)")
    user_id: str = Field(..., description="User ID")
    card_for: str = Field(..., description="Card for: self or family")
    member_details: MemberDetails


class AddUserCardRequest(BaseModel):
    """Request model for adding a card to user's collection"""
    user_id: str = Field(..., description="User ID")
    card_for: str = Field(..., description="Card for: self or family")
    member_details: MemberDetails
    card_id: str = Field(..., description="Card ID from database")
    card_name: str = Field(..., description="Name of the card")
    bank_name: str = Field(..., description="Bank name")
    card_type: str = Field(..., description="Card type: credit or debit")
    bin_number: str = Field(..., min_length=6, max_length=6, description="First 6 digits of card number (BIN)")
    scheme: Optional[str] = Field(None, description="Card scheme: VISA, MASTERCARD, etc.")
    last_four_digits: Optional[str] = Field(None, min_length=4, max_length=4, description="Last 4 digits of card (optional)")


class UserCard(BaseModel):
    """User's saved card"""
    id: Optional[str] = None
    user_id: str
    card_for: str  # self or family
    member_name: str
    member_relationship: str
    member_gender: str
    card_id: str
    card_name: str
    bank_name: str
    card_type: str  # credit or debit
    bin_number: str
    scheme: Optional[str] = None
    last_four_digits: Optional[str] = None
    logo: Optional[str] = ""
    insurance_benefits: Optional[List[str]] = []
    added_at: Optional[str] = None
