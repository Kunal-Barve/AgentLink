"""
Google Sheets Dynamic Sync Endpoint
Auto-creates tables and syncs data from Google Sheets

Flow: Google Sheets → Apps Script → This FastAPI Endpoint → Supabase
"""

from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv
import logging
import psycopg2
from psycopg2 import sql
from supabase import create_client, Client
import re
from datetime import datetime

load_dotenv()

router = APIRouter(prefix="/api/sheets", tags=["Google Sheets Sync"])

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_DB_PASSWORD = os.getenv("SUPABASE_DB_PASSWORD")
WEBHOOK_SECRET = os.getenv("SHEETS_WEBHOOK_SECRET", "change-me-in-production")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

logger = logging.getLogger(__name__)


class SheetSyncRequest(BaseModel):
    spreadsheet_id: str = Field(..., description="Google Spreadsheet ID")
    spreadsheet_name: str = Field(..., description="Name of the spreadsheet")
    tab_name: str = Field(..., description="Tab/sheet name")
    data: List[Dict[str, Any]] = Field(..., description="Array of row data")
    auto_create_table: bool = Field(default=True, description="Auto-create table if not exists")


def clean_name(name: str) -> str:
    """Clean sheet/column names for database compatibility"""
    cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', str(name).lower().strip())
    cleaned = re.sub(r'_+', '_', cleaned)
    cleaned = re.sub(r'^_|_$', '', cleaned)
    return cleaned[:63]


def infer_pg_type(values: List[Any]) -> str:
    """Infer PostgreSQL type from data values"""
    non_null_values = [v for v in values if v is not None and v != '']
    
    if not non_null_values:
        return "TEXT"
    
    sample = non_null_values[:100]
    
    all_bool = all(isinstance(v, bool) or str(v).lower() in ['true', 'false', 'yes', 'no'] for v in sample)
    if all_bool:
        return "BOOLEAN"
    
    all_int = all(isinstance(v, int) or (isinstance(v, str) and v.isdigit()) for v in sample)
    if all_int:
        return "BIGINT"
    
    all_numeric = True
    for v in sample:
        try:
            float(v)
        except (ValueError, TypeError):
            all_numeric = False
            break
    if all_numeric:
        return "DOUBLE PRECISION"
    
    all_date = True
    for v in sample:
        if isinstance(v, datetime):
            continue
        try:
            if isinstance(v, str) and ('/' in v or '-' in v):
                continue
            all_date = False
            break
        except:
            all_date = False
            break
    if all_date:
        return "TIMESTAMP"
    
    return "TEXT"


def get_pg_connection():
    """Get PostgreSQL connection"""
    return psycopg2.connect(
        host=SUPABASE_URL.replace("http://", "").replace("https://", "").split(":")[0],
        port=5432,
        database="postgres",
        user="postgres",
        password=SUPABASE_DB_PASSWORD
    )


def create_table_from_data(table_name: str, data: List[Dict[str, Any]]) -> bool:
    """Create table dynamically based on data structure"""
    if not data:
        raise ValueError("Cannot create table from empty data")
    
    columns = {}
    for row in data[:100]:
        for key, value in row.items():
            if key not in columns:
                columns[key] = []
            columns[key].append(value)
    
    column_defs = []
    for col_name, values in columns.items():
        pg_type = infer_pg_type(values)
        column_defs.append(f'"{col_name}" {pg_type}')
    
    column_defs.append('"created_at" TIMESTAMP DEFAULT NOW()')
    column_defs.append('"updated_at" TIMESTAMP DEFAULT NOW()')
    
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS "{table_name}" (
        id BIGSERIAL PRIMARY KEY,
        {', '.join(column_defs)}
    );
    """
    
    try:
        conn = get_pg_connection()
        cur = conn.cursor()
        cur.execute(create_sql)
        
        cur.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_created_at ON "{table_name}"(created_at);')
        
        conn.commit()
        cur.close()
        conn.close()
        
        logger.info(f"✅ Created table: {table_name} with {len(column_defs)} columns")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create table {table_name}: {e}")
        raise


def table_exists(table_name: str) -> bool:
    """Check if table exists in Supabase"""
    try:
        result = supabase.table(table_name).select("*").limit(1).execute()
        return True
    except Exception as e:
        return False


def clean_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Clean data for database insertion"""
    cleaned = []
    
    for row in data:
        cleaned_row = {}
        for key, value in row.items():
            if value is None or value == '':
                cleaned_row[key] = None
            elif isinstance(value, float):
                if value != value or value == float('inf') or value == float('-inf'):
                    cleaned_row[key] = None
                else:
                    cleaned_row[key] = value
            elif isinstance(value, datetime):
                cleaned_row[key] = value.isoformat()
            else:
                cleaned_row[key] = value
        
        if any(v is not None for v in cleaned_row.values()):
            cleaned.append(cleaned_row)
    
    return cleaned


