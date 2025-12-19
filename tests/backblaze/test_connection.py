"""
Test Backblaze B2 Connection
Simple script to verify connection to Backblaze B2
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.backblaze_service import BackblazeService
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_connection():
    """Test basic connection to Backblaze B2"""
    print("=" * 60)
    print("BACKBLAZE B2 CONNECTION TEST")
    print("=" * 60)
    
    # Initialize service
    print("\n1. Initializing Backblaze B2 Service...")
    service = BackblazeService()
    
    # Check credentials
    print("\n2. Checking Credentials...")
    if not service.s3_client:
        print("   ❌ FAILED: S3 client not initialized")
        print("   Please check your .env file has:")
        print("   - B2_ENDPOINT_URL")
        print("   - B2_KEY_ID")
        print("   - B2_APPLICATION_KEY")
        print("   - B2_BUCKET_NAME")
        return False
    else:
        print("   ✓ S3 client initialized")
    
    # Verify connection
    print("\n3. Verifying Connection to Bucket...")
    if service.verify_connection():
        print(f"   ✓ Successfully connected to bucket: {service.bucket_name}")
    else:
        print(f"   ❌ FAILED: Cannot access bucket: {service.bucket_name}")
        print("   Possible reasons:")
        print("   - Bucket doesn't exist")
        print("   - Incorrect credentials")
        print("   - Insufficient permissions")
        return False
    
    # List files (optional test)
    print("\n4. Testing File Listing...")
    try:
        files = service.list_files(max_keys=5)
        print(f"   ✓ Found {len(files)} files in bucket")
        if files:
            print("   Sample files:")
            for f in files[:5]:
                print(f"     - {f}")
    except Exception as e:
        print(f"   ⚠ Warning: Could not list files: {e}")
    
    print("\n" + "=" * 60)
    print("CONNECTION TEST PASSED ✓")
    print("=" * 60)
    print("\nYou can now use Backblaze B2 for file uploads!")
    return True


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
