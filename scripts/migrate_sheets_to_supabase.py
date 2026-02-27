import os
import pandas as pd
from supabase import create_client, Client
from pathlib import Path
import re
from typing import Dict, List, Tuple
import json
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse
import time
import numpy as np
from datetime import datetime, date

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
POSTGRES_PASSWORD = os.getenv("SUPABASE_DB_PASSWORD", "1d3d49c176ab3b6239b9a7f5b98b7f9c")

SHEETS_DIR = Path(__file__).parent.parent / "assets" / "google_sheets"


def clean_column_name(col_name: str) -> str:
    """Convert column names to PostgreSQL-friendly snake_case."""
    col_name = str(col_name).strip()
    col_name = re.sub(r'[^\w\s]', '', col_name)
    col_name = re.sub(r'\s+', '_', col_name)
    col_name = col_name.lower()
    if col_name[0].isdigit():
        col_name = f"col_{col_name}"
    return col_name


def clean_table_name(filename: str, sheet_name: str) -> str:
    """Generate a clean table name from filename and sheet name."""
    base = Path(filename).stem
    base = re.sub(r'^Copy of ', '', base, flags=re.IGNORECASE)
    base = re.sub(r'[^\w\s]', '', base)
    base = re.sub(r'\s+', '_', base).lower()
    
    sheet_clean = re.sub(r'[^\w\s]', '', sheet_name)
    sheet_clean = re.sub(r'\s+', '_', sheet_clean).lower()
    
    if sheet_clean and sheet_clean != 'sheet1':
        return f"{base}_{sheet_clean}"
    return base


def infer_postgres_type(series: pd.Series) -> str:
    """Infer PostgreSQL column type from pandas Series."""
    series = series.dropna()
    
    if len(series) == 0:
        return "text"
    
    if pd.api.types.is_integer_dtype(series):
        return "bigint"
    elif pd.api.types.is_float_dtype(series):
        return "double precision"
    elif pd.api.types.is_bool_dtype(series):
        return "boolean"
    elif pd.api.types.is_datetime64_any_dtype(series):
        return "timestamp with time zone"
    else:
        return "text"


