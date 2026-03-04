"""
Build merged agent_subscriptions table in Supabase.

Reads from:
  - agents_subscribed     (already synced from xlsx)
  - featured_agent_controls (already synced from xlsx)
  - au_suburbs            (already populated — used for postcode lookups)

Logic:
  - Group agents_subscribed by agent name
  - For each agent, collect all (suburb, state, postcode) into subscribed_suburbs[]
  - Look up commission rates from featured_agent_controls by agent name
  - If commission rates are the same across all states -> 1 row, state = NULL
  - If commission rates differ by state -> 1 row per distinct rate group, state = that state
  - subscribed_suburbs key format: SUBURB|STATE|POSTCODE (looked up from au_suburbs)

Run:
    python scripts/import_agent_subscriptions.py

Prerequisites:
    pip install supabase python-dotenv
    SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env
    Run supabase/migrations/alter-agent-subscriptions-constraint.sql first
"""

import os
import sys
import re
from collections import defaultdict
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
BATCH_SIZE = 100

# Map featured_agent_controls db column -> agent_subscriptions db column
COMMISSION_COL_MAP = {
    "less_than_500k_commission": "comm_less_500k",
    "500k_1m_commission":        "comm_500k_1m",
    "1m_1_5m_commission":        "comm_1m_1_5m",
    "1_5m_2m_commission":        "comm_1_5m_2m",
    "2m_2_5m_commission":        "comm_2m_2_5m",
    "2_5m_3m_commission":        "comm_2_5m_3m",
    "3_3_5m_commission":         "comm_3m_3_5m",
    "3_5m_4m_commission":        "comm_3_5m_4m",
    "4m_6m_commission":          "comm_4m_6m",
    "6m_8m_commission":          "comm_6m_8m",
    "8m_10m_commission":         "comm_8m_10m",
    "10m_commission":            "comm_10m_plus",
    "less_than_500k_marketing":  "mkt_less_500k",
    "500k_1m_marketing":         "mkt_500k_1m",
    "1m_1_5m_marketing":         "mkt_1m_1_5m",
    "1_5m_2m_marketing":         "mkt_1_5m_2m",
    "2m_2_5m_marketing":         "mkt_2m_2_5m",
    "2_5m_3m_marketing":         "mkt_2_5m_3m",
    "3m_3_5m_marketing":         "mkt_3m_3_5m",
    "3_5m_4m_marketing":         "mkt_3_5m_4m",
    "4m_6m_marketing":           "mkt_4m_6m",
    "6m_8m_marketing":           "mkt_6m_8m",
    "8m_10m_marketing":          "mkt_8m_10m",
    "10m_marketing":             "mkt_10m_plus",
}

COMM_KEYS = [k for k in COMMISSION_COL_MAP.keys()]


