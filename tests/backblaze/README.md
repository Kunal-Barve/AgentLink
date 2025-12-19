# Backblaze B2 Testing Suite

This directory contains tests for Backblaze B2 integration.

## Prerequisites

1. **Install boto3**
   ```bash
   pip install boto3
   ```

2. **Configure credentials in .env file**
   Add these variables to your `.env` file in the project root:
   ```bash
   B2_ENDPOINT_URL=https://s3.us-west-004.backblazeb2.com
   B2_KEY_ID=your_key_id_here
   B2_APPLICATION_KEY=your_application_key_here
   B2_BUCKET_NAME=your-bucket-name
   ```

3. **Get Backblaze credentials:**
   - Log into Backblaze B2 web console
   - Go to "App Keys" section
   - Create a new application key with "Read and Write" access
   - Copy the Key ID and Application Key
   - Find your bucket's S3 endpoint URL in bucket details

## Running Tests

### Test 1: Connection Test
Verify that you can connect to Backblaze B2:

```bash
python tests/backblaze/test_connection.py
```

**Expected Output:**
- ✓ S3 client initialized
- ✓ Successfully connected to bucket
- List of files in bucket (if any)

### Test 2: Upload Tests
Test file uploads and folder structure:

```bash
python tests/backblaze/test_upload.py
```

**Tests include:**
1. Simple upload (no folder)
2. Upload with folder structure
3. Nested folder structure
4. List files by folder prefix

**Expected Output:**
- ✓ Multiple successful uploads
- URLs for each uploaded file
- File listing by folder

## Test Files

- `test_connection.py` - Verify connection and credentials
- `test_upload.py` - Test file uploads and folder structure
- `temp/` - Temporary directory for test PDFs (auto-created)

## What's Being Tested

### Connection Test
- ✓ Credentials loaded from .env
- ✓ S3 client initialization
- ✓ Bucket access verification
- ✓ File listing capability

### Upload Test
- ✓ Simple file upload
- ✓ Upload to specific folders
- ✓ Nested folder structure
- ✓ URL generation
- ✓ Multiple concurrent uploads

## Folder Structure Being Created

```
your-bucket/
├── simple_test.pdf
├── Suburbs_Top_Agents/
│   └── queenscliff_test.pdf
├── Suburbs_Top_Rental_Agencies/
│   └── sydney_test.pdf
├── Commission_Rate/
│   └── commission_test.pdf
└── Reports/
    └── 2024/
        └── Agents/
            └── nested_test.pdf
```

## Troubleshooting

### "S3 client not initialized"
- Check that all environment variables are set in .env
- Verify no typos in variable names
- Ensure .env is in project root

### "Cannot access bucket"
- Verify bucket name is correct
- Check that Application Key has permissions for this bucket
- Ensure bucket exists in your Backblaze account

### "Upload failed"
- Check network connection
- Verify credentials are correct
- Check bucket permissions

### "Access denied"
- Application Key may not have write permissions
- Create a new key with "Read and Write" access

## Next Steps

After tests pass:

1. Update requirements.txt:
   ```bash
   pip freeze | grep boto3 >> requirements.txt
   ```

2. Update worker_tasks.py to use Backblaze
3. Deploy to test environment
4. Monitor production usage

## Cleanup

To remove test files from bucket:

```python
from app.services.backblaze_service import backblaze_service

# Delete test files
test_files = [
    "simple_test.pdf",
    "Suburbs_Top_Agents/queenscliff_test.pdf",
    "Suburbs_Top_Rental_Agencies/sydney_test.pdf",
    "Commission_Rate/commission_test.pdf",
    "Reports/2024/Agents/nested_test.pdf"
]

for file in test_files:
    backblaze_service.delete_file(file)
```
