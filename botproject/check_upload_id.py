import sys
sys.path.append('/Users/eazrhrushikesh/eazr_chat/botproject')

from database_storage.mongodb_chat_manager import mongodb_chat_manager

# Get database connection
db = mongodb_chat_manager.db

# Check the policy in policy_analysis collection
policy_analysis = db['policy_analysis']
policy = policy_analysis.find_one({'analysisId': 'ANL_282_23efc78197da'})

if policy:
    print('=== Policy Analysis Document ===')
    print(f'analysisId: {policy.get("analysisId")}')
    print(f'uploadId: {policy.get("uploadId")}')
    print(f'user_id: {policy.get("user_id")}')
    print(f'Has uploadId: {bool(policy.get("uploadId"))}')
    print()

    # If uploadId exists, check policy_uploads
    upload_id = policy.get('uploadId')
    if upload_id:
        policy_uploads = db['policy_uploads']
        upload_doc = policy_uploads.find_one({'upload_id': upload_id})

        if upload_doc:
            print('=== Policy Upload Document Found ===')
            print(f'upload_id: {upload_doc.get("upload_id")}')
            print(f'document_url: {upload_doc.get("document_url")}')
            print(f'uploaded_at: {upload_doc.get("uploaded_at")}')
            print(f'Available fields: {list(upload_doc.keys())}')
        else:
            print(f'❌ No document found in policy_uploads with upload_id: {upload_id}')
    else:
        print('❌ uploadId is empty in policy_analysis document')

        # Check if there's a policy_uploads entry by user_id and analysisId
        print()
        print('=== Searching policy_uploads by user_id and analysis_id ===')
        policy_uploads = db['policy_uploads']

        # Try to find by analysis_id
        upload_by_analysis = policy_uploads.find_one({'analysis_id': 'ANL_282_23efc78197da'})
        if upload_by_analysis:
            print(f'✅ Found upload by analysis_id!')
            print(f'  - upload_id: {upload_by_analysis.get("upload_id")}')
            print(f'  - document_url: {upload_by_analysis.get("document_url")}')
            print(f'  - Available fields: {list(upload_by_analysis.keys())}')
        else:
            print('❌ No upload found by analysis_id either')

            # Show some sample uploads for this user
            uploads = list(policy_uploads.find({'user_id': str(policy.get('user_id'))}).limit(3))
            print(f'\nFound {len(uploads)} total uploads for user {policy.get("user_id")}:')
            for upload in uploads:
                print(f'  - upload_id: {upload.get("upload_id")}, analysis_id: {upload.get("analysis_id")}, has document_url: {bool(upload.get("document_url"))}')
else:
    print('❌ Policy not found')
