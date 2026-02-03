/**
 * Google Sheets → FastAPI → Supabase Sync
 * 
 * CONFIGURATION:
 * 1. Go to Extensions > Apps Script
 * 2. Paste this code
 * 3. Edit the CONFIG below with your values
 * 4. Save (Ctrl+S)
 * 5. Click Triggers (clock icon) > Add Trigger > onChange > On change > Save
 * 
 * Your Spreadsheets:
 * - Copy of Leads Sent (ID: 10rEh9tS9tl10qTyUTPFZFEX0rbF60kHtBsPg9wb7Up4)
 * - Featured Agent Controls (ID: 1KyqbMETovx9qqfxVqx--MKUyrLx5o_KYI8r7tENjXOE)
 * - Agents Subscribed (ID: 1l2nXbD0q-h1in41KpbCHcuKbpADHqXW0yWkXNkGVRp4)
 * - Copy of Agents Subscribed (ID: 1qcuH6CUNZvxCR0400Ej__FYoSg1CEhn7iF8oXQ6g-sk)
 */

// ===== CONFIGURATION - EDIT THESE VALUES =====
const CONFIG = {
  // Your FastAPI endpoint URL (change to your server URL after deployment)
  API_URL: 'http://srv1165267.hstgr.cloud:8000/api/sheets/sync',
  
  // Webhook secret (must match SHEETS_WEBHOOK_SECRET in your .env)
  WEBHOOK_SECRET: 'your-secret-key-change-this',
  
  // Spreadsheet info - will be auto-detected
  SPREADSHEET_ID: SpreadsheetApp.getActiveSpreadsheet().getId(),
  SPREADSHEET_NAME: SpreadsheetApp.getActiveSpreadsheet().getName(),
  
  // Settings
  AUTO_CREATE_TABLE: true,  // Auto-create tables for new tabs
  BATCH_SIZE: 100
};
// ============================================

/**
 * Automatically triggered when sheet changes
 */
function onChange(e) {
  try {
    console.log('🔔 Change detected:', e.changeType);
    
    const sheet = SpreadsheetApp.getActiveSheet();
    const tabName = sheet.getName();
    
    if (e.changeType === 'INSERT_ROW' || e.changeType === 'EDIT') {
      syncSheetToAPI(sheet, tabName);
    } else if (e.changeType === 'REMOVE_ROW') {
      console.log('⚠️ Row deletion detected - manual cleanup may be required');
    }
    
  } catch (error) {
    console.error('❌ Error in onChange:', error);
    logError(error.toString());
  }
}

/**
 * Sync sheet data to FastAPI endpoint
 */
function syncSheetToAPI(sheet, tabName) {
  const data = getSheetData(sheet);
  
  if (data.length === 0) {
    console.log('ℹ️ No data to sync');
    return;
  }
  
  console.log(`📊 Syncing ${data.length} rows from tab: ${tabName}`);
  
  const payload = {
    spreadsheet_id: CONFIG.SPREADSHEET_ID,
    spreadsheet_name: CONFIG.SPREADSHEET_NAME,
    tab_name: tabName,
    data: data,
    auto_create_table: CONFIG.AUTO_CREATE_TABLE
  };
  
  const options = {
    method: 'post',
    headers: {
      'Content-Type': 'application/json',
      'X-Webhook-Secret': CONFIG.WEBHOOK_SECRET
    },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };
  
  try {
    const response = UrlFetchApp.fetch(CONFIG.API_URL, options);
    const statusCode = response.getResponseCode();
    const responseText = response.getContentText();
    
    if (statusCode >= 200 && statusCode < 300) {
      const result = JSON.parse(responseText);
      console.log(`✅ Sync successful: ${result.rows_synced} rows → ${result.table_name}`);
      if (result.table_created) {
        console.log(`🆕 Created new table: ${result.table_name}`);
      }
      return true;
    } else {
      console.error(`❌ API error (${statusCode}):`, responseText);
      logError(`API Error ${statusCode}: ${responseText}`);
      return false;
    }
  } catch (error) {
    console.error('❌ Failed to call API:', error);
    logError(error.toString());
    return false;
  }
}

/**
 * Get all data from sheet as array of objects
 */
function getSheetData(sheet) {
  const dataRange = sheet.getDataRange();
  const values = dataRange.getValues();
  
  if (values.length < 2) {
    return [];
  }
  
  const headers = values[0].map(h => cleanColumnName(h));
  const rows = values.slice(1);
  
  return rows.map(row => {
    const obj = {};
    headers.forEach((header, index) => {
      let value = row[index];
      
      if (value === '' || value === null) {
        obj[header] = null;
      } else if (typeof value === 'number' && !isFinite(value)) {
        obj[header] = null;
      } else if (value instanceof Date) {
        obj[header] = value.toISOString();
      } else {
        obj[header] = value;
      }
    });
    return obj;
  }).filter(row => {
    return Object.values(row).some(v => v !== null && v !== '');
  });
}

/**
 * Clean column names
 */
function cleanColumnName(name) {
  return String(name)
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9_]/g, '_')
    .replace(/_+/g, '_')
    .replace(/^_|_$/g, '')
    .substring(0, 63);
}

/**
 * Manual sync - Run this from Apps Script editor to test
 */
function manualSync() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const tabName = sheet.getName();
  
  console.log('🔄 Starting manual sync...');
  console.log(`📋 Spreadsheet: ${CONFIG.SPREADSHEET_NAME}`);
  console.log(`📄 Tab: ${tabName}`);
  
  syncSheetToAPI(sheet, tabName);
  
  console.log('✅ Manual sync completed');
}

/**
 * Log errors to a separate sheet
 */
function logError(message) {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    let logSheet = ss.getSheetByName('Sync Logs');
    
    if (!logSheet) {
      logSheet = ss.insertSheet('Sync Logs');
      logSheet.appendRow(['Timestamp', 'Error Message']);
    }
    
    logSheet.appendRow([new Date(), message]);
  } catch (e) {
    console.error('Failed to log error:', e);
  }
}

/**
 * Test API connection - Run this to verify setup
 */
function testAPIConnection() {
  const testUrl = CONFIG.API_URL.replace('/sync', '/health');
  
  try {
    const response = UrlFetchApp.fetch(testUrl, {
      method: 'get',
      muteHttpExceptions: true
    });
    
    const statusCode = response.getResponseCode();
    const responseText = response.getContentText();
    
    console.log('=== API Connection Test ===');
    console.log('URL:', testUrl);
    console.log('Status:', statusCode);
    console.log('Response:', responseText);
    
    if (statusCode === 200) {
      console.log('✅ API connection is working!');
    } else {
      console.log('❌ API connection failed');
    }
  } catch (error) {
    console.log('❌ Connection error:', error.toString());
  }
}

/**
 * View current configuration
 */
function viewConfig() {
  console.log('=== Current Configuration ===');
  console.log('API URL:', CONFIG.API_URL);
  console.log('Spreadsheet ID:', CONFIG.SPREADSHEET_ID);
  console.log('Spreadsheet Name:', CONFIG.SPREADSHEET_NAME);
  console.log('Auto Create Tables:', CONFIG.AUTO_CREATE_TABLE);
  console.log('Webhook Secret Set:', CONFIG.WEBHOOK_SECRET !== 'your-secret-key-change-this');
}
