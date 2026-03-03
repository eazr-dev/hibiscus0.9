"""
Notification Cron Service
=========================
Automated notification scheduler that runs at specific times daily.

NOTIFICATION SCHEDULE (IST - Indian Standard Time):
===================================================

| Time (IST)  | Notification Type           | Description                                    |
|-------------|-----------------------------|-------------------------------------------------|
| 09:00 AM    | Policy Expiry (30 days)     | Early reminder for policies expiring in 30 days |
| 09:00 AM    | Policy Expiry (15 days)     | Reminder for policies expiring in 15 days       |
| 10:00 AM    | Policy Expiry (7 days)      | Urgent reminder - 1 week left                   |
| 10:00 AM    | Policy Expiry (3 days)      | Critical reminder - 3 days left                 |
| 10:00 AM    | Policy Expiry (1 day)       | Final reminder - expires tomorrow               |
| 10:00 AM    | Policy Expired Today        | Alert for policies that expired today           |
| 11:00 AM    | Low Protection Score        | Alert users with score < 40                     |
| 06:00 PM    | Welcome Notification        | For new users registered today                  |
| 06:00 PM    | Policy Upload Success       | Confirmation after policy analysis              |

NOTIFICATION TYPES:
==================
1. policy_renewal   - Policy expiring soon (30, 15, 7, 3, 1 days)
2. policy_expiry    - Policy has expired
3. protection_score - Low protection score alert
4. system           - Welcome messages, policy upload success
5. new_recommendation - Coverage gap recommendations

HOW TO RUN:
===========
Option 1: Cron Job (Recommended for Production)
   Add to crontab: crontab -e

   # Morning notifications (9 AM IST = 3:30 AM UTC)
   30 3 * * * cd /home/ubuntu/chatbot/botproject && /home/ubuntu/chatbot/botenv/bin/python -c "import asyncio; from services.notification_cron import run_morning_notifications; asyncio.run(run_morning_notifications())"

   # Mid-morning notifications (10 AM IST = 4:30 AM UTC)
   30 4 * * * cd /home/ubuntu/chatbot/botproject && /home/ubuntu/chatbot/botenv/bin/python -c "import asyncio; from services.notification_cron import run_urgent_notifications; asyncio.run(run_urgent_notifications())"

   # Midday notifications (11 AM IST = 5:30 AM UTC)
   30 5 * * * cd /home/ubuntu/chatbot/botproject && /home/ubuntu/chatbot/botenv/bin/python -c "import asyncio; from services.notification_cron import run_score_notifications; asyncio.run(run_score_notifications())"

   # Evening notifications (6 PM IST = 12:30 PM UTC)
   30 12 * * * cd /home/ubuntu/chatbot/botproject && /home/ubuntu/chatbot/botenv/bin/python -c "import asyncio; from services.notification_cron import run_evening_notifications; asyncio.run(run_evening_notifications())"

Option 2: APScheduler (In-app scheduling)
   Integrated into the FastAPI app startup

Option 3: Manual Trigger via Admin API
   POST /admin/notifications/trigger-all
   POST /admin/notifications/trigger/{notification_type}
"""

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from bson import ObjectId
from pymongo import MongoClient

from services.notification_service import notification_service
from models.notification import NotificationType, NotificationPriority
from database_storage.mongodb_chat_manager import insurance_db

logger = logging.getLogger(__name__)

# Connect to eazr_chatbot database for policy_analysis collection
# This is separate from insurance_analysis_db used by the main app
MONGODB_URI = os.getenv("MONGODB_URI_PRODUCTION") or os.getenv("MONGODB_URI_LOCAL", "mongodb://localhost:27017/")
_mongo_client = MongoClient(MONGODB_URI)
eazr_chatbot_db = _mongo_client["eazr_chatbot"]


def get_ist_now():
    """Get current time in IST (Indian Standard Time - UTC+5:30)"""
    ist_timezone = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist_timezone).replace(tzinfo=None)