def parse_date(val) -> str | None:
    """Parse various date formats into YYYY-MM-DD string, or return None."""
    if not val:
        return None
    # Already a datetime object
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d")
    s = str(val).strip()
    if not s:
        return None
    # Remove ordinal suffixes: 10th -> 10, 1st -> 1, 2nd -> 2, 3rd -> 3
    s_clean = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", s)
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%B %d %Y",     # May 10 2025
        "%B %d, %Y",    # March 11, 2025
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d-%m-%Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(s_clean.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None  # unrecognised format — store NULL rather than error


def commission_signature(fc_row: dict) -> tuple:
    """Return a tuple of all commission+marketing values — used to detect rate differences."""
    return tuple(fc_row.get(k) or "" for k in COMM_KEYS)


def build_commission_record(fc_row: dict) -> dict:
    """Map featured_agent_controls columns to agent_subscriptions commission columns."""
    return {dest: fc_row.get(src) for src, dest in COMMISSION_COL_MAP.items()}


def fetch_all(supabase: Client, table: str, page_size: int = 1000) -> list[dict]:
    """Fetch all rows from a Supabase table using pagination."""
    rows = []
    offset = 0
    while True:
        result = supabase.table(table).select("*").range(offset, offset + page_size - 1).execute()
        batch = result.data or []
        rows.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size
    return rows


def build_suburb_key(suburb: str, state: str, postcode: str | None, au_suburbs_dict: dict) -> str:
    """
    Build SUBURB|STATE|POSTCODE key.
    Looks up postcode from au_suburbs if not provided.
    Falls back to SUBURB|STATE if postcode unavailable.
    """
    s = suburb.strip().upper()
    st = state.strip().upper()
    lookup_key = (s, st)

    # Try au_suburbs lookup first
    pc = au_suburbs_dict.get(lookup_key)

    # Fall back to xlsx postcode
    if not pc and postcode:
        pc = str(postcode).strip().lstrip("0") or postcode
        # re-pad to 4 digits
        try:
            pc = str(int(float(pc))).zfill(4)
        except (ValueError, TypeError):
            pc = str(postcode).strip()

    if pc:
        return f"{s}|{st}|{pc}"
    else:
        return f"{s}|{st}"


def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
        sys.exit(1)

    print("=== Build Merged agent_subscriptions ===\n")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # ----------------------------------------------------------------
    # 1. Load all source data
    # ----------------------------------------------------------------
    print("Loading agents_subscribed...")
    subscribed_rows = fetch_all(supabase, "agents_subscribed")
    print(f"  {len(subscribed_rows)} rows")

    print("Loading featured_agent_controls...")
    featured_rows = fetch_all(supabase, "featured_agent_controls")
    print(f"  {len(featured_rows)} rows")

    print("Loading au_suburbs for postcode lookups...")
    suburb_rows = fetch_all(supabase, "au_suburbs")
    # Build dict: (SUBURB_UPPER, STATE_UPPER) -> postcode
    au_suburbs_dict = {
        (r["suburb"].strip().upper(), r["state"].strip().upper()): r["postcode"]
        for r in suburb_rows
    }
    print(f"  {len(au_suburbs_dict)} suburb entries\n")

    # ----------------------------------------------------------------
    # 2. Group agents_subscribed by name
    # ----------------------------------------------------------------
    # agent_name -> list of subscription rows (may span multiple states)
    by_name: dict[str, list[dict]] = defaultdict(list)
    for row in subscribed_rows:
        name = (row.get("name") or "").strip()
        if name:
            by_name[name].append(row)

    # ----------------------------------------------------------------
    # 3. Group featured_agent_controls by name -> state -> first row
    # ----------------------------------------------------------------
    # agent_name -> state -> first fc row (commission rates)
    fc_by_name_state: dict[str, dict[str, dict]] = defaultdict(dict)
    for row in featured_rows:
        name = (row.get("name") or "").strip()
        state = (row.get("state") or "").strip().upper()
        if name and state and state not in fc_by_name_state[name]:
            fc_by_name_state[name][state] = row

    # ----------------------------------------------------------------
    # 4. Build merged rows
    # ----------------------------------------------------------------
    output_rows: list[dict] = []
    warnings: list[str] = []
    unmatched_suburbs: list[str] = []

    all_names = set(by_name.keys()) | set(fc_by_name_state.keys())

    for name in sorted(all_names):
        sub_rows = by_name.get(name, [])
        fc_states = fc_by_name_state.get(name, {})

        # Base agent info (take from first subscription row, or None if only in FC)
        base = sub_rows[0] if sub_rows else {}

        # Determine commission grouping:
        # Get unique commission signatures per state
        state_sigs: dict[str, tuple] = {}
        for state, fc_row in fc_states.items():
            state_sigs[state] = commission_signature(fc_row)

        # Group states by identical commission signature
        # sig -> list of states sharing that signature
        sig_to_states: dict[tuple, list[str]] = defaultdict(list)
        for state, sig in state_sigs.items():
            sig_to_states[sig].append(state)

        # States this agent is subscribed to (from agents_subscribed)
        subscribed_states = {(r.get("state") or "").strip().upper() for r in sub_rows if r.get("state")}

        if not sig_to_states:
            # Agent only in agents_subscribed — no commission data
            sig_to_states[tuple()] = list(subscribed_states) if subscribed_states else [None]

        for sig, fc_states_for_sig in sig_to_states.items():
            fc_states_for_sig_set = set(s for s in fc_states_for_sig if s)

            # Determine state value for this row:
            # NULL if this covers all subscribed states (or agent has uniform rates)
            # Filled if this is only a subset (different rates per state)
            all_sigs_same = len(sig_to_states) == 1
            row_state = None if all_sigs_same else (fc_states_for_sig[0] if fc_states_for_sig else None)

            # Build subscribed_suburbs array
            # Filter sub_rows to matching states if splitting
            if row_state:
                relevant_sub_rows = [r for r in sub_rows if (r.get("state") or "").strip().upper() == row_state]
            else:
                relevant_sub_rows = sub_rows

            subscribed_suburbs = []
            for r in relevant_sub_rows:
                suburb = (r.get("suburb") or "").strip()
                state = (r.get("state") or "").strip().upper()
                postcode = r.get("postcode")
                if not suburb or not state:
                    continue
                key = build_suburb_key(suburb, state, postcode, au_suburbs_dict)
                if key not in subscribed_suburbs:
                    subscribed_suburbs.append(key)
                if "|" not in key or key.count("|") < 2:
                    unmatched_suburbs.append(f"{name}: {suburb}|{state} (no postcode)")

            # Get commission data
            fc_row = None
            if fc_states_for_sig_set:
                first_fc_state = next(iter(fc_states_for_sig_set))
                fc_row = fc_by_name_state[name].get(first_fc_state)

            commission_data = build_commission_record(fc_row) if fc_row else {v: None for v in COMMISSION_COL_MAP.values()}

            if not fc_row and sub_rows:
                warnings.append(f"No commission data: {name}")

            # Subscription date: find first non-null
            subscription_date = None
            for r in relevant_sub_rows:
                if r.get("subscription_date"):
                    subscription_date = parse_date(r["subscription_date"])
                    break

            # MRR: sum across all relevant rows (may vary per suburb row)
            mrr_total = None
            for r in relevant_sub_rows:
                try:
                    val = float(r.get("mrr") or 0)
                    mrr_total = (mrr_total or 0) + val
                except (ValueError, TypeError):
                    pass

            merged = {
                "name":               name,
                "email":              base.get("email"),
                "phone":              base.get("phone"),
                "state":              row_state,
                "subscribed_suburbs": subscribed_suburbs,
                "subscription_type":  base.get("subscription_type"),
                "subscription_date":  subscription_date,
                "period":             base.get("period"),
                "agent_status":       base.get("agent_status"),
                "manually_pull_data": base.get("manully_pull_data"),
                "ad_group":           base.get("ad_group"),
                "mrr":                mrr_total,
                "total_sales":        base.get("total_sales"),
                "total_sales_value":  base.get("total_sales_value"),
                "median_sold_price":  base.get("median_sold_price"),
                "agency":             base.get("agency"),
                "agent_photo":        base.get("agent_photo"),
                "agency_photo":       base.get("agency_photo"),
                **commission_data,
            }
            output_rows.append(merged)

    # ----------------------------------------------------------------
    # 5. Clear existing data and upsert
    # ----------------------------------------------------------------
    print(f"Prepared {len(output_rows)} rows to insert into agent_subscriptions\n")

    print("Clearing existing rows from 'agent_subscriptions'...")
    supabase.table("agent_subscriptions").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

    inserted = 0
    total = len(output_rows)
    for i in range(0, total, BATCH_SIZE):
        batch = output_rows[i: i + BATCH_SIZE]
        supabase.table("agent_subscriptions").insert(batch).execute()
        inserted += len(batch)
        print(f"  Inserted {inserted}/{total} rows ({inserted/total*100:.0f}%)")

    # ----------------------------------------------------------------
    # 6. Summary report
    # ----------------------------------------------------------------
    print(f"\n{'='*60}")
    print(f"✅ Done — {inserted} rows inserted into 'agent_subscriptions'")
    print(f"{'='*60}")

    only_in_fc = set(fc_by_name_state.keys()) - set(by_name.keys())
    only_in_sub = set(by_name.keys()) - set(fc_by_name_state.keys())

    print(f"\nAgents only in Featured Controls (no suburb subscriptions): {len(only_in_fc)}")
    for n in sorted(only_in_fc):
        print(f"  - {n}")

    print(f"\nAgents only in Subscribed (no commission rates): {len(only_in_sub)}")
    for n in sorted(only_in_sub):
        print(f"  - {n}")

    if unmatched_suburbs:
        print(f"\nSuburbs not found in au_suburbs (used fallback postcode): {len(unmatched_suburbs)}")
        for s in unmatched_suburbs[:20]:
            print(f"  - {s}")
        if len(unmatched_suburbs) > 20:
            print(f"  ... and {len(unmatched_suburbs) - 20} more")


if __name__ == "__main__":
    main()
