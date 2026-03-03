"""
Notification Scheduler Service
Automatically triggers notifications based on backend events like:
- Policy renewal reminders
- Policy expiry alerts
- Claim status updates
- Payment reminders
- Protection score changes
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List

from services.notification_service import notification_service
from models.notification import NotificationType, NotificationPriority
from database_storage.mongodb_chat_manager import insurance_db

logger = logging.getLogger(__name__)


def get_ist_now():
    """Get current time in IST"""
    ist_timezone = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist_timezone).replace(tzinfo=None)


class NotificationScheduler:
    """
    Backend notification scheduler that triggers notifications based on events.
    All notification data is fetched from the database - no frontend input needed.
    """

    def __init__(self):
        self.policies_collection = insurance_db["policy_analyses"]
        self.users_collection = insurance_db["users"]

    # ========================================
    # Policy Renewal Notifications
    # ========================================

    async def send_policy_renewal_reminder(
        self,
        user_id: str,
        policy_id: str,
        days_until_expiry: int
    ) -> bool:
        """
        Send policy renewal reminder.
        Called by backend when policy is nearing expiry.
        """
        try:
            # Fetch policy details from database
            policy = self.policies_collection.find_one({
                "_id": policy_id,
                "user_id": user_id
            })

            if not policy:
                logger.warning(f"Policy {policy_id} not found for user {user_id}")
                return False

            policy_details = policy.get("policy_details", {})
            policy_type = policy_details.get("policy_type", "Insurance")
            policy_number = policy_details.get("policy_number", "N/A")
            provider = policy_details.get("insurance_provider", "Your Insurance")
            end_date = policy_details.get("end_date", "")

            # Build notification content from database data
            title = f"{policy_type} Renewal Reminder"
            body = f"Your {provider} policy ({policy_number}) expires in {days_until_expiry} days. Renew now to maintain coverage."

            data = {
                "policy_id": str(policy_id),
                "policy_number": policy_number,
                "policy_type": policy_type,
                "expiry_date": end_date,
                "days_until_expiry": str(days_until_expiry),
                "action": "renew_policy",
                "deep_link": f"eazr://policies/{policy_id}"
            }

            # Determine priority based on urgency
            if days_until_expiry <= 3:
                priority = NotificationPriority.HIGH
            elif days_until_expiry <= 7:
                priority = NotificationPriority.NORMAL
            else:
                priority = NotificationPriority.LOW

            success, message, _, _ = await notification_service.send_notification_to_user(
                user_id=user_id,
                title=title,
                body=body,
                notification_type=NotificationType.POLICY_RENEWAL,
                priority=priority,
                data=data
            )

            logger.info(f"Policy renewal notification sent: {success} - {message}")
            return success

        except Exception as e:
            logger.error(f"Error sending policy renewal notification: {e}")
            return False

    async def send_policy_expiry_alert(
        self,
        user_id: str,
        policy_id: str
    ) -> bool:
        """
        Send policy expiry alert when policy has expired.
        """
        try:
            policy = self.policies_collection.find_one({
                "_id": policy_id,
                "user_id": user_id
            })

            if not policy:
                return False

            policy_details = policy.get("policy_details", {})
            policy_type = policy_details.get("policy_type", "Insurance")
            policy_number = policy_details.get("policy_number", "N/A")
            provider = policy_details.get("insurance_provider", "Your Insurance")

            title = f"{policy_type} Policy Expired"
            body = f"Your {provider} policy ({policy_number}) has expired. You are currently unprotected."

            data = {
                "policy_id": str(policy_id),
                "policy_number": policy_number,
                "action": "view_expired_policy",
                "deep_link": f"eazr://policies/{policy_id}"
            }

            success, _, _, _ = await notification_service.send_notification_to_user(
                user_id=user_id,
                title=title,
                body=body,
                notification_type=NotificationType.POLICY_EXPIRY,
                priority=NotificationPriority.HIGH,
                data=data
            )

            return success

        except Exception as e:
            logger.error(f"Error sending policy expiry alert: {e}")
            return False

    # ========================================
    # Claim Notifications
    # ========================================

    async def send_claim_status_update(
        self,
        user_id: str,
        claim_id: str,
        status: str,
        amount: Optional[float] = None,
        remarks: Optional[str] = None
    ) -> bool:
        """
        Send claim status update notification.
        Called when claim status changes in the system.
        """
        try:
            status_messages = {
                "submitted": ("Claim Submitted", "Your claim has been submitted successfully and is under review."),
                "under_review": ("Claim Under Review", "Your claim is being reviewed by the insurance company."),
                "documents_required": ("Documents Required", "Additional documents are needed for your claim. Please upload them."),
                "approved": ("Claim Approved!", f"Great news! Your claim for Rs. {amount:,.0f} has been approved." if amount else "Your claim has been approved!"),
                "rejected": ("Claim Rejected", f"Unfortunately, your claim was rejected. Reason: {remarks}" if remarks else "Your claim was rejected."),
                "settled": ("Claim Settled", f"Your claim of Rs. {amount:,.0f} has been settled and payment is on the way." if amount else "Your claim has been settled."),
            }

            title, body = status_messages.get(status.lower(), ("Claim Update", f"Your claim status has been updated to: {status}"))

            data = {
                "claim_id": claim_id,
                "status": status,
                "action": "view_claim",
                "deep_link": f"eazr://claims/{claim_id}"
            }

            if amount:
                data["amount"] = str(amount)

            priority = NotificationPriority.HIGH if status.lower() in ["approved", "rejected", "settled"] else NotificationPriority.NORMAL

            success, _, _, _ = await notification_service.send_notification_to_user(
                user_id=user_id,
                title=title,
                body=body,
                notification_type=NotificationType.CLAIM_UPDATE,
                priority=priority,
                data=data
            )

            return success

        except Exception as e:
            logger.error(f"Error sending claim status notification: {e}")
            return False

    # ========================================
    # Payment Notifications
    # ========================================

    async def send_payment_reminder(
        self,
        user_id: str,
        policy_id: str,
        due_date: str,
        amount: float
    ) -> bool:
        """
        Send premium payment reminder.
        """
        try:
            policy = self.policies_collection.find_one({
                "_id": policy_id,
                "user_id": user_id
            })

            if not policy:
                return False

            policy_details = policy.get("policy_details", {})
            policy_type = policy_details.get("policy_type", "Insurance")
            provider = policy_details.get("insurance_provider", "")

            title = "Premium Payment Due"
            body = f"Your {provider} {policy_type} premium of Rs. {amount:,.0f} is due on {due_date}."

            data = {
                "policy_id": str(policy_id),
                "amount": str(amount),
                "due_date": due_date,
                "action": "pay_premium",
                "deep_link": f"eazr://payments/{policy_id}"
            }

            success, _, _, _ = await notification_service.send_notification_to_user(
                user_id=user_id,
                title=title,
                body=body,
                notification_type=NotificationType.PAYMENT_REMINDER,
                priority=NotificationPriority.HIGH,
                data=data
            )

            return success

        except Exception as e:
            logger.error(f"Error sending payment reminder: {e}")
            return False

    # ========================================
    # Protection Score Notifications
    # ========================================

    async def send_protection_score_update(
        self,
        user_id: str,
        new_score: int,
        old_score: int,
        reason: str
    ) -> bool:
        """
        Send protection score change notification.
        """
        try:
            score_change = new_score - old_score

            if score_change > 0:
                title = "Protection Score Improved!"
                body = f"Your protection score increased from {old_score} to {new_score}. {reason}"
                emoji = "up"
            elif score_change < 0:
                title = "Protection Score Alert"
                body = f"Your protection score dropped from {old_score} to {new_score}. {reason}"
                emoji = "down"
            else:
                return False  # No change, no notification

            data = {
                "new_score": str(new_score),
                "old_score": str(old_score),
                "change": str(score_change),
                "direction": emoji,
                "action": "view_score",
                "deep_link": "eazr://dashboard/protection-score"
            }

            success, _, _, _ = await notification_service.send_notification_to_user(
                user_id=user_id,
                title=title,
                body=body,
                notification_type=NotificationType.PROTECTION_SCORE,
                priority=NotificationPriority.NORMAL,
                data=data
            )

            return success

        except Exception as e:
            logger.error(f"Error sending protection score notification: {e}")
            return False

    # ========================================
    # Policy Upload Success
    # ========================================

    async def send_policy_upload_success(
        self,
        user_id: str,
        policy_id: str,
        policy_type: str,
        provider: str,
        protection_score: int
    ) -> bool:
        """
        Send notification when policy upload and analysis is complete.
        """
        try:
            title = "Policy Analyzed Successfully!"
            body = f"Your {provider} {policy_type} policy has been analyzed. Protection Score: {protection_score}/100"

            data = {
                "policy_id": str(policy_id),
                "policy_type": policy_type,
                "provider": provider,
                "protection_score": str(protection_score),
                "action": "view_analysis",
                "deep_link": f"eazr://policies/{policy_id}/analysis"
            }

            success, _, _, _ = await notification_service.send_notification_to_user(
                user_id=user_id,
                title=title,
                body=body,
                notification_type=NotificationType.SYSTEM,
                priority=NotificationPriority.NORMAL,
                data=data
            )

            return success

        except Exception as e:
            logger.error(f"Error sending policy upload notification: {e}")
            return False

    # ========================================
    # Recommendation Notifications
    # ========================================

    async def send_coverage_recommendation(
        self,
        user_id: str,
        gap_type: str,
        recommendation: str
    ) -> bool:
        """
        Send coverage gap/recommendation notification.
        """
        try:
            gap_titles = {
                "health": "Health Coverage Gap Detected",
                "life": "Life Insurance Recommendation",
                "motor": "Motor Insurance Suggestion",
                "term": "Term Life Coverage Gap",
                "critical_illness": "Critical Illness Coverage Needed"
            }

            title = gap_titles.get(gap_type.lower(), "Coverage Recommendation")
            body = recommendation[:150]  # Truncate to 150 chars

            data = {
                "gap_type": gap_type,
                "action": "view_recommendations",
                "deep_link": "eazr://recommendations"
            }

            success, _, _, _ = await notification_service.send_notification_to_user(
                user_id=user_id,
                title=title,
                body=body,
                notification_type=NotificationType.NEW_RECOMMENDATION,
                priority=NotificationPriority.LOW,
                data=data
            )

            return success

        except Exception as e:
            logger.error(f"Error sending recommendation notification: {e}")
            return False

    # ========================================
    # Batch Processing for Scheduled Jobs
    # ========================================

    async def process_renewal_reminders(self, days_before: int = 7) -> Dict[str, int]:
        """
        Process all policies expiring within specified days.
        Call this from a scheduled job (cron/celery).
        """
        try:
            now = get_ist_now()
            target_date = now + timedelta(days=days_before)

            # Find policies expiring within the range
            expiring_policies = self.policies_collection.find({
                "policy_details.end_date": {
                    "$gte": now.strftime("%Y-%m-%d"),
                    "$lte": target_date.strftime("%Y-%m-%d")
                },
                "policy_details.status": "active"
            })

            sent_count = 0
            failed_count = 0

            for policy in expiring_policies:
                user_id = policy.get("user_id")
                policy_id = str(policy.get("_id"))
                end_date_str = policy.get("policy_details", {}).get("end_date", "")

                if end_date_str and user_id:
                    try:
                        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
                        days_until = (end_date - now).days

                        success = await self.send_policy_renewal_reminder(
                            user_id=user_id,
                            policy_id=policy_id,
                            days_until_expiry=days_until
                        )

                        if success:
                            sent_count += 1
                        else:
                            failed_count += 1
                    except Exception as e:
                        logger.error(f"Error processing policy {policy_id}: {e}")
                        failed_count += 1

            return {"sent": sent_count, "failed": failed_count}

        except Exception as e:
            logger.error(f"Error processing renewal reminders: {e}")
            return {"sent": 0, "failed": 0, "error": str(e)}

    async def process_expired_policies(self) -> Dict[str, int]:
        """
        Process all newly expired policies.
        Call this from a scheduled job.
        """
        try:
            today = get_ist_now().strftime("%Y-%m-%d")

            # Find policies that expired today
            expired_policies = self.policies_collection.find({
                "policy_details.end_date": today,
                "policy_details.status": {"$ne": "expired"}
            })

            sent_count = 0
            failed_count = 0

            for policy in expired_policies:
                user_id = policy.get("user_id")
                policy_id = str(policy.get("_id"))

                if user_id:
                    success = await self.send_policy_expiry_alert(
                        user_id=user_id,
                        policy_id=policy_id
                    )

                    if success:
                        sent_count += 1
                        # Update policy status
                        self.policies_collection.update_one(
                            {"_id": policy.get("_id")},
                            {"$set": {"policy_details.status": "expired"}}
                        )
                    else:
                        failed_count += 1

            return {"sent": sent_count, "failed": failed_count}

        except Exception as e:
            logger.error(f"Error processing expired policies: {e}")
            return {"sent": 0, "failed": 0, "error": str(e)}


# Singleton instance
notification_scheduler = NotificationScheduler()


# ========================================
# Helper Functions for Direct Backend Calls
# ========================================

async def notify_policy_renewal(user_id: str, policy_id: str, days_until_expiry: int) -> bool:
    """Helper function to send policy renewal notification"""
    return await notification_scheduler.send_policy_renewal_reminder(user_id, policy_id, days_until_expiry)


async def notify_claim_update(user_id: str, claim_id: str, status: str, amount: float = None) -> bool:
    """Helper function to send claim update notification"""
    return await notification_scheduler.send_claim_status_update(user_id, claim_id, status, amount)


async def notify_payment_due(user_id: str, policy_id: str, due_date: str, amount: float) -> bool:
    """Helper function to send payment reminder"""
    return await notification_scheduler.send_payment_reminder(user_id, policy_id, due_date, amount)


async def notify_policy_analyzed(user_id: str, policy_id: str, policy_type: str, provider: str, score: int) -> bool:
    """Helper function to send policy analysis complete notification"""
    return await notification_scheduler.send_policy_upload_success(user_id, policy_id, policy_type, provider, score)


async def notify_score_change(user_id: str, new_score: int, old_score: int, reason: str) -> bool:
    """Helper function to send protection score change notification"""
    return await notification_scheduler.send_protection_score_update(user_id, new_score, old_score, reason)
