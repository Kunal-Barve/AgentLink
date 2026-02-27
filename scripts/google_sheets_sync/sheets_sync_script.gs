/**
 * Google Sheets to Supabase Real-Time Sync
 * 
 * Setup Instructions:
 * 1. Copy this code to Apps Script (Extensions > Apps Script)
 * 2. Set Script Properties (Project Settings > Script Properties):
 *    - SUPABASE_URL: http://srv1165267.hstgr.cloud:8000
 *    - SUPABASE_SERVICE_KEY: your-service-role-key
 *    - TABLE_NAME: your_table_name (e.g., agents_subscribed)
 * 3. Install onChange trigger (Triggers > Add Trigger > On change)
 */

// Configuration - Get from Script Properties
const CONFIG = {
  SUPABASE_URL: PropertiesService.getScriptProperties().getProperty('SUPABASE_URL'),
  SUPABASE_SERVICE_KEY: PropertiesService.getScriptProperties().getProperty('SUPABASE_SERVICE_KEY'),
  TABLE_NAME: PropertiesService.getScriptProperties().getProperty('TABLE_NAME'),
  BATCH_SIZE: 100 // Process rows in batches
};

/**
 * Main onChange trigger function
 * Automatically called when sheet changes
 */
function onChange(e) {
  try {
    console.log('Change detected:', e.changeType);
    
    if (!CONFIG.SUPABASE_URL || !CONFIG.SUPABASE_SERVICE_KEY || !CONFIG.TABLE_NAME) {
      throw new Error('Missing configuration. Please set Script Properties.');
    }
    
    const sheet = SpreadsheetApp.getActiveSheet();
    
    // Get change type
    if (e.changeType === 'INSERT_ROW' || e.changeType === 'EDIT') {
      syncSheetToSupabase(sheet);
    } else if (e.changeType === 'REMOVE_ROW') {
      // Handle row deletion if needed
      console.log('Row deletion detected - manual cleanup may be required');
    }
    
  } catch (error) {
    console.error('Error in onChange:', error);
    logError(error.toString());
  }
}

/**
 * Sync entire sheet to Supabase (upsert strategy)
 */
function syncSheetToSupabase(sheet) {
  const data = getSheetData(sheet);
  
  if (data.length === 0) {
    console.log('No data to sync');
    return;
  }
  
  console.log(`Syncing ${data.length} rows to Supabase table: ${CONFIG.TABLE_NAME}`);
  
  // Process in batches
  for (let i = 0; i < data.length; i += CONFIG.BATCH_SIZE) {
    const batch = data.slice(i, i + CONFIG.BATCH_SIZE);
    upsertToSupabase(batch);
  }
  
  console.log('Sync completed successfully');
}

/**
 * Get all data from sheet as array of objects
 */
function getSheetData(sheet) {
  const dataRange = sheet.getDataRange();
  const values = dataRange.getValues();
  
  if (values.length < 2) {
    return []; // No data rows
  }
  
  const headers = values[0].map(h => cleanColumnName(h));
  const rows = values.slice(1);
  
  return rows.map(row => {
    const obj = {};
    headers.forEach((header, index) => {
      let value = row[index];
      
      // Clean data
      if (value === '' || value === null) {
        obj[header] = null;
      } else if (typeof value === 'number' && !isFinite(value)) {
        obj[header] = null; // Handle Infinity/NaN
      } else if (value instanceof Date) {
        obj[header] = value.toISOString(); // Convert dates to ISO string
      } else {
        obj[header] = value;
      }
    });
    return obj;
  }).filter(row => {
    // Filter out completely empty rows
    return Object.values(row).some(v => v !== null && v !== '');
  });
}

/**
 * Clean column names to match database format
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
 * Upsert data to Supabase using REST API
 */
