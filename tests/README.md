# Tests Directory

This folder contains all testing and development scripts for the AgentLink project.

## 📁 Files

### Property Tracker Testing
- **`apify_scraper_testing.py`** - Main Apify scraper testing framework
  - Tests 4 different property scrapers
  - Compares performance and data quality
  - Generates comparison reports

### Google Sheets Testing
- **`setup_and_test_sheets.py`** - Google Sheets API setup and connection test
  - Validates credentials
  - Tests sheet connection
  - Saves configuration
  
- **`test_sheets_connection.py`** - Quick Google Sheets connection test
  - Simpler version for quick checks

### Agent Processing Tests
- **`test_agent_processing_flow.py`** - Tests agent processing workflow
- **`test_featured_agent.py`** - Tests featured agent functionality

### Performance Tests
- **`test-concurrent-requests.ps1`** - PowerShell script for testing concurrent requests

## 🚀 Running Tests

### Activate Environment First
```bash
# Use Anaconda Prompt (not PowerShell 7)
conda activate .\env
```

### Property Tracker Tests
```bash
# Set Apify API token
set APIFY_API_TOKEN=your_token_here

# Run Apify scraper tests
python tests/apify_scraper_testing.py
```

### Google Sheets Tests
```bash
# Full setup and test
python tests/setup_and_test_sheets.py

# Quick connection test
python tests/test_sheets_connection.py
```

### Agent Tests
```bash
python tests/test_agent_processing_flow.py
python tests/test_featured_agent.py
```

## 📋 Configuration

Tests use these configuration files:
- `credentials/service-account-credentials.json` - Google Sheets API credentials
- `google_sheets_config.json` - Saved Google Sheets configuration
- `.env` - Environment variables

## 🔒 Security

**Never commit:**
- Credentials files
- API tokens
- Configuration files with Sheet IDs

All sensitive files are in `.gitignore`

---

**Last Updated**: December 8, 2025
