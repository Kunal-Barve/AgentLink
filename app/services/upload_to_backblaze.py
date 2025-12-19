"""
Upload to Backblaze B2 Service
Handles file uploads to Backblaze B2 with automatic folder creation

This module provides:
- Folder existence checking
- Automatic folder creation (via placeholder files)
- File upload functionality
- PDF merging for completed reports
"""
import os
import logging
import tempfile
from pathlib import Path

from app.services.backblaze_service import backblaze_service, upload_to_backblaze

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    PdfReader = None
    PdfWriter = None

# Set up logger
logger = logging.getLogger("articflow.backblaze.upload")

# Required folders for the application
REQUIRED_FOLDERS = [
    "Commission_Rates",
    "Suburbs_Top_Agents",
    "Completed_Pdfs",
]


def check_folder_exists(folder_name: str) -> bool:
    """
    Check if a folder (prefix) exists in Backblaze B2
    
    In S3/B2, folders don't really exist - they're just prefixes.
    A folder "exists" if there's at least one object with that prefix.
    
    Args:
        folder_name: Name of the folder to check
        
    Returns:
        bool: True if folder exists (has files), False otherwise
    """
    if not backblaze_service.s3_client:
        logger.error("Cannot check folder: S3 client not initialized")
        return False
    
    try:
        # Ensure folder name ends with /
        prefix = folder_name.rstrip('/') + '/'
        
        response = backblaze_service.s3_client.list_objects_v2(
            Bucket=backblaze_service.bucket_name,
            Prefix=prefix,
            MaxKeys=1
        )
        
        exists = 'Contents' in response and len(response['Contents']) > 0
        logger.info(f"Folder '{folder_name}': {'exists' if exists else 'does not exist'}")
        return exists
        
    except Exception as e:
        logger.error(f"Error checking folder '{folder_name}': {e}")
        return False


def create_folder(folder_name: str) -> bool:
    """
    Create a folder in Backblaze B2
    
    In S3/B2, we create a folder by uploading a zero-byte placeholder file
    with the folder prefix. This makes the folder visible in the B2 console.
    
    Args:
        folder_name: Name of the folder to create
        
    Returns:
        bool: True if created successfully, False otherwise
    """
    if not backblaze_service.s3_client:
        logger.error("Cannot create folder: S3 client not initialized")
        return False
    
    try:
        # Create folder by uploading a placeholder file
        # The trailing slash indicates it's a folder
        folder_key = folder_name.rstrip('/') + '/'
        
        backblaze_service.s3_client.put_object(
            Bucket=backblaze_service.bucket_name,
            Key=folder_key,
            Body=b''
        )
        
        logger.info(f"✅ Created folder: {folder_name}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create folder '{folder_name}': {e}")
        return False


def ensure_folders_exist() -> dict:
    """
    Ensure all required folders exist in Backblaze B2
    Creates them if they don't exist.
    
    Returns:
        dict: Status of each folder {folder_name: 'exists'|'created'|'failed'}
    """
    logger.info("=" * 60)
    logger.info("🔍 Checking required Backblaze B2 folders...")
    logger.info("=" * 60)
    
    results = {}
    
    for folder in REQUIRED_FOLDERS:
        if check_folder_exists(folder):
            results[folder] = 'exists'
            logger.info(f"   ✅ {folder} - already exists")
        else:
            if create_folder(folder):
                results[folder] = 'created'
                logger.info(f"   📁 {folder} - created")
            else:
                results[folder] = 'failed'
                logger.error(f"   ❌ {folder} - failed to create")
    
    logger.info("=" * 60)
    return results


def list_folders() -> list:
    """
    List all top-level folders in the Backblaze B2 bucket
    
    Returns:
        list: List of folder names
    """
    if not backblaze_service.s3_client:
        logger.error("Cannot list folders: S3 client not initialized")
        return []
    
    try:
        response = backblaze_service.s3_client.list_objects_v2(
            Bucket=backblaze_service.bucket_name,
            Delimiter='/'
        )
        
        folders = []
        
        # Get common prefixes (folders)
        if 'CommonPrefixes' in response:
            for prefix in response['CommonPrefixes']:
                folder_name = prefix['Prefix'].rstrip('/')
                folders.append(folder_name)
        
        logger.info(f"Found {len(folders)} folders in bucket")
        return folders
        
    except Exception as e:
        logger.error(f"Error listing folders: {e}")
        return []


def get_folder_file_count(folder_name: str) -> int:
    """
    Get the number of files in a folder
    
    Args:
        folder_name: Name of the folder
        
    Returns:
        int: Number of files in the folder
    """
    if not backblaze_service.s3_client:
        return 0
    
    try:
        prefix = folder_name.rstrip('/') + '/'
        
        response = backblaze_service.s3_client.list_objects_v2(
            Bucket=backblaze_service.bucket_name,
            Prefix=prefix
        )
        
        count = 0
        if 'Contents' in response:
            # Don't count the folder placeholder itself
            count = sum(1 for obj in response['Contents'] if not obj['Key'].endswith('/'))
        
        return count
        
    except Exception as e:
        logger.error(f"Error counting files in '{folder_name}': {e}")
        return 0


