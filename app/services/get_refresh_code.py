import base64
import requests
import json
import os
from dotenv import load_dotenv

# Get the absolute path to the .env file
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
print(f"Loading .env from: {env_path}")

# Load environment variables
load_dotenv(env_path, override=True)

APP_KEY = os.getenv("DROPBOX_APP_KEY")
APP_SECRET = os.getenv("DROPBOX_APP_SECRET")

# This should be the authorization code, not the access token
# If you don't have an authorization code, you'll need to get one first
ACCESS_CODE = os.getenv("DROPBOX_AUTH_CODE")  # This is different from ACCESS_TOKEN

# Create Basic Auth header
BASIC_AUTH = base64.b64encode(f'{APP_KEY}:{APP_SECRET}'.encode()).decode()

headers = {
    'Authorization': f"Basic {BASIC_AUTH}",
    'Content-Type': 'application/x-www-form-urlencoded',
}

# Format data
data = f'code={ACCESS_CODE}&grant_type=authorization_code'

try:
    # Use the same request format as the reference code
    response = requests.post(
        'https://api.dropboxapi.com/oauth2/token',
        headers=headers,
        data=data
    )
    
    # Check if the request was successful
    response.raise_for_status()
    
    # Print the response
    result = response.json()
    print(json.dumps(result, indent=2))
    
    # Save the tokens to .env file
    if 'access_token' in result and 'refresh_token' in result:
        print("\nSaving tokens to .env file...")
        
        # Read current .env file
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        # Create a new list for updated lines
        new_lines = []
        
        # Track which values have been updated
        access_token_updated = False
        refresh_token_updated = False
        uid_updated = False
        account_id_updated = False
        
        # Update the values in the lines
        for line in lines:
            if line.startswith('DROPBOX_ACCESS_TOKEN='):
                new_lines.append(f'DROPBOX_ACCESS_TOKEN={result["access_token"]}\n')
                access_token_updated = True
            elif line.startswith('DROPBOX_REFRESH_TOKEN='):
                new_lines.append(f'DROPBOX_REFRESH_TOKEN={result["refresh_token"]}\n')
                refresh_token_updated = True
            elif line.startswith('DROPBOX_UID=') and 'uid' in result:
                new_lines.append(f'DROPBOX_UID={result["uid"]}\n')
                uid_updated = True
            elif line.startswith('DROPBOX_ACCOUNT_ID=') and 'account_id' in result:
                new_lines.append(f'DROPBOX_ACCOUNT_ID={result["account_id"]}\n')
                account_id_updated = True
            else:
                new_lines.append(line)
        
        # Add any values that weren't updated
        if not access_token_updated:
            new_lines.append(f'DROPBOX_ACCESS_TOKEN={result["access_token"]}\n')
        if not refresh_token_updated:
            new_lines.append(f'DROPBOX_REFRESH_TOKEN={result["refresh_token"]}\n')
        if not uid_updated and 'uid' in result:
            new_lines.append(f'DROPBOX_UID={result["uid"]}\n')
        if not account_id_updated and 'account_id' in result:
            new_lines.append(f'DROPBOX_ACCOUNT_ID={result["account_id"]}\n')
        
        # Write back to .env file
        with open(env_path, 'w') as f:
            f.writelines(new_lines)
            
        print("Tokens saved successfully!")
        
except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"Response: {e.response.text}")