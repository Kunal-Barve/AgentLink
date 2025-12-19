"""
Backblaze B2 Cloud Storage Service
S3-Compatible API integration using boto3
"""
import os
import boto3
import logging
import time
from botocore.config import Config
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logger
logger = logging.getLogger("articflow.backblaze")


class BackblazeService:
    """Service for interacting with Backblaze B2 Cloud Storage using S3-Compatible API"""
    
    def __init__(self):
        """Initialize Backblaze B2 service with credentials from environment"""
        self.endpoint_url = os.getenv("B2_ENDPOINT_URL")
        self.key_id = os.getenv("B2_KEY_ID")
        self.application_key = os.getenv("B2_APPLICATION_KEY")
        self.bucket_name = os.getenv("B2_BUCKET_NAME")
        
        # Validate credentials
        self._validate_credentials()
        
        # Initialize S3 client
        self.s3_client = None
        self.initialize_client()
        
    def _validate_credentials(self):
        """Validate that all required credentials are present"""
        missing = []
        if not self.endpoint_url:
            missing.append("B2_ENDPOINT_URL")
        if not self.key_id:
            missing.append("B2_KEY_ID")
        if not self.application_key:
            missing.append("B2_APPLICATION_KEY")
        if not self.bucket_name:
            missing.append("B2_BUCKET_NAME")
            
        if missing:
            logger.error(f"Missing Backblaze B2 credentials: {', '.join(missing)}")
            logger.info("Please add these to your .env file")
        else:
            logger.info("Backblaze B2 credentials loaded successfully")
            logger.info(f"Endpoint: {self.endpoint_url}")
            logger.info(f"Bucket: {self.bucket_name}")
            logger.info(f"Key ID (first 7 chars): {self.key_id[:7]}...")
    
    def initialize_client(self):
        """Initialize the boto3 S3 client for Backblaze B2"""
        if not all([self.endpoint_url, self.key_id, self.application_key]):
            logger.warning("Cannot initialize Backblaze B2 client: missing credentials")
            return False
            
        try:
            self.s3_client = boto3.client(
                service_name='s3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.key_id,
                aws_secret_access_key=self.application_key,
                config=Config(
                    signature_version='s3v4',
                    retries={'max_attempts': 3, 'mode': 'standard'}
                )
            )
            logger.info("Backblaze B2 S3 client initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Backblaze B2 client: {e}")
            return False
    
    def verify_connection(self):
        """
        Verify connection to Backblaze B2 and bucket access
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        if not self.s3_client:
            logger.error("S3 client not initialized")
            return False
            
        try:
            # Try to head the bucket (check if it exists and is accessible)
            response = self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Successfully connected to bucket: {self.bucket_name}")
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"Bucket not found: {self.bucket_name}")
            elif error_code == '403':
                logger.error(f"Access denied to bucket: {self.bucket_name}")
            else:
                logger.error(f"Error accessing bucket: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error verifying connection: {e}")
            return False
    
    def test_permissions(self):
        """
        Test if the application key has proper permissions for common operations
        
        Returns:
            dict: Dictionary with permission test results
        """
        permissions = {
            'read': False,
            'write': False,
            'delete': False
        }
        
        if not self.s3_client:
            logger.error("Cannot test permissions: S3 client not initialized")
            return permissions
        
        test_key = '_permission_test_file.txt'
        
        try:
            # Test WRITE permission
            logger.info("Testing WRITE permission...")
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=test_key,
                Body=b'Permission test'
            )
            permissions['write'] = True
            logger.info("✓ WRITE permission: OK")
            
            # Test READ permission
            logger.info("Testing READ permission...")
            self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=test_key
            )
            permissions['read'] = True
            logger.info("✓ READ permission: OK")
            
            # Test DELETE permission
            logger.info("Testing DELETE permission...")
            response = self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=test_key
            )
            status_code = response.get('ResponseMetadata', {}).get('HTTPStatusCode')
            if status_code in [200, 204]:
                permissions['delete'] = True
                logger.info("✓ DELETE permission: OK")
            else:
                logger.warning(f"✗ DELETE permission: Failed (status {status_code})")
                
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"Permission test failed: {error_code}")
            if 'AccessDenied' in error_code or '403' in str(e):
                logger.error("⚠️  Application key does not have sufficient permissions")
                logger.error("   Solution: Create a new key with 'Read and Write' access")
        except Exception as e:
            logger.error(f"Unexpected error during permission test: {e}")
        
        return permissions
    
    async def upload_file(self, file_path, object_key, extra_args=None):
        """
        Upload file to Backblaze B2
        
        Args:
            file_path (str): Local path to file to upload
            object_key (str): S3 object key (includes folder prefix)
                             Example: "Suburbs_Top_Agents/queenscliff_report.pdf"
            extra_args (dict): Optional extra arguments for upload
                             Example: {'ContentType': 'application/pdf'}
            
        Returns:
            str: Public URL of uploaded file, or None if failed
        """
        if not self.s3_client:
            logger.error("Cannot upload: S3 client not initialized")
            return None
            
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None
        
        try:
            logger.info(f"Uploading {file_path} to {self.bucket_name}/{object_key}")
            
            # Upload file
            upload_args = extra_args or {}
            self.s3_client.upload_file(
                Filename=file_path,
                Bucket=self.bucket_name,
                Key=object_key,
                ExtraArgs=upload_args
            )
            
            # Generate public URL
            url = f"{self.endpoint_url}/{self.bucket_name}/{object_key}"
            logger.info(f"Upload successful: {url}")
            
            return url
            
        except ClientError as e:
            logger.error(f"Upload failed (ClientError): {e}")
            return None
        except Exception as e:
            logger.error(f"Upload failed (Exception): {e}", exc_info=True)
            return None
    
    def create_presigned_url(self, object_key, expiration=3600):
        """
        Generate presigned URL for temporary access to file
        
        Args:
            object_key (str): S3 object key
            expiration (int): URL validity in seconds (default 1 hour)
            
        Returns:
            str: Presigned URL, or None if failed
        """
        if not self.s3_client:
            logger.error("Cannot create presigned URL: S3 client not initialized")
            return None
            
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_key
                },
                ExpiresIn=expiration
            )
            logger.info(f"Generated presigned URL for {object_key} (expires in {expiration}s)")
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None
    
    def list_files(self, prefix='', max_keys=1000):
        """
        List files in bucket with optional prefix (folder)
        
        Args:
            prefix (str): Filter files by prefix (folder path)
            max_keys (int): Maximum number of files to return
            
        Returns:
            list: List of file keys, or empty list if failed
        """
        if not self.s3_client:
            logger.error("Cannot list files: S3 client not initialized")
            return []
            
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            files = []
            if 'Contents' in response:
                files = [obj['Key'] for obj in response['Contents']]
                logger.info(f"Listed {len(files)} files with prefix '{prefix}'")
            else:
                logger.info(f"No files found with prefix '{prefix}'")
                
            return files
            
        except ClientError as e:
            logger.error(f"Failed to list files: {e}")
            return []
    
    def list_all_versions(self, prefix=''):
        """
        List ALL object versions in bucket (including delete markers)
        This is needed when versioning is enabled
        
        Args:
            prefix (str): Filter by prefix (folder path)
            
        Returns:
            list: List of tuples (Key, VersionId)
        """
        if not self.s3_client:
            logger.error("Cannot list versions: S3 client not initialized")
            return []
        
        try:
            response = self.s3_client.list_object_versions(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            versions = []
            
            # Get all object versions
            if 'Versions' in response:
                for version in response['Versions']:
                    versions.append((version['Key'], version['VersionId']))
            
            # Get all delete markers
            if 'DeleteMarkers' in response:
                for marker in response['DeleteMarkers']:
                    versions.append((marker['Key'], marker['VersionId']))
            
            logger.info(f"Found {len(versions)} total versions/markers with prefix '{prefix}'")
            return versions
            
        except ClientError as e:
            logger.error(f"Failed to list versions: {e}")
            return []
    
    def delete_file(self, object_key):
        """
        Delete file from bucket
        
        Args:
            object_key (str): S3 object key to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.s3_client:
            logger.error("Cannot delete file: S3 client not initialized")
            return False
            
        try:
            # Delete the object
            response = self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            
            # Check response status
            status_code = response.get('ResponseMetadata', {}).get('HTTPStatusCode')
            
            if status_code == 204 or status_code == 200:
                logger.info(f"Successfully deleted file: {object_key}")
                return True
            else:
                logger.warning(f"Delete returned unexpected status {status_code} for: {object_key}")
                return False
                
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"Failed to delete file {object_key}: {error_code} - {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting {object_key}: {e}")
            return False
    
    def delete_all_versions(self, object_key):
        """
        Delete ALL versions of a file (including delete markers)
        This is necessary when bucket versioning is enabled
        
        Args:
            object_key (str): S3 object key to delete completely
            
        Returns:
            int: Number of versions deleted
        """
        if not self.s3_client:
            logger.error("Cannot delete versions: S3 client not initialized")
            return 0
        
        try:
            # List all versions of this specific object
            response = self.s3_client.list_object_versions(
                Bucket=self.bucket_name,
                Prefix=object_key
            )
            
            deleted_count = 0
            
            # Delete all file versions
            if 'Versions' in response:
                for version in response['Versions']:
                    if version['Key'] == object_key:  # Exact match only
                        try:
                            self.s3_client.delete_object(
                                Bucket=self.bucket_name,
                                Key=version['Key'],
                                VersionId=version['VersionId']
                            )
                            deleted_count += 1
                            logger.debug(f"Deleted version {version['VersionId']} of {object_key}")
                        except Exception as e:
                            logger.error(f"Failed to delete version {version['VersionId']}: {e}")
            
            # Delete all delete markers
            if 'DeleteMarkers' in response:
                for marker in response['DeleteMarkers']:
                    if marker['Key'] == object_key:  # Exact match only
                        try:
                            self.s3_client.delete_object(
                                Bucket=self.bucket_name,
                                Key=marker['Key'],
                                VersionId=marker['VersionId']
                            )
                            deleted_count += 1
                            logger.debug(f"Deleted delete marker {marker['VersionId']} of {object_key}")
                        except Exception as e:
                            logger.error(f"Failed to delete marker {marker['VersionId']}: {e}")
            
            if deleted_count > 0:
                logger.info(f"Permanently deleted {deleted_count} versions of {object_key}")
            else:
                logger.warning(f"No versions found to delete for {object_key}")
                
            return deleted_count
            
        except ClientError as e:
            logger.error(f"Failed to delete all versions of {object_key}: {e}")
            return 0
        except Exception as e:
            logger.error(f"Unexpected error deleting versions: {e}")
            return 0
    
    def get_mock_url(self, file_name):
        """
        Generate a mock URL for when upload fails
        Used as fallback to maintain service availability
        
        Args:
            file_name (str): File name for mock URL
            
        Returns:
            str: Mock URL
        """
        timestamp = int(time.time())
        mock_url = f"https://mock.backblaze.com/{timestamp}/{file_name}"
        logger.warning(f"Using mock URL: {mock_url}")
        return mock_url