# Static PDF paths for merging
STATIC_PDFS_DIR = Path(__file__).parent.parent / "assets" / "pdfs"
SALES_PDF = STATIC_PDFS_DIR / "Sales.pdf"
COMMISSION_MARKETING_PDF = STATIC_PDFS_DIR / "Commission_and_Marketing.pdf"


def merge_pdfs_to_completed(pdf_files: list, output_path: str) -> bool:
    """
    Merge multiple PDF files into one completed PDF
    
    Args:
        pdf_files: List of PDF file paths in order to merge
        output_path: Path for the merged output PDF
    
    Returns:
        bool: True if successful, False otherwise
    """
    if PdfReader is None or PdfWriter is None:
        logger.error("pypdf library not installed. Cannot merge PDFs.")
        return False
    
    try:
        writer = PdfWriter()
        
        for pdf_path in pdf_files:
            if not os.path.exists(pdf_path):
                logger.warning(f"PDF file not found, skipping: {pdf_path}")
                continue
            
            logger.info(f"Adding to merge: {os.path.basename(pdf_path)}")
            reader = PdfReader(pdf_path)
            for page in reader.pages:
                writer.add_page(page)
        
        # Write output
        with open(output_path, "wb") as output_file:
            writer.write(output_file)
        
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path) / (1024 * 1024)
            logger.info(f"✅ Merged PDF created: {output_path} ({file_size:.2f} MB)")
            return True
        else:
            logger.error("Merged PDF was not created")
            return False
            
    except Exception as e:
        logger.error(f"Error merging PDFs: {e}", exc_info=True)
        return False


async def create_and_upload_completed_pdf(
    agent_report_path: str,
    commission_report_path: str,
    suburb: str,
    job_id: str
) -> tuple:
    """
    Create a completed PDF by merging:
    1. Sales.pdf (static)
    2. Agent Report PDF (dynamic)
    3. Commission Report PDF (dynamic)
    4. Commission_and_Marketing.pdf (static)
    
    Then upload to Backblaze B2 Completed_Pdfs folder.
    
    Args:
        agent_report_path: Path to the generated agent report PDF
        commission_report_path: Path to the generated commission report PDF
        suburb: Suburb name for the filename
        job_id: Job ID for unique filename
    
    Returns:
        tuple: (completed_pdf_url, completed_filename) or (None, None) if failed
    """
    logger.info(f"Creating completed PDF for {suburb} (job: {job_id})")
    
    # Check if static PDFs exist
    if not SALES_PDF.exists():
        logger.error(f"Static PDF not found: {SALES_PDF}")
        return None, None
    
    if not COMMISSION_MARKETING_PDF.exists():
        logger.error(f"Static PDF not found: {COMMISSION_MARKETING_PDF}")
        return None, None
    
    # Build list of PDFs to merge in order
    pdfs_to_merge = []
    
    # 1. Sales.pdf (static)
    pdfs_to_merge.append(str(SALES_PDF))
    
    # 2. Agent Report PDF (dynamic)
    if agent_report_path and os.path.exists(agent_report_path):
        pdfs_to_merge.append(agent_report_path)
    else:
        logger.warning(f"Agent report PDF not found: {agent_report_path}")
    
    # 3. Commission Report PDF (dynamic)
    if commission_report_path and os.path.exists(commission_report_path):
        pdfs_to_merge.append(commission_report_path)
    else:
        logger.warning(f"Commission report PDF not found: {commission_report_path}")
    
    # 4. Commission_and_Marketing.pdf (static)
    pdfs_to_merge.append(str(COMMISSION_MARKETING_PDF))
    
    logger.info(f"Merging {len(pdfs_to_merge)} PDFs...")
    
    # Create temp file for merged PDF
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
        merged_pdf_path = tmp_file.name
    
    try:
        # Merge PDFs
        success = merge_pdfs_to_completed(pdfs_to_merge, merged_pdf_path)
        
        if not success:
            logger.error("Failed to merge PDFs")
            return None, None
        
        # Upload to Backblaze
        # Format suburb name: replace spaces with underscores
        suburb_formatted = suburb.replace(" ", "_")
        filename = f"AgentLink_{suburb_formatted}_Agent_Suburb_Report.pdf"
        folder_path = "Completed_Pdfs"
        
        logger.info(f"Uploading completed PDF: {filename}")
        completed_url = await upload_to_backblaze(merged_pdf_path, filename, folder_path=folder_path)
        
        logger.info(f"✅ Completed PDF uploaded: {completed_url}")
        return completed_url, filename
        
    except Exception as e:
        logger.error(f"Error creating completed PDF: {e}", exc_info=True)
        return None, None
        
    finally:
        # Clean up temp file
        if os.path.exists(merged_pdf_path):
            os.remove(merged_pdf_path)
            logger.debug(f"Cleaned up temp file: {merged_pdf_path}")


# Run folder check on module import if USE_BACKBLAZE is enabled
if os.getenv("USE_BACKBLAZE", "false").lower() == "true":
    ensure_folders_exist()
