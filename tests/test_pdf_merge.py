"""
PDF Merge Test Script
Tests merging multiple PDFs in a specific order using pypdf library

Library: pypdf (successor to PyPDF2)
- Actively maintained
- Pure Python
- Simple API for merging
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    print("❌ pypdf not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pypdf"])
    from pypdf import PdfReader, PdfWriter


def get_pdf_info(pdf_path):
    """Get basic info about a PDF file"""
    try:
        reader = PdfReader(pdf_path)
        return {
            'pages': len(reader.pages),
            'size_mb': os.path.getsize(pdf_path) / (1024 * 1024)
        }
    except Exception as e:
        return {'error': str(e)}


def merge_pdfs(pdf_files, output_path):
    """
    Merge multiple PDF files into one
    
    Args:
        pdf_files: List of PDF file paths in order
        output_path: Path for the merged output PDF
    
    Returns:
        bool: True if successful, False otherwise
    """
    print("\n" + "=" * 60)
    print("📄 PDF MERGE OPERATION")
    print("=" * 60)
    
    # Verify all files exist
    print("\n📋 Checking input files...")
    total_pages = 0
    total_size = 0
    
    for i, pdf_path in enumerate(pdf_files, 1):
        if not os.path.exists(pdf_path):
            print(f"   ❌ [{i}] File not found: {pdf_path}")
            return False
        
        info = get_pdf_info(pdf_path)
        if 'error' in info:
            print(f"   ❌ [{i}] Error reading: {os.path.basename(pdf_path)} - {info['error']}")
            return False
        
        total_pages += info['pages']
        total_size += info['size_mb']
        print(f"   ✅ [{i}] {os.path.basename(pdf_path)}")
        print(f"       Pages: {info['pages']}, Size: {info['size_mb']:.2f} MB")
    
    print(f"\n📊 Total: {len(pdf_files)} files, {total_pages} pages, {total_size:.2f} MB")
    
    # Merge PDFs
    print("\n🔄 Merging PDFs...")
    
    try:
        writer = PdfWriter()
        
        for pdf_path in pdf_files:
            print(f"   Adding: {os.path.basename(pdf_path)}")
            reader = PdfReader(pdf_path)
            for page in reader.pages:
                writer.add_page(page)
        
        # Write output
        print(f"\n💾 Writing merged PDF to: {output_path}")
        with open(output_path, "wb") as output_file:
            writer.write(output_file)
        
        # Verify output
        if os.path.exists(output_path):
            output_info = get_pdf_info(output_path)
            print("\n" + "=" * 60)
            print("✅ MERGE SUCCESSFUL!")
            print("=" * 60)
            print(f"   Output: {output_path}")
            print(f"   Pages: {output_info['pages']}")
            print(f"   Size: {output_info['size_mb']:.2f} MB")
            print("=" * 60)
            return True
        else:
            print("❌ Output file was not created")
            return False
            
    except Exception as e:
        print(f"\n❌ Merge failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """
    Main test function - merge the 4 PDFs in specified order
    """
    print("=" * 60)
    print("🧪 PDF MERGE TEST")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Define paths
    test_pdfs_dir = Path(__file__).parent / "test_pdfs"
    output_dir = Path(__file__).parent / "test_pdfs" / "output"
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)
    
    # Define PDFs in the exact order specified
    # 1. sales.pdf
    # 2. Kallangur_Top_Agents
    # 3. Kallangur_Commission
    # 4. Next_and_final_step (using Commission_and_Marketing.pdf as placeholder)
    
    pdf_files = [
        test_pdfs_dir / "Sales.pdf",
        test_pdfs_dir / "Kallangur_Top_Agents_5b305bd3-a91a-4679-a45a-25d36f8857aa.pdf",
        test_pdfs_dir / "Kallangur_Commission_5b305bd3-a91a-4679-a45a-25d36f8857aa.pdf",
        test_pdfs_dir / "Commission_and_Marketing.pdf",  # Using as Next_and_final_step
    ]
    
    print("\n📁 Test PDFs Directory:", test_pdfs_dir)
    print("\n📋 Merge Order:")
    for i, pdf in enumerate(pdf_files, 1):
        print(f"   {i}. {pdf.name}")
    
    # Output file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f"merged_output_{timestamp}.pdf"
    
    # Perform merge
    success = merge_pdfs(
        pdf_files=[str(p) for p in pdf_files],
        output_path=str(output_file)
    )
    
    if success:
        print(f"\n🎉 Test PASSED!")
        print(f"   Open the merged PDF at:")
        print(f"   {output_file}")
    else:
        print(f"\n❌ Test FAILED!")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