@router.post("/sync")
async def sync_sheet(
    request: SheetSyncRequest,
    x_webhook_secret: Optional[str] = Header(None)
):
    """
    Sync Google Sheets data to Supabase with auto-table creation
    
    Flow:
    1. Receive data from Apps Script
    2. Generate table name from sheet info
    3. Check if table exists, create if needed
    4. Clean and validate data
    5. Upsert to Supabase
    6. Return success/error
    """
    
    if x_webhook_secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
    
    if not request.data:
        return {
            "status": "success",
            "message": "No data to sync",
            "rows_synced": 0
        }
    
    try:
        spreadsheet_base = clean_name(request.spreadsheet_name)
        tab_clean = clean_name(request.tab_name)
        
        if tab_clean in ['sheet1', 'sheet_1']:
            table_name = spreadsheet_base
        else:
            table_name = f"{spreadsheet_base}_{tab_clean}"
        
        logger.info(f"📊 Syncing: {request.spreadsheet_name} / {request.tab_name} → {table_name}")
        
        exists = table_exists(table_name)
        
        if not exists and request.auto_create_table:
            logger.info(f"🔨 Table {table_name} doesn't exist, creating...")
            create_table_from_data(table_name, request.data)
        elif not exists:
            raise HTTPException(
                status_code=404,
                detail=f"Table {table_name} does not exist and auto_create_table is False"
            )
        
        cleaned_data = clean_data(request.data)
        
        if not cleaned_data:
            return {
                "status": "success",
                "message": "No valid data after cleaning",
                "rows_synced": 0,
                "table_name": table_name
            }
        
        # DELETE ALL EXISTING ROWS (full replace strategy to prevent duplicates)
        logger.info(f"🗑️ Deleting existing data from {table_name}...")
        try:
            # Delete all rows where id > 0 (effectively all rows)
            supabase.table(table_name).delete().neq("id", 0).execute()
            logger.info(f"  ✅ Cleared existing data")
        except Exception as e:
            logger.warning(f"  ⚠️ Delete failed (table might be empty): {e}")
        
        # INSERT FRESH DATA
        batch_size = 100
        total_synced = 0
        
        for i in range(0, len(cleaned_data), batch_size):
            batch = cleaned_data[i:i + batch_size]
            # Use INSERT instead of UPSERT to avoid confusion
            result = supabase.table(table_name).insert(batch).execute()
            total_synced += len(batch)
            logger.info(f"  ✅ Inserted batch {i//batch_size + 1}: {len(batch)} rows")
        
        return {
            "status": "success",
            "message": f"Successfully synced {total_synced} rows to {table_name}",
            "rows_synced": total_synced,
            "table_name": table_name,
            "table_created": not exists,
            "spreadsheet_id": request.spreadsheet_id,
            "tab_name": request.tab_name
        }
        
    except Exception as e:
        logger.error(f"❌ Sync failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/tables")
async def list_tables():
    """List all synced tables"""
    try:
        conn = get_pg_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        
        tables = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        
        return {
            "status": "success",
            "tables": tables,
            "count": len(tables)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/table/{table_name}/schema")
async def get_table_schema(table_name: str):
    """Get schema for a specific table"""
    try:
        conn = get_pg_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position;
        """, (table_name,))
        
        columns = []
        for row in cur.fetchall():
            columns.append({
                "name": row[0],
                "type": row[1],
                "nullable": row[2] == 'YES'
            })
        
        cur.close()
        conn.close()
        
        return {
            "status": "success",
            "table_name": table_name,
            "columns": columns
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        supabase.table('agents_subscribed').select('*').limit(1).execute()
        return {
            "status": "healthy",
            "supabase": "connected",
            "endpoint": "sheets-sync"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
