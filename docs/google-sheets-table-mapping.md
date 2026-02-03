# Google Sheets to Supabase Table Mapping

## Current Google Sheets

### 1. Copy of Leads Sent
**Spreadsheet ID:** `10rEh9tS9tl10qTyUTPFZFEX0rbF60kHtBsPg9wb7Up4`  
**URL:** https://docs.google.com/spreadsheets/d/10rEh9tS9tl10qTyUTPFZFEX0rbF60kHtBsPg9wb7Up4/edit

| Tab Name | Supabase Table Name |
|----------|---------------------|
| Sheet1 | `copy_of_leads_sent` |
| Advocacy | `copy_of_leads_sent_advocacy` |
| Leaderboard | `copy_of_leads_sent_leaderboard` |
| Agent Report | `copy_of_leads_sent_agent_report` |

---

### 2. Featured Agent Controls
**Spreadsheet ID:** `1KyqbMETovx9qqfxVqx--MKUyrLx5o_KYI8r7tENjXOE`  
**URL:** https://docs.google.com/spreadsheets/d/1KyqbMETovx9qqfxVqx--MKUyrLx5o_KYI8r7tENjXOE/edit

| Tab Name | Supabase Table Name |
|----------|---------------------|
| Sheet1 | `featured_agent_controls` |
| Sheet3 | `featured_agent_controls_sheet3` |

---

### 3. Agents Subscribed
**Spreadsheet ID:** `1l2nXbD0q-h1in41KpbCHcuKbpADHqXW0yWkXNkGVRp4`  
**URL:** https://docs.google.com/spreadsheets/d/1l2nXbD0q-h1in41KpbCHcuKbpADHqXW0yWkXNkGVRp4/edit

| Tab Name | Supabase Table Name |
|----------|---------------------|
| Sheet1 | `agents_subscribed` |
| Cost & Charges | `agents_subscribed_cost_charges` |
| Agents Cancelled Subscriptions | `agents_subscribed_agents_cancelled_subscriptions` |
| Area Key | `agents_subscribed_area_key` |

---

### 4. Copy of Agents Subscribed
**Spreadsheet ID:** `1qcuH6CUNZvxCR0400Ej__FYoSg1CEhn7iF8oXQ6g-sk`  
**URL:** https://docs.google.com/spreadsheets/d/1qcuH6CUNZvxCR0400Ej__FYoSg1CEhn7iF8oXQ6g-sk/edit

| Tab Name | Supabase Table Name |
|----------|---------------------|
| Agents Subscribed | `copy_of_agents_subscribed_agents_subscribed` |

---

## Table Naming Convention

The sync endpoint automatically generates table names using this formula:

```
IF tab_name == "Sheet1":
    table_name = clean(spreadsheet_name)
ELSE:
    table_name = clean(spreadsheet_name) + "_" + clean(tab_name)
```

**clean() function:**
- Converts to lowercase
- Replaces spaces and special characters with underscores
- Removes consecutive underscores
- Truncates to 63 characters

**Examples:**
- `"Copy of Leads Sent"` + `"Sheet1"` → `copy_of_leads_sent`
- `"Copy of Leads Sent"` + `"Advocacy"` → `copy_of_leads_sent_advocacy`
- `"Agents Subscribed"` + `"Cost & Charges"` → `agents_subscribed_cost_charges`

---

## Auto-Table Creation

When `auto_create_table: true` (default), the FastAPI endpoint will:

1. **Detect new tabs** - When you add a new tab to any spreadsheet
2. **Infer schema** - Analyze first 100 rows to determine column types
3. **Create table** - Generate appropriate PostgreSQL table
4. **Add indexes** - Create index on `created_at` for performance
5. **Sync data** - Insert/update all rows

**Column Type Inference:**
- Boolean values → `BOOLEAN`
- Integers → `BIGINT`
- Decimals → `DOUBLE PRECISION`
- Dates/timestamps → `TIMESTAMP`
- Everything else → `TEXT`

**Auto-added columns:**
- `id` - BIGSERIAL PRIMARY KEY
- `created_at` - TIMESTAMP DEFAULT NOW()
- `updated_at` - TIMESTAMP DEFAULT NOW()

---

## Verification Checklist

- [ ] All 4 spreadsheets have Apps Script installed
- [ ] All 11 tabs are configured
- [ ] Test sync on each tab
- [ ] Verify tables created in Supabase
- [ ] Check data accuracy
- [ ] Monitor sync logs
- [ ] Test adding new tab (auto-creation)

---

## Adding New Tabs

When your client adds a new tab:

1. **No action needed** - Apps Script will auto-detect
2. **First sync** - Table will be created automatically
3. **Verify** - Check Supabase Studio for new table
4. **Monitor** - Watch sync logs for any errors

**Example:**
- Client adds tab "New Region" to "Agents Subscribed"
- User edits a cell
- onChange trigger fires
- API creates table `agents_subscribed_new_region`
- Data syncs automatically

---

## Monitoring

### Check Synced Tables
```bash
GET http://srv1165267.hstgr.cloud:8000/api/sheets/tables
```

### View Table Schema
```bash
GET http://srv1165267.hstgr.cloud:8000/api/sheets/table/{table_name}/schema
```

### Health Check
```bash
GET http://srv1165267.hstgr.cloud:8000/api/sheets/health
```

---

## Troubleshooting

**Table not created?**
- Check `auto_create_table` is `true`
- Verify data exists in tab (at least 1 row)
- Check API logs for errors

**Data not syncing?**
- Verify webhook secret matches
- Check network connectivity
- Review Apps Script execution logs

**Wrong table name?**
- Spreadsheet or tab name has special characters
- Check naming convention above
- Manually rename table if needed
