# Google Sheets API Setup Guide for Property Tracker

**Purpose**: Read property data from Google Sheets for Apify scraper testing  
**Date**: December 8, 2025  
**Project**: AgentLink Property Tracker

---

## 📋 Overview

This guide explains how to set up Google Sheets API access for reading Callum's property list (2380+ properties) in Python.

**Two Authentication Options:**
1. **Service Account** (✅ RECOMMENDED for automation/bots)
2. OAuth Client ID (for user-facing apps)

We'll use **Service Account** since this is automated testing.

---

## 🚀 Quick Start (Service Account Method)

### Prerequisites

- Python 3.11+ (✅ You have this)
- Google Account
- Google Cloud Project

### Required Python Packages

```bash
pip install gspread google-auth
```

---

## 📝 Step-by-Step Setup

### Step 1: Create Google Cloud Project

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/

2. **Create New Project**
   - Click "Select a project" dropdown (top left)
   - Click "NEW PROJECT"
   - **Project Name**: `AgentLink-Property-Tracker`
   - **Organization**: Leave default
   - Click **"CREATE"**

3. **Wait for project creation** (takes ~30 seconds)

---

### Step 2: Enable Google Sheets API

1. **Navigate to API Library**
   - In Google Cloud Console, click the hamburger menu (☰)
   - Go to: **APIs & Services** → **Library**
   - Or visit directly: https://console.cloud.google.com/apis/library

2. **Search and Enable**
   - Search for: `Google Sheets API`
   - Click on "Google Sheets API"
   - Click **"ENABLE"**

3. **Also Enable Google Drive API** (optional but recommended)
   - Search for: `Google Drive API`
   - Click **"ENABLE"**
   - This allows listing all sheets you have access to

---

### Step 3: Create Service Account

1. **Go to Credentials**
   - In Google Cloud Console
   - **APIs & Services** → **Credentials**
   - Or visit: https://console.cloud.google.com/apis/credentials

2. **Create Service Account**
   - Click **"+ CREATE CREDENTIALS"** (top)
   - Select **"Service account"**

3. **Service Account Details**
   - **Service account name**: `property-tracker-bot`
   - **Service account ID**: (auto-generated) `property-tracker-bot@...`
   - **Description**: "Bot for reading property data from Google Sheets"
   - Click **"CREATE AND CONTINUE"**

4. **Grant Access (Optional)**
   - Skip this step for now
   - Click **"CONTINUE"**

5. **Grant Users Access (Optional)**
   - Skip this step
   - Click **"DONE"**

---

### Step 4: Create Service Account Key (JSON Credentials)

1. **Find Your Service Account**
   - In **Credentials** page
   - Scroll down to **"Service Accounts"** section
   - You should see: `property-tracker-bot@agentlink-property-tracker...`

2. **Manage Keys**
   - Click on the **email address** of the service account
   - Go to **"KEYS"** tab (top)
   - Click **"ADD KEY"** → **"Create new key"**

3. **Download JSON Key**
   - Select **"JSON"** format
   - Click **"CREATE"**
   - JSON file will automatically download
   - **Filename**: `agentlink-property-tracker-xxxxx.json`

4. **⚠️ IMPORTANT: Keep this file secure!**
   - This file contains private keys
   - Never commit to Git
   - Never share publicly

---

### Step 5: Move Credentials File to Project

**Option A: Standard Location (Recommended)**

Windows:
```powershell
# Create gspread config folder
mkdir "$env:APPDATA\gspread"

# Move the downloaded JSON file
move "Downloads\agentlink-property-tracker-xxxxx.json" "$env:APPDATA\gspread\service_account.json"
```

**Option B: Project Directory (For this project)**

```powershell
# In project root
mkdir credentials

# Move JSON file
move "Downloads\agentlink-property-tracker-xxxxx.json" "credentials\google_sheets_service_account.json"
```

**Add to .gitignore:**
```bash
# Add this line to .gitignore
credentials/
*.json
!package.json
```

---

### Step 6: Share Google Sheet with Service Account

**⚠️ CRITICAL STEP - Don't skip this!**

1. **Get Service Account Email**
   - Open the JSON file you downloaded
   - Find the `client_email` field
   - Example: `property-tracker-bot@agentlink-property-tracker.iam.gserviceaccount.com`

2. **Open the Google Sheet** (from Callum)
   - The one with 2380+ properties

