# Google Sheets to Supabase Real-Time Sync

## Overview
Real-time synchronization from Google Sheets to Supabase using Google Apps Script with onChange triggers.

## Architecture
```
Google Sheets → Apps Script (onChange trigger) → Supabase REST API
```

## Setup Instructions

### 1. For Each Google Sheet:

1. Open the Google Sheet
2. Go to **Extensions > Apps Script**
3. Copy the code from `sheets_sync_script.gs`
4. Set up Script Properties:
   - `SUPABASE_URL`: `http://srv1165267.hstgr.cloud:8000`
   - `SUPABASE_SERVICE_KEY`: Your service role key
   - `TABLE_NAME`: Corresponding Supabase table name

### 2. Install Trigger:

In Apps Script editor:
1. Click **Triggers** (clock icon)
2. Click **+ Add Trigger**
3. Choose:
   - Function: `onChange`
   - Event source: **From spreadsheet**
   - Event type: **On change**
4. Save

### 3. Table Mapping:

| Google Sheet | Supabase Table |
|-------------|----------------|
| Agents Subscribed (Sheet1) | `agents_subscribed` |
| Agents Subscribed (Costs & Charges) | `agents_subscribed_costs_charges` |
| Copy of Leads Sent (Sheet1) | `leads_sent` |
| Featured Agent Controls (Sheet1) | `featured_agent_controls` |
| Suburb Leads No Agent (NSW) | `suburb_leads_no_agent_nsw` |
| etc... | etc... |

## Features

- ✅ Real-time sync on row insert/update/delete
- ✅ Batch processing for performance
- ✅ Error handling and retry logic
- ✅ Logging for debugging
- ✅ Handles datetime conversion
- ✅ Cleans NaN/Inf values

## Limitations

- Apps Script has 6-minute execution limit
- Max 20,000 API calls per day (Google quota)
- onChange trigger has ~5 second delay

## Alternative: FastAPI Webhook (Optional)

If you need custom validation/transformation, use the FastAPI middleware approach:
- See `fastapi_sync_endpoint.py` for implementation
- Webhook URL: `http://your-server.com/api/sheets-sync`
