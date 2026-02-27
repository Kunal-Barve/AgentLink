# Google Sheets → Supabase Sync Deployment Guide

## 🎯 Choose Your Approach

### **Option 1: Direct Apps Script → Supabase** ⭐ RECOMMENDED
**Best for:** Simple sync without custom validation

```
Google Sheets → Apps Script → Supabase REST API
```

**Pros:**
- ✅ No server needed
- ✅ Completely free
- ✅ Simple setup
- ✅ Real-time sync

**Cons:**
- ❌ No custom validation
- ❌ 6-minute execution limit
- ❌ 20,000 API calls/day limit

---

### **Option 2: Apps Script → FastAPI → Supabase**
**Best for:** Custom validation, transformation, or business logic

```
Google Sheets → Apps Script → FastAPI Webhook → Supabase
```

**Pros:**
- ✅ Custom validation/transformation
- ✅ Better error handling
- ✅ Audit logging
- ✅ Rate limiting control

**Cons:**
- ❌ Requires server deployment
- ❌ More complex setup

---

## 📋 Setup: Option 1 (Direct - Recommended)

### Step 1: Prepare Each Google Sheet

For each of your 7 Excel files that you want to sync:

1. **Upload to Google Sheets** (if not already)
   - Go to Google Drive
   - Upload Excel file
   - Open in Google Sheets

2. **Open Apps Script Editor**
   - Click **Extensions > Apps Script**
   - Delete any existing code
   - Copy entire code from `sheets_sync_script.gs`
   - Paste into editor
   - Click **Save** (disk icon)

3. **Configure Script Properties**
   - Click **Project Settings** (gear icon)
   - Scroll to **Script Properties**
   - Click **+ Add script property**
   - Add these 3 properties:

| Property Name | Value |
|--------------|-------|
| `SUPABASE_URL` | `http://srv1165267.hstgr.cloud:8000` |
| `SUPABASE_SERVICE_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (your full service key) |
| `TABLE_NAME` | `agents_subscribed` (see table mapping below) |

4. **Test Connection**
   - Refresh Google Sheet
   - You'll see new menu: **Supabase Sync**
   - Click **Supabase Sync > Test Connection**
   - Should show "Success!" popup

5. **Install onChange Trigger**
   - In Apps Script editor, click **Triggers** (clock icon on left)
   - Click **+ Add Trigger** (bottom right)
   - Configure:
     - **Choose function:** `onChange`
     - **Event source:** From spreadsheet
     - **Event type:** On change
   - Click **Save**
   - Authorize the script (first time only)

6. **Initial Full Sync**
   - In Google Sheet, click **Supabase Sync > Manual Full Sync**
   - Check logs: **View > Logs** in Apps Script editor

### Step 2: Table Mapping

Configure `TABLE_NAME` for each sheet:

| Excel File | Sheet Tab | TABLE_NAME |
|-----------|-----------|------------|
| Agents Subscribed.xlsx | Sheet1 | `agents_subscribed` |
| Agents Subscribed.xlsx | Costs & Charges | `agents_subscribed_costs_charges` |
| Agents Subscribed.xlsx | Agents Cancelled Subscriptions | `agents_subscribed_agents_cancelled_subscriptions` |
| Agents Subscribed.xlsx | Area Key | `agents_subscribed_area_key` |
| Copy of Leads Sent.xlsx | Sheet1 | `leads_sent` |
| Copy of Leads Sent.xlsx | Advocacy | `leads_sent_advocacy` |
| Copy of Leads Sent.xlsx | Leaderboard | `leads_sent_leaderboard` |
| Copy of Leads Sent.xlsx | Agent Report | `leads_sent_agent_report` |
| Featured Agent Controls.xlsx | Sheet1 | `featured_agent_controls` |
| Featured Agent Controls.xlsx | Sheet3 | `featured_agent_controls_sheet3` |
| Suburb Leads, No Agent.xlsx | Sheet1 | `suburb_leads_no_agent` |
| Suburb Leads, No Agent.xlsx | NSW | `suburb_leads_no_agent_nsw` |
| Suburb Leads, No Agent.xlsx | QLD | `suburb_leads_no_agent_qld` |
| Suburb Leads, No Agent.xlsx | VIC | `suburb_leads_no_agent_vic` |
| Suburb Leads, No Agent.xlsx | SA | `suburb_leads_no_agent_sa` |
| Suburb Leads, No Agent.xlsx | WA | `suburb_leads_no_agent_wa` |
| Suburb Leads, No Agent.xlsx | NT | `suburb_leads_no_agent_nt` |
| Suburb Leads, No Agent.xlsx | TAS | `suburb_leads_no_agent_tas` |

---

## 📋 Setup: Option 2 (FastAPI Webhook)

### Step 1: Deploy FastAPI Endpoint

1. **Add to your FastAPI app**
   ```bash
   # Copy fastapi_sync_endpoint.py to your app
   cp app/scripts/google_sheets_sync/fastapi_sync_endpoint.py app/routes/
   ```

2. **Update main.py**
   ```python
   from app.routes.fastapi_sync_endpoint import router as sheets_sync_router
   
   app.include_router(sheets_sync_router)
   ```

3. **Add environment variable**
   ```env
   SHEETS_WEBHOOK_SECRET=your-random-secret-key-here
   ```

4. **Deploy to your server**
   ```bash
   # Restart your FastAPI app
   docker compose restart app
   ```

### Step 2: Update Apps Script

In `sheets_sync_script.gs`, replace the `upsertToSupabase` function with webhook call:

```javascript
function upsertToSupabase(records) {
  const url = 'http://your-server.com/api/sheets-sync/webhook';
  
  const payload = {
    table_name: CONFIG.TABLE_NAME,
    data: records,
    operation: 'upsert'
  };
  
  const options = {
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      'X-Webhook-Secret': PropertiesService.getScriptProperties().getProperty('WEBHOOK_SECRET')
    },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };
  
  try {
    const response = UrlFetchApp.fetch(url, options);
    const statusCode = response.getResponseCode();
    
    if (statusCode >= 200 && statusCode < 300) {
      console.log(`Successfully synced via webhook`);
      return true;
    } else {
      console.error(`Webhook error (${statusCode}):`, response.getContentText());
      return false;
    }
  } catch (error) {
    console.error('Failed to call webhook:', error);
    return false;
  }
}
```

---

## 🧪 Testing

### Test Sync

1. **Make a change in Google Sheet**
   - Edit a cell
   - Add a new row
   - Wait 5-10 seconds

2. **Check Supabase Studio**
   - Open: `http://srv1165267.hstgr.cloud:3001`
   - Navigate to Table Editor
   - Find your table
   - Verify data updated

