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
  API_URL: 'http://72.62.64.72:9000/sync',
  WEBHOOK_SECRET: 'nimdt332mkAfvm',
  SPREADSHEET_ID: SpreadsheetApp.getActiveSpreadsheet().getId(),
  SPREADSHEET_NAME: SpreadsheetApp.getActiveSpreadsheet().getName(),
  AUTO_CREATE_TABLE: true,
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
  
  if (values.length === 0) {
    return [];
  }
  
  // Check if row 1 looks like headers or data
  const firstRow = values[0];
  const hasHeaders = firstRow.some(cell => {
    const str = String(cell).toLowerCase();
    // Common header patterns
    return str.includes('name') || str.includes('email') || str.includes('phone') || 
           str.includes('state') || str.includes('suburb') || str.includes('address') ||
           str.includes('date') || str.includes('agent') || str === 'id';
  });
  
  let headers;
  let dataRows;
  
  if (!hasHeaders && values.length >= 1) {
    // No headers detected - auto-generate all column names and include row 1 as data
    console.log(`⚠️ No headers detected in "${sheet.getName()}" - auto-generating column names`);
    headers = firstRow.map((_, index) => `column_${index + 1}`);
    dataRows = values; // Include all rows including first row
  } else {
    // Normal case: row 1 is headers
    headers = firstRow.map((h, index) => {
      const cleaned = cleanColumnName(h);
      // If header is empty after cleaning, generate a name based on position
      if (!cleaned || cleaned === '') {
        return `column_${index + 1}`;
      }
      return cleaned;
    });
    dataRows = values.slice(1);
  }
  
  if (dataRows.length === 0) {
    return [];
  }
  
  return dataRows.map(row => {
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
 * Sync ALL tabs in the spreadsheet - Run this to sync everything at once
 */
function syncAllTabs() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const allSheets = ss.getSheets();
  
  // Skip system/log tabs and unwanted tabs
  const skipTabs = ['Sync Logs', 'sync logs', 'logs', 'errors', 'Sheet1', 'Sheet6', 'Sheet3'];
  const sheets = allSheets.filter(sheet => {
    const name = sheet.getName();
    return !skipTabs.includes(name);
  });
  
  console.log('🔄 Starting sync for ALL tabs...');
  console.log(`📋 Spreadsheet: ${CONFIG.SPREADSHEET_NAME}`);
  console.log(`📊 Total tabs: ${allSheets.length}, Syncing: ${sheets.length} (skipped ${allSheets.length - sheets.length} system tabs)`);
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  
  let successCount = 0;
  let failCount = 0;
  let skippedCount = 0;
  
  sheets.forEach((sheet, index) => {
    const tabName = sheet.getName();
    console.log(`\n[${index + 1}/${sheets.length}] Syncing: ${tabName}`);
    
    try {
      const success = syncSheetToAPI(sheet, tabName);
      if (success) {
        successCount++;
      } else {
        failCount++;
      }
    } catch (error) {
      console.error(`❌ Failed to sync ${tabName}:`, error);
      failCount++;
    }
  });
  
  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log(`✅ Sync complete: ${successCount} successful, ${failCount} failed`);
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
}

/**
 * Log errors to console only (no sheet creation for sensitive data)
 */
function logError(message) {
  // Only log to execution log, don't create sheets
  console.error('🔴 Error:', message);
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

/**
 * Find empty columns in ALL tabs - Run this to debug empty column issues
 */
function findEmptyColumns() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheets = ss.getSheets();
  
  console.log('🔍 Scanning all tabs for empty columns...');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  
  let totalEmpty = 0;
  
  sheets.forEach(sheet => {
    const tabName = sheet.getName();
    const lastCol = sheet.getLastColumn();
    const headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0];
    
    let emptyCount = 0;
    const emptyPositions = [];
    
    headers.forEach((header, index) => {
      if (header === '' || header === null || String(header).trim() === '') {
        emptyCount++;
        totalEmpty++;
        const colLetter = String.fromCharCode(65 + (index % 26));
        emptyPositions.push(`Column ${colLetter} (position ${index + 1})`);
      }
    });
    
    if (emptyCount > 0) {
      console.log(`\n❌ Tab "${tabName}": ${emptyCount} empty column(s)`);
      emptyPositions.forEach(pos => console.log(`   - ${pos}`));
    } else {
      console.log(`\n✅ Tab "${tabName}": No empty columns`);
    }
  });
  
  console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log(`Total empty columns found: ${totalEmpty}`);
  console.log('💡 Tip: Delete empty columns or add header names to fix sync issues');
}
