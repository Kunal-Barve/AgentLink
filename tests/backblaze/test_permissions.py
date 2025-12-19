"""
Test Backblaze B2 Permissions
Check if the application key has proper read, write, and delete permissions
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.backblaze_service import backblaze_service
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    print("=" * 60)
    print("BACKBLAZE B2 PERMISSION TEST")
    print("=" * 60)
    
    # Check credentials
    bucket_name = os.getenv("B2_BUCKET_NAME")
    key_id = os.getenv("B2_KEY_ID")
    app_key = os.getenv("B2_APPLICATION_KEY")
    
    print(f"\n📦 Bucket: {bucket_name}")
    print(f"🔑 Key ID: {key_id[:10]}...{key_id[-4:] if len(key_id) > 14 else ''}")
    print()
    
    # Verify connection first
    print("1. Verifying Connection...")
    if not backblaze_service.verify_connection():
        print("❌ Connection failed!")
        print("\n⚠️  Check your .env configuration:")
        print("   • B2_ENDPOINT_URL")
        print("   • B2_KEY_ID")
        print("   • B2_APPLICATION_KEY")
        print("   • B2_BUCKET_NAME")
        return False
    
    print("✓ Connection successful\n")
    
    # Test permissions
    print("2. Testing Permissions...")
    print("-" * 60)
    
    permissions = backblaze_service.test_permissions()
    
    print("\n" + "=" * 60)
    print("PERMISSION TEST RESULTS")
    print("=" * 60)
    print(f"READ:   {'✓ ALLOWED' if permissions['read'] else '✗ DENIED'}")
    print(f"WRITE:  {'✓ ALLOWED' if permissions['write'] else '✗ DENIED'}")
    print(f"DELETE: {'✓ ALLOWED' if permissions['delete'] else '✗ DENIED'}")
    print("=" * 60)
    
    # Diagnosis
    if not permissions['delete']:
        print("\n⚠️  DELETE PERMISSION ISSUE DETECTED!")
        print("=" * 60)
        print("\n❌ Your application key CANNOT delete files")
        print("\n📋 How to Fix:")
        print("   1. Go to Backblaze B2 web console")
        print("   2. Navigate to App Keys section")
        print("   3. DELETE your current application key")
        print("   4. Create a NEW application key with:")
        print("      • Name: AgentLink-Full-Access")
        print("      • Type of Access: Read and Write")
        print("      • Allow access to Bucket(s): Select your bucket")
        print("   5. Copy the NEW keyID and applicationKey")
        print("   6. Update your .env file with NEW credentials")
        print("\n⚠️  IMPORTANT: Application key is shown only once!")
        print("   Save it immediately when creating the new key.")
        print("=" * 60)
        return False
    
    if all(permissions.values()):
        print("\n✅ ALL PERMISSIONS OK!")
        print("   Your application key has full access")
        print("   You can read, write, and delete files")
        return True
    else:
        print("\n⚠️  PARTIAL PERMISSIONS")
        print("   Some operations may not work correctly")
        return False


if __name__ == "__main__":
    success = main()
    print()
    sys.exit(0 if success else 1)
