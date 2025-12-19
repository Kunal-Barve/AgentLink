"""
Backblaze B2 Cleanup Script - THE ONLY CLEANUP SCRIPT
Delete all test files and folders created during testing

This is the ONLY cleanup script you need. It handles:
- Listing all files and versions
- Deleting files with version IDs (for buckets with versioning enabled)
- Verifying cleanup was successful
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


def verify_truly_empty():
    """
    Verify bucket is TRULY empty by checking versions
    """
    print("\n🔍 Verifying bucket is truly empty (checking all versions)...")
    
    # Check via list_objects (regular files)
    regular_files = backblaze_service.list_files()
    
    # Check via list_object_versions (all versions)
    all_versions = backblaze_service.list_all_versions()
    
    if not regular_files and not all_versions:
        print("✅ Bucket is COMPLETELY EMPTY!")
        print("   No files, versions, or delete markers found.")
        return True
    elif not regular_files and all_versions:
        print(f"⚠️  Bucket appears empty but has {len(all_versions)} hidden versions/markers")
        print("   These are old versions or delete markers.")
        return False
    else:
        print(f"⚠️  Bucket still has {len(regular_files)} visible files")
        return False


def list_all_files():
    """List all files in the bucket"""
    print("\n" + "=" * 60)
    print("📋 LISTING ALL FILES IN BUCKET")
    print("=" * 60)
    
    all_files = backblaze_service.list_files()
    
    if not all_files:
        print("\n✅ Bucket is empty - nothing to clean up!")
        return []
    
    print(f"\nFound {len(all_files)} files:\n")
    for i, file_key in enumerate(all_files, 1):
        print(f"  {i}. {file_key}")
    
    return all_files


def list_files_by_folder(folder_prefix):
    """List files in a specific folder"""
    files = backblaze_service.list_files(prefix=folder_prefix)
    return files if files else []


def delete_files_in_folder(folder_prefix, auto_confirm=False):
    """Delete all files in a specific folder"""
    print(f"\n📁 Checking folder: {folder_prefix}")
    
    files = list_files_by_folder(folder_prefix)
    
    if not files:
        print(f"   ✓ Empty (nothing to delete)")
        return 0
    
    print(f"   Found {len(files)} files:")
    for f in files:
        print(f"      - {f}")
    
    if not auto_confirm:
        response = input(f"\n   Delete these {len(files)} files? (y/n): ").lower()
        if response != 'y':
            print("   ⏭️  Skipped")
            return 0
    
    # Delete files (including all versions if versioning is enabled)
    deleted_count = 0
    for file_key in files:
        try:
            # Try to delete all versions (works even if versioning is disabled)
            versions_deleted = backblaze_service.delete_all_versions(file_key)
            if versions_deleted > 0:
                print(f"   ✓ Deleted: {file_key} ({versions_deleted} version(s))")
                deleted_count += 1
            else:
                print(f"   ❌ Failed to delete: {file_key}")
        except Exception as e:
            print(f"   ❌ Error deleting {file_key}: {e}")
    
    return deleted_count


def cleanup_test_folders(auto_confirm=False):
    """
    Clean up common test folders
    """
    print("\n" + "=" * 60)
    print("🧹 CLEANUP TEST FOLDERS")
    print("=" * 60)
    
    # Common test folder prefixes
    test_folders = [
        "Test_Uploads/",
        "Suburbs_Top_Agents/",
        "Suburbs_Top_Rental_Agencies/",
        "Commission_Rate/",
        "Reports/",
        # Root level test files (no folder)
        ""
    ]
    
    total_deleted = 0
    
    for folder in test_folders:
        if folder == "":
            # Skip root for now, handle separately
            continue
        
        deleted = delete_files_in_folder(folder, auto_confirm)
        total_deleted += deleted
    
    return total_deleted


def cleanup_all_files(auto_confirm=False):
    """
    Delete ALL files in the bucket
    WARNING: This deletes everything!
    """
    print("\n" + "=" * 60)
    print("⚠️  DELETE ALL FILES IN BUCKET")
    print("=" * 60)
    
    all_files = backblaze_service.list_files()
    
    if not all_files:
        print("\n✅ Bucket is already empty!")
        return 0
    
    print(f"\n⚠️  WARNING: This will delete ALL {len(all_files)} files in the bucket!")
    print("\nFiles to be deleted:")
    for f in all_files[:10]:  # Show first 10
        print(f"  - {f}")
    if len(all_files) > 10:
        print(f"  ... and {len(all_files) - 10} more files")
    
    if not auto_confirm:
        print("\n⚠️  THIS ACTION CANNOT BE UNDONE!")
        response = input("\nAre you ABSOLUTELY sure? Type 'DELETE ALL' to confirm: ")
        if response != 'DELETE ALL':
            print("\n✅ Cancelled - no files deleted")
            return 0
    
    # Delete all files (including all versions)
    deleted_count = 0
    failed_count = 0
    
    print("\n🗑️  Deleting files (including all versions)...")
    for file_key in all_files:
        try:
            versions_deleted = backblaze_service.delete_all_versions(file_key)
            if versions_deleted > 0:
                print(f"  ✓ Deleted: {file_key} ({versions_deleted} version(s))")
                deleted_count += 1
            else:
                print(f"  ❌ Failed: {file_key}")
                failed_count += 1
        except Exception as e:
            print(f"  ❌ Error deleting {file_key}: {e}")
            failed_count += 1
    
    print(f"\n{'=' * 60}")
    print(f"✅ Deleted: {deleted_count} files")
    if failed_count > 0:
        print(f"❌ Failed: {failed_count} files")
    print(f"{'=' * 60}")
    
    return deleted_count


def cleanup_specific_files(pattern):
    """
    Delete files matching a specific pattern
    """
    print(f"\n🔍 Searching for files matching: {pattern}")
    
    all_files = backblaze_service.list_files()
    matching_files = [f for f in all_files if pattern in f]
    
    if not matching_files:
        print(f"✅ No files found matching '{pattern}'")
        return 0
    
    print(f"\nFound {len(matching_files)} matching files:")
    for f in matching_files:
        print(f"  - {f}")
    
    response = input(f"\nDelete these {len(matching_files)} files? (y/n): ").lower()
    if response != 'y':
        print("⏭️  Cancelled")
        return 0
    
    deleted_count = 0
    for file_key in matching_files:
        try:
            versions_deleted = backblaze_service.delete_all_versions(file_key)
            if versions_deleted > 0:
                print(f"  ✓ Deleted: {file_key} ({versions_deleted} version(s))")
                deleted_count += 1
            else:
                print(f"  ❌ Failed: {file_key}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    return deleted_count


def interactive_cleanup():
    """
    Interactive cleanup menu
    """
    print("\n" + "=" * 60)
    print("🧹 BACKBLAZE B2 CLEANUP TOOL")
    print("=" * 60)
    
    # Verify connection first
    if not backblaze_service.verify_connection():
        print("\n❌ Cannot connect to Backblaze B2")
        print("   Check your .env credentials and bucket configuration")
        return
    
    bucket_name = os.getenv("B2_BUCKET_NAME", "unknown")
    print(f"\n📦 Bucket: {bucket_name}")
    
    while True:
        print("\n" + "-" * 60)
        print("Choose an option:")
        print("-" * 60)
        print("1. List all files in bucket")
        print("2. Clean up test folders (Test_Uploads, Suburbs_*, etc.)")
        print("3. Delete ALL files in bucket (⚠️  DANGEROUS)")
        print("4. Delete files by pattern (e.g., 'test_report')")
        print("5. Delete specific folder")
        print("0. Exit")
        print("-" * 60)
        
        choice = input("\nEnter your choice (0-5): ").strip()
        
        if choice == "0":
            print("\n👋 Cleanup tool closed")
            break
        
        elif choice == "1":
            list_all_files()
        
        elif choice == "2":
            total = cleanup_test_folders(auto_confirm=False)
            print(f"\n✅ Cleanup complete! Deleted {total} files")
        
        elif choice == "3":
            cleanup_all_files(auto_confirm=False)
        
        elif choice == "4":
            pattern = input("\nEnter pattern to search for (e.g., 'test_report'): ").strip()
            if pattern:
                cleanup_specific_files(pattern)
            else:
                print("❌ Pattern cannot be empty")
        
        elif choice == "5":
            folder = input("\nEnter folder path (e.g., 'Test_Uploads/'): ").strip()
            if folder:
                if not folder.endswith('/'):
                    folder += '/'
                deleted = delete_files_in_folder(folder, auto_confirm=False)
                print(f"\n✅ Deleted {deleted} files from {folder}")
            else:
                print("❌ Folder path cannot be empty")
        
        else:
            print("❌ Invalid choice. Please try again.")


def quick_cleanup_tests():
    """
    Quick cleanup of common test files (non-interactive)
    """
    print("\n" + "=" * 60)
    print("⚡ QUICK CLEANUP - TEST FILES")
    print("=" * 60)
    
    # Verify connection
    if not backblaze_service.verify_connection():
        print("\n❌ Cannot connect to Backblaze B2")
        return False
    
    bucket_name = os.getenv("B2_BUCKET_NAME", "unknown")
    print(f"\n📦 Bucket: {bucket_name}")
    
    # List all files first
    all_files = list_all_files()
    
    if not all_files:
        return True
    
    print("\n⚠️  This will delete test files in these folders:")
    print("   • Test_Uploads/")
    print("   • Suburbs_Top_Agents/")
    print("   • Suburbs_Top_Rental_Agencies/")
    print("   • Commission_Rate/")
    print("   • Reports/")
    
    response = input("\nProceed with cleanup? (y/n): ").lower()
    if response != 'y':
        print("\n✅ Cancelled")
        return False
    
    total = cleanup_test_folders(auto_confirm=True)
    
    print("\n" + "=" * 60)
    print(f"✅ CLEANUP COMPLETE!")
    print(f"   Deleted {total} test files")
    print("=" * 60)
    
    return True


def complete_cleanup():
    """
    COMPLETE cleanup - deletes ALL versions properly
    This is what you should use!
    """
    print("\n" + "=" * 60)
    print("🗑️  COMPLETE CLEANUP - DELETE ALL VERSIONS")
    print("=" * 60)
    print("\nThis will permanently delete ALL files and ALL their versions")
    print("from your Backblaze bucket (including hidden delete markers).\n")
    
    bucket_name = os.getenv("B2_BUCKET_NAME", "unknown")
    print(f"📦 Bucket: {bucket_name}\n")
    
    # Verify connection
    if not backblaze_service.verify_connection():
        print("❌ Cannot connect to Backblaze B2")
        return False
    
    # Get all versions
    print("🔍 Scanning for all object versions...")
    all_versions = backblaze_service.list_all_versions()
    
    if not all_versions:
        print("\n✅ Bucket is already completely empty!")
        return True
    
    # Group by key
    versions_by_key = {}
    for key, version_id in all_versions:
        if key not in versions_by_key:
            versions_by_key[key] = []
        versions_by_key[key].append(version_id)
    
    print(f"\n⚠️  FOUND {len(all_versions)} OBJECT VERSIONS:\n")
    for i, (key, version_ids) in enumerate(list(versions_by_key.items())[:10], 1):
        print(f"  {i}. {key} ({len(version_ids)} version(s))")
    
    if len(versions_by_key) > 10:
        print(f"  ... and {len(versions_by_key) - 10} more files")
    
    print(f"\n📊 Total: {len(versions_by_key)} files, {len(all_versions)} versions")
    
    # Confirm
    response = input("\nType 'DELETE ALL' to permanently delete everything: ")
    if response != 'DELETE ALL':
        print("\n✅ Cancelled")
        return False
    
    # Delete all versions
    print("\n🗑️  Deleting all versions...")
    deleted = 0
    failed = 0
    
    for key, version_ids in versions_by_key.items():
        for version_id in version_ids:
            try:
                resp = backblaze_service.s3_client.delete_object(
                    Bucket=backblaze_service.bucket_name,
                    Key=key,
                    VersionId=version_id
                )
                if resp.get('ResponseMetadata', {}).get('HTTPStatusCode') in [200, 204]:
                    deleted += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"  ❌ Error deleting {key}: {e}")
                failed += 1
    
    print(f"\n✅ Deleted {deleted} versions")
    if failed > 0:
        print(f"❌ Failed: {failed}")
    
    # Verify
    verify_truly_empty()
    
    print("\n💡 NOTE: Backblaze Web UI may take a few minutes to refresh.")
    print("   Press Ctrl+F5 in your browser to force refresh the page.\n")
    
    return deleted > 0


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Backblaze B2 Cleanup - THE ONLY CLEANUP SCRIPT',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_cleanup.py              # Interactive menu
  python test_cleanup.py --complete   # Delete ALL versions (recommended!)
  python test_cleanup.py --quick      # Delete test folders only
  python test_cleanup.py --list       # Just list files
        """
    )
    parser.add_argument('--complete', action='store_true',
                       help='Complete cleanup - delete ALL versions (recommended!)')
    parser.add_argument('--quick', action='store_true',
                       help='Quick cleanup of test folders')
    parser.add_argument('--all', action='store_true',
                       help='Delete ALL files (may not work if versioning enabled)')
    parser.add_argument('--list', action='store_true',
                       help='Just list all files')
    
    args = parser.parse_args()
    
    if args.complete:
        # RECOMMENDED: Complete cleanup with version deletion
        complete_cleanup()
    elif args.list:
        # Just list files
        list_all_files()
        verify_truly_empty()
    elif args.quick:
        # Quick cleanup
        quick_cleanup_tests()
        verify_truly_empty()
    elif args.all:
        # Delete everything (old method)
        cleanup_all_files(auto_confirm=False)
        verify_truly_empty()
    else:
        # Interactive mode - add complete cleanup option
        print("\n" + "=" * 60)
        print("🧹 BACKBLAZE B2 CLEANUP")
        print("=" * 60)
        print("\n⭐ RECOMMENDED: Use --complete flag for proper cleanup")
        print("   python test_cleanup.py --complete")
        print("\nOr use interactive mode:\n")
        interactive_cleanup()
