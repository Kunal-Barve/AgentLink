"""
Dropbox to Backblaze Migration Tool
Interactive tool to migrate files from Dropbox to Backblaze B2
"""
import os
import sys
from pathlib import Path
import asyncio

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.dropbox_service import dropbox_service
from app.services.backblaze_service import upload_to_backblaze
from dotenv import load_dotenv
import tempfile
import dropbox

# Load environment variables
load_dotenv()


def list_dropbox_folders(path=""):
    """
    List all folders in Dropbox at given path
    
    Args:
        path: Dropbox path (empty string for root)
    
    Returns:
        list: List of folder paths
    """
    print(f"\n🔍 Scanning Dropbox folders{' in ' + path if path else ' (root)'}...")
    
    try:
        # List all entries in the path
        result = dropbox_service.dbx.files_list_folder(path)
        
        folders = []
        files_count = {}
        
        # Get all entries
        while True:
            for entry in result.entries:
                if isinstance(entry, dropbox.files.FolderMetadata):
                    folder_path = entry.path_display
                    folders.append(folder_path)
                    
                    # Count files in this folder
                    try:
                        folder_contents = dropbox_service.dbx.files_list_folder(folder_path)
                        file_count = sum(1 for e in folder_contents.entries 
                                       if isinstance(e, dropbox.files.FileMetadata))
                        files_count[folder_path] = file_count
                    except Exception:
                        files_count[folder_path] = 0
            
            if not result.has_more:
                break
            result = dropbox_service.dbx.files_list_folder_continue(result.cursor)
        
        return folders, files_count
    
    except Exception as e:
        print(f"❌ Error listing Dropbox folders: {e}")
        return [], {}


def list_files_in_folder(folder_path):
    """
    List all files in a specific Dropbox folder
    
    Args:
        folder_path: Dropbox folder path
    
    Returns:
        list: List of file metadata
    """
    try:
        result = dropbox_service.dbx.files_list_folder(folder_path)
        files = []
        
        while True:
            for entry in result.entries:
                if isinstance(entry, dropbox.files.FileMetadata):
                    files.append({
                        'path': entry.path_display,
                        'name': entry.name,
                        'size': entry.size,
                        'modified': entry.client_modified
                    })
            
            if not result.has_more:
                break
            result = dropbox_service.dbx.files_list_folder_continue(result.cursor)
        
        return files
    
    except Exception as e:
        print(f"❌ Error listing files in {folder_path}: {e}")
        return []


async def download_and_upload_file(dropbox_path, backblaze_folder, filename, temp_dir):
    """
    Download file from Dropbox and upload to Backblaze
    
    Args:
        dropbox_path: Full path in Dropbox
        backblaze_folder: Target folder in Backblaze
        filename: Name of the file
        temp_dir: Temporary directory for downloads
    
    Returns:
        tuple: (success: bool, url: str or None)
    """
    try:
        # Download from Dropbox
        temp_file_path = os.path.join(temp_dir, filename)
        
        print(f"   ⬇️  Downloading: {filename}")
        metadata, response = dropbox_service.dbx.files_download(dropbox_path)
        
        with open(temp_file_path, 'wb') as f:
            f.write(response.content)
        
        print(f"   ⬆️  Uploading to Backblaze...")
        
        # Upload to Backblaze
        url = await upload_to_backblaze(
            file_path=temp_file_path,
            filename=filename,
            folder_path=backblaze_folder
        )
        
        # Clean up temp file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        if url and "mock" not in url.lower():
            print(f"   ✅ Success: {url}")
            return True, url
        else:
            print(f"   ❌ Upload failed")
            return False, None
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, None


