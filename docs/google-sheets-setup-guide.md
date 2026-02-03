# Google Sheets Sync - Complete Setup Guide

## 🎯 Overview

**Flow:** Google Sheets → Apps Script → FastAPI → Supabase

**Benefits:**
- ✅ Auto-creates tables for new tabs
- ✅ Real-time sync (~5-10 seconds)
- ✅ Handles schema changes
- ✅ No manual table creation needed

---

## 📋 Prerequisites

1. Google Sheets with data (4 spreadsheets, 11 tabs total)
2. Supabase instance running (port 8000)
3. FastAPI server (local or deployed)
4. PostgreSQL credentials

---

## 🚀 Step 1: Deploy FastAPI Endpoint

### 1.1 Add Route to Main App

Edit `main.py` or your FastAPI app file:

```python
from app.routes.google_sheets_sync import router as sheets_sync_router

app.include_router(sheets_sync_router)
```

### 1.2 Configure Environment Variables

Add to `.env`:

```env
# Google Sheets Sync
SHEETS_WEBHOOK_SECRET=your-random-secret-key-here-change-this
```

Generate a secure secret:
```bash
# PowerShell
-join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | % {[char]$_})
```

### 1.3 Test Endpoint Locally

```bash
# Start your FastAPI server
python -m uvicorn main:app --reload --port 8000

# Test health endpoint
curl http://localhost:8000/api/sheets/health
```

Expected response:
```json
{
  "status": "healthy",
  "supabase": "connected",
  "endpoint": "sheets-sync"
}
```

---

## 📝 Step 2: Install Apps Script

For **each** of your 4 Google Sheets:

### 2.1 Open Apps Script Editor

1. Open the Google Sheet
2. Click **Extensions** → **Apps Script**
3. Delete any existing code
4. Copy entire code from `app/scripts/google_sheets_sync/apps_script_webhook.gs`
5. Paste into editor

### 2.2 Configure Settings

**Edit the CONFIG section at the top:**

```javascript
const CONFIG = {
  // Change this to your server URL
  API_URL: 'http://srv1165267.hstgr.cloud:8000/api/sheets/sync',
  
  // Must match SHEETS_WEBHOOK_SECRET in .env
  WEBHOOK_SECRET: 'your-random-secret-key-here-change-this',
  
  // Auto-detected (don't change these)
  SPREADSHEET_ID: SpreadsheetApp.getActiveSpreadsheet().getId(),
  SPREADSHEET_NAME: SpreadsheetApp.getActiveSpreadsheet().getName(),
  
  AUTO_CREATE_TABLE: true,
  BATCH_SIZE: 100
};
```

### 2.3 Save Script

1. Click **Save** (disk icon or Ctrl+S)
2. Name it: "Supabase Sync Script"

### 2.4 Test Configuration

1. Click **Run** dropdown → Select `viewConfig`
2. Click **Run**
3. Check logs (View → Logs)
4. Verify all values are correct

### 2.5 Test API Connection

1. Click **Run** dropdown → Select `testAPIConnection`
2. Click **Run**
3. Check logs - should see "✅ API connection is working!"

### 2.6 Install Trigger

1. Click **Triggers** icon (clock on left sidebar)
2. Click **+ Add Trigger** (bottom right)
3. Configure:
   - **Choose which function to run:** `onChange`
   - **Select event source:** From spreadsheet
   - **Select event type:** On change
4. Click **Save**
5. **Authorize** the script (first time only)
   - Click "Review permissions"
   - Select your Google account
   - Click "Advanced" → "Go to [Script Name] (unsafe)"
   - Click "Allow"

### 2.7 Initial Manual Sync

1. Click **Run** dropdown → Select `manualSync`
2. Click **Run**
3. Check logs - should see rows synced
4. Verify in Supabase Studio (port 3001)

---

## 🔄 Step 3: Repeat for All Sheets

Install Apps Script on all 4 spreadsheets:

- [ ] **Copy of Leads Sent** (4 tabs)
  - Sheet1, Advocacy, Leaderboard, Agent Report
  
- [ ] **Featured Agent Controls** (2 tabs)
  - Sheet1, Sheet3
  
- [ ] **Agents Subscribed** (4 tabs)
  - Sheet1, Cost & Charges, Agents Cancelled Subscriptions, Area Key
  
- [ ] **Copy of Agents Subscribed** (1 tab)
  - Agents Subscribed

