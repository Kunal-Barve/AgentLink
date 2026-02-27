# Supabase

This folder contains all database-related files for the AgentLink Supabase instance.

## Structure

```
supabase/
├── migrations/     SQL scripts — run these in Supabase SQL Editor in order
└── seeds/          One-off data import scripts (CSV/SQL)
```

## Migrations (run in this order)

| File | Description |
|------|-------------|
| `create-suburb-leads-tables-with-columns.sql` | Creates suburb leads tables per state |
| `recreate-suburb-leads-tables.sql` | Recreates suburb leads tables (use if resetting) |
| `fix-agents-subscribed-table.sql` | Fixes/alters the agents_subscribed table |
| `create-au-suburbs-table.sql` | Creates the `au_suburbs` reference table (suburb/state/postcode) |
| `cleanup-all-tables.sql` | Drops all tables — **destructive, use with caution** |

## Running a Migration

1. Open Supabase Dashboard → SQL Editor
2. Copy contents of the migration file
3. Paste and run

## Import Scripts

To populate `au_suburbs` after running its migration:

```bash
python scripts/import_au_suburbs.py
```