class NotificationCronService:
    """
    Comprehensive notification cron service for automated policy notifications.

    Uses the 'policy_analysis' collection from eazr_chatbot database which has:
    Document structure:
    {
        "user_id": 291,  (integer at root level)
        "extractedData": {
            "endDate": "2026-02-16",
            "startDate": "2025-02-17",
            "policyNumber": "2805207167032100000",
            "policyType": "health",
            "insuranceProvider": "HDFC ERGO General Insurance",
            "policyHolderName": "Mr. Vijay Patil",
            "insuredName": "Mr. Vijay Patil"
        }
    }
    """

    def __init__(self):
        self.db = insurance_db
        # Use policy_analysis collection from eazr_chatbot database
        self.policies_collection = eazr_chatbot_db["policy_analysis"]
        self.users_collection = self.db["user_profiles"]
        self.notification_logs = self.db["notification_logs"]
        self.sent_notifications_tracker = self.db["notification_sent_tracker"]

    # ========================================
    # Helper: Check if notification already sent today
    # ========================================

    def _was_notification_sent_today(
        self,
        user_id: str,
        notification_type: str,
        reference_id: str = None
    ) -> bool:
        """Check if this notification was already sent today to avoid duplicates."""
        today = get_ist_now().strftime("%Y-%m-%d")

        query = {
            "user_id": user_id,
            "notification_type": notification_type,
            "sent_date": today
        }
        if reference_id:
            query["reference_id"] = reference_id

        return self.sent_notifications_tracker.find_one(query) is not None

    def _mark_notification_sent(
        self,
        user_id: str,
        notification_type: str,
        reference_id: str = None
    ):
        """Mark notification as sent for today."""
        today = get_ist_now().strftime("%Y-%m-%d")

        doc = {
            "user_id": user_id,
            "notification_type": notification_type,
            "sent_date": today,
            "sent_at": get_ist_now()
        }
        if reference_id:
            doc["reference_id"] = reference_id

        self.sent_notifications_tracker.update_one(
            {
                "user_id": user_id,
                "notification_type": notification_type,
                "sent_date": today,
                "reference_id": reference_id
            },
            {"$set": doc},
            upsert=True
        )

    # ========================================
    # Policy Expiry Notifications
    # ========================================

    async def send_policy_expiry_reminders(self, days_before: int) -> Dict[str, int]:
        """
        Send policy expiry reminders for policies expiring in X days.

        Args:
            days_before: Number of days before expiry (30, 15, 7, 3, 1)

        Uses policy_analysis collection from eazr_chatbot database.
        Data is stored in extractedData subdocument:
        - extractedData.endDate: "YYYY-MM-DD" format
        - user_id: User ID (integer at root level)
        - extractedData.policyType: health, auto, life, etc.
        - extractedData.policyNumber: Policy number
        - extractedData.insuranceProvider: Insurance company name
        - extractedData.policyHolderName: Policy holder name
        """
        try:
            now = get_ist_now()
            target_date = (now + timedelta(days=days_before)).strftime("%Y-%m-%d")

            logger.info(f"Processing policy expiry reminders for {days_before} days (target: {target_date})")

            # Find policies expiring on the target date
            # Data is in extractedData.endDate
            expiring_policies = list(self.policies_collection.find({
                "extractedData.endDate": target_date
            }))

            sent_count = 0
            skipped_count = 0
            failed_count = 0

            for policy in expiring_policies:
                # Get user_id from root level (stored as integer)
                user_id = str(policy.get("user_id") or policy.get("userId") or "")
                policy_id = str(policy.get("_id", ""))

                if not user_id:
                    logger.warning(f"Policy {policy_id} has no user_id, skipping")
                    continue

                # Check if already sent today
                tracker_key = f"expiry_{days_before}d_{policy_id}"
                if self._was_notification_sent_today(user_id, "policy_renewal", tracker_key):
                    skipped_count += 1
                    continue

                # Get policy details from extractedData subdocument
                extracted = policy.get("extractedData", {})
                policy_type = (
                    extracted.get("policyType") or
                    policy.get("policyType") or
                    "Insurance"
                )
                policy_number = (
                    extracted.get("policyNumber") or
                    policy.get("policyNumber") or
                    "N/A"
                )
                provider = (
                    extracted.get("insuranceProvider") or
                    policy.get("insuranceProvider") or
                    "Your Insurance"
                )
                policy_holder = extracted.get("policyHolderName") or extracted.get("insuredName") or ""

                # Build notification
                if days_before == 1:
                    title = f"⚠️ {policy_type} Expires Tomorrow!"
                    body = f"Your {provider} policy ({policy_number}) expires tomorrow. Renew now to avoid coverage gap."
                    priority = NotificationPriority.HIGH
                elif days_before <= 3:
                    title = f"🔔 {policy_type} Expiring in {days_before} Days"
                    body = f"Your {provider} policy ({policy_number}) expires in {days_before} days. Renew soon!"
                    priority = NotificationPriority.HIGH
                elif days_before <= 7:
                    title = f"📅 {policy_type} Renewal Reminder"
                    body = f"Your {provider} policy ({policy_number}) expires in {days_before} days."
                    priority = NotificationPriority.NORMAL
                else:
                    title = f"📋 {policy_type} Expiring Soon"
                    body = f"Your {provider} policy ({policy_number}) will expire in {days_before} days. Plan your renewal."
                    priority = NotificationPriority.LOW

                data = {
                    "policy_id": policy_id,
                    "policy_number": policy_number,
                    "policy_type": policy_type,
                    "policy_holder": policy_holder,
                    "provider": provider,
                    "days_until_expiry": str(days_before),
                    "expiry_date": target_date,
                    "action": "renew_policy",
                    "deep_link": f"eazr://policies/{policy_id}"
                }

                try:
                    success, message, _, _ = await notification_service.send_notification_to_user(
                        user_id=user_id,
                        title=title,
                        body=body,
                        notification_type=NotificationType.POLICY_RENEWAL,
                        priority=priority,
                        data=data
                    )

                    if success:
                        sent_count += 1
                        self._mark_notification_sent(user_id, "policy_renewal", tracker_key)
                        logger.info(f"Sent {days_before}-day expiry reminder to user {user_id} for policy {policy_id}")
                    else:
                        failed_count += 1
                        logger.warning(f"Failed to send notification: {message}")

                except Exception as e:
                    failed_count += 1
                    logger.error(f"Error sending notification to user {user_id}: {e}")

            result = {
                "days_before": days_before,
                "total_policies": len(expiring_policies),
                "sent": sent_count,
                "skipped": skipped_count,
                "failed": failed_count
            }
            logger.info(f"Policy expiry reminders ({days_before} days) completed: {result}")
            return result

        except Exception as e:
            logger.error(f"Error in send_policy_expiry_reminders: {e}")
            return {"error": str(e), "sent": 0, "failed": 0}

    async def send_expired_policy_alerts(self) -> Dict[str, int]:
        """
        Send alerts for policies that expired today.

        Uses policy_analysis collection from eazr_chatbot database.
        Data is in extractedData.endDate field.
        """
        try:
            today = get_ist_now().strftime("%Y-%m-%d")

            logger.info(f"Processing expired policy alerts for {today}")

            # Find policies that expired today using extractedData.endDate
            expired_policies = list(self.policies_collection.find({
                "extractedData.endDate": today
            }))

            sent_count = 0
            skipped_count = 0
            failed_count = 0

            for policy in expired_policies:
                # Get user_id from root level (stored as integer)
                user_id = str(policy.get("user_id") or policy.get("userId") or "")
                policy_id = str(policy.get("_id", ""))

                if not user_id:
                    logger.warning(f"Expired policy {policy_id} has no user_id, skipping")
                    continue

                # Check if already sent today
                tracker_key = f"expired_{policy_id}"
                if self._was_notification_sent_today(user_id, "policy_expiry", tracker_key):
                    skipped_count += 1
                    continue

                # Get policy details from extractedData subdocument
                extracted = policy.get("extractedData", {})
                policy_type = (
                    extracted.get("policyType") or
                    policy.get("policyType") or
                    "Insurance"
                )
                policy_number = (
                    extracted.get("policyNumber") or
                    policy.get("policyNumber") or
                    "N/A"
                )
                provider = (
                    extracted.get("insuranceProvider") or
                    policy.get("insuranceProvider") or
                    "Your Insurance"
                )

                title = f"❌ {policy_type} Policy Expired"
                body = f"Your {provider} policy ({policy_number}) has expired today. You are currently unprotected. Renew immediately!"

                data = {
                    "policy_id": policy_id,
                    "policy_number": policy_number,
                    "policy_type": policy_type,
                    "action": "renew_policy",
                    "deep_link": f"eazr://policies/{policy_id}"
                }

                try:
                    success, _, _, _ = await notification_service.send_notification_to_user(
                        user_id=user_id,
                        title=title,
                        body=body,
                        notification_type=NotificationType.POLICY_EXPIRY,
                        priority=NotificationPriority.HIGH,
                        data=data
                    )

                    if success:
                        sent_count += 1
                        self._mark_notification_sent(user_id, "policy_expiry", tracker_key)
                        # Update policy status
                        self.policies_collection.update_one(
                            {"_id": policy.get("_id")},
                            {"$set": {"policy_details.status": "expired"}}
                        )
                    else:
                        failed_count += 1

                except Exception as e:
                    failed_count += 1
                    logger.error(f"Error sending expired alert: {e}")

            result = {
                "total_expired": len(expired_policies),
                "sent": sent_count,
                "skipped": skipped_count,
                "failed": failed_count
            }
            logger.info(f"Expired policy alerts completed: {result}")
            return result

        except Exception as e:
            logger.error(f"Error in send_expired_policy_alerts: {e}")
            return {"error": str(e), "sent": 0, "failed": 0}

    # ========================================
    # Protection Score Notifications
    # ========================================

    async def send_low_protection_score_alerts(self, threshold: int = 40) -> Dict[str, int]:
        """
        Send alerts to users with low protection scores.
        Only sends once per week per user.
        """
        try:
            logger.info(f"Processing low protection score alerts (threshold: {threshold})")

            # Find users with low protection scores
            low_score_users = list(self.db["user_profiles"].find({
                "protection_score": {"$lt": threshold, "$gt": 0}
            }))

            sent_count = 0
            skipped_count = 0
            failed_count = 0

            # Check weekly limit
            week_start = (get_ist_now() - timedelta(days=get_ist_now().weekday())).strftime("%Y-%m-%d")

            for user in low_score_users:
                user_id = str(user.get("user_id", ""))
                if not user_id:
                    continue

                # Check if sent this week
                tracker_key = f"low_score_{week_start}"
                if self._was_notification_sent_today(user_id, "protection_score", tracker_key):
                    skipped_count += 1
                    continue

                score = user.get("protection_score", 0)
                name = user.get("name", "")

                if score < 20:
                    title = "⚠️ Critical: Very Low Protection Score"
                    body = f"Your protection score is only {score}/100. You may have significant coverage gaps. Review your insurance portfolio now."
                    priority = NotificationPriority.HIGH
                elif score < 30:
                    title = "🔴 Low Protection Score Alert"
                    body = f"Your protection score is {score}/100. Consider adding more coverage to protect yourself and your family."
                    priority = NotificationPriority.HIGH
                else:
                    title = "📊 Improve Your Protection Score"
                    body = f"Your protection score is {score}/100. There's room for improvement. Check our recommendations."
                    priority = NotificationPriority.NORMAL

                data = {
                    "score": str(score),
                    "action": "view_score",
                    "deep_link": "eazr://dashboard/protection-score"
                }

                try:
                    success, _, _, _ = await notification_service.send_notification_to_user(
                        user_id=user_id,
                        title=title,
                        body=body,
                        notification_type=NotificationType.PROTECTION_SCORE,
                        priority=priority,
                        data=data
                    )

                    if success:
                        sent_count += 1
                        self._mark_notification_sent(user_id, "protection_score", tracker_key)
                    else:
                        failed_count += 1

                except Exception as e:
                    failed_count += 1
                    logger.error(f"Error sending score alert: {e}")

            result = {
                "threshold": threshold,
                "total_users": len(low_score_users),
                "sent": sent_count,
                "skipped": skipped_count,
                "failed": failed_count
            }
            logger.info(f"Low protection score alerts completed: {result}")
            return result

        except Exception as e:
            logger.error(f"Error in send_low_protection_score_alerts: {e}")
            return {"error": str(e), "sent": 0, "failed": 0}

    # ========================================
    # Welcome & System Notifications
    # ========================================

    async def send_welcome_notifications(self) -> Dict[str, int]:
        """Send welcome notifications to new users registered today."""
        try:
            today = get_ist_now().strftime("%Y-%m-%d")

            logger.info(f"Processing welcome notifications for {today}")

            # Find users registered today
            today_start = datetime.strptime(today, "%Y-%m-%d")
            today_end = today_start + timedelta(days=1)

            new_users = list(self.db["user_profiles"].find({
                "created_at": {
                    "$gte": today_start,
                    "$lt": today_end
                }
            }))

            sent_count = 0
            skipped_count = 0
            failed_count = 0

            for user in new_users:
                user_id = str(user.get("user_id", ""))
                if not user_id:
                    continue

                # Check if already sent
                if self._was_notification_sent_today(user_id, "welcome", "welcome"):
                    skipped_count += 1
                    continue

                name = user.get("name", "").split()[0] if user.get("name") else ""
                greeting = f"Hi {name}! " if name else ""

                title = "🎉 Welcome to EAZR!"
                body = f"{greeting}Your account is ready. Upload your insurance policies to get personalized insights and never miss a renewal."

                data = {
                    "action": "view_dashboard",
                    "deep_link": "eazr://dashboard"
                }

                try:
                    success, _, _, _ = await notification_service.send_notification_to_user(
                        user_id=user_id,
                        title=title,
                        body=body,
                        notification_type=NotificationType.SYSTEM,
                        priority=NotificationPriority.NORMAL,
                        data=data
                    )

                    if success:
                        sent_count += 1
                        self._mark_notification_sent(user_id, "welcome", "welcome")
                    else:
                        failed_count += 1

                except Exception as e:
                    failed_count += 1
                    logger.error(f"Error sending welcome notification: {e}")

            result = {
                "total_new_users": len(new_users),
                "sent": sent_count,
                "skipped": skipped_count,
                "failed": failed_count
            }
            logger.info(f"Welcome notifications completed: {result}")
            return result

        except Exception as e:
            logger.error(f"Error in send_welcome_notifications: {e}")
            return {"error": str(e), "sent": 0, "failed": 0}

    # ========================================
    # Coverage Gap Recommendations
    # ========================================

    async def send_coverage_gap_recommendations(self) -> Dict[str, int]:
        """
        Send coverage gap recommendations to users missing essential coverage.
        Runs weekly.

        Uses policy_analysis collection from eazr_chatbot database.
        Policy type is in extractedData.policyType field.
        """
        try:
            logger.info("Processing coverage gap recommendations")

            week_start = (get_ist_now() - timedelta(days=get_ist_now().weekday())).strftime("%Y-%m-%d")

            # Get all users with policies - user_id is at root level
            users_with_policies = self.policies_collection.distinct("user_id")
            users_with_policies = [str(u) for u in users_with_policies if u]

            sent_count = 0
            skipped_count = 0
            failed_count = 0

            for user_id in users_with_policies:
                user_id = str(user_id)

                # Check if already sent this week
                tracker_key = f"recommendation_{week_start}"
                if self._was_notification_sent_today(user_id, "recommendation", tracker_key):
                    skipped_count += 1
                    continue

                # Analyze user's policies
                user_policies = list(self.policies_collection.find({
                    "user_id": int(user_id) if user_id.isdigit() else user_id
                }))

                policy_types = set()
                for p in user_policies:
                    # Get policy type from extractedData.policyType
                    extracted = p.get("extractedData", {})
                    policy_type = (
                        extracted.get("policyType") or
                        p.get("policyType") or
                        ""
                    ).lower()
                    if "health" in policy_type:
                        policy_types.add("health")
                    elif "life" in policy_type or "term" in policy_type:
                        policy_types.add("life")
                    elif "motor" in policy_type or "car" in policy_type or "bike" in policy_type or "auto" in policy_type:
                        policy_types.add("motor")

                # Determine recommendation
                recommendation = None
                gap_type = None

                if "health" not in policy_types:
                    gap_type = "health"
                    title = "🏥 Health Insurance Recommended"
                    recommendation = "You don't have health insurance. Medical emergencies can be expensive. Get covered today!"
                elif "life" not in policy_types:
                    gap_type = "life"
                    title = "👨‍👩‍👧‍👦 Life Insurance Recommended"
                    recommendation = "Protect your family's future with life insurance. Explore term plans for comprehensive coverage."

                if not recommendation:
                    skipped_count += 1
                    continue

                data = {
                    "gap_type": gap_type,
                    "action": "view_recommendations",
                    "deep_link": "eazr://recommendations"
                }

                try:
                    success, _, _, _ = await notification_service.send_notification_to_user(
                        user_id=user_id,
                        title=title,
                        body=recommendation,
                        notification_type=NotificationType.NEW_RECOMMENDATION,
                        priority=NotificationPriority.LOW,
                        data=data
                    )

                    if success:
                        sent_count += 1
                        self._mark_notification_sent(user_id, "recommendation", tracker_key)
                    else:
                        failed_count += 1

                except Exception as e:
                    failed_count += 1
                    logger.error(f"Error sending recommendation: {e}")

            result = {
                "total_users_checked": len(users_with_policies),
                "sent": sent_count,
                "skipped": skipped_count,
                "failed": failed_count
            }
            logger.info(f"Coverage gap recommendations completed: {result}")
            return result

        except Exception as e:
            logger.error(f"Error in send_coverage_gap_recommendations: {e}")
            return {"error": str(e), "sent": 0, "failed": 0}

    # ========================================
    # Master Run Functions (for cron jobs)
    # ========================================

    async def run_all_notifications(self) -> Dict[str, Any]:
        """Run all notification jobs. Use for testing or manual trigger."""
        results = {
            "timestamp": get_ist_now().isoformat(),
            "jobs": {}
        }

        # Policy expiry reminders
        for days in [30, 15, 7, 3, 1]:
            results["jobs"][f"expiry_{days}_days"] = await self.send_policy_expiry_reminders(days)

        # Expired policies
        results["jobs"]["expired_today"] = await self.send_expired_policy_alerts()

        # Protection score alerts
        results["jobs"]["low_score_alerts"] = await self.send_low_protection_score_alerts()

        # Welcome notifications
        results["jobs"]["welcome"] = await self.send_welcome_notifications()

        # Coverage recommendations
        results["jobs"]["recommendations"] = await self.send_coverage_gap_recommendations()

        return results