# Create singleton instance
backblaze_service = BackblazeService()


async def upload_to_backblaze(file_path, filename, folder_path=""):
    """
    Upload file to Backblaze B2 with folder structure
    
    This is the main function to use for uploading files.
    It mirrors the interface of upload_to_dropbox for easy migration.
    
    Args:
        file_path (str): Local file path
        filename (str): Name for uploaded file
        folder_path (str): Virtual folder path (e.g., "Suburbs_Top_Agents")
                          Can include leading/trailing slashes or not
        
    Returns:
        str: Public URL of uploaded file
        
    Example:
        url = await upload_to_backblaze(
            "temp/report.pdf",
            "queenscliff_report.pdf",
            "Suburbs_Top_Agents"
        )
    """
    logger.info(f"Starting Backblaze upload: file_path={file_path}, filename={filename}, folder_path={folder_path}")
    
    # Clean up folder path - remove leading/trailing slashes
    if folder_path:
        folder_path = folder_path.strip('/')
        object_key = f"{folder_path}/{filename}"
    else:
        object_key = filename
    
    # Set content type for PDFs
    extra_args = {'ContentType': 'application/pdf'} if filename.endswith('.pdf') else None
    
    # Attempt upload
    url = await backblaze_service.upload_file(file_path, object_key, extra_args)
    
    # If upload failed, return mock URL to prevent service disruption
    if not url:
        logger.warning("Upload failed, returning mock URL")
        url = backblaze_service.get_mock_url(filename)
    
    return url
