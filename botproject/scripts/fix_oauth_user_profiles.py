"""
Migration Script: Fix OAuth User Profiles

This script updates existing OAuth user profiles that have:
1. Email stored in the 'phone' field instead of 'email' field
2. Full name stored in 'user_name' instead of 'full_name'
3. Missing proper username format (firstname+user_id)

Usage:
    python3 scripts/fix_oauth_user_profiles.py
    python3 scripts/fix_oauth_user_profiles.py --preview  # Preview without changes

What it does:
1. Finds OAuth users (those with oauth_provider field or email-like phone)
2. Moves email from phone to email field
3. Moves full name from user_name to full_name
4. Generates proper username: firstname + user_id (e.g., hitesh414)
"""

import sys
sys.path.append('/Users/eazrhrushikesh/eazr_chat/botproject')

from database_storage.mongodb_chat_manager import mongodb_chat_manager
from datetime import datetime
import re


def generate_username(full_name: str, user_id: int, email: str = None) -> str:
    """
    Generate username in format: firstname + user_id

    Examples:
        - "Hitesh Meghwal" + 414 -> "hitesh414"
        - "John Doe" + 123 -> "john123"
        - "" (no name) + 414 + email "john@gmail.com" -> "john414"
    """
    if full_name and full_name.strip() and full_name != 'User':
        # Extract first name (first word before space)
        first_name = full_name.strip().split()[0]
        # Remove any special characters, keep only alphanumeric
        first_name = re.sub(r'[^a-zA-Z0-9]', '', first_name)
        # Convert to lowercase
        first_name = first_name.lower()

        if first_name:
            return f"{first_name}{user_id}"

    # Fallback: use email prefix if available
    if email and '@' in email:
        email_prefix = email.split('@')[0]
        email_prefix = re.sub(r'[^a-zA-Z0-9]', '', email_prefix)
        email_prefix = email_prefix.lower()
        if email_prefix:
            return f"{email_prefix}{user_id}"

    # Final fallback
    return f"user{user_id}"


def is_email(value: str) -> bool:
    """Check if a string looks like an email"""
    if not value:
        return False
    return '@' in value and '.' in value


def looks_like_email_prefix(value: str) -> bool:
    """Check if a string looks like an email prefix (not a phone number)"""
    if not value:
        return False
    # Phone numbers are typically digits with optional +
    # If value starts with a letter, it's likely an email prefix
    # Or if it has dots but no @ (like "eazr.ai.32")
    return (
        value[0].isalpha() or  # Starts with letter
        ('.' in value and '@' not in value) or  # Has dot but no @
        not value.replace('+', '').replace('-', '').replace(' ', '').isdigit()  # Not a phone number
    )


