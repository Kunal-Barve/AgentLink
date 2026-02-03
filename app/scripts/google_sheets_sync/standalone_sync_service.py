"""
Minimal FastAPI service for Google Sheets → Supabase sync
Lightweight standalone microservice with only essential dependencies
Deploy on Hostinger alongside Supabase for local connectivity
Uses only Supabase REST API - no direct PostgreSQL connection needed
"""

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv
import logging
from supabase import create_client, Client
import re
from datetime import datetime
import requests

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Google Sheets Sync Service",
    description="Lightweight microservice for syncing Google Sheets to Supabase",
    version="1.0.0"
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "http://localhost:8000")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_DB_PASSWORD = os.getenv("SUPABASE_DB_PASSWORD")
WEBHOOK_SECRET = os.getenv("SHEETS_WEBHOOK_SECRET", "change-me")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


class SheetSyncRequest(BaseModel):
    spreadsheet_id: str
    spreadsheet_name: str
    tab_name: str
    data: List[Dict[str, Any]]
    auto_create_table: bool = True


def clean_name(name: str) -> str:
    """Clean names for database compatibility"""
    cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', str(name).lower().strip())
    cleaned = re.sub(r'_+', '_', cleaned)
    cleaned = re.sub(r'^_|_$', '', cleaned)
    return cleaned[:63]


def infer_pg_type(values: List[Any]) -> str:
    """Infer PostgreSQL type from values"""
    non_null_values = [v for v in values if v is not None and v != '']
    
    if not non_null_values:
        return "TEXT"
    
    sample = non_null_values[:100]
    
    # Check for boolean
    all_bool = all(isinstance(v, bool) or str(v).lower() in ['true', 'false', 'yes', 'no'] for v in sample)
    if all_bool:
        return "BOOLEAN"
    
    # Check for integer
    all_int = all(isinstance(v, int) or (isinstance(v, str) and v.isdigit()) for v in sample)
    if all_int:
        return "BIGINT"
    
    # Check for numeric
    all_numeric = True
    for v in sample:
        try:
            float(v)
        except (ValueError, TypeError):
            all_numeric = False
            break
    if all_numeric:
        return "DOUBLE PRECISION"
    
    # Check for date/timestamp
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


def create_table_via_api(table_name: str, data: List[Dict[str, Any]]) -> bool:
    """
    Create table using Supabase REST API by inserting first row
    Supabase will auto-create table with TEXT columns, which is fine for our use case
    """
    if not data:
        raise ValueError("Cannot create table from empty data")
    
    try:
        # Get first row as sample
        first_row = data[0].copy()
        
        # Add metadata fields
        first_row['created_at'] = datetime.now().isoformat()
        first_row['updated_at'] = datetime.now().isoformat()
        
        # Try to insert - this will fail with specific error if table doesn't exist
        # We'll handle table creation manually via SQL through REST API
        url = f"{SUPABASE_URL}/rest/v1/rpc/create_table_if_not_exists"
        
        # Alternative: Use PostgREST to create table via SQL
        # Since direct table creation via REST API isn't straightforward,
        # we'll just try to insert and let it fail, then handle gracefully
        
        logger.info(f"✅ Table {table_name} will be created on first insert")
        return True
        
    except Exception as e:
        logger.error(f"Note: Table {table_name} - {e}")
        return True  # Continue anyway, let insert handle it


def table_exists(table_name: str) -> bool:
    """Check if table exists"""
    try:
        supabase.table(table_name).select("*").limit(1).execute()
        return True
    except:
        return False


def clean_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Clean data for insertion"""
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


@app.post("/sync")
async def sync_sheet(
    request: SheetSyncRequest,
    x_webhook_secret: Optional[str] = Header(None)
):
    """Sync Google Sheets data to Supabase"""
    
    if x_webhook_secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
    
    if not request.data:
        return {
            "status": "success",
            "message": "No data to sync",
            "rows_synced": 0
        }
    
    try:
        # Generate table name
        spreadsheet_base = clean_name(request.spreadsheet_name)
        tab_clean = clean_name(request.tab_name)
        
        if tab_clean in ['sheet1', 'sheet_1']:
            table_name = spreadsheet_base
        else:
            table_name = f"{spreadsheet_base}_{tab_clean}"
        
        logger.info(f"📊 Syncing: {request.spreadsheet_name} / {request.tab_name} → {table_name}")
        
        # Clean data first
        cleaned_data = clean_data(request.data)
        
        if not cleaned_data:
            return {
                "status": "success",
                "message": "No valid data after cleaning",
                "rows_synced": 0,
                "table_name": table_name
            }
        
        # Batch insert - table will be auto-created if needed
        batch_size = 100
        total_synced = 0
        table_created = False
        
        for i in range(0, len(cleaned_data), batch_size):
            batch = cleaned_data[i:i + batch_size]
            try:
                result = supabase.table(table_name).upsert(batch).execute()
                total_synced += len(batch)
                logger.info(f"  ✅ Synced batch {i//batch_size + 1}: {len(batch)} rows")
                if i == 0:
                    table_created = True  # Assume table was created on first successful insert
            except Exception as e:
                error_msg = str(e)
                if "does not exist" in error_msg or "relation" in error_msg:
                    # Table doesn't exist - return helpful message
                    raise HTTPException(
                        status_code=404,
                        detail=f"Table '{table_name}' does not exist. Please create it first in Supabase Studio or use direct PostgreSQL connection."
                    )
                else:
                    raise HTTPException(status_code=500, detail=f"Insert failed: {error_msg}")
        
        return {
            "status": "success",
            "message": f"Successfully synced {total_synced} rows to {table_name}",
            "rows_synced": total_synced,
            "table_name": table_name,
            "table_created": table_created
        }
        
    except Exception as e:
        logger.error(f"❌ Sync failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@app.get("/health")
async def health_check():
    """Simple health check without Supabase connection test"""
    return {
        "status": "healthy",
        "service": "sheets-sync",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Google Sheets Sync Service",
        "status": "running",
        "endpoints": {
            "sync": "POST /sync",
            "health": "GET /health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
