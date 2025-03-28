import os
import dropbox
from dropbox.exceptions import AuthError
import time
import logging
import requests
import configparser
from dotenv import load_dotenv
from datetime import datetime

# Get the absolute path to the .env file
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
print(f"Loading .env from: {env_path}")
# Force reload the .env file
load_dotenv(env_path, override=True)

# Set up logger for Dropbox service
logger = logging.getLogger("articflow.dropbox")

# Ensure the logger is properly configured
if not logger.handlers and not logging.getLogger().handlers:
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Set up file handler for unified logging
    log_file = os.path.join(logs_dir, 'articflow.log')
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # Add handler to root logger to ensure all logs go to the same file
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    
    # Also add a console handler for immediate feedback
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    root_logger.addHandler(console_handler)
    
    logger.info(f"Dropbox service logging initialized. Logs will be written to {log_file}")

class DropboxService:
    def __init__(self):
        # Get credentials from environment variables
        self.access_token = os.getenv("DROPBOX_ACCESS_TOKEN")
        self.refresh_token = os.getenv("DROPBOX_REFRESH_TOKEN")
        self.app_key = os.getenv("DROPBOX_APP_KEY")
        self.app_secret = os.getenv("DROPBOX_APP_SECRET")
        self.account_id = os.getenv("DROPBOX_ACCOUNT_ID")  # Add account ID from env
        
        # Print partial tokens for debugging
        print(f"Access Token (first 7 chars): {self.access_token[:7]}..." if self.access_token else "Access Token: None")
        print(f"Refresh Token (first 7 chars): {self.refresh_token[:7]}..." if self.refresh_token else "Refresh Token: None")
        print(f"App Key (first 7 chars): {self.app_key[:7]}..." if self.app_key else "App Key: None")
        print(f"App Secret (first 7 chars): {self.app_secret[:7]}..." if self.app_secret else "App Secret: None")
        print(f"Account ID: {self.account_id}" if self.account_id else "Account ID: None")
        
        # Initialize Dropbox client
        self.dbx = None
        self.initialize_client()
        
        # Verify account on startup
        if self.dbx:
            self.verify_account()
    
    def initialize_client(self):
        """Initialize the Dropbox client with the current access token"""
        if self.access_token:
            self.dbx = dropbox.Dropbox(
                oauth2_access_token=self.access_token,
                app_key=self.app_key,
                app_secret=self.app_secret,
                oauth2_refresh_token=self.refresh_token
            )
            logger.info("Dropbox client initialized")
        else:
            logger.warning("No access token available for Dropbox")
    
    def verify_account(self):
        """Verify we're connected to the correct account"""
        try:
            account = self.dbx.users_get_current_account()
            logger.info(f"Connected to Dropbox account: {account.name.display_name} (ID: {account.account_id})")
            
            # If we have an expected account ID, verify it matches
            if self.account_id and account.account_id != self.account_id:
                logger.error(f"Connected to wrong Dropbox account! Expected: {self.account_id}, Got: {account.account_id}")
                logger.error("Please update your .env file with the correct DROPBOX_ACCESS_TOKEN and DROPBOX_REFRESH_TOKEN")
                
                # Save the current account ID to .env if it doesn't exist
                if not self.account_id:
                    logger.info(f"Saving current account ID to .env: {account.account_id}")
                    self.update_env_file("DROPBOX_ACCOUNT_ID", account.account_id)
                    self.account_id = account.account_id
                
                return False
            
            # If we don't have an account ID saved, save the current one
            if not self.account_id:
                logger.info(f"Saving current account ID to .env: {account.account_id}")
                self.update_env_file("DROPBOX_ACCOUNT_ID", account.account_id)
                self.account_id = account.account_id
            
            return True
        except Exception as e:
            logger.error(f"Error verifying account: {e}")
            return False
    
    def generate_new_access_token(self):
        """Generate a new access token using the refresh token"""
        if not self.refresh_token or not self.app_key or not self.app_secret:
            logger.error("Missing refresh token, app key, or app secret")
            return False
        
        url = "https://api.dropboxapi.com/oauth2/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.app_key,
            "client_secret": self.app_secret,
        }
        
        try:
            logger.info("Requesting new access token")
            # Add timeout to prevent hanging requests
            response = requests.post(url, headers=headers, data=data, timeout=30)
            
            if response.status_code == 200:
                new_token = response.json().get("access_token")
                self.access_token = new_token
                
                # Update the client with the new token
                self.initialize_client()
                
                # Verify we're still connected to the right account
                if not self.verify_account():
                    logger.error("After token refresh, connected to wrong account!")
                    return False
                
                # Save the new token to .env file if possible
                try:
                    self.update_env_file("DROPBOX_ACCESS_TOKEN", new_token)
                except Exception as e:
                    logger.warning(f"Could not update .env file: {e}")
                
                logger.info("Successfully generated new access token")
                return True
            else:
                logger.error(f"Failed to get new access token. Status: {response.status_code}, Response: {response.text}")
                return False
        except requests.exceptions.Timeout:
            logger.error("Timeout while requesting new access token")
            return False
        except requests.exceptions.ConnectionError:
            logger.error("Connection error while requesting new access token")
            return False
        except Exception as e:
            logger.error(f"Error generating new access token: {e}")
            return False
    
    def update_env_file(self, key, value):
        """Update a key-value pair in the .env file"""
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
        
        if not os.path.exists(env_path):
            logger.warning(f".env file not found at {env_path}")
            return
        
        # Read the current .env file
        with open(env_path, 'r') as file:
            lines = file.readlines()
        
        # Update the specific key
        updated = False
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}\n"
                updated = True
                break
        
        # Add the key if it doesn't exist
        if not updated:
            lines.append(f"{key}={value}\n")
        
        # Write back to the .env file
        with open(env_path, 'w') as file:
            file.writelines(lines)
        
        logger.info(f"Updated {key} in .env file")
    
    # Keep only one check_token_validity method (remove the duplicate)
    def check_token_validity(self):
        """Check if the current token is valid and refresh if needed"""
        if not self.dbx:
            if not self.access_token:
                logger.error("No access token available")
                return False
            self.initialize_client()
        
        try:
            # Test the connection
            self.dbx.users_get_current_account()
            logger.info("Dropbox token is valid")
            return True
        except AuthError:
            logger.warning("Dropbox token is expired, generating new access token")
            return self.generate_new_access_token()
        except Exception as e:
            logger.error(f"Error checking token validity: {e}")
            return False
    
    # Remove this synchronous upload_file method as it's redundant and has an error (using self.client instead of self.dbx)
    def upload_file(self, file_path, dropbox_path):
        """Upload a file to Dropbox"""
        if not self.client:  # This is incorrect - should be self.dbx
            logger.error("Dropbox client not initialized")
            return False
        
        try:
            # First try to validate the token
            if not self.verify_account():
                logger.warning("Token validation failed, attempting to refresh token")
                if not self.generate_new_access_token():
                    logger.error("Failed to refresh token")
                    return False
            
            # Now proceed with upload
            with open(file_path, 'rb') as f:
                logger.info(f"Uploading {file_path} to Dropbox path {dropbox_path}")
                self.client.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode.overwrite)
            
            logger.info(f"Successfully uploaded {file_path} to Dropbox")
            return True
        except dropbox.exceptions.AuthError:
            logger.warning("Authentication error, attempting to refresh token")
            if self.generate_new_access_token():
                # Try upload again with new token
                return self.upload_file(file_path, dropbox_path)
            else:
                logger.error("Failed to refresh token after auth error")
                return False
        except dropbox.exceptions.ApiError as e:
            logger.error(f"Dropbox API error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error uploading file to Dropbox: {e}")
            return False
    
    # Keep this async upload_file method as it's the one being used by the upload_to_dropbox function
    async def upload_file(self, file_path, dropbox_path):
        """Upload a file to Dropbox and return a shareable link"""
        # Check if we have credentials
        if not self.access_token and not self.refresh_token:
            logger.warning("No Dropbox credentials available")
            return self.get_mock_url(dropbox_path)
        
        # Check token validity
        if not self.check_token_validity():
            logger.warning("Could not validate or refresh Dropbox token")
            return self.get_mock_url(dropbox_path)
        
        try:
            # Fix the path format - ensure no double slashes
            if dropbox_path.startswith('/'):
                dropbox_path = dropbox_path[1:]  # Remove leading slash
            
            # Upload the file
            logger.info(f"Uploading file to Dropbox: {file_path} -> {dropbox_path}")
            with open(file_path, 'rb') as f:
                self.dbx.files_upload(f.read(), f"/{dropbox_path}", mode=dropbox.files.WriteMode.overwrite)
            
            # Create a shared link
            logger.info(f"Creating shared link for {dropbox_path}")
            shared_link = self.dbx.sharing_create_shared_link_with_settings(f"/{dropbox_path}")
            
            # Keep the original URL for preview in browser (just ensure dl=0)
            dl_url = shared_link.url.replace("?dl=1", "?dl=0")
            logger.info(f"Generated preview link: {dl_url}")
            return dl_url
            
        except Exception as e:
            logger.error(f"Error uploading to Dropbox: {e}", exc_info=True)
            return self.get_mock_url(dropbox_path)
    
    def get_mock_url(self, file_name):
        """Generate a mock URL for when Dropbox upload fails"""
        timestamp = int(time.time())
        mock_url = f"https://www.dropbox.com/s/mock-link/{timestamp}/{file_name}?dl=1"
        logger.warning(f"Using mock URL: {mock_url}")
        return mock_url

# Create a singleton instance
dropbox_service = DropboxService()

async def upload_to_dropbox(file_path, filename, folder_path="/property_pdf"):
    """
    Upload a file to Dropbox and return a shareable link
    """
    logger.info(f"Starting Dropbox upload: file_path={file_path}, filename={filename}, folder_path={folder_path}")
    
    # Ensure folder_path doesn't start with a slash
    if folder_path.startswith('/'):
        folder_path = folder_path[1:]
    
    # Construct the Dropbox path with the folder
    dropbox_path = f"{folder_path}/{filename}"
    
    # Use the service to upload the file
    return await dropbox_service.upload_file(file_path, dropbox_path)