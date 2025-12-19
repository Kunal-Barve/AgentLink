"""
Test script to check and create required Backblaze B2 folders

Required folders:
- Commission_Rates
- Suburbs_Top_Agents
"""
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

from app.services.backblaze_service import backblaze_service
from app.services.upload_to_backblaze import (
    check_folder_exists,
    create_folder,
    ensure_folders_exist,
    list_folders,
    get_folder_file_count,
    REQUIRED_FOLDERS
)


def main():
    print("=" * 60)
    print("🔍 BACKBLAZE B2 FOLDER CHECK")
    print("=" * 60)
    
    # Verify connection first
    print("\n📡 Checking Backblaze B2 connection...")
    if not backblaze_service.verify_connection():
        print("❌ Failed to connect to Backblaze B2")
        print("   Please check your credentials in .env file")
        return 1
    
    print("✅ Connected to Backblaze B2")
    print(f"   Bucket: {backblaze_service.bucket_name}")
    
    # List existing folders
    print("\n📁 Existing folders in bucket:")
    existing_folders = list_folders()
    if existing_folders:
        for folder in existing_folders:
            file_count = get_folder_file_count(folder)
            print(f"   • {folder}/ ({file_count} files)")
    else:
        print("   (no folders found)")
    
    # Check required folders
    print("\n" + "=" * 60)
    print("📋 REQUIRED FOLDERS CHECK")
    print("=" * 60)
    
    results = ensure_folders_exist()
    
    # Summary
    print("\n📊 SUMMARY:")
    created = sum(1 for v in results.values() if v == 'created')
    existed = sum(1 for v in results.values() if v == 'exists')
    failed = sum(1 for v in results.values() if v == 'failed')
    
    print(f"   ✅ Already existed: {existed}")
    print(f"   📁 Created: {created}")
    print(f"   ❌ Failed: {failed}")
    
    # List folders again to confirm
    print("\n📁 Folders after check:")
    final_folders = list_folders()
    for folder in final_folders:
        file_count = get_folder_file_count(folder)
        status = "✅" if folder in REQUIRED_FOLDERS else "  "
        print(f"   {status} {folder}/ ({file_count} files)")
    
    print("\n" + "=" * 60)
    if failed == 0:
        print("✅ All required folders are ready!")
    else:
        print("⚠️  Some folders failed to create. Check logs above.")
    print("=" * 60)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