3. **Check Logs**
   - In Google Sheet: **Supabase Sync > View Sync Logs**
   - Or in Apps Script: **View > Executions**

### Troubleshooting

**Sync not working?**
- Check Script Properties are set correctly
- Check trigger is installed (Triggers tab)
- Check logs for errors (View > Executions)
- Run **Test Connection** from menu

**Data not updating in Supabase?**
- Check Supabase URL is correct
- Check Service Role Key is valid
- Check table name matches exactly
- Check network/firewall (port 8000 accessible)

---

## 🔄 Sync Behavior

- **INSERT_ROW**: Syncs entire sheet on new row
- **EDIT**: Syncs entire sheet on cell edit
- **REMOVE_ROW**: Logs warning (manual cleanup needed)
- **Delay**: ~5 seconds after change
- **Batch Size**: 100 rows per API call
- **Strategy**: Upsert (insert or update if exists)

---

## 📊 Monitoring

### View Sync Logs

Apps Script creates a "Sync Logs" sheet automatically with:
- Timestamp
- Error messages
- Sync status

### Apps Script Quotas

Free tier limits:
- **Execution time:** 6 minutes max per trigger
- **URL Fetch calls:** 20,000/day
- **Triggers:** 20 time-based, unlimited event-based

---

## 🚀 Production Checklist

- [ ] All 18 sheets have Apps Script installed
- [ ] All scripts have correct `TABLE_NAME` configured
- [ ] onChange triggers installed for each sheet
- [ ] Test connection successful for all sheets
- [ ] Initial full sync completed
- [ ] Test edit/insert in each sheet
- [ ] Verify data in Supabase Studio
- [ ] Monitor "Sync Logs" sheet for errors
- [ ] Document any custom validation rules

---

## 🔐 Security Notes

- Service Role Key has full database access - keep secure
- Use Script Properties (not hardcoded keys)
- Consider using webhook approach for production
- Add rate limiting if using webhook
- Monitor Apps Script execution logs