def create_table_from_dataframe(
    pg_conn,
    table_name: str,
    df: pd.DataFrame
) -> Tuple[bool, str]:
    """Create a Supabase table based on DataFrame structure using direct PostgreSQL connection."""
    try:
        columns = []
        for col in df.columns:
            col_name = clean_column_name(col)
            col_type = infer_postgres_type(df[col])
            columns.append(f'"{col_name}" {col_type}')
        
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS "{table_name}" (
            id BIGSERIAL PRIMARY KEY,
            {', '.join(columns)},
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        cursor = pg_conn.cursor()
        cursor.execute(create_sql)
        pg_conn.commit()
        cursor.close()
        
        return True, f"Table '{table_name}' created successfully"
    
    except Exception as e:
        return False, f"Error creating table '{table_name}': {str(e)}"


def insert_dataframe_to_supabase(
    supabase: Client,
    table_name: str,
    df: pd.DataFrame,
    batch_size: int = 100
) -> Tuple[int, List[str]]:
    """Insert DataFrame data into Supabase table in batches."""
    df_clean = df.copy()
    df_clean.columns = [clean_column_name(col) for col in df_clean.columns]
    
    df_clean = df_clean.replace({pd.NA: None, pd.NaT: None, np.inf: None, -np.inf: None, np.nan: None})
    df_clean = df_clean.where(pd.notnull(df_clean), None)
    
    for col in df_clean.columns:
        if pd.api.types.is_datetime64_any_dtype(df_clean[col]):
            df_clean[col] = df_clean[col].apply(
                lambda x: x.isoformat() if pd.notna(x) else None
            )
    
    total_inserted = 0
    errors = []
    
    for i in range(0, len(df_clean), batch_size):
        batch = df_clean.iloc[i:i+batch_size]
        records = batch.to_dict('records')
        
        for record in records:
            for key, value in record.items():
                if isinstance(value, (pd.Timestamp, np.datetime64, datetime, date)):
                    if value is not None and pd.notna(value):
                        if isinstance(value, date) and not isinstance(value, datetime):
                            record[key] = value.isoformat()
                        else:
                            record[key] = pd.Timestamp(value).isoformat()
                    else:
                        record[key] = None
                elif isinstance(value, float):
                    if np.isnan(value) or np.isinf(value):
                        record[key] = None
        
        try:
            result = supabase.table(table_name).insert(records).execute()
            total_inserted += len(records)
            print(f"  Inserted batch {i//batch_size + 1}: {len(records)} rows")
        except Exception as e:
            error_msg = f"Batch {i//batch_size + 1} failed: {str(e)}"
            errors.append(error_msg)
            print(f"  ❌ {error_msg}")
    
    return total_inserted, errors


def migrate_excel_file(
    supabase: Client,
    pg_conn,
    excel_path: Path
) -> Dict:
    """Migrate all sheets from an Excel file to Supabase."""
    print(f"\n{'='*60}")
    print(f"Processing: {excel_path.name}")
    print(f"{'='*60}")
    
    results = {
        'file': excel_path.name,
        'sheets': []
    }
    
    try:
        xl_file = pd.ExcelFile(excel_path)
        sheet_names = xl_file.sheet_names
        print(f"Found {len(sheet_names)} sheet(s): {', '.join(sheet_names)}")
        
        for sheet_name in sheet_names:
            print(f"\n--- Processing sheet: {sheet_name} ---")
            
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            
            if df.empty:
                print(f"⚠️  Sheet '{sheet_name}' is empty, skipping...")
                continue
            
            table_name = clean_table_name(excel_path.name, sheet_name)
            print(f"Table name: {table_name}")
            print(f"Rows: {len(df)}, Columns: {len(df.columns)}")
            print(f"Columns: {list(df.columns)}")
            
            success, message = create_table_from_dataframe(pg_conn, table_name, df)
            
            if success:
                print(f"✅ {message}")
                print("   Waiting for schema cache to update...")
                time.sleep(2)
                inserted, errors = insert_dataframe_to_supabase(supabase, table_name, df)
                
                results['sheets'].append({
                    'sheet_name': sheet_name,
                    'table_name': table_name,
                    'rows_total': len(df),
                    'rows_inserted': inserted,
                    'success': len(errors) == 0,
                    'errors': errors
                })
                
                if errors:
                    print(f"⚠️  Completed with {len(errors)} error(s)")
                else:
                    print(f"✅ Successfully migrated {inserted} rows")
            else:
                print(f"❌ {message}")
                results['sheets'].append({
                    'sheet_name': sheet_name,
                    'table_name': table_name,
                    'success': False,
                    'error': message
                })
    
    except Exception as e:
        print(f"❌ Error processing file: {str(e)}")
        results['error'] = str(e)
    
    return results


def main():
    """Main migration function."""
    print("="*60)
    print("Google Sheets to Supabase Migration")
    print("="*60)
    print(f"Supabase URL: {SUPABASE_URL}")
    print(f"Sheets directory: {SHEETS_DIR}")
    
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Connected to Supabase API")
    
    parsed_url = urlparse(SUPABASE_URL)
    db_host = parsed_url.hostname
    
    try:
        pg_conn = psycopg2.connect(
            host=db_host,
            port=5432,
            database="postgres",
            user="postgres.your-tenant-id",
            password=POSTGRES_PASSWORD
        )
        print("✅ Connected to PostgreSQL database (session mode)")
    except Exception as e:
        print(f"⚠️  Session mode failed, trying transaction mode...")
        try:
            pg_conn = psycopg2.connect(
                host=db_host,
                port=6543,
                database="postgres",
                user="postgres.your-tenant-id",
                password=POSTGRES_PASSWORD
            )
            print("✅ Connected to PostgreSQL database (transaction mode)")
        except Exception as e2:
            print(f"❌ Both connection attempts failed.")
            print(f"   Session mode error: {str(e)}")
            print(f"   Transaction mode error: {str(e2)}")
            raise
    
    excel_files = list(SHEETS_DIR.glob("*.xlsx"))
    print(f"\nFound {len(excel_files)} Excel file(s) to migrate")
    
    if not excel_files:
        print("❌ No Excel files found in the directory")
        pg_conn.close()
        return
    
    all_results = []
    
    try:
        for excel_file in excel_files:
            result = migrate_excel_file(supabase, pg_conn, excel_file)
            all_results.append(result)
    finally:
        pg_conn.close()
        print("\n✅ PostgreSQL connection closed")
    
    print("\n" + "="*60)
    print("MIGRATION SUMMARY")
    print("="*60)
    
    for result in all_results:
        print(f"\n📄 {result['file']}")
        if 'error' in result:
            print(f"   ❌ Error: {result['error']}")
        else:
            for sheet in result['sheets']:
                status = "✅" if sheet['success'] else "❌"
                print(f"   {status} {sheet['sheet_name']} → {sheet['table_name']}")
                if 'rows_inserted' in sheet:
                    print(f"      Rows: {sheet['rows_inserted']}/{sheet['rows_total']}")
                if sheet.get('errors'):
                    print(f"      Errors: {len(sheet['errors'])}")
    
    report_path = SHEETS_DIR.parent.parent / "migration_report.json"
    with open(report_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\n📊 Full report saved to: {report_path}")


if __name__ == "__main__":
    main()
