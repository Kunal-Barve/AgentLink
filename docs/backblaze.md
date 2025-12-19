# Backblaze B2 Cloud Storage Integration

**Document Created:** December 11, 2025  
**Purpose:** Complete analysis and implementation guide for migrating from Dropbox to Backblaze B2 S3 storage

---

## Table of Contents
1. [Current System Analysis](#current-system-analysis)
2. [Why Backblaze B2?](#why-backblaze-b2)
3. [**Security & Privacy Settings**](#security--privacy-settings) 🔒
4. [Backblaze B2 S3-Compatible API Overview](#backblaze-b2-s3-compatible-api-overview)
5. [Python SDK Integration Guide](#python-sdk-integration-guide)
6. [Folder Structure in S3 Buckets](#folder-structure-in-s3-buckets)
7. [Implementation Plan](#implementation-plan)
8. [Migration Steps](#migration-steps)
9. [Testing Strategy](#testing-strategy)

---

## Current System Analysis

### PDF Generation & Upload Process

Our current system follows this workflow:

1. **API Request Received** (`app/main.py`)
   - FastAPI endpoints receive requests for agent or agency reports
   - Endpoints: `/api/generate-agents-report` and `/api/generate-agency-report`
   - Request is assigned a unique `job_id` using UUID

2. **Background Processing** (`app/worker_tasks.py`)
   - Jobs are enqueued to Redis Queue (RQ) for async processing
   - Worker tasks: `process_agents_report_task` and `process_agency_report_task`
   - Status updates stored in Redis with keys like `job:{job_id}`

3. **PDF Generation** (`app/services/html_pdf_service.py`)
   - Uses WeasyPrint to convert HTML templates to PDF
   - Templates: `agents_report.html`, `agency_report.html`, `commission_report.html`
   - PDFs stored temporarily in `temp/` directory
   - Filenames: `job_{job_id}_{timestamp}.pdf`

4. **Dropbox Upload** (`app/services/dropbox_service.py`)
   - Current service uses Dropbox SDK (`dropbox==12.0.2`)
   - Uploads to folders:
     - `/Suburbs Top Agents` - for agent reports
     - `/Suburbs Top Rental Agencies` - for agency reports
     - `/Commission Rate` - for commission reports
   - Returns shareable link with `?dl=0` for browser preview
   - Handles OAuth token refresh automatically

### Current Issues with Dropbox
- **Slow Internal Processing:** Dropbox takes time to process uploaded files
- **Performance Bottleneck:** Affects user experience with delayed file access
- **Need for Alternative:** Moving to Backblaze B2 for faster, more reliable storage

---

## Why Backblaze B2?

### Benefits
- **Cost-Effective:** $6/month package selected
- **S3-Compatible API:** Easy migration using boto3 (AWS SDK for Python)
- **Better Performance:** Faster upload and access times
- **Scalability:** Handles large files and high volume
- **No Processing Delays:** Files immediately accessible after upload

### Pricing (Your Plan)
- **Package:** $6 USD/month
- **Storage:** Typically includes generous storage limits
- **Bandwidth:** First 1GB/day download free
- **API Calls:** Unlimited

---

## Security & Privacy Settings

### Critical Decision: Public vs Private Bucket

**RECOMMENDATION FOR YOUR USE CASE: Use PUBLIC bucket** ✅

#### Understanding Your Use Case:
- **PDFs contain public data** (top agent listings for suburbs)
- **No sensitive client information** in PDFs
- **Temporary files** - used for make.com merging, then emailed to client
- **Need easy integration** with make.com automation platform
- **No encryption needed** - public agent ranking information

#### Public Bucket (RECOMMENDED for Your Project) ✅
- **Anyone with the URL can access files** (no authentication needed)
- Files are publicly accessible on the internet
- URL format: `https://s3.endpoint.com/bucket-name/file.pdf`

**✅ BEST for your use case because:**
- ✅ Agent listings are public information (not sensitive)
- ✅ Simpler integration with make.com (no auth needed)
- ✅ Direct URLs - no presigned URL generation
- ✅ Faster access and less overhead
- ✅ Cost effective (fewer API calls)
- ✅ Perfect for temporary workflow files

**Your Workflow:**
1. Generate agent PDF → Upload to PUBLIC bucket
2. make.com fetches PDF directly (simple URL)
3. make.com merges with other documents
4. Final PDF emailed to client
5. Original PDFs can be deleted after processing

#### Private Bucket (Alternative)
- **Requires authentication to access files**
- Files are NOT publicly accessible
- Only authorized users/applications can access

**Use Private bucket if:**
- ❌ PDFs contained sensitive client data (they don't)
- ❌ Need to restrict who can access files
- ❌ Compliance requirements mandate access control

**Your case:** Public data + temporary files + automation = **PUBLIC bucket is perfect**

### Public Bucket - Direct URL Access

With PUBLIC bucket, file sharing is simple:

```python
# Upload returns direct public URL
url = await upload_to_backblaze(
    pdf_path, 
    filename, 
    folder_path="Suburbs_Top_Agents"
)

# URL format: https://s3.endpoint.com/bucket-name/Suburbs_Top_Agents/file.pdf
# This URL can be used directly in make.com without any authentication
```

**Benefits for Your Workflow:**
- ✅ Direct URL - works immediately
- ✅ No expiration - stable for automation
- ✅ No authentication needed in make.com
- ✅ Simpler code - no presigned URL generation
- ✅ Perfect for temporary workflow files

### Private Bucket Alternative (If Needed Later)

If you ever need private bucket with secure sharing:

#### Pre-Signed URLs
Generate temporary URLs with expiration:

```python
# Only needed for PRIVATE bucket
presigned_url = backblaze_service.create_presigned_url(
    object_key="Suburbs_Top_Agents/report.pdf",
    expiration=3600  # URL valid for 1 hour
)
```

**Use presigned URLs if:**
- You switch to private bucket
- Need temporary access control
- Have compliance requirements

**Your current use case:** Public bucket with direct URLs is simpler and better!

### Encryption Settings

**For Your Use Case: TLS Only (Automatic)** ✅

#### 1. Transport Layer Security (TLS) - Always Enabled
- **All data transfers use HTTPS/TLS encryption**
- Automatically enabled - no configuration needed
- Data encrypted in transit between your server and Backblaze
- Uses industry-standard TLS 1.2+ protocols

**✅ This is sufficient for your use case!**
- Public agent listing data (not sensitive)
- Files are temporary (deleted after make.com processing)
- No compliance requirements for at-rest encryption

#### 2. Server-Side Encryption at Rest - OPTIONAL (Not Needed for Your Case)

**Two encryption options available:**

##### SSE-B2: Backblaze-Managed Keys (Recommended)
- **Easiest to implement**
- Backblaze manages encryption keys
- Uses AES-256 encryption
- Enable at bucket level or per-file
- **No extra cost**

**How it works:**
1. Each file encrypted with unique key
2. File keys encrypted with master key
3. Backblaze manages all keys
4. Transparent decryption on download

**Enable SSE-B2 for bucket:**
```python
# Enable encryption when creating bucket or via API
s3_client.put_bucket_encryption(
    Bucket='your-bucket-name',
    ServerSideEncryptionConfiguration={
        'Rules': [{
            'ApplyServerSideEncryptionByDefault': {
                'SSEAlgorithm': 'AES256'
            }
        }]
    }
)
```

##### SSE-C: Customer-Managed Keys
- **You manage the encryption keys**
- More control but more complexity
- Must provide key with each upload/download
- Key never stored by Backblaze
- AES-256 encryption

**Use SSE-C if:**
- Regulatory requirements mandate customer-managed keys
- Need complete control over encryption keys
- Have existing key management infrastructure

#### 3. Client-Side Encryption - Additional Layer
**Optional: Encrypt files before uploading**

```python
# Example: Encrypt PDF before upload
from cryptography.fernet import Fernet

# Generate key (store securely!)
key = Fernet.generate_key()
cipher = Fernet(key)

# Encrypt file
with open('report.pdf', 'rb') as f:
    encrypted_data = cipher.encrypt(f.read())

# Upload encrypted file
with open('encrypted_report.pdf', 'wb') as f:
    f.write(encrypted_data)

# Then upload to Backblaze
await upload_to_backblaze('encrypted_report.pdf', 'report.pdf', 'Reports')
```

### Best Practices for Your Use Case

#### Recommended Configuration:

1. **Bucket Type: PUBLIC** ✅
   ```bash
   # When creating bucket, select "Public"
   # Files accessible via direct URL
   # Perfect for automation workflows
   ```

2. **TLS Encryption: Automatic** ✅
   - All traffic automatically encrypted via HTTPS
   - No additional configuration needed
   - Sufficient for public data

3. **No Server-Side Encryption Needed** ✅
   - Data is public (agent listings)
   - Files are temporary
   - Keeps it simple and fast

4. **Lifecycle Policy (Optional)** 💡
   - Auto-delete files after 30 days
   - Clean up old temporary PDFs
   - Reduce storage costs

#### Implementation Example:

```python
# In worker_tasks.py - Simple PUBLIC bucket workflow

# Upload file (to PUBLIC bucket)
backblaze_url = await upload_to_backblaze(
    pdf_path, 
    filename, 
    folder_path="Suburbs_Top_Agents"
)

# backblaze_url is ready to use immediately!
# Format: https://s3.endpoint.com/bucket-name/Suburbs_Top_Agents/filename.pdf

# Send URL to make.com for merging
# No authentication, no expiration, works instantly!

# Later: Optional cleanup
# await backblaze_service.delete_file(f"Suburbs_Top_Agents/{filename}")
```

#### make.com Integration:

```plaintext
1. Your API generates PDF
2. Uploads to Backblaze PUBLIC bucket
3. Returns direct URL to make.com
4. make.com fetches PDF using direct URL (no auth needed)
5. make.com merges with other documents
6. Final PDF emailed to client
7. Optional: Delete original PDFs to save space
```

### Bucket Configuration

When creating your bucket:

```python
# Bucket configuration for your use case
bucket_config = {
    "name": "your-bucket-name",  # e.g., "agentlink-reports"
    "privacy": "public",  # ← PUBLIC for direct URL access
    "region": "us-west-004",  # Choose closest to your server
    "encryption": {
        "enabled": False  # Not needed for public data
    }
}
```

**Via Backblaze Web Console:**
1. Go to Backblaze B2 → Buckets
2. Click "Create Bucket"
3. Enter bucket name
4. Select **"Public"** under Files in Bucket are
5. Choose region
6. No encryption needed
7. Click Create

### Application Key Scoping

**Create application keys with minimal permissions:**

```plaintext
Key Name: AgentLink-Upload-Only
Type: Read and Write
Bucket Access: agentlink-reports (your bucket only)
File Prefix: (leave empty for full bucket, or specify like "Suburbs_Top_Agents/")
Duration: No expiration (or set expiration date)
```

**Best Practice:**
- One key for uploads (your server)
- Separate keys for specific operations
- Never expose keys in client-side code

### Compliance & Data Protection

**Backblaze B2 Security Features:**
- ✅ Data stored redundantly across multiple drives/servers
- ✅ AES-256 encryption (industry standard)
- ✅ TLS 1.2+ for data in transit
- ✅ SOC 2 Type II certified
- ✅ GDPR compliant
- ✅ Multiple data center locations

### Implementation Checklist for Your Use Case

- [ ] Create PUBLIC bucket in Backblaze B2
- [ ] Name bucket (e.g., "agentlink-reports")
- [ ] Select "Public" visibility
- [ ] Choose region closest to your server
- [ ] Store Backblaze credentials securely in .env (never in code)
- [ ] Use application keys with minimal required permissions
- [ ] Test direct URL access works with make.com
- [ ] Optional: Set up lifecycle policy to auto-delete old files (30+ days)
- [ ] Regularly audit access keys
- [ ] Never expose Application Keys in client-side code

**What you DON'T need:**
- ❌ Server-side encryption (SSE-B2) - not needed for public data
- ❌ Pre-signed URLs - direct URLs work fine
- ❌ Complex access control - public bucket is intentional

---

## Backblaze B2 S3-Compatible API Overview

### Key Concepts

#### 1. S3-Compatible API
Backblaze B2 provides an S3-compatible API, meaning:
- You can use AWS SDK (boto3 for Python)
- Same API calls as Amazon S3
- Just point to Backblaze endpoint instead

#### 2. Buckets
- Containers for your files (like Dropbox folders, but at root level)
- Each bucket has a unique name
- Buckets are region-specific

#### 3. Objects (Files)
- Files stored in buckets are called "objects"
- Each object has a unique key (path/filename)
- Objects can have metadata

#### 4. Folders/Prefixes
- **Important:** S3 (and Backblaze B2) is a flat storage system
- Folders are "virtual" - they're simulated using file prefixes
- Use `/` as delimiter in object keys to create folder structure
- Example: `Suburbs_Top_Agents/queenscliff_report.pdf`

---

## Python SDK Integration Guide

### Required Library
```bash
pip install boto3
```

**Version Required:** AWS SDK for Python (Boto3) 1.28.0 or greater

### Configuration Requirements

You need three pieces of information from your Backblaze B2 account:

1. **Endpoint URL** - Your bucket's S3 endpoint
   - Format: `https://s3.<region>.backblazeb2.com`
   - Example: `https://s3.us-west-004.backblazeb2.com`
   - Find in: Backblaze web console → Bucket details

2. **Application Key ID** (equivalent to AWS Access Key ID)
   - Find in: Backblaze web console → App Keys
   - Create a new application key with "Read and Write" access

3. **Application Key** (equivalent to AWS Secret Access Key)
   - Generated when you create the Application Key ID
   - **Important:** Save this immediately - shown only once!

### Basic Connection Code

```python
import boto3
from botocore.config import Config

def get_b2_client(endpoint_url, key_id, application_key):
    """
    Create and return a boto3 S3 client configured for Backblaze B2
    """
    s3_client = boto3.client(
        service_name='s3',
        endpoint_url=endpoint_url,              # Backblaze endpoint
        aws_access_key_id=key_id,               # Backblaze keyID
        aws_secret_access_key=application_key,  # Backblaze applicationKey
        config=Config(
            signature_version='s3v4'
        )
    )
    return s3_client
```

### Alternative: Using Resource Interface

```python
def get_b2_resource(endpoint_url, key_id, application_key):
    """
    Create and return a boto3 S3 resource configured for Backblaze B2
    """
    s3_resource = boto3.resource(
        service_name='s3',
        endpoint_url=endpoint_url,
        aws_access_key_id=key_id,
        aws_secret_access_key=application_key,
        config=Config(
            signature_version='s3v4'
        )
    )
    return s3_resource
```

### Environment Variables Setup

Add to your `.env` file:
```bash
# Backblaze B2 Configuration
B2_ENDPOINT_URL=https://s3.us-west-004.backblazeb2.com
B2_KEY_ID=your_key_id_here
B2_APPLICATION_KEY=your_application_key_here
B2_BUCKET_NAME=your-bucket-name
```

**Alternative Method:** Configure using AWS config file
```bash
# Set environment variable
export AWS_ENDPOINT_URL=https://s3.us-west-004.backblazeb2.com
export AWS_ACCESS_KEY_ID=your_key_id
export AWS_SECRET_ACCESS_KEY=your_application_key
```

---

## Folder Structure in S3 Buckets

### Understanding Virtual Folders

**Important Concept:** S3 storage (including Backblaze B2) doesn't actually have folders!
- It's a flat key-value storage system
- "Folders" are simulated using forward slashes `/` in object keys

### Creating Folder Structure

#### Method 1: Using Object Key with Prefix
```python
# Upload file with "folder" in the key
s3_client.upload_file(
    Filename='local_file.pdf',
    Bucket='my-bucket',
    Key='Suburbs_Top_Agents/queenscliff_report.pdf'  # This creates virtual folder
)
```

The key `Suburbs_Top_Agents/queenscliff_report.pdf` creates a virtual folder structure:
```
my-bucket/
└── Suburbs_Top_Agents/
    └── queenscliff_report.pdf
```

#### Method 2: Creating Empty "Folder" Marker
```python
# Create an empty object with trailing slash to represent folder
s3_client.put_object(
    Bucket='my-bucket',
    Key='Suburbs_Top_Agents/'  # Trailing slash indicates folder
)
```

### Multiple Folder Levels

**Yes, you can create multiple nested "folders":**

```python
# Example: Deep folder structure
keys = [
    'Reports/2024/Agents/queenscliff_report.pdf',
    'Reports/2024/Agencies/sydney_report.pdf',
    'Commission/2024/Q4/rates.pdf'
]

for key in keys:
    s3_client.upload_file(
        Filename='local_file.pdf',
        Bucket='my-bucket',
        Key=key
    )
```

This creates:
```
my-bucket/
├── Reports/
│   └── 2024/
│       ├── Agents/
│       │   └── queenscliff_report.pdf
│       └── Agencies/
│           └── sydney_report.pdf
└── Commission/
    └── 2024/
        └── Q4/
            └── rates.pdf
```

### Best Practices for Folder Organization

1. **Use Forward Slash `/` as Delimiter**
   - Standard convention in S3
   - Makes file organization intuitive
   - Works with GUI tools and browsers

2. **Recommended Structure for Our Project**
   ```
   your-bucket/
   ├── Suburbs_Top_Agents/
   │   ├── queenscliff_top_agents_20241211.pdf
   │   └── sydney_top_agents_20241211.pdf
   ├── Suburbs_Top_Rental_Agencies/
   │   ├── queenscliff_rental_agencies_20241211.pdf
   │   └── sydney_rental_agencies_20241211.pdf
   └── Commission_Rate/
       ├── queenscliff_commission_20241211.pdf
       └── sydney_commission_20241211.pdf
   ```

3. **Naming Conventions**
   - Use underscores or hyphens, avoid spaces
   - Include dates for versioning
   - Keep names descriptive but concise

### Listing Files by "Folder" (Prefix)

```python
# List all files in "Suburbs_Top_Agents" folder
response = s3_client.list_objects_v2(
    Bucket='my-bucket',
    Prefix='Suburbs_Top_Agents/'
)

for obj in response.get('Contents', []):
    print(obj['Key'])
```

---

## Implementation Plan

### Phase 1: Setup and Configuration
1. **Install boto3**
   ```bash
   pip install boto3
   ```

2. **Get Backblaze B2 Credentials**
   - Log into Backblaze web console
   - Navigate to "App Keys" section
   - Create new application key with "Read and Write" access
   - Save Key ID and Application Key

3. **Find Your Endpoint URL**
   - Go to Bucket details in Backblaze console
   - Copy S3 endpoint URL
   - Format: `https://s3.<region>.backblazeb2.com`

4. **Update Environment Variables**
   - Add credentials to `.env` file
   - Never commit credentials to repository!

### Phase 2: Create Service Module
Create `app/services/backblaze_service.py`:

```python
import os
import boto3
import logging
from botocore.config import Config
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("articflow.backblaze")

class BackblazeService:
    def __init__(self):
        self.endpoint_url = os.getenv("B2_ENDPOINT_URL")
        self.key_id = os.getenv("B2_KEY_ID")
        self.application_key = os.getenv("B2_APPLICATION_KEY")
        self.bucket_name = os.getenv("B2_BUCKET_NAME")
        
        # Initialize S3 client
        self.s3_client = self._create_client()
        
    def _create_client(self):
        """Create boto3 S3 client for Backblaze B2"""
        return boto3.client(
            service_name='s3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.key_id,
            aws_secret_access_key=self.application_key,
            config=Config(
                signature_version='s3v4',
                retries={'max_attempts': 3}
            )
        )
    
    async def upload_file(self, file_path, object_key):
        """
        Upload file to Backblaze B2
        
        Args:
            file_path: Local path to file
            object_key: S3 object key (includes folder prefix)
            
        Returns:
            Public URL of uploaded file
        """
        try:
            logger.info(f"Uploading {file_path} to {object_key}")
            
            # Upload file
            self.s3_client.upload_file(
                Filename=file_path,
                Bucket=self.bucket_name,
                Key=object_key
            )
            
            # Generate public URL
            url = f"{self.endpoint_url}/{self.bucket_name}/{object_key}"
            logger.info(f"Upload successful: {url}")
            return url
            
        except ClientError as e:
            logger.error(f"Upload failed: {e}")
            raise
    
    def create_presigned_url(self, object_key, expiration=3600):
        """
        Generate presigned URL for temporary access
        
        Args:
            object_key: S3 object key
            expiration: URL validity in seconds (default 1 hour)
            
        Returns:
            Presigned URL
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_key
                },
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None

# Singleton instance
backblaze_service = BackblazeService()

async def upload_to_backblaze(file_path, filename, folder_path=""):
    """
    Upload file to Backblaze B2 with folder structure
    
    Args:
        file_path: Local file path
        filename: Name for uploaded file
        folder_path: Virtual folder path (e.g., "Suburbs_Top_Agents")
        
    Returns:
        Public URL of uploaded file
    """
    # Construct object key with folder prefix
    if folder_path:
        object_key = f"{folder_path}/{filename}"
    else:
        object_key = filename
    
    return await backblaze_service.upload_file(file_path, object_key)
```

### Phase 3: Update Worker Tasks
Modify `app/worker_tasks.py` to use Backblaze instead of Dropbox:

```python
# Replace this line:
from app.services.dropbox_service import upload_to_dropbox

# With:
from app.services.backblaze_service import upload_to_backblaze

# Then in the worker functions, replace upload_to_dropbox calls:
# OLD:
# dropbox_url = loop.run_until_complete(upload_to_dropbox(pdf_path, filename, folder_path=dropbox_folder))

# NEW:
backblaze_url = loop.run_until_complete(upload_to_backblaze(pdf_path, filename, folder_path=folder_name))
```

### Phase 4: Update Requirements
Add to `requirements.txt`:
```
boto3>=1.28.0
botocore>=1.31.0
```

---

## Migration Steps

### Step 1: Keep Both Services (Recommended)
During transition, maintain both Dropbox and Backblaze:

1. Keep existing `dropbox_service.py`
2. Add new `backblaze_service.py`
3. Use environment variable to toggle between services

```python
# In worker_tasks.py
USE_BACKBLAZE = os.getenv("USE_BACKBLAZE", "false").lower() == "true"

if USE_BACKBLAZE:
    from app.services.backblaze_service import upload_to_backblaze as upload_service
else:
    from app.services.dropbox_service import upload_to_dropbox as upload_service
```

### Step 2: Test Thoroughly
1. Test uploads with various file sizes
2. Verify folder structure creation
3. Test URL generation and access
4. Monitor for errors

### Step 3: Gradual Rollout
1. Start with one report type (e.g., agent reports)
2. Monitor for issues
3. Expand to other report types
4. Eventually deprecate Dropbox service

### Step 4: Cleanup
Once fully migrated:
1. Remove Dropbox SDK from requirements
2. Archive `dropbox_service.py`
3. Update documentation
4. Remove Dropbox credentials from `.env`

---

## Testing Strategy

### Unit Tests
Create `tests/test_backblaze_service.py`:

```python
import pytest
import os
from app.services.backblaze_service import BackblazeService

@pytest.fixture
def backblaze_service():
    return BackblazeService()

def test_upload_file(backblaze_service, tmp_path):
    # Create test file
    test_file = tmp_path / "test.pdf"
    test_file.write_text("Test content")
    
    # Upload
    url = await backblaze_service.upload_file(
        str(test_file),
        "test_folder/test.pdf"
    )
    
    assert url is not None
    assert "test_folder/test.pdf" in url

def test_presigned_url(backblaze_service):
    url = backblaze_service.create_presigned_url("test_folder/test.pdf")
    assert url is not None
    assert "X-Amz-Algorithm" in url  # Signature in URL
```

### Integration Tests
Create test files in `tests/` folder to verify:

1. **Connection Test**
   - Verify credentials work
   - Test bucket access

2. **Upload Test**
   - Upload small file
   - Verify file appears in bucket
   - Check URL accessibility

3. **Folder Structure Test**
   - Create files in multiple folders
   - Verify organization
   - Test file listing

4. **Performance Test**
   - Compare upload times vs Dropbox
   - Test with various file sizes
   - Monitor for timeouts

### Manual Testing Checklist
- [ ] Credentials configured correctly
- [ ] Can connect to Backblaze B2
- [ ] Can create bucket (if needed)
- [ ] Can upload files
- [ ] Folder structure works as expected
- [ ] Can generate accessible URLs
- [ ] Files download correctly
- [ ] Error handling works
- [ ] Logging provides useful info

---

## Implementation Commands

### 1. Install Dependencies
```bash
pip install boto3>=1.28.0
```

### 2. Update .env File
```bash
# Add these lines to .env
B2_ENDPOINT_URL=https://s3.us-west-004.backblazeb2.com  # Replace with your region
B2_KEY_ID=your_key_id_here
B2_APPLICATION_KEY=your_application_key_here
B2_BUCKET_NAME=your-bucket-name
USE_BACKBLAZE=false  # Set to true when ready to switch
```

### 3. Test Connection
Create a simple test script to verify connection.

---

## Next Steps

1. **Get Backblaze Credentials**
   - Log into Backblaze B2 account
   - Create application key
   - Note endpoint URL

2. **Create Service Module**
   - Implement `backblaze_service.py`
   - Add error handling
   - Add logging

3. **Create Test Suite**
   - Unit tests for service
   - Integration tests for uploads
   - Test folder structure

4. **Update Worker Tasks**
   - Integrate Backblaze service
   - Keep Dropbox as fallback initially
   - Add toggle mechanism

5. **Deploy and Monitor**
   - Deploy to test environment
   - Monitor logs for issues
   - Compare performance

---

## Reference Links

- [Backblaze B2 Documentation](https://www.backblaze.com/docs/cloud-storage)
- [S3-Compatible API](https://www.backblaze.com/apidocs/introduction-to-the-s3-compatible-api)
- [Python SDK Guide](https://www.backblaze.com/bb/docs/cloud-storage-use-the-aws-sdk-for-python-with-backblaze-b2)
- [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [GitHub Sample Code](https://github.com/backblaze-b2-samples/b2-python-s3-sample)

---

## Questions & Answers

**Q: Can we create multiple folders in S3 bucket?**  
A: Yes! While S3 is flat storage, you can create unlimited virtual folders using prefixes with `/` delimiter. Example: `folder1/subfolder/file.pdf`

**Q: How do folder permissions work?**  
A: Permissions are set at bucket or object level. You can restrict application keys to specific prefixes (folders).

**Q: What about file versioning?**  
A: Backblaze B2 supports file versioning. Enable on bucket to keep multiple versions of same file.

**Q: Can we migrate existing Dropbox files?**  
A: Yes, you can download from Dropbox and re-upload to Backblaze, or use migration tools.

**Q: Performance compared to Dropbox?**  
A: Backblaze B2 typically faster for direct API access, no processing delays like Dropbox.

---

---

## Quick Start Guide - Step by Step

### Step 1: Get Backblaze B2 Credentials

#### 1.1 Log into Backblaze B2
Go to: https://secure.backblaze.com/user_signin.htm

#### 1.2 Create Application Key
1. In left sidebar, click **"App Keys"** (3rd from bottom)
2. Click **"Add a New Application Key"**
3. Configure:
   - **Name:** `AgentLink-Production` (or any name)
   - **Type of Access:** Select **"Read and Write"**
   - **Allow access to Bucket(s):** Choose your bucket or "All"
4. Click **"Create New Key"**

#### 1.3 Save Credentials
**IMPORTANT:** The Application Key is shown only once!

Copy these three values:
- **keyID** (starts with numbers, e.g., `0027464dd94917b...`)
- **applicationKey** (starts with K00..., e.g., `K002WU+TkHXkksxI...`)
- **S3 Endpoint** (find in bucket details, e.g., `https://s3.us-west-004.backblazeb2.com`)

### Step 2: Configure Environment Variables

Add to your `.env` file:

```bash
# Backblaze B2 Cloud Storage Configuration
B2_ENDPOINT_URL=https://s3.us-west-004.backblazeb2.com  # Replace with your endpoint
B2_KEY_ID=your_key_id_here                              # Your keyID
B2_APPLICATION_KEY=your_application_key_here            # Your applicationKey
B2_BUCKET_NAME=your-bucket-name                         # Your bucket name (PUBLIC recommended)
USE_BACKBLAZE=false                                     # Set to true when ready
```

**Configuration Notes:**
- ⚠️ Never commit .env file to git
- ✅ Create PUBLIC bucket for agent listing PDFs
- ✅ Direct URLs work immediately with make.com
- ✅ TLS encryption automatic (no additional setup needed)

### Step 3: Install Dependencies

```bash
pip install boto3>=1.28.0
# Or update entire environment
pip install -r requirements.txt
```

### Step 4: Test Connection

```bash
python tests/backblaze/test_connection.py
```

**Expected output:**
```
============================================================
BACKBLAZE B2 CONNECTION TEST
============================================================
✓ S3 client initialized
✓ Successfully connected to bucket
CONNECTION TEST PASSED ✓
============================================================
```

**If test fails:**
- **"S3 client not initialized"** - Check .env file has all 4 variables
- **"Cannot access bucket"** - Verify bucket name and credentials
- **"Access denied"** - Create new key with "Read and Write" access

### Step 5: Test File Uploads

```bash
python tests/backblaze/test_upload.py
```

This will create test PDFs and upload to different folders to verify folder structure works.

### Step 6: Integrate with Application

Add to `worker_tasks.py`:

```python
import os

# At top of file after imports
USE_BACKBLAZE = os.getenv("USE_BACKBLAZE", "false").lower() == "true"

if USE_BACKBLAZE:
    from app.services.backblaze_service import upload_to_backblaze
    logger.info("Using Backblaze B2 for file storage")
else:
    from app.services.dropbox_service import upload_to_dropbox
    logger.info("Using Dropbox for file storage")

# Then in your upload code, replace upload_to_dropbox with:
if USE_BACKBLAZE:
    url = loop.run_until_complete(upload_to_backblaze(pdf_path, filename, folder_path=folder_name))
else:
    url = loop.run_until_complete(upload_to_dropbox(pdf_path, filename, folder_path=folder_name))
```

### Step 7: Enable Backblaze

When ready to switch, update `.env`:
```bash
USE_BACKBLAZE=true
```

### Step 8: Monitor and Verify

```bash
# Check logs
tail -f logs/ArticFlow_*.log | grep backblaze

# Look for:
# - "Upload successful"
# - Correct URLs generated
# - No error messages
```

---

## Troubleshooting Guide

### Upload Returns Mock URL
- Check credentials are correct in .env
- Verify bucket access permissions
- Check network connectivity
- Review logs for specific error

### Files Not Appearing in Bucket
- Wait a few seconds (may be slight delay)
- Refresh bucket view in web console
- Check folder prefix is correct

### Permission Errors
- Recreate Application Key with "Read and Write" access
- Verify bucket name matches exactly
- Check bucket-specific permissions in Backblaze console

### Slow Uploads
- Check internet connection speed
- Verify file size (large files take longer)
- Consider endpoint region closer to your server

### Rollback to Dropbox
If issues occur, simply set in `.env`:
```bash
USE_BACKBLAZE=false
```

---

## Folder Mapping Reference

Current Dropbox → Backblaze B2:

| Current Dropbox Path | Backblaze B2 Key |
|---------------------|------------------|
| `/Suburbs Top Agents` | `Suburbs_Top_Agents/` |
| `/Suburbs Top Rental Agencies` | `Suburbs_Top_Rental_Agencies/` |
| `/Commission Rate` | `Commission_Rate/` |

---

## Files Created

### Service Implementation
- `app/services/backblaze_service.py` - Main Backblaze B2 service
- `requirements.txt` - Updated with boto3 dependencies

### Testing Suite
- `tests/backblaze/test_connection.py` - Connection verification test
- `tests/backblaze/test_upload.py` - Upload and folder structure tests
- `tests/backblaze/README.md` - Test documentation

---

---

## Summary of Key Decisions

### 📋 Configuration for Your Use Case

**Bucket Configuration:**
- ✅ **Use PUBLIC bucket** for agent listing PDFs
- ✅ **TLS encryption** automatically enabled for all transfers (HTTPS)
- ✅ **No SSE-B2 encryption needed** - data is public, files are temporary
- ✅ **Direct URLs** work immediately with make.com

**Reasoning:**
- PDFs contain public data (agent rankings)
- No sensitive client information
- Files are temporary (used for merging, then deleted)
- Easier integration with make.com automation
- Simpler code, no presigned URL generation needed

**File Access:**
- ✅ **Direct public URLs** - instant access
- ✅ **No expiration** - stable for automation workflow
- ✅ **No authentication** needed in make.com
- ✅ **Simple integration** - upload and use immediately

**Your Workflow:**
1. Generate agent PDF → Upload to PUBLIC Backblaze bucket
2. Get direct URL → Send to make.com
3. make.com fetches PDF (no auth needed)
4. make.com merges with other documents
5. Final PDF emailed to client
6. Optional: Auto-delete old files after 30 days

**Best Practices:**
- Keep API credentials in .env file (never commit)
- Use application keys with minimal permissions
- Optional: Set lifecycle policy to auto-delete old files
- Monitor storage usage

### ✅ Folders in S3 Buckets
**YES - Multiple folders fully supported!**
- Use `/` delimiter in keys (e.g., `Suburbs_Top_Agents/file.pdf`)
- Unlimited nesting supported
- Virtual folders work perfectly with S3-Compatible API
- Folder mapping from Dropbox maintained

---

**Document Status:** Complete with Security Guidelines  
**Last Updated:** December 11, 2025  
**All Backblaze information consolidated in this single file**
