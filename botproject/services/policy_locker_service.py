"""
Policy Locker Service
Business logic for Policy Locker, Family Management, Claims, and Emergency Services

This service provides DYNAMIC data operations using MongoDB.
All API data is stored and retrieved from the database.
"""
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from bson import ObjectId

logger = logging.getLogger(__name__)


def get_ist_now():
    """Get current time in IST"""
    ist_timezone = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist_timezone).replace(tzinfo=None)


class PolicyLockerService:
    """
    Service for Policy Locker operations

    Handles:
    - Policy CRUD operations
    - Family member management
    - Policy analysis and gap detection
    - Claims management
    - Emergency services
    - Export and sharing
    """

    def __init__(self):
        """Initialize Policy Locker service"""
        from core.dependencies import MONGODB_AVAILABLE

        self.mongodb_available = MONGODB_AVAILABLE
        self.mongodb_manager = None
        self.policy_locker_collection = None
        self.family_members_collection = None
        self.claims_collection = None
        self.uploads_collection = None
        self.analysis_collection = None
        self.flow_sessions_collection = None  # Add Policy Flow state management

        if MONGODB_AVAILABLE:
            from database_storage.mongodb_chat_manager import mongodb_chat_manager
            self.mongodb_manager = mongodb_chat_manager
            self._ensure_collections()
        else:
            logger.warning("MongoDB not available for PolicyLockerService")

    def _try_reconnect_mongodb(self):
        """
        Try to reconnect to MongoDB if initial connection failed.
        This enables lazy initialization when MongoDB becomes available later.
        """
        if self.flow_sessions_collection is not None:
            return True  # Already connected

        try:
            from database_storage.mongodb_chat_manager import mongodb_chat_manager
            if mongodb_chat_manager and mongodb_chat_manager.db is not None:
                self.mongodb_manager = mongodb_chat_manager
                self.mongodb_available = True
                self._ensure_collections()
                logger.info("MongoDB reconnected successfully for PolicyLockerService")
                return self.flow_sessions_collection is not None
        except Exception as e:
            logger.error(f"MongoDB reconnection failed: {e}")

        return False

    def _ensure_collections(self):
        """Ensure required collections exist with indexes"""
        if not self.mongodb_manager:
            return

        try:
            db = self.mongodb_manager.db

            # Initialize ALL collections FIRST (before index creation)
            self.policy_locker_collection = db['policy_locker']
            self.family_members_collection = db['family_members']
            self.claims_collection = db['insurance_claims']
            self.uploads_collection = db['policy_uploads']
            self.analysis_collection = db['policy_analysis']
            self.flow_sessions_collection = db['flow_sessions']

            logger.info("Policy Locker collections initialized")

            # Create indexes with individual error handling (index errors shouldn't break the service)
            self._create_indexes_safely()

        except Exception as e:
            logger.error(f"Error initializing Policy Locker collections: {e}")

    def _create_indexes_safely(self):
        """Create indexes with individual error handling"""
        # Policy locker indexes
        self._safe_create_index(self.policy_locker_collection, [("user_id", 1), ("status", 1)])
        self._safe_create_index(self.policy_locker_collection, [("user_id", 1), ("category", 1)])
        self._safe_create_index(self.policy_locker_collection, [("member_id", 1)])
        self._safe_create_index(self.policy_locker_collection, [("policy_number", 1)], unique=True, sparse=True)

        # Family members indexes
        self._safe_create_index(self.family_members_collection, [("user_id", 1)])
        self._safe_create_index(self.family_members_collection, [("user_id", 1), ("relationship", 1)])

        # Claims indexes
        self._safe_create_index(self.claims_collection, [("user_id", 1), ("status", 1)])
        self._safe_create_index(self.claims_collection, [("policy_id", 1)])
        self._safe_create_index(self.claims_collection, [("claim_number", 1)], unique=True, sparse=True)

        # Uploads indexes
        self._safe_create_index(self.uploads_collection, [("user_id", 1)])
        self._safe_create_index(self.uploads_collection, [("upload_id", 1)], unique=True, sparse=True)

        # Analysis indexes - use sparse=True to allow null values
        self._safe_create_index(self.analysis_collection, [("user_id", 1)])
        self._safe_create_index(self.analysis_collection, [("analysis_id", 1)], unique=True, sparse=True)

        # Flow sessions indexes
        self._safe_create_index(self.flow_sessions_collection, [("user_id", 1)])
        self._safe_create_index(self.flow_sessions_collection, [("flow_id", 1)], unique=True)
        self._safe_create_index(self.flow_sessions_collection, [("created_at", 1)], expireAfterSeconds=3600)

        logger.info("Policy Locker indexes created/verified")

    def _safe_create_index(self, collection, keys, **kwargs):
        """Safely create an index, handling duplicate key errors gracefully"""
        try:
            collection.create_index(keys, **kwargs)
        except Exception as e:
            error_str = str(e)
            # Ignore duplicate key errors and existing index conflicts
            if "11000" in error_str or "IndexKeySpecsConflict" in error_str or "86" in error_str:
                logger.debug(f"Index already exists or has conflicts, skipping: {keys}")
            else:
                logger.warning(f"Index creation warning for {keys}: {e}")

    def _serialize_doc(self, doc: Dict) -> Dict:
        """Convert MongoDB document for JSON serialization"""
        if doc is None:
            return None
        doc = dict(doc)
        if '_id' in doc:
            doc['_id'] = str(doc['_id'])
        return doc

    # ==================== LOCKER APIs ====================

    async def get_self_policies(
        self,
        user_id: int,
        category: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get all policies owned by the authenticated user from MongoDB

        Args:
            user_id: User's ID
            category: Filter by category
            status: Filter by status
            page: Page number
            limit: Items per page

        Returns:
            Dict with policies list and pagination
        """
        try:
            if self.policy_locker_collection is None:
                return {"policies": [], "pagination": {"currentPage": page, "totalPages": 0, "totalCount": 0}}

            # Build query
            query = {"user_id": user_id, "is_for_self": True}

            if category:
                query["category"] = category

            if status:
                query["status"] = status

            # Get total count
            total_count = self.policy_locker_collection.count_documents(query)
            total_pages = (total_count + limit - 1) // limit if total_count > 0 else 0

            # Get paginated results
            skip = (page - 1) * limit
            policies_cursor = self.policy_locker_collection.find(query).sort("created_at", -1).skip(skip).limit(limit)

            policies = []
            for policy in policies_cursor:
                policy = self._serialize_doc(policy)
                # Update status based on expiry date
                policy = self._update_policy_status(policy)
                policies.append(self._format_policy_summary(policy))

            return {
                "policies": policies,
                "pagination": {
                    "currentPage": page,
                    "totalPages": total_pages,
                    "totalCount": total_count
                }
            }

        except Exception as e:
            logger.error(f"Error getting self policies: {e}")
            raise

    async def get_self_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Get aggregated summary for user's own policies from MongoDB

        Args:
            user_id: User's ID

        Returns:
            Dict with summary statistics
        """
        try:
            if self.policy_locker_collection is None:
                return {
                    "totalPolicies": 0,
                    "activePolicies": 0,
                    "expiringPolicies": 0,
                    "totalCoverage": "₹0",
                    "averageProtectionScore": 0
                }

            # Aggregation pipeline
            pipeline = [
                {"$match": {"user_id": user_id, "is_for_self": True}},
                {"$group": {
                    "_id": None,
                    "totalPolicies": {"$sum": 1},
                    "totalCoverage": {"$sum": {"$toInt": {"$ifNull": ["$coverage_amount", "0"]}}},
                    "totalScore": {"$sum": {"$ifNull": ["$protection_score", 0]}},
                    "activeCount": {
                        "$sum": {"$cond": [{"$eq": ["$status", "Active"]}, 1, 0]}
                    },
                    "expiringCount": {
                        "$sum": {"$cond": [{"$eq": ["$status", "Expiring Soon"]}, 1, 0]}
                    }
                }}
            ]

            result = list(self.policy_locker_collection.aggregate(pipeline))

            if result:
                data = result[0]
                avg_score = int(data["totalScore"] / data["totalPolicies"]) if data["totalPolicies"] > 0 else 0
                return {
                    "totalPolicies": data["totalPolicies"],
                    "activePolicies": data["activeCount"],
                    "expiringPolicies": data["expiringCount"],
                    "totalCoverage": self._format_currency(data["totalCoverage"]),
                    "averageProtectionScore": avg_score
                }

            return {
                "totalPolicies": 0,
                "activePolicies": 0,
                "expiringPolicies": 0,
                "totalCoverage": "₹0",
                "averageProtectionScore": 0
            }

        except Exception as e:
            logger.error(f"Error getting self summary: {e}")
            raise

    async def get_portfolio_statistics(self, user_id: int) -> Dict[str, Any]:
        """
        Get category-wise breakdown of coverage from MongoDB

        Args:
            user_id: User's ID

        Returns:
            Dict with category breakdown
        """
        try:
            if self.policy_locker_collection is None:
                return {"categoryBreakdown": [], "totalCoverage": "₹0"}

            # Aggregation by category
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {
                    "_id": "$category",
                    "policyCount": {"$sum": 1},
                    "totalCoverage": {"$sum": {"$toInt": {"$ifNull": ["$coverage_amount", "0"]}}}
                }}
            ]

            category_results = list(self.policy_locker_collection.aggregate(pipeline))

            # Calculate total coverage
            total_coverage = sum(cat["totalCoverage"] for cat in category_results)

            # Format breakdown
            breakdown = []
            for cat in category_results:
                percentage = round((cat["totalCoverage"] / total_coverage * 100), 1) if total_coverage > 0 else 0
                breakdown.append({
                    "category": cat["_id"],
                    "displayName": self._get_category_display_name(cat["_id"]),
                    "policyCount": cat["policyCount"],
                    "totalCoverage": self._format_currency(cat["totalCoverage"]),
                    "coveragePercentage": percentage
                })

            # Sort by coverage percentage descending
            breakdown.sort(key=lambda x: x["coveragePercentage"], reverse=True)

            return {
                "categoryBreakdown": breakdown,
                "totalCoverage": self._format_currency(total_coverage)
            }

        except Exception as e:
            logger.error(f"Error getting portfolio statistics: {e}")
            raise

    # ==================== FAMILY APIs ====================

    async def get_family_members(self, user_id: int) -> Dict[str, Any]:
        """
        Fetch all family members with their policy summary from MongoDB

        Args:
            user_id: User's ID

        Returns:
            Dict with members list and summary
        """
        try:
            if self.family_members_collection is None:
                return {"members": [], "summary": {"totalMembers": 0, "totalPolicies": 0, "totalCoverage": "₹0"}}

            # Get all family members
            members_cursor = self.family_members_collection.find({"user_id": user_id}).sort("created_at", -1)
            members = []
            total_policies = 0
            total_coverage = 0

            for member in members_cursor:
                member = self._serialize_doc(member)

                # Get policies count and coverage for this member
                if self.policy_locker_collection is not None:
                    member_pipeline = [
                        {"$match": {"member_id": member.get("member_id")}},
                        {"$group": {
                            "_id": None,
                            "count": {"$sum": 1},
                            "coverage": {"$sum": {"$toInt": {"$ifNull": ["$coverage_amount", "0"]}}}
                        }}
                    ]
                    member_stats = list(self.policy_locker_collection.aggregate(member_pipeline))

                    if member_stats:
                        member["policiesCount"] = member_stats[0]["count"]
                        member["totalCoverage"] = self._format_currency(member_stats[0]["coverage"])
                        total_policies += member_stats[0]["count"]
                        total_coverage += member_stats[0]["coverage"]
                    else:
                        member["policiesCount"] = 0
                        member["totalCoverage"] = "₹0"
                else:
                    member["policiesCount"] = 0
                    member["totalCoverage"] = "₹0"

                members.append({
                    "id": member.get("member_id"),
                    "name": member.get("name"),
                    "relation": member.get("relationship"),
                    "avatar": member.get("avatar", "👤"),
                    "gender": member.get("gender"),
                    "dateOfBirth": member.get("date_of_birth"),
                    "policiesCount": member["policiesCount"],
                    "totalCoverage": member["totalCoverage"],
                    "protectionScore": member.get("protection_score", 0)
                })

            return {
                "members": members,
                "summary": {
                    "totalMembers": len(members),
                    "totalPolicies": total_policies,
                    "totalCoverage": self._format_currency(total_coverage)
                }
            }

        except Exception as e:
            logger.error(f"Error getting family members: {e}")
            raise

    async def get_family_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Get aggregated summary for family policies from MongoDB

        Args:
            user_id: User's ID

        Returns:
            Dict with family summary
        """
        try:
            result = await self.get_family_members(user_id)
            members = result.get("members", [])

            avg_score = 0
            if members:
                total_score = sum(m.get("protectionScore", 0) for m in members)
                avg_score = int(total_score / len(members))

            return {
                "totalMembers": result["summary"]["totalMembers"],
                "totalPolicies": result["summary"]["totalPolicies"],
                "totalCoverage": result["summary"]["totalCoverage"],
                "averageProtectionScore": avg_score
            }

        except Exception as e:
            logger.error(f"Error getting family summary: {e}")
            raise

    async def get_family_member_policies(
        self,
        user_id: int,
        member_id: str,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Fetch all policies for a specific family member from MongoDB

        Args:
            user_id: User's ID
            member_id: Family member ID
            page: Page number
            limit: Items per page

        Returns:
            Dict with policies and pagination
        """
        try:
            if self.policy_locker_collection is None:
                return {"policies": [], "pagination": {"currentPage": page, "totalPages": 0, "totalCount": 0}}

            # Verify member belongs to user
            if self.family_members_collection is not None:
                member = self.family_members_collection.find_one({"user_id": user_id, "member_id": member_id})
                if not member:
                    raise ValueError(f"Family member not found: {member_id}")

            # Get policies for member
            query = {"member_id": member_id}
            total_count = self.policy_locker_collection.count_documents(query)
            total_pages = (total_count + limit - 1) // limit if total_count > 0 else 0

            skip = (page - 1) * limit
            policies_cursor = self.policy_locker_collection.find(query).sort("created_at", -1).skip(skip).limit(limit)

            policies = []
            for policy in policies_cursor:
                policy = self._serialize_doc(policy)
                policy = self._update_policy_status(policy)
                policies.append(self._format_policy_summary(policy))

            return {
                "policies": policies,
                "pagination": {
                    "currentPage": page,
                    "totalPages": total_pages,
                    "totalCount": total_count
                }
            }

        except Exception as e:
            logger.error(f"Error getting family member policies: {e}")
            raise

    async def add_family_member(
        self,
        user_id: int,
        name: str,
        relationship: str,
        date_of_birth: Optional[str] = None,
        gender: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a new family member to MongoDB

        Args:
            user_id: User's ID
            name: Member's name
            relationship: Relationship to user
            date_of_birth: DOB (optional)
            gender: Gender (optional)

        Returns:
            Dict with new member details
        """
        try:
            if self.family_members_collection is None:
                raise ValueError("MongoDB not available")

            member_id = f"FAM_{user_id}_{secrets.token_hex(4)}"

            member_data = {
                "member_id": member_id,
                "user_id": user_id,
                "name": name,
                "relationship": relationship,
                "date_of_birth": date_of_birth,
                "gender": gender,
                "avatar": self._get_avatar_for_relationship(relationship, gender),
                "protection_score": 0,
                "created_at": get_ist_now(),
                "updated_at": get_ist_now()
            }

            self.family_members_collection.insert_one(member_data)

            return {
                "memberId": member_id,
                "name": name,
                "relationship": relationship
            }

        except Exception as e:
            logger.error(f"Error adding family member: {e}")
            raise

    async def update_family_member(
        self,
        user_id: int,
        member_id: str,
        name: Optional[str] = None,
        relationship: Optional[str] = None,
        date_of_birth: Optional[str] = None,
        gender: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update a family member in MongoDB"""
        try:
            if self.family_members_collection is None:
                raise ValueError("MongoDB not available")

            # Build update document
            update_fields = {"updated_at": get_ist_now()}
            if name:
                update_fields["name"] = name
            if relationship:
                update_fields["relationship"] = relationship
                update_fields["avatar"] = self._get_avatar_for_relationship(relationship, gender)
            if date_of_birth:
                update_fields["date_of_birth"] = date_of_birth
            if gender:
                update_fields["gender"] = gender

            result = self.family_members_collection.update_one(
                {"user_id": user_id, "member_id": member_id},
                {"$set": update_fields}
            )

            if result.matched_count == 0:
                raise ValueError(f"Family member not found: {member_id}")

            return {"memberId": member_id, "updated": True}

        except Exception as e:
            logger.error(f"Error updating family member: {e}")
            raise

    async def delete_family_member(self, user_id: int, member_id: str) -> Dict[str, Any]:
        """Delete a family member from MongoDB"""
        try:
            if self.family_members_collection is None:
                raise ValueError("MongoDB not available")

            result = self.family_members_collection.delete_one({"user_id": user_id, "member_id": member_id})

            if result.deleted_count == 0:
                raise ValueError(f"Family member not found: {member_id}")

            # Also delete associated policies
            if self.policy_locker_collection is not None:
                self.policy_locker_collection.delete_many({"member_id": member_id})

            return {"memberId": member_id, "deleted": True}

        except Exception as e:
            logger.error(f"Error deleting family member: {e}")
            raise

    async def get_member_details(self, user_id: int, member_id: str) -> Dict[str, Any]:
        """
        Get details of a specific family member from MongoDB

        Args:
            user_id: User's ID
            member_id: Member's ID

        Returns:
            Dict with member details
        """
        try:
            if self.family_members_collection is None:
                raise ValueError("MongoDB not available")

            member = self.family_members_collection.find_one({"user_id": user_id, "member_id": member_id})

            if not member:
                raise ValueError(f"Member not found: {member_id}")

            member = self._serialize_doc(member)

            return {
                "id": member.get("member_id"),
                "name": member.get("name"),
                "relation": member.get("relationship"),
                "avatar": member.get("avatar", "👤"),
                "gender": member.get("gender"),
                "dateOfBirth": member.get("date_of_birth"),
                "protectionScore": member.get("protection_score", 0)
            }

        except Exception as e:
            logger.error(f"Error getting member details: {e}")
            raise

    # ==================== POLICY DETAILS APIs ====================

    async def get_policy_details(self, user_id: int, policy_id: str) -> Dict[str, Any]:
        """
        Get complete details of a specific policy from MongoDB

        Args:
            user_id: User's ID
            policy_id: Policy ID

        Returns:
            Dict with full policy details
        """
        try:
            if self.policy_locker_collection is None:
                raise ValueError("MongoDB not available")

            policy = self.policy_locker_collection.find_one({"policy_id": policy_id, "user_id": user_id})

            if not policy:
                # Also check member policies
                policy = self.policy_locker_collection.find_one({"policy_id": policy_id})
                if policy:
                    # Verify user owns the member
                    if self.family_members_collection is not None:
                        member = self.family_members_collection.find_one({
                            "user_id": user_id,
                            "member_id": policy.get("member_id")
                        })
                        if not member:
                            raise ValueError(f"Policy not found: {policy_id}")
                else:
                    raise ValueError(f"Policy not found: {policy_id}")

            policy = self._serialize_doc(policy)
            policy = self._update_policy_status(policy)

            # Format response
            return {
                "id": policy.get("policy_id"),
                "policyNumber": policy.get("policy_number"),
                "provider": policy.get("provider"),
                "category": policy.get("category"),
                "subType": policy.get("sub_type"),
                "policyHolderName": policy.get("policy_holder_name"),
                "startDate": policy.get("start_date"),
                "expiryDate": policy.get("expiry_date"),
                "premium": policy.get("premium"),
                "premiumType": policy.get("premium_type"),
                "coverageAmount": policy.get("coverage_amount"),
                "idv": policy.get("idv"),
                "status": policy.get("status"),
                "protectionScore": policy.get("protection_score", 0),
                "needsAction": policy.get("needs_action", False),
                "actionMessage": policy.get("action_message"),
                "insuredMembers": policy.get("insured_members", 1),
                "keyBenefits": policy.get("key_benefits", []),
                "coverageGaps": policy.get("coverage_gaps", []),
                "exclusions": policy.get("exclusions", []),
                "documents": policy.get("documents", []),
                "insuredMemberNames": policy.get("insured_member_names", []),
                "categorySpecificData": policy.get("category_specific_data", {})
            }

        except Exception as e:
            logger.error(f"Error getting policy details: {e}")
            raise

    async def add_policy(
        self,
        user_id: int,
        policy_data: Dict[str, Any],
        member_id: Optional[str] = None,
        is_for_self: bool = True
    ) -> Dict[str, Any]:
        """
        Add a new policy to the locker

        Args:
            user_id: User's ID
            policy_data: Policy details
            member_id: Family member ID (if not for self)
            is_for_self: Whether policy is for the user themselves

        Returns:
            Dict with new policy ID
        """
        try:
            if self.policy_locker_collection is None:
                raise ValueError("MongoDB not available")

            policy_id = f"POL_{user_id}_{secrets.token_hex(6)}"

            # Build policy document
            policy_doc = {
                "policy_id": policy_id,
                "user_id": user_id,
                "member_id": member_id,
                "is_for_self": is_for_self,
                "policy_number": policy_data.get("policyNumber"),
                "provider": policy_data.get("provider"),
                "category": policy_data.get("category"),
                "sub_type": policy_data.get("subType"),
                "policy_holder_name": policy_data.get("policyHolderName"),
                "start_date": policy_data.get("startDate"),
                "expiry_date": policy_data.get("expiryDate"),
                "premium": policy_data.get("premium"),
                "premium_type": policy_data.get("premiumType", "Annual"),
                "coverage_amount": policy_data.get("coverageAmount"),
                "idv": policy_data.get("idv"),
                "status": "Active",
                "protection_score": policy_data.get("protectionScore", 75),
                "needs_action": False,
                "insured_members": policy_data.get("insuredMembers", 1),
                "key_benefits": policy_data.get("keyBenefits", []),
                "coverage_gaps": policy_data.get("coverageGaps", []),
                "exclusions": policy_data.get("exclusions", []),
                "documents": policy_data.get("documents", []),
                "insured_member_names": policy_data.get("insuredMemberNames", []),
                "category_specific_data": policy_data.get("categorySpecificData", {}),
                "created_at": get_ist_now(),
                "updated_at": get_ist_now()
            }

            self.policy_locker_collection.insert_one(policy_doc)

            return {"policyId": policy_id, "message": "Policy added successfully"}

        except Exception as e:
            logger.error(f"Error adding policy: {e}")
            raise

    async def delete_policy(self, user_id: int, policy_id: str) -> Dict[str, Any]:
        """Delete a policy from MongoDB"""
        try:
            if self.policy_locker_collection is None:
                raise ValueError("MongoDB not available")

            result = self.policy_locker_collection.delete_one({"policy_id": policy_id, "user_id": user_id})

            if result.deleted_count == 0:
                raise ValueError(f"Policy not found: {policy_id}")

            return {"policyId": policy_id, "deleted": True}

        except Exception as e:
            logger.error(f"Error deleting policy: {e}")
            raise

    async def get_policy_gap_analysis(self, user_id: int, policy_id: str) -> Dict[str, Any]:
        """
        Get AI-generated gap analysis for a policy

        Args:
            user_id: User's ID
            policy_id: Policy ID

        Returns:
            Dict with gap analysis
        """
        try:
            policy = await self.get_policy_details(user_id, policy_id)
            category = policy.get("category", "health")
            score = policy.get("protectionScore", 75)

            gaps = self._generate_gap_analysis(category, score, policy.get("categorySpecificData", {}))

            return {
                "gaps": gaps,
                "overallScore": score,
                "recommendations": self._get_recommendations(category, policy.get("categorySpecificData", {}))
            }

        except Exception as e:
            logger.error(f"Error getting gap analysis: {e}")
            raise

    async def get_policy_documents(self, user_id: int, policy_id: str) -> Dict[str, Any]:
        """
        Get documents associated with a policy

        Args:
            user_id: User's ID
            policy_id: Policy ID

        Returns:
            Dict with documents list
        """
        try:
            policy = await self.get_policy_details(user_id, policy_id)
            documents = policy.get("documents", [])

            # Format documents
            formatted_docs = []
            for i, doc in enumerate(documents):
                if isinstance(doc, str):
                    formatted_docs.append({
                        "id": f"DOC_{policy_id}_{i+1:03d}",
                        "name": doc,
                        "type": "pdf",
                        "size": "Unknown",
                        "uploadedAt": policy.get("startDate", get_ist_now().isoformat()),
                        "downloadUrl": f"/api/v1/documents/{policy_id}/{i+1}"
                    })
                elif isinstance(doc, dict):
                    formatted_docs.append(doc)

            return {"documents": formatted_docs}

        except Exception as e:
            logger.error(f"Error getting policy documents: {e}")
            raise

    # ==================== ANALYSIS & RECOMMENDATIONS ====================

    async def get_analysis_report(self, user_id: int, policy_id: str) -> Dict[str, Any]:
        """
        Get comprehensive AI-powered analysis report

        Args:
            user_id: User's ID
            policy_id: Policy ID

        Returns:
            Dict with analysis report
        """
        try:
            policy = await self.get_policy_details(user_id, policy_id)

            return {
                "generatedAt": get_ist_now().isoformat(),
                "coverageAmount": self._format_currency(int(policy.get("coverageAmount", 0))),
                "protectionScore": policy.get("protectionScore", 75),
                "insights": self._generate_insights(policy),
                "recommendations": self._generate_report_recommendations(policy)
            }

        except Exception as e:
            logger.error(f"Error getting analysis report: {e}")
            raise

    async def get_policy_recommendations(self, user_id: int, policy_id: str) -> Dict[str, Any]:
        """
        Get personalized recommendations for policy enhancement

        Args:
            user_id: User's ID
            policy_id: Policy ID

        Returns:
            Dict with recommendations
        """
        try:
            policy = await self.get_policy_details(user_id, policy_id)
            category = policy.get("category", "health")
            category_data = policy.get("categorySpecificData", {})

            recommendations = self._get_detailed_recommendations(category, category_data)

            return {"recommendations": recommendations}

        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            raise

    # ==================== EMERGENCY SERVICES ====================

    async def get_emergency_categories(self) -> Dict[str, Any]:
        """Get emergency service categories"""
        return {
            "categories": [
                {
                    "id": "medical",
                    "title": "Medical Emergency",
                    "description": "Ambulance, hospitals, blood banks",
                    "icon": "🏥"
                },
                {
                    "id": "vehicle",
                    "title": "Vehicle Emergency",
                    "description": "Roadside assistance, towing",
                    "icon": "🚗"
                },
                {
                    "id": "other",
                    "title": "Other Emergency",
                    "description": "Police, fire, general helplines",
                    "icon": "🆘"
                }
            ]
        }

    async def get_emergency_contacts(self, category: str) -> Dict[str, Any]:
        """Get emergency contacts by category"""
        contacts_map = {
            "medical": [
                {"id": "EMG_001", "name": "National Emergency", "number": "112", "description": "All emergencies", "isEmergency": True},
                {"id": "EMG_002", "name": "Ambulance", "number": "102", "description": "Medical emergency", "isEmergency": True},
                {"id": "EMG_003", "name": "Apollo Hospital", "number": "1800-102-0288", "description": "24/7 helpline", "isEmergency": False},
                {"id": "EMG_004", "name": "Fortis Hospital", "number": "1800-102-2244", "description": "24/7 helpline", "isEmergency": False},
                {"id": "EMG_005", "name": "Blood Bank", "number": "104", "description": "Blood donation helpline", "isEmergency": False}
            ],
            "vehicle": [
                {"id": "EMG_006", "name": "Road Accident", "number": "1073", "description": "Highway helpline", "isEmergency": True},
                {"id": "EMG_007", "name": "HDFC Ergo RSA", "number": "1800-266-0700", "description": "Roadside assistance", "isEmergency": False},
                {"id": "EMG_008", "name": "Bajaj Allianz RSA", "number": "1800-209-5858", "description": "Roadside assistance", "isEmergency": False},
                {"id": "EMG_009", "name": "Traffic Police", "number": "103", "description": "Traffic helpline", "isEmergency": False}
            ],
            "other": [
                {"id": "EMG_010", "name": "Police", "number": "100", "description": "Police emergency", "isEmergency": True},
                {"id": "EMG_011", "name": "Fire", "number": "101", "description": "Fire emergency", "isEmergency": True},
                {"id": "EMG_012", "name": "Women Helpline", "number": "1091", "description": "Women safety", "isEmergency": True},
                {"id": "EMG_013", "name": "Child Helpline", "number": "1098", "description": "Child welfare", "isEmergency": True},
                {"id": "EMG_014", "name": "Disaster Management", "number": "108", "description": "Natural disasters", "isEmergency": True}
            ]
        }

        return {"contacts": contacts_map.get(category, [])}

    # ==================== CLAIMS APIs ====================

    async def get_claim_types(self, policy_id: str) -> Dict[str, Any]:
        """Get available claim types for a policy"""
        claim_types = [
            {"id": "hospitalization", "title": "Hospitalization", "description": "Hospital admission claims", "icon": "🏥"},
            {"id": "outpatient", "title": "Outpatient", "description": "OPD treatment claims", "icon": "💊"},
            {"id": "daycare", "title": "Day Care", "description": "Day care procedures", "icon": "🩺"},
            {"id": "pharmacy", "title": "Pharmacy", "description": "Medicine reimbursement", "icon": "💉"}
        ]

        return {"claimTypes": claim_types}

    async def get_required_documents(self, policy_id: str, claim_type: str) -> Dict[str, Any]:
        """Get required documents for claim filing"""
        documents = [
            {"id": "DOC_001", "name": "Claim Form", "description": "Filled and signed claim form", "isMandatory": True},
            {"id": "DOC_002", "name": "Hospital Bills", "description": "Original hospital bills", "isMandatory": True},
            {"id": "DOC_003", "name": "Discharge Summary", "description": "Hospital discharge summary", "isMandatory": True},
            {"id": "DOC_004", "name": "Doctor's Prescription", "description": "Treating doctor's prescription", "isMandatory": True},
            {"id": "DOC_005", "name": "Test Reports", "description": "All diagnostic test reports", "isMandatory": False},
            {"id": "DOC_006", "name": "ID Proof", "description": "Valid government ID", "isMandatory": True}
        ]

        return {"requiredDocuments": documents}

    async def initiate_claim(
        self,
        user_id: int,
        policy_id: str,
        claim_type: str,
        description: str,
        documents: List[str]
    ) -> Dict[str, Any]:
        """Initiate a new claim and store in MongoDB"""
        try:
            if self.claims_collection is None:
                raise ValueError("MongoDB not available")

            claim_id = f"CLM_{user_id}_{secrets.token_hex(4)}"
            claim_number = f"EAZR-{datetime.now().strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}"

            claim_data = {
                "claim_id": claim_id,
                "claim_number": claim_number,
                "user_id": user_id,
                "policy_id": policy_id,
                "claim_type": claim_type,
                "description": description,
                "documents": documents,
                "status": "initiated",
                "created_at": get_ist_now(),
                "updated_at": get_ist_now()
            }

            self.claims_collection.insert_one(claim_data)

            return {
                "claimId": claim_id,
                "claimNumber": claim_number,
                "status": "initiated",
                "nextSteps": [
                    "Your claim has been registered",
                    "Upload all required documents within 48 hours",
                    "Our team will review and process within 5-7 business days",
                    "You will receive updates via SMS and email"
                ]
            }

        except Exception as e:
            logger.error(f"Error initiating claim: {e}")
            raise

    async def get_claim_status(self, user_id: int, claim_id: str) -> Dict[str, Any]:
        """Get status of a claim from MongoDB"""
        try:
            if self.claims_collection is None:
                raise ValueError("MongoDB not available")

            claim = self.claims_collection.find_one({"user_id": user_id, "claim_id": claim_id})

            if not claim:
                raise ValueError(f"Claim not found: {claim_id}")

            claim = self._serialize_doc(claim)

            return {
                "claimId": claim.get("claim_id"),
                "claimNumber": claim.get("claim_number"),
                "status": claim.get("status"),
                "policyId": claim.get("policy_id"),
                "claimType": claim.get("claim_type"),
                "description": claim.get("description"),
                "createdAt": claim.get("created_at").isoformat() if claim.get("created_at") else None,
                "updatedAt": claim.get("updated_at").isoformat() if claim.get("updated_at") else None
            }

        except Exception as e:
            logger.error(f"Error getting claim status: {e}")
            raise

    async def get_user_claims(self, user_id: int, status: Optional[str] = None) -> Dict[str, Any]:
        """Get all claims for a user"""
        try:
            if self.claims_collection is None:
                return {"claims": []}

            query = {"user_id": user_id}
            if status:
                query["status"] = status

            claims_cursor = self.claims_collection.find(query).sort("created_at", -1)

            claims = []
            for claim in claims_cursor:
                claim = self._serialize_doc(claim)
                claims.append({
                    "claimId": claim.get("claim_id"),
                    "claimNumber": claim.get("claim_number"),
                    "status": claim.get("status"),
                    "policyId": claim.get("policy_id"),
                    "claimType": claim.get("claim_type"),
                    "createdAt": claim.get("created_at").isoformat() if claim.get("created_at") else None
                })

            return {"claims": claims}

        except Exception as e:
            logger.error(f"Error getting user claims: {e}")
            raise

    # ==================== RENEWAL APIs ====================

    async def get_renewal_quote(self, user_id: int, policy_id: str) -> Dict[str, Any]:
        """Get renewal quote for a policy"""
        try:
            policy = await self.get_policy_details(user_id, policy_id)
            current_premium = int(policy.get("premium", 10000))

            # Calculate renewal premium
            base_premium = int(current_premium * 1.05)  # 5% increase
            taxes = int(base_premium * 0.18)  # 18% GST

            discounts = []
            total_discount = 0

            # NCB discount for motor
            if policy.get("category") == "motor":
                ncb_percent = policy.get("categorySpecificData", {}).get("ncbPercentage", "0%")
                ncb_value = int(ncb_percent.replace("%", "")) if ncb_percent else 0
                if ncb_value > 0:
                    ncb_discount = int(base_premium * ncb_value / 100)
                    discounts.append({
                        "type": "NCB",
                        "amount": self._format_currency(ncb_discount),
                        "description": f"No Claim Bonus - {ncb_percent}"
                    })
                    total_discount += ncb_discount

            # Loyalty discount
            loyalty_discount = int(base_premium * 0.05)
            discounts.append({
                "type": "Loyalty",
                "amount": self._format_currency(loyalty_discount),
                "description": "Loyalty discount - 5%"
            })
            total_discount += loyalty_discount

            final_premium = base_premium + taxes - total_discount

            return {
                "policyId": policy_id,
                "currentPremium": self._format_currency(current_premium),
                "renewalPremium": self._format_currency(final_premium),
                "basePremium": self._format_currency(base_premium),
                "taxes": self._format_currency(taxes),
                "totalPremium": self._format_currency(final_premium),
                "expiryDate": policy.get("expiryDate"),
                "renewalBenefits": [
                    {"title": "Continuous Coverage", "description": "No break in coverage"},
                    {"title": "Accumulated Benefits", "description": "All accumulated bonuses retained"},
                    {"title": "Hassle-free Process", "description": "No medical tests required"}
                ],
                "discounts": discounts
            }

        except Exception as e:
            logger.error(f"Error getting renewal quote: {e}")
            raise

    async def renew_policy(
        self,
        user_id: int,
        policy_id: str,
        payment_method: str,
        modifications: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Initiate policy renewal"""
        try:
            quote = await self.get_renewal_quote(user_id, policy_id)
            renewal_id = f"REN_{user_id}_{secrets.token_hex(4)}"

            return {
                "renewalId": renewal_id,
                "paymentUrl": f"https://pay.eazr.in/renewal/{renewal_id}",
                "amount": quote["totalPremium"]
            }

        except Exception as e:
            logger.error(f"Error renewing policy: {e}")
            raise

    # ==================== EXPORT & SHARE APIs ====================

    async def export_policy(
        self,
        user_id: int,
        policy_id: str,
        format: str
    ) -> Dict[str, Any]:
        """Export policy in specified format"""
        try:
            export_id = secrets.token_hex(8)
            expires_at = (get_ist_now() + timedelta(hours=24)).isoformat()

            return {
                "downloadUrl": f"https://api.eazr.in/exports/{export_id}/policy.{format}",
                "expiresAt": expires_at
            }

        except Exception as e:
            logger.error(f"Error exporting policy: {e}")
            raise

    async def share_policy(
        self,
        user_id: int,
        policy_id: str,
        method: str,
        email: Optional[str] = None,
        expiry_hours: int = 24
    ) -> Dict[str, Any]:
        """Share policy via email or link"""
        try:
            share_id = secrets.token_hex(8)
            expires_at = (get_ist_now() + timedelta(hours=expiry_hours)).isoformat()

            result = {
                "shareUrl": None,
                "emailSent": False,
                "expiresAt": expires_at
            }

            if method in ["link", "print"]:
                result["shareUrl"] = f"https://eazr.in/shared/{share_id}"

            if method == "email" and email:
                result["emailSent"] = True
                # In production, send actual email

            return result

        except Exception as e:
            logger.error(f"Error sharing policy: {e}")
            raise

    # ==================== CONFIG APIs ====================

    async def get_relationships(self) -> Dict[str, Any]:
        """Get available relationship types"""
        return {
            "relationships": [
                {"id": "spouse", "label": "Spouse", "icon": "💑"},
                {"id": "son", "label": "Son", "icon": "👦"},
                {"id": "daughter", "label": "Daughter", "icon": "👧"},
                {"id": "father", "label": "Father", "icon": "👨"},
                {"id": "mother", "label": "Mother", "icon": "👩"},
                {"id": "brother", "label": "Brother", "icon": "👨‍👦"},
                {"id": "sister", "label": "Sister", "icon": "👩‍👧"},
                {"id": "friend", "label": "Friend", "icon": "🤝"}
            ]
        }

    async def get_insurance_categories(self) -> Dict[str, Any]:
        """Get all supported insurance categories"""
        return {
            "categories": [
                {
                    "id": "life",
                    "displayName": "Life Insurance",
                    "subTypes": [
                        {"id": "term", "name": "Term Life"},
                        {"id": "endowment", "name": "Endowment"},
                        {"id": "ulip", "name": "ULIP"},
                        {"id": "retirement", "name": "Retirement"},
                        {"id": "group", "name": "Group Life"}
                    ]
                },
                {
                    "id": "health",
                    "displayName": "Health Insurance",
                    "subTypes": [
                        {"id": "individual", "name": "Individual Health"},
                        {"id": "family_floater", "name": "Family Floater"},
                        {"id": "super_topup", "name": "Super Top-Up"},
                        {"id": "critical_illness", "name": "Critical Illness"},
                        {"id": "senior_citizen", "name": "Senior Citizen"}
                    ]
                },
                {
                    "id": "motor",
                    "displayName": "Motor Insurance",
                    "subTypes": [
                        {"id": "car_comprehensive", "name": "Car Comprehensive"},
                        {"id": "car_tp", "name": "Car Third Party"},
                        {"id": "bike_comprehensive", "name": "Two Wheeler Comprehensive"},
                        {"id": "bike_tp", "name": "Two Wheeler Third Party"},
                        {"id": "commercial", "name": "Commercial Vehicle"}
                    ]
                },
                {
                    "id": "general",
                    "displayName": "General Insurance",
                    "subTypes": [
                        {"id": "home", "name": "Home Insurance"},
                        {"id": "travel", "name": "Travel Insurance"},
                        {"id": "property", "name": "Property Insurance"}
                    ]
                },
                {
                    "id": "business",
                    "displayName": "Business Insurance",
                    "subTypes": [
                        {"id": "shop", "name": "Shop Insurance"},
                        {"id": "liability", "name": "Liability Insurance"},
                        {"id": "cyber", "name": "Cyber Insurance"}
                    ]
                },
                {
                    "id": "specialty",
                    "displayName": "Specialty Insurance",
                    "subTypes": [
                        {"id": "critical_illness", "name": "Critical Illness"},
                        {"id": "hospital_cash", "name": "Hospital Cash"}
                    ]
                }
            ]
        }

    async def get_upload_config(self) -> Dict[str, Any]:
        """Get upload configuration"""
        return {
            "supportedFormats": ["pdf", "jpg", "jpeg", "png"],
            "maxFileSizeMB": 10,
            "supportedPolicyTypes": ["Health", "Life", "Vehicle", "Property", "Travel", "Business"]
        }

    # ==================== ADD POLICY FLOW APIs ====================
    # Flow Steps:
    # For Self: SELECT_OWNER -> SELECT_INSURANCE_TYPE -> UPLOAD_DOCUMENT -> ANALYZING -> REVIEW_ANALYSIS -> CONFIRM_POLICY -> COMPLETED
    # For Family: SELECT_OWNER -> SELECT_RELATIONSHIP -> ENTER_MEMBER_DETAILS -> SELECT_INSURANCE_TYPE -> UPLOAD_DOCUMENT -> ANALYZING -> REVIEW_ANALYSIS -> CONFIRM_POLICY -> COMPLETED

    async def start_add_policy_flow(self, user_id: int) -> Dict[str, Any]:
        """
        Start a new Add Policy flow

        Args:
            user_id: User's ID

        Returns:
            Dict with flow ID and initial state
        """
        try:
            # Try lazy initialization if MongoDB wasn't available at startup
            if self.flow_sessions_collection is None:
                if not self._try_reconnect_mongodb():
                    raise ValueError("MongoDB not available. Please check database connection.")

            flow_id = f"FLOW_{user_id}_{secrets.token_hex(6)}"

            flow_data = {
                "flow_id": flow_id,
                "user_id": user_id,
                "current_step": "select_owner",
                "owner_type": None,
                "member_id": None,
                "member_name": None,
                "relationship": None,
                "gender": None,
                "date_of_birth": None,
                "category": None,
                "sub_type": None,
                "upload_id": None,
                "analysis_id": None,
                "analysis_status": None,
                "policy_id": None,
                "created_at": get_ist_now(),
                "updated_at": get_ist_now()
            }

            self.flow_sessions_collection.insert_one(flow_data)

            return {
                "flowId": flow_id,
                "currentStep": "select_owner",
                "ownerType": None,
                "memberId": None,
                "memberName": None,
                "relationship": None,
                "category": None,
                "subType": None,
                "uploadId": None,
                "analysisId": None,
                "analysisStatus": None,
                "nextStep": "select_owner",
                "message": "Flow started. Please select who this policy is for."
            }

        except Exception as e:
            logger.error(f"Error starting add policy flow: {e}")
            raise

    async def select_owner_type(
        self,
        user_id: int,
        flow_id: str,
        owner_type: str
    ) -> Dict[str, Any]:
        """
        Step 1: Select policy owner (self or family/friend)

        Args:
            user_id: User's ID
            flow_id: Flow session ID
            owner_type: "self", "family", or "friend"

        Returns:
            Dict with updated flow state
        """
        try:
            # Try lazy initialization if MongoDB wasn't available at startup
            if self.flow_sessions_collection is None:
                if not self._try_reconnect_mongodb():
                    raise ValueError("MongoDB not available. Please check database connection.")

            # Validate flow exists and belongs to user
            flow = self.flow_sessions_collection.find_one({
                "flow_id": flow_id,
                "user_id": user_id
            })

            if not flow:
                raise ValueError(f"Flow not found: {flow_id}")

            if flow.get("current_step") != "select_owner":
                raise ValueError(f"Invalid step. Current step is: {flow.get('current_step')}")

            # Determine next step based on owner type
            if owner_type == "self":
                next_step = "select_insurance_type"
            else:  # family or friend
                next_step = "select_relationship"

            # Update flow state
            self.flow_sessions_collection.update_one(
                {"flow_id": flow_id},
                {"$set": {
                    "owner_type": owner_type,
                    "current_step": next_step,
                    "updated_at": get_ist_now()
                }}
            )

            message = "Owner selected as self. Please select insurance type." if owner_type == "self" else "Please select the relationship."

            return {
                "flowId": flow_id,
                "currentStep": next_step,
                "ownerType": owner_type,
                "memberId": None,
                "memberName": None,
                "relationship": None,
                "category": None,
                "subType": None,
                "uploadId": None,
                "analysisId": None,
                "analysisStatus": None,
                "nextStep": next_step,
                "message": message
            }

        except Exception as e:
            logger.error(f"Error selecting owner type: {e}")
            raise

    async def select_relationship(
        self,
        user_id: int,
        flow_id: str,
        relationship: str
    ) -> Dict[str, Any]:
        """
        Step 2 (Family): Select relationship type

        Args:
            user_id: User's ID
            flow_id: Flow session ID
            relationship: Relationship type (spouse, son, daughter, etc.)

        Returns:
            Dict with updated flow state
        """
        try:
            # Try lazy initialization if MongoDB wasn't available at startup
            if self.flow_sessions_collection is None:
                if not self._try_reconnect_mongodb():
                    raise ValueError("MongoDB not available. Please check database connection.")

            # Validate flow
            flow = self.flow_sessions_collection.find_one({
                "flow_id": flow_id,
                "user_id": user_id
            })

            if not flow:
                raise ValueError(f"Flow not found: {flow_id}")

            if flow.get("current_step") != "select_relationship":
                raise ValueError(f"Invalid step. Current step is: {flow.get('current_step')}")

            if flow.get("owner_type") == "self":
                raise ValueError("Relationship selection is only for family/friend policies")

            # Update flow state
            self.flow_sessions_collection.update_one(
                {"flow_id": flow_id},
                {"$set": {
                    "relationship": relationship,
                    "current_step": "enter_member_details",
                    "updated_at": get_ist_now()
                }}
            )

            return {
                "flowId": flow_id,
                "currentStep": "enter_member_details",
                "ownerType": flow.get("owner_type"),
                "memberId": None,
                "memberName": None,
                "relationship": relationship,
                "category": None,
                "subType": None,
                "uploadId": None,
                "analysisId": None,
                "analysisStatus": None,
                "nextStep": "enter_member_details",
                "message": f"Relationship set to {relationship}. Please enter member details."
            }

        except Exception as e:
            logger.error(f"Error selecting relationship: {e}")
            raise

    async def enter_member_details(
        self,
        user_id: int,
        flow_id: str,
        name: str,
        gender: str,
        date_of_birth: str
    ) -> Dict[str, Any]:
        """
        Step 3 (Family): Enter member details

        Args:
            user_id: User's ID
            flow_id: Flow session ID
            name: Member's name
            gender: Member's gender
            date_of_birth: Member's DOB (YYYY-MM-DD)

        Returns:
            Dict with updated flow state and member ID
        """
        try:
            # Try lazy initialization if MongoDB wasn't available at startup
            if self.flow_sessions_collection is None:
                if not self._try_reconnect_mongodb():
                    raise ValueError("MongoDB not available. Please check database connection.")

            # Validate flow
            flow = self.flow_sessions_collection.find_one({
                "flow_id": flow_id,
                "user_id": user_id
            })

            if not flow:
                raise ValueError(f"Flow not found: {flow_id}")

            if flow.get("current_step") != "enter_member_details":
                raise ValueError(f"Invalid step. Current step is: {flow.get('current_step')}")

            # Create or get family member
            relationship = flow.get("relationship")

            # Check if member already exists
            existing_member = None
            if self.family_members_collection is not None:
                existing_member = self.family_members_collection.find_one({
                    "user_id": user_id,
                    "name": name,
                    "relationship": relationship
                })

            if existing_member:
                member_id = existing_member.get("member_id")
            else:
                # Create new family member
                member_result = await self.add_family_member(
                    user_id=user_id,
                    name=name,
                    relationship=relationship,
                    date_of_birth=date_of_birth,
                    gender=gender
                )
                member_id = member_result.get("memberId")

            # Update flow state
            self.flow_sessions_collection.update_one(
                {"flow_id": flow_id},
                {"$set": {
                    "member_id": member_id,
                    "member_name": name,
                    "gender": gender,
                    "date_of_birth": date_of_birth,
                    "current_step": "select_insurance_type",
                    "updated_at": get_ist_now()
                }}
            )

            return {
                "flowId": flow_id,
                "currentStep": "select_insurance_type",
                "ownerType": flow.get("owner_type"),
                "memberId": member_id,
                "memberName": name,
                "relationship": relationship,
                "category": None,
                "subType": None,
                "uploadId": None,
                "analysisId": None,
                "analysisStatus": None,
                "nextStep": "select_insurance_type",
                "message": f"Member {name} added. Please select insurance type."
            }

        except Exception as e:
            logger.error(f"Error entering member details: {e}")
            raise

    async def select_insurance_type(
        self,
        user_id: int,
        flow_id: str,
        category: str,
        sub_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Step 4: Select insurance category and sub-type

        Args:
            user_id: User's ID
            flow_id: Flow session ID
            category: Insurance category (health, life, motor, etc.)
            sub_type: Sub-type within category (optional)

        Returns:
            Dict with updated flow state
        """
        try:
            # Try lazy initialization if MongoDB wasn't available at startup
            if self.flow_sessions_collection is None:
                if not self._try_reconnect_mongodb():
                    raise ValueError("MongoDB not available. Please check database connection.")

            # Validate flow
            flow = self.flow_sessions_collection.find_one({
                "flow_id": flow_id,
                "user_id": user_id
            })

            if not flow:
                raise ValueError(f"Flow not found: {flow_id}")

            if flow.get("current_step") != "select_insurance_type":
                raise ValueError(f"Invalid step. Current step is: {flow.get('current_step')}")

            # Update flow state
            self.flow_sessions_collection.update_one(
                {"flow_id": flow_id},
                {"$set": {
                    "category": category,
                    "sub_type": sub_type,
                    "current_step": "upload_document",
                    "updated_at": get_ist_now()
                }}
            )

            category_display = self._get_category_display_name(category)

            return {
                "flowId": flow_id,
                "currentStep": "upload_document",
                "ownerType": flow.get("owner_type"),
                "memberId": flow.get("member_id"),
                "memberName": flow.get("member_name"),
                "relationship": flow.get("relationship"),
                "category": category,
                "subType": sub_type,
                "uploadId": None,
                "analysisId": None,
                "analysisStatus": None,
                "nextStep": "upload_document",
                "message": f"{category_display} selected. Please upload the policy document."
            }

        except Exception as e:
            logger.error(f"Error selecting insurance type: {e}")
            raise

    async def flow_upload_document(
        self,
        user_id: int,
        flow_id: str,
        file_content: bytes,
        filename: str
    ) -> Dict[str, Any]:
        """
        Step 5: Upload policy document within the flow

        This method performs upload AND analysis synchronously,
        returning the complete analysis result directly.

        Args:
            user_id: User's ID
            flow_id: Flow session ID
            file_content: File bytes
            filename: Original filename

        Returns:
            Dict with upload ID, analysis results, and flow state
        """
        try:
            # Try lazy initialization if MongoDB wasn't available at startup
            if self.flow_sessions_collection is None:
                if not self._try_reconnect_mongodb():
                    raise ValueError("MongoDB not available. Please check database connection.")

            # Validate flow
            flow = self.flow_sessions_collection.find_one({
                "flow_id": flow_id,
                "user_id": user_id
            })

            if not flow:
                raise ValueError(f"Flow not found: {flow_id}")

            if flow.get("current_step") != "upload_document":
                raise ValueError(f"Invalid step. Current step is: {flow.get('current_step')}")

            # Upload the document
            member_id = flow.get("member_id")
            is_for_self = flow.get("owner_type") == "self"

            upload_result = await self.upload_policy_document(
                user_id=user_id,
                file_content=file_content,
                filename=filename,
                member_id=member_id,
                is_for_self=is_for_self
            )

            upload_id = upload_result.get("uploadId")

            # Create analysis record
            analysis_result = await self.analyze_policy_document(
                user_id=user_id,
                upload_id=upload_id,
                member_id=member_id,
                member_name=flow.get("member_name"),
                member_dob=flow.get("date_of_birth"),
                member_gender=flow.get("gender"),
                relationship=flow.get("relationship")
            )

            analysis_id = analysis_result.get("analysisId")

            # Perform immediate AI analysis (synchronous)
            # In production, this would use actual OCR/AI services
            extracted_data, protection_score, gap_analysis, key_features, confidence = await self._perform_policy_analysis(
                file_content=file_content,
                filename=filename,
                category=flow.get("category"),
                sub_type=flow.get("sub_type"),
                member_name=flow.get("member_name")
            )

            # Update analysis record with results
            await self.update_analysis_result(
                analysis_id=analysis_id,
                extracted_data=extracted_data,
                protection_score=protection_score,
                gap_analysis=gap_analysis,
                key_features=key_features,
                confidence=confidence
            )

            # Update flow state to review_analysis (skip analyzing step)
            self.flow_sessions_collection.update_one(
                {"flow_id": flow_id},
                {"$set": {
                    "upload_id": upload_id,
                    "analysis_id": analysis_id,
                    "analysis_status": "completed",
                    "current_step": "review_analysis",
                    "updated_at": get_ist_now()
                }}
            )

            return {
                "flowId": flow_id,
                "currentStep": "review_analysis",
                "ownerType": flow.get("owner_type"),
                "memberId": flow.get("member_id"),
                "memberName": flow.get("member_name"),
                "relationship": flow.get("relationship"),
                "category": flow.get("category"),
                "subType": flow.get("sub_type"),
                "uploadId": upload_id,
                "analysisId": analysis_id,
                "analysisStatus": "completed",
                "nextStep": "confirm_policy",
                "message": "Document analyzed successfully. Please review the extracted details.",
                "extractedData": extracted_data,
                "protectionScore": protection_score,
                "gapAnalysis": gap_analysis,
                "keyFeatures": key_features,
                "confidence": confidence
            }

        except Exception as e:
            logger.error(f"Error uploading document in flow: {e}")
            raise

    async def _perform_policy_analysis(
        self,
        file_content: bytes,
        filename: str,
        category: Optional[str] = None,
        sub_type: Optional[str] = None,
        member_name: Optional[str] = None
    ) -> tuple:
        """
        Perform AI analysis on the uploaded policy document.

        In production, this would:
        1. Extract text using OCR (for images) or PDF parser
        2. Use LLM to extract structured policy data
        3. Calculate protection score based on coverage
        4. Identify coverage gaps

        For now, returns simulated analysis based on category.

        Returns:
            Tuple of (extracted_data, protection_score, gap_analysis, key_features, confidence)
        """
        import random
        from datetime import datetime, timedelta

        # Simulate analysis delay (reduced for better UX)
        # In production, actual OCR/AI processing would happen here

        # Generate realistic policy data based on category
        category = category or "health"

        # Provider mapping by category
        providers = {
            "health": ["Star Health", "HDFC Ergo Health", "ICICI Lombard", "Max Bupa", "Care Health"],
            "life": ["LIC", "HDFC Life", "ICICI Prudential", "SBI Life", "Max Life"],
            "motor": ["ICICI Lombard", "Bajaj Allianz", "HDFC Ergo", "New India Assurance", "Tata AIG"],
            "general": ["Bajaj Allianz", "ICICI Lombard", "HDFC Ergo", "New India Assurance"],
            "business": ["ICICI Lombard", "Bajaj Allianz", "HDFC Ergo", "Tata AIG"],
            "specialty": ["Star Health", "HDFC Ergo", "ICICI Lombard", "Care Health"],
            "agricultural": ["New India Assurance", "United India", "Oriental Insurance"]
        }

        provider = random.choice(providers.get(category, providers["health"]))

        # Generate policy number
        prefix_map = {
            "health": "HLTH",
            "life": "LIFE",
            "motor": "MTR",
            "general": "GEN",
            "business": "BIZ",
            "specialty": "SPEC",
            "agricultural": "AGRI"
        }
        prefix = prefix_map.get(category, "POL")
        policy_number = f"{prefix}-{datetime.now().strftime('%Y')}-{secrets.token_hex(4).upper()}"

        # Generate dates
        start_date = datetime.now() - timedelta(days=random.randint(30, 180))
        expiry_date = start_date + timedelta(days=365)

        # Generate amounts based on category
        coverage_ranges = {
            "health": (300000, 2000000),
            "life": (2500000, 10000000),
            "motor": (50000, 500000),
            "general": (100000, 1000000),
            "business": (500000, 5000000),
            "specialty": (200000, 1000000),
            "agricultural": (100000, 500000)
        }
        min_cov, max_cov = coverage_ranges.get(category, (100000, 1000000))
        coverage_amount = random.randint(min_cov // 100000, max_cov // 100000) * 100000

        # Premium is typically 2-5% of coverage for health, less for others
        premium_percent = {"health": 0.03, "life": 0.02, "motor": 0.04, "general": 0.01}.get(category, 0.02)
        premium = int(coverage_amount * premium_percent)

        # Holder name
        holder_name = member_name or "Policy Holder"

        extracted_data = {
            "policyNumber": policy_number,
            "provider": provider,
            "category": category,
            "subType": sub_type,
            "policyHolderName": holder_name,
            "startDate": start_date.strftime("%Y-%m-%d"),
            "expiryDate": expiry_date.strftime("%Y-%m-%d"),
            "premium": str(premium),
            "premiumType": "Annual",
            "coverageAmount": str(coverage_amount),
            "insuredMembers": random.randint(1, 4) if category == "health" else 1
        }

        # Generate key benefits based on category
        benefits_by_category = {
            "health": [
                "Cashless hospitalization at 10,000+ network hospitals",
                "Pre and post hospitalization cover (60/90 days)",
                "Day care procedures covered",
                "Annual health check-up included",
                "No claim bonus up to 50%"
            ],
            "life": [
                "Death benefit payout to nominees",
                "Tax benefits under Section 80C",
                "Optional critical illness rider",
                "Premium waiver on disability",
                "Flexible premium payment options"
            ],
            "motor": [
                "Comprehensive own damage cover",
                "Third party liability coverage",
                "Personal accident cover for owner-driver",
                "24/7 roadside assistance",
                "Cashless repairs at network garages"
            ]
        }
        key_features = random.sample(
            benefits_by_category.get(category, benefits_by_category["health"]),
            min(4, len(benefits_by_category.get(category, benefits_by_category["health"])))
        )
        extracted_data["keyBenefits"] = key_features

        # Generate protection score (60-95)
        protection_score = random.randint(65, 92)

        # Generate gap analysis
        gaps_by_category = {
            "health": [
                {
                    "type": "warning",
                    "title": "Room rent sub-limit",
                    "description": "Policy has room rent capping at 1% of sum insured. Consider upgrading for better coverage.",
                    "severity": "Medium"
                },
                {
                    "type": "info",
                    "title": "Co-payment clause",
                    "description": "10% co-payment applicable for claims. Factor this into your emergency fund.",
                    "severity": "Low"
                },
                {
                    "type": "warning",
                    "title": "Disease waiting period",
                    "description": "2-year waiting period for pre-existing diseases.",
                    "severity": "Medium"
                }
            ],
            "life": [
                {
                    "type": "info",
                    "title": "No critical illness rider",
                    "description": "Consider adding critical illness rider for comprehensive protection.",
                    "severity": "Medium"
                },
                {
                    "type": "info",
                    "title": "Review nominee details",
                    "description": "Ensure nominee details are up to date.",
                    "severity": "Low"
                }
            ],
            "motor": [
                {
                    "type": "warning",
                    "title": "Depreciation on parts",
                    "description": "Standard depreciation applies on plastic/rubber parts. Consider zero depreciation add-on.",
                    "severity": "Medium"
                },
                {
                    "type": "info",
                    "title": "No engine protection",
                    "description": "Engine and gearbox damage from water ingress not covered.",
                    "severity": "Low"
                }
            ]
        }
        gap_analysis = random.sample(
            gaps_by_category.get(category, gaps_by_category["health"]),
            min(2, len(gaps_by_category.get(category, gaps_by_category["health"])))
        )

        # Confidence score (0.85 - 0.98)
        confidence = round(random.uniform(0.85, 0.98), 2)

        return extracted_data, protection_score, gap_analysis, key_features, confidence

    async def get_flow_analysis_status(
        self,
        user_id: int,
        flow_id: str
    ) -> Dict[str, Any]:
        """
        Step 6: Check analysis status

        Args:
            user_id: User's ID
            flow_id: Flow session ID

        Returns:
            Dict with analysis status and results if completed
        """
        try:
            # Try lazy initialization if MongoDB wasn't available at startup
            if self.flow_sessions_collection is None:
                if not self._try_reconnect_mongodb():
                    raise ValueError("MongoDB not available. Please check database connection.")

            # Get flow state
            flow = self.flow_sessions_collection.find_one({
                "flow_id": flow_id,
                "user_id": user_id
            })

            if not flow:
                raise ValueError(f"Flow not found: {flow_id}")

            analysis_id = flow.get("analysis_id")
            if not analysis_id:
                raise ValueError("No analysis found for this flow")

            # Get analysis result
            analysis_result = await self.get_analysis_result(user_id, analysis_id)

            status = analysis_result.get("status", "processing")

            # Update flow if completed
            if status == "completed":
                self.flow_sessions_collection.update_one(
                    {"flow_id": flow_id},
                    {"$set": {
                        "analysis_status": "completed",
                        "current_step": "review_analysis",
                        "updated_at": get_ist_now()
                    }}
                )

            return {
                "flowId": flow_id,
                "analysisId": analysis_id,
                "status": status,
                "extractedData": analysis_result.get("extractedData"),
                "protectionScore": analysis_result.get("protectionScore"),
                "gapAnalysis": analysis_result.get("gapAnalysis", []),
                "keyFeatures": analysis_result.get("keyFeatures", []),
                "confidence": analysis_result.get("confidence"),
                "nextStep": "review_analysis" if status == "completed" else "analyzing"
            }

        except Exception as e:
            logger.error(f"Error getting flow analysis status: {e}")
            raise

    async def review_and_confirm_policy(
        self,
        user_id: int,
        flow_id: str,
        corrections: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Step 7 & 8: Review extracted data and confirm policy addition

        Args:
            user_id: User's ID
            flow_id: Flow session ID
            corrections: Optional corrections to extracted data

        Returns:
            Dict with policy ID and completion status
        """
        try:
            # Try lazy initialization if MongoDB wasn't available at startup
            if self.flow_sessions_collection is None:
                if not self._try_reconnect_mongodb():
                    raise ValueError("MongoDB not available. Please check database connection.")

            # Get flow state
            flow = self.flow_sessions_collection.find_one({
                "flow_id": flow_id,
                "user_id": user_id
            })

            if not flow:
                raise ValueError(f"Flow not found: {flow_id}")

            if flow.get("current_step") not in ["review_analysis", "analyzing"]:
                raise ValueError(f"Invalid step. Current step is: {flow.get('current_step')}")

            analysis_id = flow.get("analysis_id")
            if not analysis_id:
                raise ValueError("No analysis found for this flow")

            # Get analysis result
            analysis_result = await self.get_analysis_result(user_id, analysis_id)

            if analysis_result.get("status") != "completed":
                raise ValueError("Analysis not completed yet. Please wait.")

            # Prepare policy data
            extracted_data = analysis_result.get("extractedData", {})

            # Apply corrections
            if corrections:
                extracted_data.update(corrections)

            # Set category from flow
            if flow.get("category"):
                extracted_data["category"] = flow.get("category")
            if flow.get("sub_type"):
                extracted_data["subType"] = flow.get("sub_type")

            # Add policy to locker
            member_id = flow.get("member_id")
            is_for_self = flow.get("owner_type") == "self"

            result = await self.add_policy(
                user_id=user_id,
                policy_data=extracted_data,
                member_id=member_id,
                is_for_self=is_for_self
            )

            policy_id = result.get("policyId")

            # Update flow state
            self.flow_sessions_collection.update_one(
                {"flow_id": flow_id},
                {"$set": {
                    "policy_id": policy_id,
                    "current_step": "completed",
                    "updated_at": get_ist_now()
                }}
            )

            return {
                "policyId": policy_id,
                "policyNumber": extracted_data.get("policyNumber"),
                "message": "Policy added successfully to your locker!",
                "flowCompleted": True
            }

        except Exception as e:
            logger.error(f"Error confirming policy in flow: {e}")
            raise

    async def get_flow_state(self, user_id: int, flow_id: str) -> Dict[str, Any]:
        """
        Get current state of an Add Policy flow

        Args:
            user_id: User's ID
            flow_id: Flow session ID

        Returns:
            Dict with complete flow state
        """
        try:
            # Try lazy initialization if MongoDB wasn't available at startup
            if self.flow_sessions_collection is None:
                if not self._try_reconnect_mongodb():
                    raise ValueError("MongoDB not available. Please check database connection.")

            flow = self.flow_sessions_collection.find_one({
                "flow_id": flow_id,
                "user_id": user_id
            })

            if not flow:
                raise ValueError(f"Flow not found: {flow_id}")

            flow = self._serialize_doc(flow)

            return {
                "flowId": flow.get("flow_id"),
                "currentStep": flow.get("current_step"),
                "ownerType": flow.get("owner_type"),
                "memberId": flow.get("member_id"),
                "memberName": flow.get("member_name"),
                "relationship": flow.get("relationship"),
                "category": flow.get("category"),
                "subType": flow.get("sub_type"),
                "uploadId": flow.get("upload_id"),
                "analysisId": flow.get("analysis_id"),
                "analysisStatus": flow.get("analysis_status"),
                "policyId": flow.get("policy_id"),
                "nextStep": self._get_next_step(flow),
                "message": self._get_step_message(flow)
            }

        except Exception as e:
            logger.error(f"Error getting flow state: {e}")
            raise

    async def cancel_flow(self, user_id: int, flow_id: str) -> Dict[str, Any]:
        """
        Cancel an in-progress Add Policy flow

        Args:
            user_id: User's ID
            flow_id: Flow session ID

        Returns:
            Dict with cancellation confirmation
        """
        try:
            # Try lazy initialization if MongoDB wasn't available at startup
            if self.flow_sessions_collection is None:
                if not self._try_reconnect_mongodb():
                    raise ValueError("MongoDB not available. Please check database connection.")

            result = self.flow_sessions_collection.delete_one({
                "flow_id": flow_id,
                "user_id": user_id
            })

            if result.deleted_count == 0:
                raise ValueError(f"Flow not found: {flow_id}")

            return {
                "flowId": flow_id,
                "cancelled": True,
                "message": "Flow cancelled successfully"
            }

        except Exception as e:
            logger.error(f"Error cancelling flow: {e}")
            raise

    def _get_next_step(self, flow: Dict) -> str:
        """Determine next step based on current flow state"""
        current_step = flow.get("current_step")
        owner_type = flow.get("owner_type")

        step_mapping = {
            "select_owner": "select_owner",
            "select_relationship": "select_relationship",
            "enter_member_details": "enter_member_details",
            "select_insurance_type": "select_insurance_type",
            "upload_document": "upload_document",
            "analyzing": "review_analysis",
            "review_analysis": "confirm_policy",
            "confirm_policy": "completed",
            "completed": None
        }

        return step_mapping.get(current_step, current_step)

    def _get_step_message(self, flow: Dict) -> str:
        """Get message for current step"""
        current_step = flow.get("current_step")
        owner_type = flow.get("owner_type")

        messages = {
            "select_owner": "Please select who this policy is for.",
            "select_relationship": "Please select the relationship.",
            "enter_member_details": "Please enter member details (name, gender, date of birth).",
            "select_insurance_type": "Please select the insurance category.",
            "upload_document": "Please upload the policy document (PDF).",
            "analyzing": "Analyzing your policy document...",
            "review_analysis": "Please review the extracted policy details.",
            "confirm_policy": "Confirm to add this policy to your locker.",
            "completed": "Policy added successfully!"
        }

        return messages.get(current_step, "Unknown step")

    # ==================== UPLOAD & ANALYSIS APIs ====================

    async def upload_policy_document(
        self,
        user_id: int,
        file_content: bytes,
        filename: str,
        member_id: Optional[str] = None,
        is_for_self: bool = True
    ) -> Dict[str, Any]:
        """Upload policy document for OCR processing"""
        try:
            if self.uploads_collection is None:
                raise ValueError("MongoDB not available")

            upload_id = f"UPL_{user_id}_{secrets.token_hex(6)}"

            # Upload original PDF to S3
            document_url = None
            try:
                from database_storage.s3_bucket import upload_pdf_to_s3
                from io import BytesIO
                import os

                # Create BytesIO buffer from file content
                pdf_buffer = BytesIO(file_content)

                # Generate unique filename for original document
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                s3_filename = f"policy_original_{upload_id}_{timestamp}.pdf"
                bucket_name = os.getenv('AWS_S3_BUCKET_NAME', 'raceabove-dev')

                # Upload to S3
                s3_result = upload_pdf_to_s3(pdf_buffer, s3_filename, bucket_name)

                if s3_result.get("success"):
                    document_url = s3_result.get("s3_url")
                    logger.info(f"Original policy document uploaded to S3: {document_url}")
                else:
                    logger.error(f"Failed to upload original document to S3: {s3_result.get('error')}")

            except Exception as s3_error:
                logger.error(f"Error uploading original document to S3: {str(s3_error)}")
                # Continue without S3 URL - don't fail the upload

            upload_data = {
                "upload_id": upload_id,
                "user_id": user_id,
                "member_id": member_id,
                "is_for_self": is_for_self,
                "filename": filename,
                "file_size": len(file_content),
                "status": "uploaded",
                "document_url": document_url,  # Add S3 URL
                "created_at": get_ist_now()
            }

            self.uploads_collection.insert_one(upload_data)

            return {
                "uploadId": upload_id,
                "status": "uploaded",
                "fileName": filename,
                "fileSize": f"{len(file_content) / 1024:.1f} KB",
                "documentUrl": document_url  # Return S3 URL
            }

        except Exception as e:
            logger.error(f"Error uploading document: {e}")
            raise

    async def analyze_policy_document(
        self,
        user_id: int,
        upload_id: str,
        member_id: Optional[str] = None,
        member_name: Optional[str] = None,
        member_dob: Optional[str] = None,
        member_gender: Optional[str] = None,
        relationship: Optional[str] = None
    ) -> Dict[str, Any]:
        """Trigger AI analysis on uploaded document"""
        try:
            if self.analysis_collection is None:
                raise ValueError("MongoDB not available")

            analysis_id = f"ANL_{user_id}_{secrets.token_hex(6)}"

            analysis_data = {
                "analysis_id": analysis_id,
                "user_id": user_id,
                "upload_id": upload_id,
                "member_id": member_id,
                "member_name": member_name,
                "member_dob": member_dob,
                "member_gender": member_gender,
                "relationship": relationship,
                "status": "processing",
                "created_at": get_ist_now()
            }

            self.analysis_collection.insert_one(analysis_data)

            return {
                "analysisId": analysis_id,
                "status": "processing",
                "estimatedTime": 30  # seconds
            }

        except Exception as e:
            logger.error(f"Error analyzing document: {e}")
            raise

    async def get_analysis_result(self, user_id: int, analysis_id: str) -> Dict[str, Any]:
        """Get AI analysis results from MongoDB"""
        try:
            if self.analysis_collection is None:
                raise ValueError("MongoDB not available")

            analysis = self.analysis_collection.find_one({"user_id": user_id, "analysis_id": analysis_id})

            if not analysis:
                raise ValueError(f"Analysis not found: {analysis_id}")

            analysis = self._serialize_doc(analysis)

            # Return analysis result if completed
            if analysis.get("status") == "completed" and analysis.get("extracted_data"):
                return {
                    "status": "completed",
                    "extractedData": analysis.get("extracted_data"),
                    "protectionScore": analysis.get("protection_score", 75),
                    "gapAnalysis": analysis.get("gap_analysis", []),
                    "keyFeatures": analysis.get("key_features", []),
                    "confidence": analysis.get("confidence", 0.0)
                }

            # Return processing status
            return {
                "status": analysis.get("status", "processing"),
                "extractedData": None,
                "protectionScore": None,
                "gapAnalysis": [],
                "keyFeatures": [],
                "confidence": None
            }

        except Exception as e:
            logger.error(f"Error getting analysis result: {e}")
            raise

    async def update_analysis_result(
        self,
        analysis_id: str,
        extracted_data: Dict[str, Any],
        protection_score: int,
        gap_analysis: List[Dict],
        key_features: List[str],
        confidence: float
    ) -> Dict[str, Any]:
        """Update analysis result after OCR processing"""
        try:
            if self.analysis_collection is None:
                raise ValueError("MongoDB not available")

            self.analysis_collection.update_one(
                {"analysis_id": analysis_id},
                {"$set": {
                    "status": "completed",
                    "extracted_data": extracted_data,
                    "protection_score": protection_score,
                    "gap_analysis": gap_analysis,
                    "key_features": key_features,
                    "confidence": confidence,
                    "completed_at": get_ist_now()
                }}
            )

            return {"analysisId": analysis_id, "status": "completed"}

        except Exception as e:
            logger.error(f"Error updating analysis result: {e}")
            raise

    async def confirm_policy_addition(
        self,
        user_id: int,
        analysis_id: str,
        member_id: Optional[str] = None,
        corrections: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Confirm and save analyzed policy to locker"""
        try:
            # Get analysis result
            analysis_result = await self.get_analysis_result(user_id, analysis_id)

            if analysis_result.get("status") != "completed":
                raise ValueError("Analysis not completed yet")

            extracted_data = analysis_result.get("extractedData", {})

            # Apply corrections
            if corrections:
                extracted_data.update(corrections)

            # Get analysis doc to get member info
            analysis = self.analysis_collection.find_one({"analysis_id": analysis_id})
            is_for_self = analysis.get("member_id") is None if analysis else True

            # Add policy to locker
            result = await self.add_policy(
                user_id=user_id,
                policy_data=extracted_data,
                member_id=member_id or (analysis.get("member_id") if analysis else None),
                is_for_self=is_for_self
            )

            return result

        except Exception as e:
            logger.error(f"Error confirming policy: {e}")
            raise

    # ==================== HELPER METHODS ====================

    def _format_currency(self, amount: int) -> str:
        """Format amount in Indian currency notation"""
        if amount >= 10000000:  # 1 Cr+
            return f"₹{amount / 10000000:.1f}Cr"
        elif amount >= 100000:  # 1L+
            return f"₹{amount / 100000:.1f}L"
        elif amount >= 1000:
            return f"₹{amount / 1000:.1f}K"
        else:
            return f"₹{amount}"

    def _get_category_display_name(self, category: str) -> str:
        """Get display name for category"""
        names = {
            "health": "Health",
            "life": "Life",
            "motor": "Motor",
            "general": "General",
            "agricultural": "Agricultural",
            "business": "Business",
            "specialty": "Specialty",
            "other": "Other"
        }
        return names.get(category, category.title() if category else "Other")

    def _get_avatar_for_relationship(self, relationship: str, gender: Optional[str]) -> str:
        """Get avatar emoji based on relationship and gender"""
        if not relationship:
            return "👤"
        rel_lower = relationship.lower()
        if rel_lower == "spouse":
            return "👩" if gender == "Female" else "👨"
        elif rel_lower in ["son", "brother", "father"]:
            return "👦" if rel_lower == "son" else "👨"
        elif rel_lower in ["daughter", "sister", "mother"]:
            return "👧" if rel_lower == "daughter" else "👩"
        return "👤"

    def _update_policy_status(self, policy: Dict) -> Dict:
        """Update policy status based on expiry date"""
        try:
            expiry_str = policy.get("expiry_date") or policy.get("expiryDate")
            if expiry_str:
                if isinstance(expiry_str, str):
                    expiry_date = datetime.fromisoformat(expiry_str.replace("Z", "+00:00").replace("T", " ").split("+")[0])
                else:
                    expiry_date = expiry_str

                now = get_ist_now()
                days_until_expiry = (expiry_date - now).days

                if days_until_expiry < 0:
                    policy["status"] = "Expired"
                    policy["needs_action"] = True
                    policy["action_message"] = "Policy has expired"
                elif days_until_expiry <= 30:
                    policy["status"] = "Expiring Soon"
                    policy["needs_action"] = True
                    policy["action_message"] = f"Expires in {days_until_expiry} days"
                else:
                    policy["status"] = "Active"
                    policy["needs_action"] = False
        except Exception as e:
            logger.warning(f"Error updating policy status: {e}")

        return policy

    def _format_policy_summary(self, policy: Dict) -> Dict:
        """Format policy for summary response"""
        return {
            "id": policy.get("policy_id"),
            "policyNumber": policy.get("policy_number"),
            "provider": policy.get("provider"),
            "category": policy.get("category"),
            "subType": policy.get("sub_type"),
            "policyHolderName": policy.get("policy_holder_name"),
            "startDate": policy.get("start_date"),
            "expiryDate": policy.get("expiry_date"),
            "premium": policy.get("premium"),
            "premiumType": policy.get("premium_type"),
            "coverageAmount": policy.get("coverage_amount"),
            "idv": policy.get("idv"),
            "status": policy.get("status"),
            "protectionScore": policy.get("protection_score", 0),
            "needsAction": policy.get("needs_action", False),
            "actionMessage": policy.get("action_message"),
            "insuredMembers": policy.get("insured_members", 1),
            "categorySpecificData": policy.get("category_specific_data")
        }

    def _generate_gap_analysis(self, category: str, score: int, category_data: Dict) -> List[Dict[str, Any]]:
        """Generate dynamic gap analysis based on policy data and actual coverage details"""
        gaps = []

        if score < 60:
            gaps.append({
                "type": "warning",
                "title": "Protection score critically low",
                "description": f"Your protection score is {score}/100. Significant coverage gaps need urgent attention.",
                "severity": "High",
                "icon": "🔴"
            })
        elif score < 80:
            gaps.append({
                "type": "warning",
                "title": "Coverage has room for improvement",
                "description": f"Protection score: {score}/100. Some gaps identified that could leave you exposed.",
                "severity": "Medium",
                "icon": "⚠️"
            })

        if category == "health":
            # Sum Insured adequacy check
            sum_insured = category_data.get("sumInsured") or category_data.get("coverageAmount") or 0
            try:
                sum_insured = float(str(sum_insured).replace(',', '').replace('₹', '').replace('Rs.', '').strip()) if sum_insured else 0
            except (ValueError, TypeError):
                sum_insured = 0

            if sum_insured > 0 and sum_insured < 500000:
                gaps.append({
                    "type": "warning",
                    "title": "Critically low sum insured",
                    "description": f"Sum insured of ₹{sum_insured:,.0f} is insufficient for major hospitalization. Recommended: ₹15L+",
                    "severity": "High",
                    "icon": "🔴"
                })
            elif sum_insured > 0 and sum_insured < 1000000:
                gaps.append({
                    "type": "warning",
                    "title": "Sum insured below recommended level",
                    "description": f"₹{sum_insured:,.0f} may not cover critical illness treatment. Consider ₹10L+ per person.",
                    "severity": "Medium",
                    "icon": "⚠️"
                })

            # Room rent limit
            room_rent = category_data.get("roomRentLimit", "")
            if room_rent and str(room_rent).lower() not in ["no limit", "no sub-limit", "none", "nil", ""]:
                gaps.append({
                    "type": "warning",
                    "title": "Room rent sub-limit exists",
                    "description": f"Room rent limit: {room_rent}. This can cause significant out-of-pocket costs during hospitalization.",
                    "severity": "Medium",
                    "icon": "⚠️"
                })

            # Co-payment check
            copay = category_data.get("coPayment") or category_data.get("copayment", "")
            if copay and str(copay) not in ["0%", "0", "", "nil", "none", "no"]:
                gaps.append({
                    "type": "info",
                    "title": "Co-payment applicable",
                    "description": f"Co-payment of {copay} means you pay that percentage of every claim out of pocket.",
                    "severity": "Low",
                    "icon": "ℹ️"
                })

            # Restoration benefit
            if not category_data.get("restoration") and not category_data.get("restoreBenefit"):
                gaps.append({
                    "type": "warning",
                    "title": "No restoration benefit",
                    "description": "If sum insured is exhausted in one claim, no coverage remains for rest of the year.",
                    "severity": "Medium",
                    "icon": "⚠️"
                })

            # Waiting period for pre-existing
            waiting = category_data.get("preExistingWaitingPeriod", "")
            if waiting and str(waiting).lower() not in ["", "0", "none"]:
                gaps.append({
                    "type": "info",
                    "title": f"Pre-existing disease waiting: {waiting}",
                    "description": "Pre-existing conditions won't be covered until waiting period expires.",
                    "severity": "Low",
                    "icon": "ℹ️"
                })

            # Positive: Cashless
            if category_data.get("networkHospitals") or category_data.get("cashlessFacility"):
                network_count = len(category_data.get("networkHospitals", []))
                gaps.append({
                    "type": "positive",
                    "title": "Cashless facility available",
                    "description": f"Access to {network_count}+ network hospitals for cashless treatment" if network_count else "Cashless treatment available at network hospitals",
                    "severity": "Low",
                    "icon": "✅"
                })

        elif category == "motor":
            # Zero depreciation
            if not category_data.get("zeroDepreciation") and not category_data.get("zeroDep"):
                gaps.append({
                    "type": "warning",
                    "title": "No zero depreciation cover",
                    "description": "Claims will have depreciation deduction (15-50% on parts depending on age). You pay the difference.",
                    "severity": "High",
                    "icon": "🔴"
                })

            # Engine protection
            if not category_data.get("engineProtection") and not category_data.get("engineProtect"):
                gaps.append({
                    "type": "warning",
                    "title": "No engine protection",
                    "description": "Engine damage from water ingress/flooding is not covered. Engine repair costs ₹50K-3L+.",
                    "severity": "Medium",
                    "icon": "⚠️"
                })

            # NCB protection
            ncb = category_data.get("ncbPercentage") or category_data.get("ncb", 0)
            try:
                ncb = int(str(ncb).replace('%', ''))
            except (ValueError, TypeError):
                ncb = 0
            if ncb > 0 and not category_data.get("ncbProtection") and not category_data.get("ncbProtect"):
                gaps.append({
                    "type": "warning",
                    "title": f"NCB ({ncb}%) not protected",
                    "description": f"Your {ncb}% No Claim Bonus will reset to 0% on any claim. NCB protection costs ₹500-1500.",
                    "severity": "Medium",
                    "icon": "⚠️"
                })

            # Key replacement
            if not category_data.get("keyReplacement") and not category_data.get("keyReplace"):
                gaps.append({
                    "type": "info",
                    "title": "No key replacement cover",
                    "description": "Key loss/damage not covered. Modern car key replacement costs ₹5K-25K.",
                    "severity": "Low",
                    "icon": "ℹ️"
                })

            # Personal accident cover for owner-driver
            if not category_data.get("paOwnerDriver") and not category_data.get("personalAccident"):
                gaps.append({
                    "type": "warning",
                    "title": "PA cover for owner-driver missing",
                    "description": "Compulsory PA cover of ₹15L for owner-driver. Ensure this is included.",
                    "severity": "High",
                    "icon": "🔴"
                })

            # Consumables cover
            if not category_data.get("consumablesCover") and not category_data.get("consumables"):
                gaps.append({
                    "type": "info",
                    "title": "No consumables cover",
                    "description": "Nuts, bolts, oils, lubricants etc. not covered during claims. Can add ₹2K-5K to claim cost.",
                    "severity": "Low",
                    "icon": "ℹ️"
                })

            # Positive: Roadside assistance
            if category_data.get("roadsideAssistance") or category_data.get("rsa"):
                gaps.append({
                    "type": "positive",
                    "title": "Roadside assistance included",
                    "description": "24/7 roadside assistance available for breakdowns and emergencies",
                    "severity": "Low",
                    "icon": "✅"
                })

            # IDV check
            idv = category_data.get("idv") or category_data.get("insuredDeclaredValue", 0)
            try:
                idv = float(str(idv).replace(',', '').replace('₹', '').strip()) if idv else 0
            except (ValueError, TypeError):
                idv = 0
            if idv > 0 and idv < 100000:
                gaps.append({
                    "type": "warning",
                    "title": "Very low IDV",
                    "description": f"IDV of ₹{idv:,.0f} seems low. In total loss, you only get this amount.",
                    "severity": "Medium",
                    "icon": "⚠️"
                })

        elif category == "life":
            # Sum assured adequacy
            sum_assured = category_data.get("sumAssured") or category_data.get("coverageAmount") or 0
            try:
                sum_assured = float(str(sum_assured).replace(',', '').replace('₹', '').replace('Rs.', '').strip()) if sum_assured else 0
            except (ValueError, TypeError):
                sum_assured = 0

            if sum_assured > 0 and sum_assured < 5000000:
                gaps.append({
                    "type": "warning",
                    "title": "Sum assured critically low",
                    "description": f"₹{sum_assured:,.0f} is insufficient. Recommended: 10-15x annual income (min ₹1 Cr).",
                    "severity": "High",
                    "icon": "🔴"
                })
            elif sum_assured > 0 and sum_assured < 10000000:
                gaps.append({
                    "type": "warning",
                    "title": "Sum assured below recommended level",
                    "description": f"₹{sum_assured:,.0f} may not cover family's long-term needs. Consider ₹1 Cr+.",
                    "severity": "Medium",
                    "icon": "⚠️"
                })

            # Riders check
            riders = category_data.get("riders", [])
            if riders and len(riders) > 0:
                gaps.append({
                    "type": "positive",
                    "title": "Additional riders included",
                    "description": f"{len(riders)} riders for extra protection: {', '.join(riders[:3])}",
                    "severity": "Low",
                    "icon": "✅"
                })
            else:
                gaps.append({
                    "type": "warning",
                    "title": "No additional riders",
                    "description": "No critical illness, accidental death, or waiver of premium riders. These provide crucial added protection.",
                    "severity": "Medium",
                    "icon": "⚠️"
                })

            # Policy term check
            policy_term = category_data.get("policyTerm") or category_data.get("coverTill", 0)
            try:
                policy_term = int(str(policy_term).replace(' years', '').replace('yrs', '').strip()) if policy_term else 0
            except (ValueError, TypeError):
                policy_term = 0
            if policy_term > 0 and policy_term < 15:
                gaps.append({
                    "type": "warning",
                    "title": "Short policy term",
                    "description": f"Policy term of {policy_term} years may leave you uncovered during peak earning/liability years.",
                    "severity": "Medium",
                    "icon": "⚠️"
                })

            # Nominee check
            if not category_data.get("nominee") and not category_data.get("nomineeName"):
                gaps.append({
                    "type": "info",
                    "title": "Nominee details not found",
                    "description": "Ensure nominee is properly assigned for smooth claim settlement.",
                    "severity": "Low",
                    "icon": "ℹ️"
                })

        return gaps

    def _get_recommendations(self, category: str, category_data: Dict) -> List[str]:
        """Get recommendations based on category and policy data"""
        recs = []

        if category == "health":
            if not category_data.get("restoration"):
                recs.append("Consider adding restoration benefit for additional coverage")
            recs.append("Review room rent limits periodically")
            recs.append("Check pre-existing disease coverage after waiting period")

        elif category == "life":
            recs.append("Review sum assured every 3-5 years based on income growth")
            recs.append("Update nominee details if family situation changes")
            if not category_data.get("riders"):
                recs.append("Consider adding critical illness or accidental death riders")

        elif category == "motor":
            if not category_data.get("zeroDepreciation") and not category_data.get("zeroDep"):
                recs.append("Add zero depreciation cover - get full claim without depreciation deduction")
            if not category_data.get("engineProtection") and not category_data.get("engineProtect"):
                recs.append("Consider engine protection add-on for water/flood damage")
            if not category_data.get("ncbProtection") and not category_data.get("ncbProtect"):
                recs.append("Add NCB protection to preserve your no-claim bonus discount")
            if not category_data.get("consumablesCover") and not category_data.get("consumables"):
                recs.append("Consider consumables cover for nuts, bolts, oil costs during claims")
            recs.append("Maintain no-claim bonus by avoiding small claims")

        else:
            recs.append("Review your policy annually for adequate coverage")

        return recs

    def _get_detailed_recommendations(self, category: str, category_data: Dict) -> List[Dict]:
        """Get detailed recommendations for policy enhancement"""
        recommendations = []

        if category == "health":
            if not category_data.get("restoration"):
                recommendations.append({
                    "id": "REC_HEALTH_001",
                    "title": "Add Restoration Benefit",
                    "description": "Get 100% sum insured restored after a claim",
                    "type": "addon",
                    "priority": "High",
                    "estimatedCost": "₹1,500-3,000/year"
                })
            recommendations.append({
                "id": "REC_HEALTH_002",
                "title": "Consider Super Top-Up",
                "description": "Extend coverage with a cost-effective super top-up plan",
                "type": "new_policy",
                "priority": "Medium",
                "estimatedCost": "₹3,000-5,000/year"
            })

        elif category == "life":
            recommendations.append({
                "id": "REC_LIFE_001",
                "title": "Review Sum Assured",
                "description": "Ensure coverage is 10-15x your annual income",
                "type": "upgrade",
                "priority": "Medium",
                "estimatedCost": "Varies"
            })

        elif category == "motor":
            if not category_data.get("zeroDepreciation") and not category_data.get("zeroDep"):
                recommendations.append({
                    "id": "REC_MOTOR_001",
                    "title": "Add Zero Depreciation",
                    "description": "Get full claim amount without depreciation deduction on parts",
                    "type": "addon",
                    "priority": "High",
                    "estimatedCost": "₹1,000-2,500/year"
                })
            if not category_data.get("engineProtection") and not category_data.get("engineProtect"):
                recommendations.append({
                    "id": "REC_MOTOR_002",
                    "title": "Add Engine Protection",
                    "description": "Cover engine damage from water ingress/flooding. Engine repairs cost ₹50K-3L+",
                    "type": "addon",
                    "priority": "Medium",
                    "estimatedCost": "₹800-1,500/year"
                })
            if not category_data.get("ncbProtection") and not category_data.get("ncbProtect"):
                recommendations.append({
                    "id": "REC_MOTOR_003",
                    "title": "Add NCB Protection",
                    "description": "Protect your No Claim Bonus discount even after a claim",
                    "type": "addon",
                    "priority": "Medium",
                    "estimatedCost": "₹500-1,500/year"
                })
            if not category_data.get("consumablesCover") and not category_data.get("consumables"):
                recommendations.append({
                    "id": "REC_MOTOR_004",
                    "title": "Add Consumables Cover",
                    "description": "Cover nuts, bolts, oils, lubricants etc. during claim repairs",
                    "type": "addon",
                    "priority": "Low",
                    "estimatedCost": "₹300-800/year"
                })

        return recommendations

    def _generate_insights(self, policy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate insights for analysis report"""
        insights = []
        score = policy.get("protectionScore", 75)

        if score >= 85:
            insights.append({
                "type": "positive",
                "title": "Excellent Protection",
                "description": "Your policy provides comprehensive coverage"
            })
        elif score >= 70:
            insights.append({
                "type": "info",
                "title": "Good Protection",
                "description": "Your policy covers most essential needs"
            })
        else:
            insights.append({
                "type": "warning",
                "title": "Room for Improvement",
                "description": "Consider enhancing your coverage for better protection"
            })

        insights.append({
            "type": "info",
            "title": "Policy Status",
            "description": f"Your policy is {policy.get('status', 'Active')}"
        })

        return insights

    def _generate_report_recommendations(self, policy: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations for analysis report"""
        return [
            {
                "action": "Review coverage annually",
                "priority": "Medium",
                "potential_benefit": "Ensure adequate protection as needs change"
            },
            {
                "action": "Compare with market rates",
                "priority": "Low",
                "potential_benefit": "Potential premium savings of 10-20%"
            }
        ]


# Create singleton instance
policy_locker_service = PolicyLockerService()
