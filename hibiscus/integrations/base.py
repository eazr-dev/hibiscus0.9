"""
Insurer Integration Base
========================
Abstract base class for all insurer API integrations.

When real API access is granted, swap the mock implementation →
live implementation. Agent code stays unchanged.

All methods return Optional results — None means "data not available".
"""
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class QuoteResult:
    """Result from a quote request."""
    insurer: str
    product_name: str
    premium_annual: float
    sum_insured: float
    features: Dict[str, Any] = field(default_factory=dict)
    source: str = "mock_kg"          # "mock_kg" | "live_api"
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "insurer": self.insurer,
            "product_name": self.product_name,
            "premium_annual": self.premium_annual,
            "sum_insured": self.sum_insured,
            "features": self.features,
            "source": self.source,
            "timestamp": self.timestamp,
        }


@dataclass
class ClaimsStatusResult:
    """Result from a claims status check."""
    claim_id: str
    status: str                       # submitted|under_review|approved|rejected|settled
    amount_claimed: float
    amount_approved: Optional[float] = None
    last_updated: str = ""
    next_steps: List[str] = field(default_factory=list)
    source: str = "mock_kg"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "status": self.status,
            "amount_claimed": self.amount_claimed,
            "amount_approved": self.amount_approved,
            "last_updated": self.last_updated,
            "next_steps": self.next_steps,
            "source": self.source,
        }


@dataclass
class PolicyDetailResult:
    """Result from a policy detail lookup."""
    policy_number: str
    insurer: str
    product_name: str
    status: str                       # active|lapsed|expired|cancelled
    sum_insured: float
    premium_annual: float
    start_date: str
    end_date: str
    features: Dict[str, Any] = field(default_factory=dict)
    source: str = "mock_kg"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_number": self.policy_number,
            "insurer": self.insurer,
            "product_name": self.product_name,
            "status": self.status,
            "sum_insured": self.sum_insured,
            "premium_annual": self.premium_annual,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "features": self.features,
            "source": self.source,
        }


@dataclass
class RenewalStatusResult:
    """Result from a renewal status check."""
    policy_number: str
    renewal_due_date: str
    premium_amount: float
    auto_renewal: bool = False
    renewal_discount: float = 0.0
    source: str = "mock_kg"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_number": self.policy_number,
            "renewal_due_date": self.renewal_due_date,
            "premium_amount": self.premium_amount,
            "auto_renewal": self.auto_renewal,
            "renewal_discount": self.renewal_discount,
            "source": self.source,
        }


class InsurerIntegration(ABC):
    """
    Abstract base class for insurer API integrations.

    To add a new insurer:
    1. Create a new file in hibiscus/integrations/
    2. Subclass InsurerIntegration
    3. Implement all abstract methods
    4. Register in registry.py
    """

    name: str = "Unknown Insurer"
    supported_features: List[str] = []  # ["quote", "claims_status", "policy_details", "renewal"]

    @abstractmethod
    async def get_quote(
        self,
        age: int,
        sum_insured: float,
        product_type: str = "health",
        city: str = "Mumbai",
        family_size: int = 1,
    ) -> Optional[QuoteResult]:
        """Get a premium quote for the given parameters."""

    @abstractmethod
    async def get_claims_status(
        self,
        policy_number: str,
        claim_id: str = "",
    ) -> Optional[ClaimsStatusResult]:
        """Check the status of a claim."""

    @abstractmethod
    async def get_policy_details(
        self,
        policy_number: str,
    ) -> Optional[PolicyDetailResult]:
        """Get details of a policy by number."""

    @abstractmethod
    async def check_renewal_status(
        self,
        policy_number: str,
    ) -> Optional[RenewalStatusResult]:
        """Check renewal status and upcoming due date."""