# Singleton instance
notification_cron = NotificationCronService()


# ========================================
# Cron Job Entry Points
# ========================================

async def run_morning_notifications():
    """
    Run at 9:00 AM IST
    - 30-day expiry reminders
    - 15-day expiry reminders
    """
    logger.info("=== Running Morning Notifications (9 AM IST) ===")
    results = {}
    results["30_day_expiry"] = await notification_cron.send_policy_expiry_reminders(30)
    results["15_day_expiry"] = await notification_cron.send_policy_expiry_reminders(15)
    logger.info(f"Morning notifications complete: {results}")
    return results


async def run_urgent_notifications():
    """
    Run at 10:00 AM IST
    - 7-day expiry reminders
    - 3-day expiry reminders
    - 1-day expiry reminders
    - Expired policy alerts
    """
    logger.info("=== Running Urgent Notifications (10 AM IST) ===")
    results = {}
    results["7_day_expiry"] = await notification_cron.send_policy_expiry_reminders(7)
    results["3_day_expiry"] = await notification_cron.send_policy_expiry_reminders(3)
    results["1_day_expiry"] = await notification_cron.send_policy_expiry_reminders(1)
    results["expired_today"] = await notification_cron.send_expired_policy_alerts()
    logger.info(f"Urgent notifications complete: {results}")
    return results


async def run_score_notifications():
    """
    Run at 11:00 AM IST
    - Low protection score alerts
    - Coverage gap recommendations (weekly)
    """
    logger.info("=== Running Score Notifications (11 AM IST) ===")
    results = {}
    results["low_score"] = await notification_cron.send_low_protection_score_alerts()

    # Only run recommendations on Mondays
    if get_ist_now().weekday() == 0:
        results["recommendations"] = await notification_cron.send_coverage_gap_recommendations()

    logger.info(f"Score notifications complete: {results}")
    return results


async def run_evening_notifications():
    """
    Run at 6:00 PM IST
    - Welcome notifications for new users
    """
    logger.info("=== Running Evening Notifications (6 PM IST) ===")
    results = {}
    results["welcome"] = await notification_cron.send_welcome_notifications()
    logger.info(f"Evening notifications complete: {results}")
    return results


async def run_all():
    """Run all notification jobs (for testing/manual trigger)."""
    return await notification_cron.run_all_notifications()
