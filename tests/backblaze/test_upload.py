"""
Test Backblaze B2 File Upload
Test uploading files and folder structure
"""
import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.backblaze_service import upload_to_backblaze, backblaze_service
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def create_test_pdf(filename="test_report.pdf", custom_text=None):
    """Create a simple test PDF file"""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    
    # Create temp directory if it doesn't exist
    temp_dir = Path(__file__).parent / "temp"
    temp_dir.mkdir(exist_ok=True)
    
    file_path = temp_dir / filename
    
    # Create PDF
    c = canvas.Canvas(str(file_path), pagesize=letter)
    c.drawString(100, 750, custom_text or "Test PDF for Backblaze B2 Upload")
    c.drawString(100, 730, f"Generated: {datetime.now()}")
    c.drawString(100, 710, f"File: {filename}")
    c.save()
    
    print(f"✓ Created test PDF: {file_path}")
    return str(file_path)


async def upload_single_pdf_and_get_url(folder="Test_Uploads", filename=None):
    """
    SIMPLE TEST: Upload a single PDF and get the public URL
    
    This is the easiest way to test Backblaze upload and get a public URL.
    Perfect for testing with make.com or verifying public bucket access.
    
    Args:
        folder: Folder path in bucket (e.g., "Test_Uploads" or "Suburbs_Top_Agents")
        filename: Custom filename (optional, auto-generated if not provided)
    
    Returns:
        str: Public URL of the uploaded PDF
    """
    print("\n" + "=" * 60)
    print("🚀 SINGLE PDF UPLOAD TEST - GET PUBLIC URL")
    print("=" * 60)
    
    # Generate filename if not provided
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_report_{timestamp}.pdf"
    
    print(f"\n📋 Configuration:")
    print(f"   Folder: {folder}")
    print(f"   Filename: {filename}")
    
    # Create dummy PDF
    print(f"\n1️⃣  Creating dummy PDF...")
    test_file = create_test_pdf(
        filename=filename,
        custom_text="Backblaze B2 Public URL Test - This is a dummy PDF"
    )
    
    try:
        # Upload to Backblaze
        print(f"\n2️⃣  Uploading to Backblaze B2...")
        print(f"   ⏳ Please wait...")
        
        url = await upload_to_backblaze(
            file_path=test_file,
            filename=filename,
            folder_path=folder
        )
        
        # Display results
        print(f"\n{'=' * 60}")
        if url and "mock" not in url.lower():
            print("✅ UPLOAD SUCCESSFUL!")
            print(f"{'=' * 60}")
            print(f"\n📎 PUBLIC URL:")
            print(f"   {url}")
            print(f"\n📁 Full Path in Bucket:")
            print(f"   {folder}/{filename}")
            print(f"\n💡 How to use:")
            print(f"   • Copy the URL above")
            print(f"   • Paste it in your browser to download the PDF")
            print(f"   • Use it in make.com for PDF merging")
            print(f"   • Share with anyone (public bucket)")
            print(f"\n{'=' * 60}")
            return url
        else:
            print("❌ UPLOAD FAILED")
            print(f"{'=' * 60}")
            print(f"   Received: {url}")
            print(f"   This looks like a mock URL - check your credentials")
            print(f"\n💡 Troubleshooting:")
            print(f"   1. Verify .env has correct B2_KEY_ID and B2_APPLICATION_KEY")
            print(f"   2. Check bucket name is correct")
            print(f"   3. Ensure bucket is PUBLIC")
            print(f"   4. Run: python tests/backblaze/test_connection.py")
            print(f"{'=' * 60}")
            return None
            
    except Exception as e:
        print(f"\n❌ ERROR DURING UPLOAD")
        print(f"{'=' * 60}")
        print(f"   {str(e)}")
        print(f"\n💡 Check your .env configuration and credentials")
        print(f"{'=' * 60}")
        return None
        
    finally:
        # Cleanup local file
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"\n🧹 Cleaned up local test file")


async def test_simple_upload():
    """Test simple file upload without folder"""
    print("\n" + "=" * 60)
    print("TEST 1: Simple Upload (No Folder)")
    print("=" * 60)
    
    # Create test file
    test_file = create_test_pdf("simple_test.pdf")
    
    try:
        # Upload
        print("\nUploading file...")
        url = await upload_to_backblaze(
            test_file,
            "simple_test.pdf",
            ""
        )
        
        if url and "mock" not in url.lower():
            print(f"✓ Upload successful!")
            print(f"  URL: {url}")
            return True
        else:
            print(f"❌ Upload failed or returned mock URL")
            return False
            
    except Exception as e:
        print(f"❌ Error during upload: {e}")
        return False
    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)


