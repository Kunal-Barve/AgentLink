"""
Service Account Sync - Alternative to Apps Script
Polls Google Sheets API and syncs to Supabase

Use cases:
- Backup sync (run nightly)
- High-volume sheets (>100 sheets)
- Need historical change tracking
- Apps Script quota exceeded

Setup:
1. Create Google Service Account: https://console.cloud.google.com/
2. Download JSON key file
3. Share each Google Sheet with service account email
4. Configure environment variables
5. Run as cron job or scheduled task
"""

import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import json

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from supabase import create_client, Client
from dotenv import load_dotenv
import pandas as pd
import numpy as np

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sheets_sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON', 'service_account.json')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
BATCH_SIZE = 100

# Google Sheets API scopes
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# Sheet to Table mapping
SHEET_MAPPING = {
    'YOUR_SHEET_ID_1': {
        'name': 'Agents Subscribed',
        'tabs': {
            'Sheet1': 'agents_subscribed',
            'Costs & Charges': 'agents_subscribed_costs_charges',
            'Agents Cancelled Subscriptions': 'agents_subscribed_agents_cancelled_subscriptions',
            'Area Key': 'agents_subscribed_area_key'
        }
    },
    'YOUR_SHEET_ID_2': {
        'name': 'Copy of Leads Sent',
        'tabs': {
            'Sheet1': 'leads_sent',
            'Advocacy': 'leads_sent_advocacy',
            'Leaderboard': 'leads_sent_leaderboard',
            'Agent Report': 'leads_sent_agent_report'
        }
    },
    'YOUR_SHEET_ID_3': {
        'name': 'Featured Agent Controls',
        'tabs': {
            'Sheet1': 'featured_agent_controls',
            'Sheet3': 'featured_agent_controls_sheet3'
        }
    },
    'YOUR_SHEET_ID_4': {
        'name': 'Suburb Leads No Agent',
        'tabs': {
            'Sheet1': 'suburb_leads_no_agent',
            'NSW': 'suburb_leads_no_agent_nsw',
            'QLD': 'suburb_leads_no_agent_qld',
            'VIC': 'suburb_leads_no_agent_vic',
            'SA': 'suburb_leads_no_agent_sa',
            'WA': 'suburb_leads_no_agent_wa',
            'NT': 'suburb_leads_no_agent_nt',
            'TAS': 'suburb_leads_no_agent_tas'
        }
    }
}


class GoogleSheetsSync:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        self.sheets_service = self._get_sheets_service()
        
    def _get_sheets_service(self):
        """Initialize Google Sheets API service"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES
            )
            service = build('sheets', 'v4', credentials=credentials)
            logger.info("Google Sheets API service initialized")
            return service
        except Exception as e:
            logger.error(f"Failed to initialize Sheets API: {e}")
            raise
    
    def clean_column_name(self, name: str) -> str:
        """Clean column names to match database format"""
        return str(name).lower().strip() \
            .replace(' ', '_') \
            .replace('/', '_') \
            .replace('-', '_') \
            .replace('?', '') \
            .replace('!', '') \
            .replace('(', '') \
            .replace(')', '') \
            .replace('.', '') \
            [:63]
    
    def get_sheet_data(self, spreadsheet_id: str, range_name: str) -> List[Dict[str, Any]]:
        """Fetch data from Google Sheet"""
        try:
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            if not values or len(values) < 2:
                logger.warning(f"No data found in {range_name}")
                return []
            
            headers = [self.clean_column_name(h) for h in values[0]]
            rows = values[1:]
            
            data = []
            for row in rows:
                # Pad row to match header length
                while len(row) < len(headers):
                    row.append('')
                
                row_dict = {}
                for i, header in enumerate(headers):
                    value = row[i] if i < len(row) else None
                    
                    # Clean data
                    if value == '' or value is None:
                        row_dict[header] = None
                    elif isinstance(value, (int, float)):
                        if np.isnan(value) or np.isinf(value):
                            row_dict[header] = None
                        else:
                            row_dict[header] = value
                    else:
                        row_dict[header] = value
                
                # Only include rows with at least one non-null value
                if any(v is not None for v in row_dict.values()):
                    data.append(row_dict)
            
            logger.info(f"Fetched {len(data)} rows from {range_name}")
            return data
            
        except HttpError as e:
            logger.error(f"HTTP error fetching {range_name}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching {range_name}: {e}")
            return []
    
    def upsert_to_supabase(self, table_name: str, data: List[Dict[str, Any]]) -> bool:
        """Upsert data to Supabase in batches"""
        if not data:
            logger.info(f"No data to upsert to {table_name}")
            return True
        
        try:
            total_inserted = 0
            
            for i in range(0, len(data), BATCH_SIZE):
                batch = data[i:i + BATCH_SIZE]
                
                result = self.supabase.table(table_name).upsert(batch).execute()
                total_inserted += len(batch)
                logger.info(f"Upserted batch {i//BATCH_SIZE + 1} ({len(batch)} rows) to {table_name}")
            
            logger.info(f"✅ Successfully upserted {total_inserted} rows to {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upsert to {table_name}: {e}")
            return False
    
    def sync_sheet(self, spreadsheet_id: str, tab_name: str, table_name: str) -> bool:
        """Sync a single sheet tab to Supabase"""
        logger.info(f"Syncing {tab_name} → {table_name}")
        
        data = self.get_sheet_data(spreadsheet_id, tab_name)
        
        if not data:
            logger.warning(f"No data to sync for {tab_name}")
            return True
        
        return self.upsert_to_supabase(table_name, data)
    
    def sync_all(self):
        """Sync all configured sheets"""
        logger.info("=" * 60)
        logger.info("Starting full sync of all Google Sheets")
        logger.info("=" * 60)
        
        start_time = time.time()
        success_count = 0
        fail_count = 0
        
        for spreadsheet_id, config in SHEET_MAPPING.items():
            sheet_name = config['name']
            logger.info(f"\n📄 Processing: {sheet_name}")
            
            for tab_name, table_name in config['tabs'].items():
                try:
                    success = self.sync_sheet(spreadsheet_id, tab_name, table_name)
                    if success:
                        success_count += 1
                    else:
                        fail_count += 1
                except Exception as e:
                    logger.error(f"Error syncing {tab_name}: {e}")
                    fail_count += 1
        
        elapsed = time.time() - start_time
        
        logger.info("\n" + "=" * 60)
        logger.info("Sync Summary")
        logger.info("=" * 60)
        logger.info(f"✅ Successful: {success_count}")
        logger.info(f"❌ Failed: {fail_count}")
        logger.info(f"⏱️  Duration: {elapsed:.2f} seconds")
        logger.info("=" * 60)


def main():
    """Main entry point"""
    logger.info("Google Sheets → Supabase Service Account Sync")
    
    try:
        sync = GoogleSheetsSync()
        sync.sync_all()
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        raise


if __name__ == "__main__":
    main()


# Cron job examples:
"""
# Run every 15 minutes
*/15 * * * * cd /path/to/project && python app/scripts/google_sheets_sync/service_account_sync.py

# Run every hour
0 * * * * cd /path/to/project && python app/scripts/google_sheets_sync/service_account_sync.py

# Run every night at 2 AM (backup sync)
0 2 * * * cd /path/to/project && python app/scripts/google_sheets_sync/service_account_sync.py

# Windows Task Scheduler
# Create task: Run daily at 2 AM
# Action: python D:\path\to\service_account_sync.py
"""