async def migrate_folder(dropbox_folder, backblaze_folder=None):
    """
    Migrate entire folder from Dropbox to Backblaze
    
    Args:
        dropbox_folder: Source folder path in Dropbox
        backblaze_folder: Target folder in Backblaze (uses folder name if not specified)
    
    Returns:
        dict: Migration statistics
    """
    # Default backblaze folder to Dropbox folder name without leading slash
    if not backblaze_folder:
        # Convert "/Suburbs Top Agents" to "Suburbs_Top_Agents"
        backblaze_folder = dropbox_folder.strip('/').replace(' ', '_').replace('/', '_')
    
    print("\n" + "=" * 60)
    print(f"📁 MIGRATING FOLDER")
    print("=" * 60)
    print(f"Source:      {dropbox_folder}")
    print(f"Destination: {backblaze_folder}")
    print("=" * 60)
    
    # List files in folder
    print("\n📋 Scanning files...")
    files = list_files_in_folder(dropbox_folder)
    
    if not files:
        print("⚠️  No files found in this folder")
        return {'total': 0, 'success': 0, 'failed': 0}
    
    print(f"Found {len(files)} files\n")
    
    # Show files
    total_size = sum(f['size'] for f in files)
    print("Files to migrate:")
    for i, f in enumerate(files[:10], 1):
        size_mb = f['size'] / (1024 * 1024)
        print(f"  {i}. {f['name']} ({size_mb:.2f} MB)")
    
    if len(files) > 10:
        print(f"  ... and {len(files) - 10} more files")
    
    print(f"\nTotal size: {total_size / (1024 * 1024):.2f} MB")
    
    # Confirm
    response = input("\nProceed with migration? (y/n): ").lower()
    if response != 'y':
        print("❌ Cancelled")
        return {'total': 0, 'success': 0, 'failed': 0}
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    print(f"\n📦 Starting migration...")
    print(f"Temp directory: {temp_dir}\n")
    
    stats = {'total': len(files), 'success': 0, 'failed': 0, 'urls': []}
    
    # Migrate each file
    for i, file_info in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}] {file_info['name']}")
        
        success, url = await download_and_upload_file(
            dropbox_path=file_info['path'],
            backblaze_folder=backblaze_folder,
            filename=file_info['name'],
            temp_dir=temp_dir
        )
        
        if success:
            stats['success'] += 1
            stats['urls'].append(url)
        else:
            stats['failed'] += 1
    
    # Clean up temp directory
    try:
        os.rmdir(temp_dir)
    except:
        pass
    
    return stats


def main():
    """
    Main interactive migration tool
    """
    print("=" * 60)
    print("🔄 DROPBOX TO BACKBLAZE MIGRATION TOOL")
    print("=" * 60)
    
    # Verify Dropbox connection
    if not dropbox_service.dbx:
        print("\n❌ Dropbox not connected!")
        print("   Check your DROPBOX_ACCESS_TOKEN in .env")
        return
    
    print("\n✅ Dropbox connected")
    
    # List folders
    folders, files_count = list_dropbox_folders()
    
    if not folders:
        print("\n⚠️  No folders found in Dropbox")
        return
    
    print(f"\n📁 Found {len(folders)} folders in Dropbox:\n")
    
    # Display folders with selection
    for i, folder in enumerate(folders, 1):
        file_count = files_count.get(folder, 0)
        print(f"  {i}. {folder} ({file_count} files)")
    
    print("\n" + "=" * 60)
    print("SELECT FOLDERS TO MIGRATE")
    print("=" * 60)
    print("Options:")
    print("  • Enter folder numbers (e.g., 1,3,5)")
    print("  • Enter 'all' to migrate all folders")
    print("  • Enter 'quit' to exit")
    print()
    
    selection = input("Your selection: ").strip().lower()
    
    if selection == 'quit':
        print("👋 Cancelled")
        return
    
    # Parse selection
    selected_folders = []
    
    if selection == 'all':
        selected_folders = folders
    else:
        try:
            indices = [int(x.strip()) for x in selection.split(',')]
            selected_folders = [folders[i-1] for i in indices if 1 <= i <= len(folders)]
        except (ValueError, IndexError):
            print("❌ Invalid selection")
            return
    
    if not selected_folders:
        print("⚠️  No folders selected")
        return
    
    print(f"\n✅ Selected {len(selected_folders)} folders:\n")
    for folder in selected_folders:
        print(f"  • {folder}")
    
    # Confirm
    print()
    response = input("Start migration? (y/n): ").lower()
    if response != 'y':
        print("❌ Cancelled")
        return
    
    # Migrate each folder
    total_stats = {'total': 0, 'success': 0, 'failed': 0}
    
    for folder in selected_folders:
        stats = asyncio.run(migrate_folder(folder))
        total_stats['total'] += stats['total']
        total_stats['success'] += stats['success']
        total_stats['failed'] += stats['failed']
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 MIGRATION COMPLETE")
    print("=" * 60)
    print(f"Folders migrated:  {len(selected_folders)}")
    print(f"Total files:       {total_stats['total']}")
    print(f"✅ Successful:     {total_stats['success']}")
    print(f"❌ Failed:         {total_stats['failed']}")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
