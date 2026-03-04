"""
Import Australian Postcodes & Suburbs into Supabase au_suburbs table.

Source: app/assets/google_sheets/Australian Postcodes & Suburbs.xlsx
Target: Supabase table `au_suburbs`

Run:
    python scripts/import_au_suburbs.py

Prerequisites:
    pip install openpyxl supabase python-dotenv
    SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env
"""

import os
import sys
from pathlib import Path
import openpyxl
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

XLSX_PATH = Path(__file__).parent.parent / "app" / "assets" / "google_sheets" / "Australian Postcodes & Suburbs.xlsx"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
TABLE_NAME = "au_suburbs"
BATCH_SIZE = 500


def load_xlsx(path: Path) -> list[dict]:
    """Read the xlsx and return list of dicts with suburb, state, postcode."""
    print(f"Loading: {path}")
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    ws = wb.active

    rows = []
    seen = set()  # track (suburb, state, postcode) to deduplicate exact duplicates only

    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        suburb_raw, state_raw, postcode_raw = row[0], row[1], row[2]

        # Skip blank rows
        if not suburb_raw or not state_raw or not postcode_raw:
            continue

        suburb   = str(suburb_raw).strip()
        state    = str(state_raw).strip().upper()
        # Postcode arrives as float (e.g. 800.0) from xlsx — convert safely
        postcode = str(int(float(postcode_raw))).zfill(4)

        key = (suburb.upper(), state, postcode)
        if key in seen:
            print(f"  [SKIP exact duplicate] {suburb} | {state} | {postcode}")
            continue
        seen.add(key)

        rows.append({
            "suburb":   suburb,
            "state":    state,
            "postcode": postcode,
        })

    wb.close()
    print(f"Loaded {len(rows)} unique suburb+state+postcode rows")
    return rows


def upsert_to_supabase(supabase: Client, rows: list[dict]) -> None:
    """Upsert all rows in batches. Uses ON CONFLICT (suburb, state, postcode) DO UPDATE."""
    total = len(rows)
    inserted = 0

    for i in range(0, total, BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        try:
            supabase.table(TABLE_NAME).upsert(
                batch,
                on_conflict="suburb,state,postcode"
            ).execute()
            inserted += len(batch)
            pct = (inserted / total) * 100
            print(f"  Upserted {inserted}/{total} rows ({pct:.0f}%)")
        except Exception as e:
            print(f"  ERROR on batch {i//BATCH_SIZE + 1}: {e}")
            raise

    print(f"\n✅ Done — {inserted} rows upserted to '{TABLE_NAME}'")


def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
        sys.exit(1)

    if not XLSX_PATH.exists():
        print(f"ERROR: File not found: {XLSX_PATH}")
        sys.exit(1)

    print("=== Australian Suburbs Import ===\n")

    rows = load_xlsx(XLSX_PATH)

    print(f"\nConnecting to Supabase: {SUPABASE_URL}")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    print(f"Upserting {len(rows)} rows into '{TABLE_NAME}' (batch size {BATCH_SIZE})...\n")
    upsert_to_supabase(supabase, rows)


if __name__ == "__main__":
    main()