async def test_folder_upload():
    """Test upload with folder structure"""
    print("\n" + "=" * 60)
    print("TEST 2: Upload with Folder Structure")
    print("=" * 60)
    
    # Test different folder structures
    test_cases = [
        ("Suburbs_Top_Agents", "queenscliff_test.pdf"),
        ("Suburbs_Top_Rental_Agencies", "sydney_test.pdf"),
        ("Commission_Rate", "commission_test.pdf"),
        ("Reports/2024/Agents", "nested_test.pdf")  # Nested folders
    ]
    
    results = []
    
    for folder, filename in test_cases:
        print(f"\n📁 Testing: {folder}/{filename}")
        
        # Create test file
        test_file = create_test_pdf(filename)
        
        try:
            # Upload
            url = await upload_to_backblaze(test_file, filename, folder)
            
            if url and "mock" not in url.lower():
                print(f"  ✓ Success: {url}")
                results.append(True)
            else:
                print(f"  ❌ Failed or mock URL")
                results.append(False)
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results.append(False)
        finally:
            # Cleanup
            if os.path.exists(test_file):
                os.remove(test_file)
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"\n{'=' * 60}")
    print(f"Results: {success_count}/{total_count} uploads successful")
    print(f"{'=' * 60}")
    
    return all(results)


async def test_list_folders():
    """Test listing files in different folders"""
    print("\n" + "=" * 60)
    print("TEST 3: List Files by Folder")
    print("=" * 60)
    
    folders = [
        "Suburbs_Top_Agents",
        "Suburbs_Top_Rental_Agencies",
        "Commission_Rate"
    ]
    
    for folder in folders:
        print(f"\n📂 Listing files in: {folder}/")
        files = backblaze_service.list_files(prefix=folder + "/")
        
        if files:
            print(f"  Found {len(files)} files:")
            for f in files[:5]:  # Show first 5
                print(f"    - {f}")
        else:
            print(f"  No files found (or folder doesn't exist yet)")
    
    return True


async def run_all_tests():
    """Run all upload tests"""
    print("=" * 60)
    print("BACKBLAZE B2 UPLOAD TESTS")
    print("=" * 60)
    
    # Verify connection first
    print("\n0. Verifying Connection...")
    if not backblaze_service.verify_connection():
        print("❌ Connection failed. Please run test_connection.py first")
        return False
    print("✓ Connection verified")
    
    # Run tests
    test1 = await test_simple_upload()
    test2 = await test_folder_upload()
    test3 = await test_list_folders()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Simple Upload:        {'✓ PASSED' if test1 else '❌ FAILED'}")
    print(f"Folder Upload:        {'✓ PASSED' if test2 else '❌ FAILED'}")
    print(f"List Folders:         {'✓ PASSED' if test3 else '❌ FAILED'}")
    print("=" * 60)
    
    return test1 and test2 and test3


async def quick_upload_test():
    """
    Quick single PDF upload - just get a public URL!
    This is the simplest way to test Backblaze upload.
    """
    print("=" * 60)
    print("QUICK UPLOAD TEST")
    print("=" * 60)
    print("\nThis will upload a single dummy PDF and return the public URL.")
    print("Perfect for testing make.com integration!\n")
    
    # Upload to Test_Uploads folder by default
    url = await upload_single_pdf_and_get_url(
        folder="Test_Uploads",
        filename=None  # Auto-generate filename with timestamp
    )
    
    if url:
        print("\n✅ Test completed successfully!")
        print(f"\nYou can now:")
        print(f"  1. Open this URL in your browser to verify it works")
        print(f"  2. Use this URL in make.com to test PDF fetching")
        print(f"  3. Try different folder names if needed")
        return True
    else:
        print("\n❌ Test failed - check your configuration")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Backblaze B2 Upload Tests')
    parser.add_argument('--quick', action='store_true', 
                       help='Run quick single upload test (default)')
    parser.add_argument('--all', action='store_true', 
                       help='Run all comprehensive tests')
    parser.add_argument('--folder', type=str, default='Test_Uploads',
                       help='Folder path for quick test (default: Test_Uploads)')
    parser.add_argument('--filename', type=str, default=None,
                       help='Custom filename for quick test (optional)')
    
    args = parser.parse_args()
    
    # Default to quick test if no arguments
    if args.all:
        print("\n🔍 Running ALL comprehensive tests...\n")
        success = asyncio.run(run_all_tests())
    else:
        print("\n⚡ Running QUICK upload test...\n")
        if args.folder != 'Test_Uploads' or args.filename:
            # Custom folder/filename specified
            async def custom_quick_test():
                await upload_single_pdf_and_get_url(
                    folder=args.folder,
                    filename=args.filename
                )
            success = asyncio.run(custom_quick_test())
        else:
            success = asyncio.run(quick_upload_test())
    
    sys.exit(0 if success else 1)
