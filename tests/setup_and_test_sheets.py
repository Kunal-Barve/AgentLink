"""
Quick Setup and Test Script for Google Sheets API

This script will:
1. Check for required packages
2. Locate your credentials file
3. Test connection to Google Sheets

Run: python setup_and_test_sheets.py
"""

import sys
import os
import json

print("=" * 70)
print("🚀 GOOGLE SHEETS API - QUICK SETUP & TEST")
print("=" * 70)

# Step 1: Check required packages
print("\n📦 Step 1: Checking required packages...")

try:
    import gspread
    print("   ✅ gspread installed")
except ImportError:
    print("   ❌ gspread not installed")
    print("   Run: pip install gspread")
    sys.exit(1)

try:
    from google.oauth2.service_account import Credentials
    print("   ✅ google-auth installed")
except ImportError:
    print("   ⚠️  google-auth not installed")
    print("   Installing now...")
    import subprocess
    result = subprocess.run([sys.executable, "-m", "pip", "install", "google-auth"], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        print("   ✅ google-auth installed successfully")
        from google.oauth2.service_account import Credentials
    else:
        print("   ❌ Failed to install google-auth")
        print("   Run manually: pip install google-auth")
        sys.exit(1)

# Step 2: Find credentials file
print("\n🔍 Step 2: Looking for credentials file...")

possible_locations = [
    "service-account-credentials.json",
    "credentials/service-account-credentials.json",
    os.path.join(os.path.expanduser("~"), "Downloads", "service-account-credentials.json"),
]

creds_file = None
for location in possible_locations:
    if os.path.exists(location):
        creds_file = location
        print(f"   ✅ Found: {location}")
        break

if not creds_file:
    print("   ❌ Credentials file not found!")
    print("\n   Looking for: service-account-credentials.json")
    print("   Checked locations:")
    for loc in possible_locations:
        print(f"      - {loc}")
    
    # Ask user for file location
    print("\n   Please provide the full path to your credentials file:")
    user_path = input("   Path: ").strip().strip('"')
    
    if os.path.exists(user_path):
        creds_file = user_path
        print(f"   ✅ Found: {creds_file}")
    else:
        print(f"   ❌ File not found: {user_path}")
        sys.exit(1)

# Step 3: Move file to credentials folder if not already there
target_path = "credentials/service-account-credentials.json"

if creds_file != target_path:
    print(f"\n📁 Step 3: Moving credentials to secure location...")
    try:
        import shutil
        os.makedirs("credentials", exist_ok=True)
        shutil.copy2(creds_file, target_path)
        print(f"   ✅ Copied to: {target_path}")
        
        if creds_file.startswith(os.path.expanduser("~")):
            print(f"   💡 You can delete the original from Downloads")
        
        creds_file = target_path
    except Exception as e:
        print(f"   ⚠️  Could not move file: {e}")
        print(f"   Using original location: {creds_file}")

# Step 4: Validate JSON file
print(f"\n✅ Step 4: Validating credentials file...")
try:
    with open(creds_file, 'r') as f:
        creds_data = json.load(f)
    
    required_fields = ['type', 'project_id', 'private_key', 'client_email']
    missing_fields = [field for field in required_fields if field not in creds_data]
    
    if missing_fields:
        print(f"   ❌ Invalid credentials file - missing: {missing_fields}")
        sys.exit(1)
    
    print(f"   ✅ Valid credentials file")
    print(f"   📧 Service account: {creds_data['client_email']}")
    print(f"   🔑 Project: {creds_data['project_id']}")
    
    service_email = creds_data['client_email']
    
except json.JSONDecodeError:
    print(f"   ❌ Invalid JSON file")
    sys.exit(1)
except Exception as e:
    print(f"   ❌ Error reading file: {e}")
    sys.exit(1)

# Step 5: Test connection
print(f"\n🔗 Step 5: Testing Google Sheets connection...")
print(f"\n💡 You need to:")
print(f"   1. Open your Google Sheet")
print(f"   2. Click 'Share' button")
print(f"   3. Add this email: {service_email}")
print(f"   4. Set permission: Viewer")
print(f"   5. Uncheck 'Notify people'")
print(f"   6. Click 'Share'")

ready = input("\n✅ Have you shared the sheet with the service account? (y/n): ").lower()

if ready != 'y':
    print("\n⏸️  Please share the sheet first, then run this script again.")
    sys.exit(0)

# Get sheet ID
print("\n📊 Enter your Google Sheet details:")
print("💡 Sheet ID is in the URL:")
print("   https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit")

sheet_id = input("\n🔗 Sheet ID: ").strip()

if not sheet_id:
    print("❌ No sheet ID provided")
    sys.exit(1)

# Try to connect
try:
    print(f"\n🔄 Connecting to Google Sheets...")
    
    gc = gspread.service_account(filename=creds_file)
    sheet = gc.open_by_key(sheet_id)
    worksheet = sheet.sheet1
    
    print(f"   ✅ Connected successfully!")
    print(f"   📄 Sheet name: {sheet.title}")
    print(f"   📋 Worksheet: {worksheet.title}")
    print(f"   📊 Total rows: {worksheet.row_count}")
    print(f"   📊 Total columns: {worksheet.col_count}")
    
    # Get sample data
    print(f"\n📋 Reading sample data...")
    all_data = worksheet.get_all_values()
    
    if all_data:
        headers = all_data[0]
        print(f"   ✅ Headers: {headers}")
        print(f"   ✅ Data rows: {len(all_data) - 1}")
        
        # Check for required columns
        required_cols = ['address', 'suburb', 'state']
        found_cols = []
        for col in required_cols:
            if any(col.lower() in h.lower() for h in headers):
                found_cols.append(col)
        
        if len(found_cols) == len(required_cols):
            print(f"   ✅ All required columns found!")
        else:
            missing = set(required_cols) - set(found_cols)
            print(f"   ⚠️  Missing columns: {missing}")
        
        # Show first data row
        if len(all_data) > 1:
            print(f"\n   Sample row 1:")
            for header, value in zip(headers, all_data[1]):
                if value:
                    print(f"      {header}: {value}")
    
    print("\n" + "=" * 70)
    print("✅ SUCCESS! Everything is working!")
    print("=" * 70)
    
    print(f"\n📝 Configuration saved:")
    print(f"   Credentials: {creds_file}")
    print(f"   Sheet ID: {sheet_id}")
    
    print(f"\n🚀 Next steps:")
    print(f"   1. You can now run: python apify_scraper_testing.py")
    print(f"   2. Update the script with this Sheet ID: {sheet_id}")
    
    # Save config for future use
    config = {
        "sheet_id": sheet_id,
        "credentials_path": creds_file,
        "service_email": service_email
    }
    
    with open("google_sheets_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"   3. Config saved to: google_sheets_config.json")
    
except gspread.exceptions.SpreadsheetNotFound:
    print(f"\n❌ ERROR: Spreadsheet not found!")
    print(f"\n⚠️  Make sure you:")
    print(f"   1. Shared the sheet with: {service_email}")
    print(f"   2. Used the correct Sheet ID")
    print(f"   3. Service account has 'Viewer' permission")
    sys.exit(1)

except gspread.exceptions.APIError as e:
    print(f"\n❌ API ERROR: {e}")
    print(f"\n⚠️  Possible fixes:")
    print(f"   1. Enable Google Sheets API in Google Cloud Console")
    print(f"   2. Check if API is enabled: https://console.cloud.google.com/apis/library")
    sys.exit(1)

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print(f"   Type: {type(e).__name__}")
    sys.exit(1)
