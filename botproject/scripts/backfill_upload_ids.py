"""
Backfill Script: Populate uploadId for Existing Policies

This script updates existing policy_analysis documents to include the uploadId field
by matching them with corresponding records in the policy_uploads collection.

Usage:
    python3 scripts/backfill_upload_ids.py

What it does:
1. Finds all policies in policy_analysis where uploadId is missing or empty
2. For each policy, searches policy_uploads for a matching record by user_id and analysis_id
3. Updates the policy_analysis document with the found upload_id

Note: This is optional. New uploads already include uploadId automatically.
"""

import sys
sys.path.append('/Users/eazrhrushikesh/eazr_chat/botproject')

from database_storage.mongodb_chat_manager import mongodb_chat_manager

def backfill_upload_ids():
    """Backfill uploadId for existing policies"""

    # Get database connection
    db = mongodb_chat_manager.db

    if db is None:
        print("❌ MongoDB connection not available")
        return

    policy_analysis = db['policy_analysis']
    policy_uploads = db['policy_uploads']

    print("=== Backfilling Upload IDs ===\n")

    # Find policies missing uploadId
    print("🔍 Searching for policies without uploadId...")
    policies_without_upload_id = list(policy_analysis.find({
        "$or": [
            {"uploadId": {"$exists": False}},
            {"uploadId": ""},
            {"uploadId": None}
        ]
    }))

    total_policies = len(policies_without_upload_id)
    print(f"📊 Found {total_policies} policies without uploadId\n")

    if total_policies == 0:
        print("✅ All policies already have uploadId!")
        return

    updated_count = 0
    not_found_count = 0

    for idx, policy in enumerate(policies_without_upload_id, 1):
        analysis_id = policy.get("analysisId")
        user_id = policy.get("user_id")

        print(f"[{idx}/{total_policies}] Processing {analysis_id}...")

        # Find matching upload by analysis_id
        upload = policy_uploads.find_one({
            "analysis_id": analysis_id
        })

        if upload:
            # Update policy with uploadId
            upload_id = upload.get("upload_id")

            result = policy_analysis.update_one(
                {"analysisId": analysis_id},
                {"$set": {"uploadId": upload_id}}
            )

            if result.modified_count > 0:
                print(f"  ✅ Updated with uploadId: {upload_id}")
                updated_count += 1
            else:
                print(f"  ⚠️  Already had uploadId: {upload_id}")
        else:
            # Try finding by user_id as fallback
            uploads_by_user = list(policy_uploads.find({"user_id": str(user_id)}))

            if len(uploads_by_user) == 1:
                # Only one upload for this user, likely a match
                upload_id = uploads_by_user[0].get("upload_id")

                result = policy_analysis.update_one(
                    {"analysisId": analysis_id},
                    {"$set": {"uploadId": upload_id}}
                )

                print(f"  ⚠️  Matched by user_id only: {upload_id}")
                updated_count += 1
            else:
                print(f"  ❌ No upload found (user has {len(uploads_by_user)} uploads)")
                not_found_count += 1

    # Summary
    print("\n" + "="*50)
    print("=== Migration Complete ===")
    print("="*50)
    print(f"Total policies processed: {total_policies}")
    print(f"✅ Successfully updated: {updated_count}")
    print(f"❌ Not found: {not_found_count}")
    print(f"📊 Success rate: {(updated_count/total_policies*100):.1f}%")
    print("="*50)

if __name__ == "__main__":
    try:
        backfill_upload_ids()
    except Exception as e:
        print(f"\n❌ Error during migration: {str(e)}")
        import traceback
        traceback.print_exc()
