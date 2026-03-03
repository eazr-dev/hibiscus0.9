"""
Migration Script: Fix Default 'User' Usernames

This script updates existing user profiles that have the default 'User' username
to a more meaningful default based on their phone number: User_XXXX (last 4 digits)

Usage:
    python3 scripts/fix_default_usernames.py

What it does:
1. Finds all users in user_profiles where preferences.user_name is 'User'
2. Updates them to 'User_XXXX' format using last 4 digits of phone number
3. Reports how many users were updated
"""

import sys
sys.path.append('/Users/eazrhrushikesh/eazr_chat/botproject')

from database_storage.mongodb_chat_manager import mongodb_chat_manager
from datetime import datetime


def fix_default_usernames():
    """Fix default 'User' usernames to include phone suffix"""

    # Get database connection
    db = mongodb_chat_manager.db

    if db is None:
        print("MongoDB connection not available")
        return

    users_collection = db['user_profiles']

    print("=== Fixing Default Usernames ===\n")

    # Find users with default 'User' username
    print("Searching for users with default 'User' username...")
    users_with_default_name = list(users_collection.find({
        "$or": [
            {"preferences.user_name": "User"},
            {"preferences.user_name": {"$exists": False}},
            {"preferences.user_name": None},
            {"preferences.user_name": ""}
        ]
    }))

    total_users = len(users_with_default_name)
    print(f"Found {total_users} users with default username\n")

    if total_users == 0:
        print("All users already have proper usernames!")
        return

    updated_count = 0
    skipped_count = 0

    for idx, user in enumerate(users_with_default_name, 1):
        user_id = user.get("user_id")
        phone = user.get("preferences", {}).get("phone", "")
        email = user.get("preferences", {}).get("email", "")
        full_name = user.get("preferences", {}).get("full_name", "")
        current_name = user.get("preferences", {}).get("user_name", "User")

        print(f"[{idx}/{total_users}] Processing user_id: {user_id}")
        print(f"  Current name: {current_name}")
        print(f"  Phone: {phone}")
        print(f"  Email: {email}")

        # Determine new username
        new_username = None

        # Priority 1: Use full_name if available
        if full_name and full_name not in ["User", "", None]:
            new_username = full_name
            print(f"  -> Using full_name: {new_username}")

        # Priority 2: Generate from phone number
        elif phone and len(phone) >= 4 and not phone.startswith("@"):
            # Get last 4 digits of phone
            phone_suffix = phone[-4:]
            new_username = f"User_{phone_suffix}"
            print(f"  -> Generated from phone: {new_username}")

        # Priority 3: Generate from email
        elif email and "@" in email:
            email_prefix = email.split("@")[0]
            # Capitalize first letter
            new_username = email_prefix.capitalize()
            print(f"  -> Generated from email: {new_username}")

        else:
            print(f"  -> Skipping: No phone or email available")
            skipped_count += 1
            continue

        # Update the user
        result = users_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "preferences.user_name": new_username,
                    "updated_at": datetime.utcnow()
                }
            }
        )

        if result.modified_count > 0:
            print(f"  Updated: {current_name} -> {new_username}")
            updated_count += 1
        else:
            print(f"  No changes made")

        print()

    # Summary
    print("\n" + "=" * 50)
    print("=== Migration Complete ===")
    print("=" * 50)
    print(f"Total users processed: {total_users}")
    print(f"Successfully updated: {updated_count}")
    print(f"Skipped (no phone/email): {skipped_count}")
    if total_users > 0:
        print(f"Success rate: {(updated_count / total_users * 100):.1f}%")
    print("=" * 50)


def preview_changes():
    """Preview changes without applying them"""

    db = mongodb_chat_manager.db

    if db is None:
        print("MongoDB connection not available")
        return

    users_collection = db['user_profiles']

    print("=== Preview: Users with Default Username ===\n")

    users = list(users_collection.find({
        "$or": [
            {"preferences.user_name": "User"},
            {"preferences.user_name": {"$exists": False}},
            {"preferences.user_name": None},
            {"preferences.user_name": ""}
        ]
    }).limit(20))

    print(f"Showing first {len(users)} users:\n")

    for user in users:
        user_id = user.get("user_id")
        phone = user.get("preferences", {}).get("phone", "N/A")
        email = user.get("preferences", {}).get("email", "N/A")
        current_name = user.get("preferences", {}).get("user_name", "N/A")

        print(f"  user_id: {user_id}")
        print(f"  current_name: {current_name}")
        print(f"  phone: {phone}")
        print(f"  email: {email}")
        print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fix default usernames")
    parser.add_argument("--preview", action="store_true", help="Preview changes without applying")
    args = parser.parse_args()

    try:
        if args.preview:
            preview_changes()
        else:
            # Ask for confirmation
            print("This will update all users with 'User' username.\n")
            confirm = input("Do you want to proceed? (yes/no): ")

            if confirm.lower() == "yes":
                fix_default_usernames()
            else:
                print("Migration cancelled.")
    except Exception as e:
        print(f"\nError during migration: {str(e)}")
        import traceback
        traceback.print_exc()