3. **Share the Sheet**
   - Click **"Share"** button (top right)
   - Paste the service account email
   - Set permission: **"Viewer"** (read-only)
   - **UNCHECK** "Notify people" (it's a bot, not a person)
   - Click **"Share"**

4. **Verify**
   - The service account email should now appear in "People with access"

---

## 💻 Python Code Examples

### Example 1: Basic Connection Test

Create `test_google_sheets.py`:

```python
import gspread
from google.oauth2.service_account import Credentials

# Define scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/drive.readonly'
]

# Load credentials
credentials = Credentials.from_service_account_file(
    'credentials/google_sheets_service_account.json',
    scopes=SCOPES
)

# Authorize gspread
gc = gspread.authorize(credentials)

# Open the spreadsheet by name or URL
# Option 1: By name
sheet = gc.open("Callum Property List")

# Option 2: By URL (more reliable)
sheet = gc.open_by_url("https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/...")

# Option 3: By ID (most reliable)
sheet = gc.open_by_key("YOUR_SHEET_ID")

# Get first worksheet
worksheet = sheet.sheet1  # or sheet.get_worksheet(0)

# Test: Read first 5 rows
data = worksheet.get_all_values()
print(f"Total rows: {len(data)}")
print("First 5 rows:")
for row in data[:5]:
    print(row)
```

### Example 2: Using gspread Shortcut

```python
import gspread

# If credentials are in default location (%APPDATA%\gspread\service_account.json)
gc = gspread.service_account()

# If credentials are elsewhere
gc = gspread.service_account(filename='credentials/google_sheets_service_account.json')

# Open sheet
sheet = gc.open_by_key("YOUR_SHEET_ID")
worksheet = sheet.sheet1

# Read all data
all_data = worksheet.get_all_records()  # Returns list of dicts
print(f"Found {len(all_data)} properties")
```

### Example 3: Read Property Data with Pandas

```python
import gspread
import pandas as pd

gc = gspread.service_account(filename='credentials/google_sheets_service_account.json')

# Open sheet
sheet = gc.open_by_key("YOUR_SHEET_ID")
worksheet = sheet.sheet1

# Get all values
data = worksheet.get_all_values()

# Convert to pandas DataFrame
df = pd.DataFrame(data[1:], columns=data[0])  # First row as header

print(f"Total properties: {len(df)}")
print("\nColumn names:")
print(df.columns.tolist())

print("\nFirst 5 properties:")
print(df.head())

# Expected columns: address, suburb, state, postcode (optional)
```

---

## 🔧 Integration with Apify Scraper Testing

Update `apify_scraper_testing.py` to load from Google Sheets:

```python
import gspread
import pandas as pd
from typing import List, Dict

class GoogleSheetsLoader:
    """Load property data from Google Sheets"""
    
    def __init__(self, credentials_path: str):
        self.gc = gspread.service_account(filename=credentials_path)
    
    def load_properties_from_sheet(
        self, 
        sheet_id: str, 
        worksheet_name: str = None
    ) -> List[Dict[str, str]]:
        """
        Load properties from Google Sheet
        
        Args:
            sheet_id: Google Sheet ID (from URL)
            worksheet_name: Name of worksheet (default: first sheet)
            
        Returns:
            List of property dictionaries
        """
        # Open sheet
        sheet = self.gc.open_by_key(sheet_id)
        
        # Get worksheet
        if worksheet_name:
            worksheet = sheet.worksheet(worksheet_name)
        else:
            worksheet = sheet.sheet1
        
        # Get all records
        data = worksheet.get_all_records()
        
        print(f"✅ Loaded {len(data)} properties from Google Sheet")
        
        # Clean data
        properties = []
        for row in data:
            # Skip empty rows
            if not row.get('address') or not row.get('suburb'):
                continue
            
            properties.append({
                'address': str(row.get('address', '')).strip(),
                'suburb': str(row.get('suburb', '')).strip(),
                'state': str(row.get('state', '')).strip().upper(),
                'postcode': str(row.get('postcode', '')).strip() if row.get('postcode') else None
            })
        
        print(f"✅ After cleaning: {len(properties)} valid properties")
        return properties

# Usage in main script
if __name__ == "__main__":
    # Initialize Google Sheets loader
    sheets_loader = GoogleSheetsLoader(
        credentials_path='credentials/google_sheets_service_account.json'
    )
    
    # Load properties
    SHEET_ID = "YOUR_GOOGLE_SHEET_ID_HERE"  # Get from Callum
    properties = sheets_loader.load_properties_from_sheet(SHEET_ID)
    
    # Now use with Apify tester
    tester = ApifyScraperTester()
    tester.run_tests(properties, sample_size=10)
```

---

## 🆔 How to Get Sheet ID

From the Google Sheets URL:

```
https://docs.google.com/spreadsheets/d/1ABC123xyz_SHEET_ID_HERE_789/edit#gid=0
                                      ^^^^^^^^^^^^^^^^^^^^^^^^
                                      This is the Sheet ID
```

Example:
- **Full URL**: `https://docs.google.com/spreadsheets/d/1a2b3c4d5e6f7g8h9i0j/edit`
- **Sheet ID**: `1a2b3c4d5e6f7g8h9i0j`

---

## 🧪 Testing Your Setup

Create `test_sheets_connection.py`:

```python
import gspread
import sys

def test_connection():
    """Test Google Sheets connection"""
    
    print("=" * 60)
    print("Testing Google Sheets API Connection")
    print("=" * 60)
    
    try:
        # Load credentials
        print("\n1. Loading credentials...")
        gc = gspread.service_account(
            filename='credentials/google_sheets_service_account.json'
        )
        print("   ✅ Credentials loaded")
        
        # Test with sample sheet ID (replace with actual)
        sheet_id = input("\n2. Enter Google Sheet ID: ").strip()
        
        print(f"\n3. Opening sheet: {sheet_id[:20]}...")
        sheet = gc.open_by_key(sheet_id)
        print(f"   ✅ Sheet opened: {sheet.title}")
        
        # Get first worksheet
        print("\n4. Reading first worksheet...")
        worksheet = sheet.sheet1
        print(f"   ✅ Worksheet: {worksheet.title}")
        print(f"   ✅ Rows: {worksheet.row_count}")
        print(f"   ✅ Columns: {worksheet.col_count}")
        
        # Read sample data
        print("\n5. Reading first 3 rows...")
        data = worksheet.get_all_values()[:3]
        for i, row in enumerate(data, 1):
            print(f"   Row {i}: {row}")
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        return True
        
    except gspread.exceptions.SpreadsheetNotFound:
        print("\n❌ ERROR: Spreadsheet not found!")
        print("   Make sure:")
        print("   1. Sheet ID is correct")
        print("   2. Service account email has access to the sheet")
        return False
        
    except gspread.exceptions.APIError as e:
        print(f"\n❌ API ERROR: {e}")
        print("   Check if Google Sheets API is enabled")
        return False
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    test_connection()
```

**Run test:**
```bash
python test_sheets_connection.py
```

---

## ⚠️ Troubleshooting

### Error: `SpreadsheetNotFound`

**Cause**: Service account doesn't have access to the sheet

**Solution**:
1. Copy service account email from JSON file (`client_email`)
2. Open Google Sheet
3. Click "Share"
4. Add service account email with "Viewer" permission

### Error: `APIError 403: Google Sheets API has not been used`

**Cause**: API not enabled in Google Cloud Project

**Solution**:
1. Go to: https://console.cloud.google.com/apis/library
2. Search "Google Sheets API"
3. Click "ENABLE"

### Error: `APIError 429: Quota exceeded`

**Cause**: Too many API requests

**Solution**:
- Google Sheets API has rate limits:
  - 300 requests per minute per project
  - 60 requests per minute per user
- Add delays between requests
- Consider batching operations

### Error: Credentials file not found

**Check file path:**
```python
import os
print(os.path.exists('credentials/google_sheets_service_account.json'))
```

---

## 📊 Expected Data Format from Callum's Sheet

Based on meeting notes, the sheet should have:

| address | suburb | state | postcode | (other columns) |
|---------|--------|-------|----------|-----------------|
| 123 Main St | Frankston | VIC | 3199 | ... |
| 45 Beach Rd | Bondi | NSW | 2026 | ... |

**Required columns:**
- `address` - Full street address
- `suburb` - Suburb name
- `state` - State abbreviation (NSW, VIC, QLD, etc.)
- `postcode` - Postal code (optional but recommended)

---

## 🔐 Security Best Practices

1. **Never commit credentials to Git**
   ```bash
   # Add to .gitignore
   credentials/
   *.json
   !package.json
   ```

2. **Use environment variables for sensitive data**
   ```python
   import os
   CREDS_PATH = os.getenv('GOOGLE_SHEETS_CREDS', 'credentials/service_account.json')
   ```

3. **Limit service account permissions**
   - Only share sheets that need to be accessed
   - Use "Viewer" permission (not "Editor")

4. **Rotate credentials periodically**
   - Delete old keys in Google Cloud Console
   - Generate new keys every 90 days

---

## 📚 Additional Resources

- **gspread Documentation**: https://docs.gspread.org/
- **Google Sheets API Docs**: https://developers.google.com/sheets/api
- **Google Auth Library**: https://google-auth.readthedocs.io/
- **Rate Limits**: https://developers.google.com/sheets/api/limits

---

## ✅ Checklist

Before running Apify tests, make sure:

- [ ] Google Cloud Project created
- [ ] Google Sheets API enabled
- [ ] Service Account created
- [ ] JSON credentials downloaded
- [ ] Credentials moved to project folder
- [ ] Sheet shared with service account email
- [ ] `gspread` and `google-auth` installed
- [ ] Test connection script runs successfully
- [ ] Got Sheet ID from Callum
- [ ] Can read property data

---

## 🚀 Next Steps

After completing this setup:

1. **Get Sheet ID from Callum**
2. **Run test connection script**
3. **Update `apify_scraper_testing.py`** with Google Sheets loader
4. **Clean property data** (remove invalid/empty rows)
5. **Proceed with Apify actor testing**

---

**Last Updated**: December 8, 2025  
**Status**: ✅ Ready for implementation
