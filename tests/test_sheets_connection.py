"""
Google Sheets Connection Test Script

Tests the connection to Google Sheets API and reads sample property data.

Usage:
    python test_sheets_connection.py
"""

import sys
import os

try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    print("❌ Missing required packages!")
    print("\nPlease install:")
    print("  pip install gspread google-auth")
    sys.exit(1)


def test_connection():
    """Test Google Sheets API connection"""
    
    print("=" * 70)
    print("🔍 GOOGLE SHEETS API CONNECTION TEST")
    print("=" * 70)
    
    # Check credentials file exists
    creds_path = 'credentials/google_sheets_service_account.json'
    alt_creds_path = os.path.join(os.getenv('APPDATA', ''), 'gspread', 'service_account.json')
    
    print("\n📁 Step 1: Checking for credentials file...")
    
    if os.path.exists(creds_path):
        print(f"   ✅ Found: {creds_path}")
        use_creds = creds_path
    elif os.path.exists(alt_creds_path):
        print(f"   ✅ Found: {alt_creds_path}")
        use_creds = alt_creds_path
    else:
        print(f"   ❌ Not found: {creds_path}")
        print(f"   ❌ Not found: {alt_creds_path}")
        print("\n⚠️  Please follow the setup guide:")
        print("   docs/GOOGLE_SHEETS_API_SETUP.md")
        return False
    
    try:
        # Load credentials
        print("\n🔑 Step 2: Loading credentials...")
        gc = gspread.service_account(filename=use_creds)
        print("   ✅ Credentials loaded successfully")
        
        # Display service account email
        with open(use_creds, 'r') as f:
            import json
            creds_data = json.load(f)
            service_email = creds_data.get('client_email', 'Unknown')
            print(f"   📧 Service account: {service_email}")
        
        # Get sheet ID from user
        print("\n📊 Step 3: Connecting to Google Sheet...")
        print("\n💡 How to get Sheet ID:")
        print("   From URL: https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit")
        print("   Copy the SHEET_ID_HERE part")
        
        sheet_id = input("\n🔗 Enter Google Sheet ID: ").strip()
        
        if not sheet_id:
            print("   ❌ No sheet ID provided")
            return False
        
        print(f"\n   Connecting to sheet: {sheet_id[:20]}...")
        sheet = gc.open_by_key(sheet_id)
        print(f"   ✅ Sheet opened: '{sheet.title}'")
        
        # Get first worksheet
        print("\n📄 Step 4: Reading worksheet...")
        worksheet = sheet.sheet1
        print(f"   ✅ Worksheet: '{worksheet.title}'")
        print(f"   ✅ Total rows: {worksheet.row_count}")
        print(f"   ✅ Total columns: {worksheet.col_count}")
        
        # Read sample data
        print("\n📋 Step 5: Reading sample data...")
        all_data = worksheet.get_all_values()
        
        if not all_data:
            print("   ⚠️  Sheet is empty")
            return False
        
        # Display headers
        headers = all_data[0]
        print(f"   ✅ Headers ({len(headers)} columns):")
        for i, header in enumerate(headers, 1):
            print(f"      {i}. {header}")
        
        # Display first 3 data rows
        print(f"\n   📊 First 3 data rows:")
        for i, row in enumerate(all_data[1:4], 1):
            print(f"\n   Row {i}:")
            for header, value in zip(headers, row):
                if value:  # Only show non-empty values
                    print(f"      {header}: {value}")
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        
        # Additional info
        print("\n💡 Next Steps:")
        print("   1. Verify the data looks correct")
        print("   2. Check if 'address', 'suburb', 'state' columns exist")
        print("   3. Ready to use this sheet in apify_scraper_testing.py")
        
        print(f"\n📝 Sheet ID for testing: {sheet_id}")
        
        return True
        
    except gspread.exceptions.SpreadsheetNotFound:
        print("\n❌ ERROR: Spreadsheet not found!")
        print("\n⚠️  Possible reasons:")
        print("   1. Sheet ID is incorrect")
        print("   2. Service account doesn't have access to the sheet")
        print("\n✅ To fix:")
        print(f"   1. Open the Google Sheet")
        print(f"   2. Click 'Share' button")
        print(f"   3. Add this email with 'Viewer' permission:")
        print(f"      {service_email}")
        print(f"   4. Uncheck 'Notify people'")
        print(f"   5. Click 'Share'")
        return False
        
    except gspread.exceptions.APIError as e:
        print(f"\n❌ API ERROR: {e}")
        print("\n⚠️  Possible reasons:")
        print("   1. Google Sheets API not enabled in Google Cloud Project")
        print("   2. Rate limit exceeded")
        print("   3. Invalid credentials")
        print("\n✅ To fix:")
        print("   1. Go to: https://console.cloud.google.com/apis/library")
        print("   2. Search 'Google Sheets API'")
        print("   3. Click 'ENABLE'")
        return False
        
    except json.JSONDecodeError:
        print(f"\n❌ ERROR: Invalid credentials file")
        print("   The JSON file is corrupted or invalid")
        return False
        
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        print(f"\n   Error type: {type(e).__name__}")
        return False


def quick_test_with_id(sheet_id: str):
    """Quick test with provided sheet ID"""
    creds_path = 'credentials/google_sheets_service_account.json'
    
    try:
        gc = gspread.service_account(filename=creds_path)
        sheet = gc.open_by_key(sheet_id)
        worksheet = sheet.sheet1
        data = worksheet.get_all_values()
        
        print(f"✅ Connected to: {sheet.title}")
        print(f"✅ Rows: {len(data)}")
        print(f"✅ Headers: {data[0]}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    # Check if sheet ID provided as argument
    if len(sys.argv) > 1:
        sheet_id = sys.argv[1]
        print(f"Testing with provided Sheet ID: {sheet_id[:20]}...")
        success = quick_test_with_id(sheet_id)
    else:
        success = test_connection()
    
    sys.exit(0 if success else 1)