function upsertToSupabase(records) {
  const url = `${CONFIG.SUPABASE_URL}/rest/v1/${CONFIG.TABLE_NAME}`;
  
  const options = {
    method: 'post',
    headers: {
      'apikey': CONFIG.SUPABASE_SERVICE_KEY,
      'Authorization': `Bearer ${CONFIG.SUPABASE_SERVICE_KEY}`,
      'Content-Type': 'application/json',
      'Prefer': 'resolution=merge-duplicates' // Upsert on conflict
    },
    payload: JSON.stringify(records),
    muteHttpExceptions: true
  };
  
  try {
    const response = UrlFetchApp.fetch(url, options);
    const statusCode = response.getResponseCode();
    
    if (statusCode >= 200 && statusCode < 300) {
      console.log(`Successfully upserted ${records.length} records`);
      return true;
    } else {
      const errorText = response.getContentText();
      console.error(`Supabase API error (${statusCode}):`, errorText);
      logError(`API Error ${statusCode}: ${errorText}`);
      return false;
    }
  } catch (error) {
    console.error('Failed to upsert data:', error);
    logError(error.toString());
    return false;
  }
}

/**
 * Manual full sync function (can be run from Apps Script editor)
 */
function manualFullSync() {
  const sheet = SpreadsheetApp.getActiveSheet();
  console.log('Starting manual full sync...');
  syncSheetToSupabase(sheet);
}

/**
 * Log errors to a separate sheet for debugging
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
 * Setup function - Run this once to configure
 */
function setupSync() {
  const ui = SpreadsheetApp.getUi();
  
  // Get configuration from user
  const urlResponse = ui.prompt('Supabase URL', 'Enter your Supabase URL:', ui.ButtonSet.OK_CANCEL);
  if (urlResponse.getSelectedButton() !== ui.Button.OK) return;
  
  const keyResponse = ui.prompt('Service Role Key', 'Enter your Supabase Service Role Key:', ui.ButtonSet.OK_CANCEL);
  if (keyResponse.getSelectedButton() !== ui.Button.OK) return;
  
  const tableResponse = ui.prompt('Table Name', 'Enter the Supabase table name:', ui.ButtonSet.OK_CANCEL);
  if (tableResponse.getSelectedButton() !== ui.Button.OK) return;
  
  // Save to Script Properties
  const properties = PropertiesService.getScriptProperties();
  properties.setProperty('SUPABASE_URL', urlResponse.getResponseText().trim());
  properties.setProperty('SUPABASE_SERVICE_KEY', keyResponse.getResponseText().trim());
  properties.setProperty('TABLE_NAME', tableResponse.getResponseText().trim());
  
  ui.alert('Setup Complete!', 
    'Configuration saved. Now add an onChange trigger:\n\n' +
    '1. Click Triggers (clock icon)\n' +
    '2. Click + Add Trigger\n' +
    '3. Select onChange function\n' +
    '4. Event type: On change\n' +
    '5. Save', 
    ui.ButtonSet.OK);
}

/**
 * Test connection to Supabase
 */
function testConnection() {
  const url = `${CONFIG.SUPABASE_URL}/rest/v1/${CONFIG.TABLE_NAME}?limit=1`;
  
  const options = {
    method: 'get',
    headers: {
      'apikey': CONFIG.SUPABASE_SERVICE_KEY,
      'Authorization': `Bearer ${CONFIG.SUPABASE_SERVICE_KEY}`
    },
    muteHttpExceptions: true
  };
  
  try {
    const response = UrlFetchApp.fetch(url, options);
    const statusCode = response.getResponseCode();
    
    if (statusCode === 200) {
      SpreadsheetApp.getUi().alert('Success!', 'Connection to Supabase is working.', SpreadsheetApp.getUi().ButtonSet.OK);
    } else {
      SpreadsheetApp.getUi().alert('Error', `Failed to connect: ${response.getContentText()}`, SpreadsheetApp.getUi().ButtonSet.OK);
    }
  } catch (error) {
    SpreadsheetApp.getUi().alert('Error', `Connection failed: ${error.toString()}`, SpreadsheetApp.getUi().ButtonSet.OK);
  }
}

/**
 * Add custom menu to Google Sheets
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('Supabase Sync')
    .addItem('Setup Sync', 'setupSync')
    .addItem('Manual Full Sync', 'manualFullSync')
    .addItem('Test Connection', 'testConnection')
    .addToUi();
}