def fix_oauth_user_profiles(preview_only: bool = False):
    """Fix OAuth user profiles with incorrect data structure"""

    # Get database connection
    db = mongodb_chat_manager.db

    if db is None:
        print("MongoDB connection not available")
        return

    users_collection = db['user_profiles']

    print("=== Fixing OAuth User Profiles ===\n")

    # Find OAuth users or users with email in phone field
    print("Searching for OAuth users or users with email in phone field...")

    # Query: oauth_provider exists OR phone looks like email/email-prefix
    oauth_users = list(users_collection.find({
        "$or": [
            {"oauth_provider": {"$exists": True}},
            {"preferences.phone": {"$regex": "@.*\\.", "$options": "i"}},  # Contains @
            {"preferences.phone": {"$regex": "^[a-zA-Z]", "$options": ""}},  # Starts with letter
            {"preferences.phone": {"$regex": "\\.", "$options": ""}},  # Contains dot (like eazr.ai.32)
            {"preferences.auth_method": {"$in": ["google", "apple"]}}  # OAuth auth method
        ]
    }))

    total_users = len(oauth_users)
    print(f"Found {total_users} OAuth/problematic users\n")

    if total_users == 0:
        print("No OAuth users found to fix!")
        return

    updated_count = 0
    skipped_count = 0
    already_correct = 0

    for idx, user in enumerate(oauth_users, 1):
        user_id = user.get("user_id")
        preferences = user.get("preferences", {})

        phone_value = preferences.get("phone", "")
        email_value = preferences.get("email", "")
        current_user_name = preferences.get("user_name", "")
        current_full_name = preferences.get("full_name", "")
        oauth_provider = user.get("oauth_provider", "")

        print(f"[{idx}/{total_users}] Processing user_id: {user_id}")
        print(f"  OAuth Provider: {oauth_provider or 'N/A'}")
        print(f"  Current phone: {phone_value}")
        print(f"  Current email: {email_value}")
        print(f"  Current user_name: {current_user_name}")
        print(f"  Current full_name: {current_full_name}")

        # Determine what needs to be fixed
        update_data = {}
        needs_update = False

        # Check if phone field contains an email or email-like value
        if is_email(phone_value):
            # Move full email from phone to email field
            if not email_value:
                update_data["preferences.email"] = phone_value
                print(f"  -> Moving email from phone to email field: {phone_value}")
            # Clear the phone field (OAuth users don't have phone)
            update_data["preferences.phone"] = None
            needs_update = True
        elif looks_like_email_prefix(phone_value):
            # Phone contains something that's not a valid phone (like "eazr.ai.32")
            # This is likely an OAuth user with malformed data
            print(f"  -> Phone field contains non-phone value: {phone_value}")
            # Clear the phone field
            update_data["preferences.phone"] = None
            needs_update = True

        # Check if user_name contains what looks like a full name (has space)
        # and full_name is empty
        if ' ' in current_user_name and not current_full_name:
            # The user_name is actually a full name
            actual_full_name = current_user_name
            update_data["preferences.full_name"] = actual_full_name
            print(f"  -> Moving full name from user_name to full_name: {actual_full_name}")
            needs_update = True

            # Now determine what email to use for username generation
            actual_email = email_value or (phone_value if is_email(phone_value) else "")

            # Generate proper username
            new_username = generate_username(actual_full_name, user_id, actual_email)
            update_data["preferences.user_name"] = new_username
            print(f"  -> Generating new username: {new_username}")

        # Check if username is in old format (User_XXXX or just 'User')
        elif current_user_name == 'User' or current_user_name.startswith('User_'):
            actual_full_name = current_full_name or current_user_name
            actual_email = email_value or (phone_value if is_email(phone_value) else "")

            new_username = generate_username(actual_full_name, user_id, actual_email)
            if new_username != current_user_name:
                update_data["preferences.user_name"] = new_username
                print(f"  -> Updating username from '{current_user_name}' to '{new_username}'")
                needs_update = True

        if not needs_update:
            print("  -> Already correct, skipping")
            already_correct += 1
            print()
            continue

        if preview_only:
            print(f"  [PREVIEW] Would update with: {update_data}")
            updated_count += 1
        else:
            # Apply the update
            update_data["updated_at"] = datetime.utcnow()

            result = users_collection.update_one(
                {"user_id": user_id},
                {"$set": update_data}
            )

            if result.modified_count > 0:
                print(f"  Updated successfully!")
                updated_count += 1
            else:
                print(f"  No changes made")
                skipped_count += 1

        print()

    # Summary
    print("\n" + "=" * 50)
    print("=== Migration Complete ===")
    print("=" * 50)
    print(f"Total OAuth users found: {total_users}")
    print(f"Already correct: {already_correct}")
    if preview_only:
        print(f"Would update: {updated_count}")
    else:
        print(f"Successfully updated: {updated_count}")
        print(f"Skipped (no changes): {skipped_count}")
    if total_users > 0:
        print(f"Success rate: {((updated_count + already_correct) / total_users * 100):.1f}%")
    print("=" * 50)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fix OAuth user profiles")
    parser.add_argument("--preview", action="store_true", help="Preview changes without applying")
    args = parser.parse_args()

    try:
        fix_oauth_user_profiles(preview_only=args.preview)
    except Exception as e:
        print(f"\nError during migration: {str(e)}")
        import traceback
        traceback.print_exc()
