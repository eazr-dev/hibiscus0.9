"""
HBF/GBF (Hospital/Garage Bill Financing) Service
Handles eligibility checks, EAZR score calculation, offer generation, and loan management.
"""

import logging
import uuid
import math
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)


def get_ist_now():
    ist_timezone = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist_timezone).replace(tzinfo=None)


# HBF product limits
HBF_CONFIG = {
    "hbf": {
        "min_amount": 15000,
        "max_amount": 500000,
        "tenures": [3, 6, 9, 12],
        "base_rate": 12.0,
        "max_rate": 18.0,
        "processing_fee_pct": 2.0,
    },
    "gbf": {
        "min_amount": 10000,
        "max_amount": 200000,
        "tenures": [3, 6, 9],
        "base_rate": 14.0,
        "max_rate": 18.0,
        "processing_fee_pct": 2.5,
    },
}

# EAZR score thresholds
SCORE_THRESHOLDS = {
    "platinum": {"min": 80, "rate_discount": 2.0},
    "gold": {"min": 60, "rate_discount": 1.0},
    "silver": {"min": 40, "rate_discount": 0.0},
    "bronze": {"min": 0, "rate_discount": -1.0},
}

MIN_ELIGIBLE_SCORE = 40


class HBFService:
    """
    Service for HBF/GBF financing operations.

    Handles:
    - EAZR score calculation (6 factors, 100 points)
    - Eligibility checks
    - Loan offer generation with EMI calculations
    - Loan application management
    """

    def __init__(self):
        from core.dependencies import MONGODB_AVAILABLE

        self.mongodb_available = MONGODB_AVAILABLE
        self.mongodb_manager = None
        self.hbf_collection = None

        if MONGODB_AVAILABLE:
            from database_storage.mongodb_chat_manager import mongodb_chat_manager
            self.mongodb_manager = mongodb_chat_manager
            self._ensure_collections()
        else:
            logger.warning("MongoDB not available for HBFService")

    def _try_reconnect_mongodb(self):
        if self.hbf_collection is not None:
            return True

        try:
            from database_storage.mongodb_chat_manager import mongodb_chat_manager
            if mongodb_chat_manager and mongodb_chat_manager.db is not None:
                self.mongodb_manager = mongodb_chat_manager
                self.mongodb_available = True
                self._ensure_collections()
                logger.info("MongoDB reconnected for HBFService")
                return self.hbf_collection is not None
        except Exception as e:
            logger.error(f"MongoDB reconnection failed: {e}")

        return False

    def _ensure_collections(self):
        if not self.mongodb_manager:
            return

        try:
            db = self.mongodb_manager.db
            self.hbf_collection = db['hbf_applications']

            self._safe_create_index(self.hbf_collection, [("user_id", 1), ("status", 1)])
            self._safe_create_index(self.hbf_collection, [("loan_id", 1)], unique=True)
            self._safe_create_index(self.hbf_collection, [("created_at", -1)])

            logger.info("HBF collections initialized")
        except Exception as e:
            logger.error(f"Error initializing HBF collections: {e}")

    def _safe_create_index(self, collection, keys, **kwargs):
        try:
            collection.create_index(keys, **kwargs)
        except Exception as e:
            error_str = str(e)
            if "11000" in error_str or "IndexKeySpecsConflict" in error_str or "86" in error_str:
                logger.debug(f"Index already exists, skipping: {keys}")
            else:
                logger.warning(f"Index creation warning for {keys}: {e}")

    def _serialize_doc(self, doc: Dict) -> Dict:
        if doc is None:
            return None
        doc = dict(doc)
        if '_id' in doc:
            doc['_id'] = str(doc['_id'])
        return doc

    async def calculate_eazr_score(self, user_id: int) -> Dict[str, Any]:
        """
        Calculate EAZR score for user (6 factors, 100 points total).

        Factors:
        - Policy count (0-20): More policies = higher score
        - Protection score (0-25): From dashboard calculation
        - Policy age (0-15): Average age of policies
        - Claim history (0-15): Clean history = higher score
        - Engagement (0-15): App usage, logins
        - Profile completeness (0-10): KYC, details filled
        """
        factors = {}

        try:
            # Factor 1: Policy count (0-20)
            policy_count = await self._get_policy_count(user_id)
            if policy_count >= 5:
                factors["policy_count"] = 20
            elif policy_count >= 3:
                factors["policy_count"] = 15
            elif policy_count >= 2:
                factors["policy_count"] = 10
            elif policy_count >= 1:
                factors["policy_count"] = 5
            else:
                factors["policy_count"] = 0

            # Factor 2: Protection score (0-25)
            protection_score = await self._get_protection_score(user_id)
            if protection_score >= 80:
                factors["protection_score"] = 25
            elif protection_score >= 60:
                factors["protection_score"] = 20
            elif protection_score >= 40:
                factors["protection_score"] = 15
            elif protection_score >= 20:
                factors["protection_score"] = 10
            else:
                factors["protection_score"] = 0

            # Factor 3: Policy age (0-15)
            avg_policy_age_months = await self._get_avg_policy_age(user_id)
            if avg_policy_age_months >= 24:
                factors["policy_age"] = 15
            elif avg_policy_age_months >= 12:
                factors["policy_age"] = 10
            elif avg_policy_age_months >= 6:
                factors["policy_age"] = 5
            else:
                factors["policy_age"] = 0

            # Factor 4: Claim history (0-15)
            claim_ratio = await self._get_claim_ratio(user_id)
            if claim_ratio == 0:
                factors["claim_history"] = 15
            elif claim_ratio <= 0.2:
                factors["claim_history"] = 10
            elif claim_ratio <= 0.5:
                factors["claim_history"] = 5
            else:
                factors["claim_history"] = 0

            # Factor 5: Engagement (0-15)
            engagement_score = await self._get_engagement_score(user_id)
            factors["engagement"] = min(15, engagement_score)

            # Factor 6: Profile completeness (0-10)
            profile_score = await self._get_profile_completeness(user_id)
            factors["profile_completeness"] = min(10, profile_score)

        except Exception as e:
            logger.error(f"Error calculating EAZR score: {e}")
            factors = {
                "policy_count": 0, "protection_score": 0, "policy_age": 0,
                "claim_history": 0, "engagement": 0, "profile_completeness": 0,
            }

        total_score = sum(factors.values())

        # Determine tier
        tier = "bronze"
        for tier_name, config in SCORE_THRESHOLDS.items():
            if total_score >= config["min"]:
                tier = tier_name
                break

        is_eligible = total_score >= MIN_ELIGIBLE_SCORE

        return {
            "total_score": total_score,
            "factors": factors,
            "is_eligible": is_eligible,
            "tier": tier,
            "message": f"EAZR Score: {total_score}/100 ({tier.capitalize()} tier)" if is_eligible
                else f"Score {total_score}/100 below minimum {MIN_ELIGIBLE_SCORE}. Add more policies to improve.",
        }

    async def check_eligibility(
        self, user_id: int, loan_type: str, amount: float, audit_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Check eligibility for HBF/GBF financing."""
        config = HBF_CONFIG.get(loan_type)
        if not config:
            return {"is_eligible": False, "message": "Invalid loan type"}

        # Validate amount range
        if amount < config["min_amount"] or amount > config["max_amount"]:
            return {
                "is_eligible": False,
                "message": f"Amount must be between Rs.{config['min_amount']:,.0f} and Rs.{config['max_amount']:,.0f}",
            }

        # Calculate EAZR score
        eazr_score = await self.calculate_eazr_score(user_id)

        # Determine max eligible amount based on tier
        tier = eazr_score["tier"]
        if tier == "platinum":
            max_amount = config["max_amount"]
        elif tier == "gold":
            max_amount = config["max_amount"] * 0.75
        elif tier == "silver":
            max_amount = config["max_amount"] * 0.5
        else:
            max_amount = 0

        is_eligible = eazr_score["is_eligible"] and amount <= max_amount

        # Indicative rate range
        rate_discount = SCORE_THRESHOLDS.get(tier, {}).get("rate_discount", 0)
        low_rate = max(config["base_rate"], config["base_rate"] - rate_discount)
        high_rate = config["max_rate"] - rate_discount
        rate_range = f"{low_rate:.1f}% - {high_rate:.1f}% p.a."

        # Create loan record
        loan_id = f"HBF-{uuid.uuid4().hex[:10].upper()}"

        loan_doc = {
            "loan_id": loan_id,
            "user_id": user_id,
            "loan_type": loan_type,
            "audit_id": audit_id,
            "amount": amount,
            "status": "pre_qualified" if is_eligible else "rejected",
            "eazr_score": eazr_score,
            "max_eligible_amount": max_amount,
            "created_at": get_ist_now(),
            "updated_at": get_ist_now(),
        }

        if self.hbf_collection is not None:
            try:
                self.hbf_collection.insert_one(loan_doc)
            except Exception as e:
                logger.error(f"Failed to save loan record: {e}")

        return {
            "loan_id": loan_id,
            "loan_type": loan_type,
            "is_eligible": is_eligible,
            "eazr_score": eazr_score,
            "max_eligible_amount": max_amount,
            "indicative_rate_range": rate_range if is_eligible else "",
            "message": "Pre-qualified for financing" if is_eligible
                else eazr_score.get("message", "Not eligible"),
        }

    async def generate_offers(self, user_id: int, loan_id: str) -> Optional[Dict[str, Any]]:
        """Generate loan offers with EMI options."""
        if self.hbf_collection is None:
            if not self._try_reconnect_mongodb():
                return None

        try:
            loan = self.hbf_collection.find_one({"loan_id": loan_id, "user_id": user_id})
            if not loan:
                return None

            if loan.get("status") not in ("pre_qualified", "offers_generated"):
                return None

            loan_type = loan["loan_type"]
            amount = loan["amount"]
            config = HBF_CONFIG.get(loan_type)
            if not config:
                return None

            tier = loan.get("eazr_score", {}).get("tier", "silver")
            rate_discount = SCORE_THRESHOLDS.get(tier, {}).get("rate_discount", 0)

            offers = []
            for tenure in config["tenures"]:
                # Calculate interest rate based on tier and tenure
                base = config["base_rate"] + (tenure / 12) * 1.0  # Longer tenure = slightly higher
                rate = max(config["base_rate"], base - rate_discount)
                rate = min(rate, config["max_rate"])

                emi = self._calculate_emi(amount, rate, tenure)
                total_payable = emi * tenure
                processing_fee = amount * config["processing_fee_pct"] / 100

                offers.append({
                    "offer_id": f"OFR-{uuid.uuid4().hex[:8].upper()}",
                    "tenure_months": tenure,
                    "interest_rate": round(rate, 2),
                    "emi_amount": round(emi, 2),
                    "total_payable": round(total_payable, 2),
                    "processing_fee": round(processing_fee, 2),
                })

            valid_until = get_ist_now() + timedelta(days=7)

            # Update loan record
            self.hbf_collection.update_one(
                {"loan_id": loan_id},
                {"$set": {
                    "status": "offers_generated",
                    "offers": offers,
                    "valid_until": valid_until,
                    "updated_at": get_ist_now(),
                }}
            )

            return {
                "loan_id": loan_id,
                "loan_type": loan_type,
                "amount": amount,
                "offers": offers,
                "valid_until": valid_until,
            }

        except Exception as e:
            logger.error(f"Failed to generate offers: {e}")
            return None

    async def apply_loan(
        self, user_id: int, loan_id: str, selected_offer_id: str
    ) -> Optional[Dict[str, Any]]:
        """Apply for a loan by selecting an offer."""
        if self.hbf_collection is None:
            if not self._try_reconnect_mongodb():
                return None

        try:
            loan = self.hbf_collection.find_one({"loan_id": loan_id, "user_id": user_id})
            if not loan:
                return None

            if loan.get("status") != "offers_generated":
                return {"error": "Loan is not in offers_generated state"}

            # Find selected offer
            offers = loan.get("offers", [])
            selected = None
            for offer in offers:
                if offer["offer_id"] == selected_offer_id:
                    selected = offer
                    break

            if not selected:
                return {"error": "Invalid offer ID"}

            # Check offer validity
            valid_until = loan.get("valid_until")
            if valid_until and get_ist_now() > valid_until:
                return {"error": "Offers have expired. Please regenerate."}

            # Update loan
            self.hbf_collection.update_one(
                {"loan_id": loan_id},
                {"$set": {
                    "status": "applied",
                    "selected_offer_id": selected_offer_id,
                    "selected_offer": selected,
                    "tenure_months": selected["tenure_months"],
                    "interest_rate": selected["interest_rate"],
                    "emi_amount": selected["emi_amount"],
                    "total_payable": selected["total_payable"],
                    "processing_fee": selected["processing_fee"],
                    "applied_at": get_ist_now(),
                    "updated_at": get_ist_now(),
                }}
            )

            return {
                "loan_id": loan_id,
                "status": "applied",
                "selected_offer": selected,
                "message": "Application submitted successfully",
                "next_steps": [
                    "Complete e-KYC verification",
                    "Set up e-NACH mandate for EMI auto-debit",
                    "Sign digital loan agreement",
                ],
            }

        except Exception as e:
            logger.error(f"Failed to apply for loan: {e}")
            return None

    async def complete_loan(self, user_id: int, loan_id: str) -> Optional[Dict[str, Any]]:
        """Mark loan as approved/disbursed (placeholder for e-NACH/e-Sign flow)."""
        if self.hbf_collection is None:
            if not self._try_reconnect_mongodb():
                return None

        try:
            loan = self.hbf_collection.find_one({"loan_id": loan_id, "user_id": user_id})
            if not loan:
                return None

            if loan.get("status") != "applied":
                return {"error": "Loan must be in applied state"}

            self.hbf_collection.update_one(
                {"loan_id": loan_id},
                {"$set": {
                    "status": "approved",
                    "approved_at": get_ist_now(),
                    "updated_at": get_ist_now(),
                }}
            )

            return {
                "loan_id": loan_id,
                "status": "approved",
                "message": "Loan approved. Disbursement will be processed within 24 hours.",
            }

        except Exception as e:
            logger.error(f"Failed to complete loan: {e}")
            return None

    async def get_loan_status(self, user_id: int, loan_id: str) -> Optional[Dict[str, Any]]:
        """Get loan status details."""
        if self.hbf_collection is None:
            if not self._try_reconnect_mongodb():
                return None

        try:
            loan = self.hbf_collection.find_one({"loan_id": loan_id, "user_id": user_id})
            if not loan:
                return None

            return {
                "loan_id": loan["loan_id"],
                "loan_type": loan.get("loan_type", "hbf"),
                "status": loan.get("status", "unknown"),
                "amount": loan.get("amount", 0),
                "tenure_months": loan.get("tenure_months", 0),
                "interest_rate": loan.get("interest_rate", 0),
                "emi_amount": loan.get("emi_amount", 0),
                "total_payable": loan.get("total_payable", 0),
                "disbursement_date": loan.get("disbursement_date"),
                "next_emi_date": loan.get("next_emi_date"),
                "emis_paid": loan.get("emis_paid", 0),
                "emis_remaining": loan.get("emis_remaining", loan.get("tenure_months", 0)),
                "outstanding_amount": loan.get("outstanding_amount", loan.get("total_payable", 0)),
            }

        except Exception as e:
            logger.error(f"Failed to get loan status: {e}")
            return None

    def _calculate_emi(self, principal: float, annual_rate: float, tenure_months: int) -> float:
        """Calculate EMI using standard formula: P * r * (1+r)^n / ((1+r)^n - 1)"""
        if annual_rate <= 0 or tenure_months <= 0:
            return principal / max(tenure_months, 1)

        r = annual_rate / (12 * 100)  # Monthly interest rate
        n = tenure_months
        emi = principal * r * math.pow(1 + r, n) / (math.pow(1 + r, n) - 1)
        return emi

    # ==================== Helper Methods for Score Calculation ====================

    async def _get_policy_count(self, user_id: int) -> int:
        try:
            from services.policy_locker_service import policy_locker_service
            if policy_locker_service.policy_locker_collection:
                return policy_locker_service.policy_locker_collection.count_documents({
                    "user_id": user_id, "status": {"$ne": "deleted"}
                })
        except Exception:
            pass
        return 0

    async def _get_protection_score(self, user_id: int) -> float:
        try:
            from services.policy_locker_service import policy_locker_service
            if policy_locker_service.policy_locker_collection:
                policies = list(policy_locker_service.policy_locker_collection.find({
                    "user_id": user_id, "status": {"$ne": "deleted"}
                }))
                # Simple protection score: count categories covered
                categories = set(p.get("category", "").lower() for p in policies)
                essential = {"health", "life", "auto"}
                covered = categories & essential
                return (len(covered) / len(essential)) * 100 if essential else 0
        except Exception:
            pass
        return 0

    async def _get_avg_policy_age(self, user_id: int) -> float:
        try:
            from services.policy_locker_service import policy_locker_service
            if policy_locker_service.policy_locker_collection:
                policies = list(policy_locker_service.policy_locker_collection.find({
                    "user_id": user_id, "status": {"$ne": "deleted"}
                }, {"created_at": 1}))
                if policies:
                    now = get_ist_now()
                    ages = []
                    for p in policies:
                        created = p.get("created_at")
                        if created:
                            age_months = (now - created).days / 30
                            ages.append(age_months)
                    return sum(ages) / len(ages) if ages else 0
        except Exception:
            pass
        return 0

    async def _get_claim_ratio(self, user_id: int) -> float:
        try:
            from services.policy_locker_service import policy_locker_service
            if policy_locker_service.policy_locker_collection and hasattr(policy_locker_service, 'claims_collection') and policy_locker_service.claims_collection:
                total_policies = policy_locker_service.policy_locker_collection.count_documents({
                    "user_id": user_id, "status": {"$ne": "deleted"}
                })
                total_claims = policy_locker_service.claims_collection.count_documents({
                    "user_id": user_id
                })
                return total_claims / max(total_policies, 1)
        except Exception:
            pass
        return 0

    async def _get_engagement_score(self, user_id: int) -> int:
        # Simplified engagement score based on policy count and activity
        policy_count = await self._get_policy_count(user_id)
        if policy_count >= 5:
            return 15
        elif policy_count >= 3:
            return 10
        elif policy_count >= 1:
            return 5
        return 0

    async def _get_profile_completeness(self, user_id: int) -> int:
        try:
            from database_storage.mongodb_chat_manager import mongodb_chat_manager
            if mongodb_chat_manager and mongodb_chat_manager.db:
                user = mongodb_chat_manager.db['users'].find_one({"user_id": user_id})
                if user:
                    score = 0
                    if user.get("name"):
                        score += 3
                    if user.get("email"):
                        score += 3
                    if user.get("phone"):
                        score += 2
                    if user.get("dob") or user.get("date_of_birth"):
                        score += 2
                    return min(10, score)
        except Exception:
            pass
        return 0


# Global singleton instance
hbf_service = HBFService()
