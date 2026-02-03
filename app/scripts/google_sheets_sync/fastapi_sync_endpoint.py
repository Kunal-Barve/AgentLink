"""
FastAPI Webhook Endpoint for Google Sheets Sync (Optional)
Use this if you need custom validation/transformation before Supabase insert

Setup:
1. Add to your main.py or create separate FastAPI app
2. Deploy to your server
3. Update Apps Script to call this webhook instead of direct Supabase
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
import os
from dotenv import load_dotenv
import logging

load_dotenv()

router = APIRouter(prefix="/api/sheets-sync", tags=["Sheets Sync"])

# Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

# Security: Webhook secret for validation
WEBHOOK_SECRET = os.getenv("SHEETS_WEBHOOK_SECRET", "your-secret-key-here")

logger = logging.getLogger(__name__)


class SheetSyncRequest(BaseModel):
    table_name: str
    data: List[Dict[str, Any]]
    operation: str = "upsert"  # upsert, insert, update, delete


@router.post("/google_sheets_sync")
async def sync_from_sheets(
    request: SheetSyncRequest,
    x_webhook_secret: Optional[str] = Header(None)
):
    """
    Webhook endpoint for Google Sheets sync
    
    Usage in Apps Script:
    ```javascript
    const url = 'http://your-server.com/api/sheets-sync/webhook';
    const options = {
      method: 'post',
      headers: {
        'Content-Type': 'application/json',
        'X-Webhook-Secret': 'your-secret-key-here'
      },
      payload: JSON.stringify({
        table_name: 'agents_subscribed',
        data: records,
        operation: 'upsert'
      })
    };
    UrlFetchApp.fetch(url, options);
    ```
    """
    
    # Validate webhook secret
    if x_webhook_secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
    
    # Validate table name (whitelist approach for security)
    ALLOWED_TABLES = [
        'agents_subscribed',
        'agents_subscribed_costs_charges',
        'agents_subscribed_agents_cancelled_subscriptions',
        'agents_subscribed_area_key',
        'leads_sent',
        'leads_sent_advocacy',
        'leads_sent_leaderboard',
        'leads_sent_agent_report',
        'featured_agent_controls',
        'featured_agent_controls_sheet3',
        'suburb_leads_no_agent',
        'suburb_leads_no_agent_nsw',
        'suburb_leads_no_agent_qld',
        'suburb_leads_no_agent_vic',
        'suburb_leads_no_agent_sa',
        'suburb_leads_no_agent_wa',
        'suburb_leads_no_agent_nt',
        'suburb_leads_no_agent_tas'
    ]
    
    if request.table_name not in ALLOWED_TABLES:
        raise HTTPException(status_code=400, detail="Invalid table name")
    
    if not request.data:
        return {"status": "success", "message": "No data to sync", "rows_affected": 0}
    
    try:
        # Custom validation/transformation logic here
        cleaned_data = validate_and_clean_data(request.data, request.table_name)
        
        # Sync to Supabase
        if request.operation == "upsert":
            result = supabase.table(request.table_name).upsert(cleaned_data).execute()
        elif request.operation == "insert":
            result = supabase.table(request.table_name).insert(cleaned_data).execute()
        elif request.operation == "update":
            # Requires primary key in data
            result = supabase.table(request.table_name).update(cleaned_data).execute()
        elif request.operation == "delete":
            # Requires filter criteria
            raise HTTPException(status_code=400, detail="Delete operation requires filter criteria")
        else:
            raise HTTPException(status_code=400, detail="Invalid operation")
        
        logger.info(f"Synced {len(cleaned_data)} rows to {request.table_name}")
        
        return {
            "status": "success",
            "message": f"Successfully synced {len(cleaned_data)} rows",
            "rows_affected": len(cleaned_data),
            "table": request.table_name
        }
        
    except Exception as e:
        logger.error(f"Sync error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def validate_and_clean_data(data: List[Dict[str, Any]], table_name: str) -> List[Dict[str, Any]]:
    """
    Custom validation and transformation logic
    Add your business rules here
    """
    cleaned = []
    
    for row in data:
        cleaned_row = {}
        
        for key, value in row.items():
            # Handle None/empty values
            if value is None or value == '':
                cleaned_row[key] = None
                continue
            
            # Handle infinity/NaN
            if isinstance(value, float):
                if not (value != value or value == float('inf') or value == float('-inf')):
                    cleaned_row[key] = value
                else:
                    cleaned_row[key] = None
                continue
            
            # Custom validation by table
            if table_name == 'agents_subscribed':
                # Example: Validate email format
                if key == 'email' and '@' not in str(value):
                    logger.warning(f"Invalid email: {value}")
                    cleaned_row[key] = None
                    continue
                
                # Example: Ensure phone is numeric
                if key == 'phone' and value:
                    cleaned_row[key] = ''.join(filter(str.isdigit, str(value)))
                    continue
            
            cleaned_row[key] = value
        
        # Only add if row has at least one non-null value
        if any(v is not None for v in cleaned_row.values()):
            cleaned.append(cleaned_row)
    
    return cleaned


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Supabase connection
        supabase.table('agents_subscribed').select('*').limit(1).execute()
        return {"status": "healthy", "supabase": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


# Apps Script webhook caller example
APPS_SCRIPT_WEBHOOK_EXAMPLE = """
// Add this to your Google Apps Script instead of direct Supabase call

function upsertToWebhook(records) {
  const url = 'http://your-server.com/api/sheets-sync/google_sheets_sync';
  
  const payload = {
    table_name: CONFIG.TABLE_NAME,
    data: records,
    operation: 'upsert'
  };
  
  const options = {
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      'X-Webhook-Secret': 'your-secret-key-here'
    },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };
  
  try {
    const response = UrlFetchApp.fetch(url, options);
    const statusCode = response.getResponseCode();
    
    if (statusCode >= 200 && statusCode < 300) {
      const result = JSON.parse(response.getContentText());
      console.log(`Successfully synced ${result.rows_affected} records`);
      return true;
    } else {
      console.error(`Webhook error (${statusCode}):`, response.getContentText());
      logError(`Webhook Error ${statusCode}: ${response.getContentText()}`);
      return false;
    }
  } catch (error) {
    console.error('Failed to call webhook:', error);
    logError(error.toString());
    return false;
  }
}
"""