**For each spreadsheet:**
1. Open sheet
2. Extensions → Apps Script
3. Paste code
4. Configure CONFIG (same values)
5. Save
6. Add onChange trigger
7. Run manualSync
8. Verify in Supabase

---

## ✅ Step 4: Verify Setup

### 4.1 Check All Tables Created

```bash
curl http://srv1165267.hstgr.cloud:8000/api/sheets/tables
```

Expected: 11 tables listed

### 4.2 Test Live Sync

For each spreadsheet:
1. Open sheet
2. Edit a cell in any tab
3. Wait 10 seconds
4. Check Supabase Studio
5. Verify data updated

### 4.3 Test New Tab Creation

1. Add a new tab to any spreadsheet
2. Add some data (at least headers + 1 row)
3. Edit a cell
4. Wait 10 seconds
5. Check Supabase Studio
6. Verify new table created

---

## 🔐 Step 5: Secure for Production

### 5.1 Update Webhook Secret

Generate strong secret:
```powershell
-join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | % {[char]$_})
```

Update in:
- `.env` file → `SHEETS_WEBHOOK_SECRET`
- All 4 Apps Scripts → `CONFIG.WEBHOOK_SECRET`

### 5.2 Deploy to Server

```bash
# SSH to server
ssh -i D:\Articflow\ssh-keys\agentlink-hostinger-n8n root@72.62.64.72

# Update code
cd /path/to/your/app
git pull

# Update .env with webhook secret
nano .env
# Add: SHEETS_WEBHOOK_SECRET=your-secret-here

# Restart app
docker compose restart app
```

### 5.3 Update Apps Script URLs

In all 4 spreadsheets, update:
```javascript
API_URL: 'http://srv1165267.hstgr.cloud:8000/api/sheets/sync',
```

---

## 📊 Step 6: Monitor & Maintain

### View Sync Logs

Each spreadsheet has a "Sync Logs" tab:
- Timestamp of errors
- Error messages
- Helps debug issues

### Check Apps Script Executions

1. Open Apps Script
2. Click **Executions** (left sidebar)
3. View all trigger runs
4. Filter by status (success/failure)

### API Monitoring

```bash
# List all tables
GET /api/sheets/tables

# Get table schema
GET /api/sheets/table/{table_name}/schema

# Health check
GET /api/sheets/health
```

---

## 🆘 Troubleshooting

### Apps Script Error: "Cannot call SpreadsheetApp.getUi()"

**Solution:** Don't run `setupSync()` - it's deprecated. Use the new `apps_script_webhook.gs` which doesn't use UI prompts.

### Table Not Created

**Check:**
- `AUTO_CREATE_TABLE` is `true`
- Tab has at least 2 rows (headers + data)
- Apps Script execution log shows no errors
- API endpoint is reachable

**Debug:**
```javascript
// In Apps Script, run:
manualSync()
// Check logs for detailed error
```

### Data Not Syncing

**Check:**
- Webhook secret matches in both places
- API URL is correct
- onChange trigger is installed
- Server is running

**Test:**
```javascript
// In Apps Script:
testAPIConnection()  // Should return 200
viewConfig()         // Verify all settings
```

### Wrong Table Name

**Tables are named:**
- `spreadsheet_name` (for Sheet1)
- `spreadsheet_name_tab_name` (for other tabs)

All lowercase, spaces/special chars → underscores

**Fix:**
```sql
-- Rename table in Supabase
ALTER TABLE wrong_name RENAME TO correct_name;
```

---

## 📈 Adding New Tabs (Future)

When your client adds a new tab:

1. **No manual setup needed!**
2. Client adds tab and enters data
3. Client edits any cell
4. onChange triggers
5. API auto-creates table
6. Data syncs

**Verify:**
- Check Supabase Studio for new table
- Verify data synced correctly
- Check Apps Script execution log

---

## 🎉 Success Checklist

- [ ] FastAPI endpoint deployed
- [ ] Environment variables configured
- [ ] Apps Script installed on all 4 spreadsheets
- [ ] All 11 tabs have triggers
- [ ] Initial sync completed for all tabs
- [ ] Live sync tested (edit cell → verify in Supabase)
- [ ] New tab creation tested
- [ ] Webhook secret is secure
- [ ] Monitoring in place
- [ ] Team knows how to check sync logs

---

**Your sync is now fully automated! Any changes in Google Sheets will appear in Supabase within 10 seconds.** 🚀
