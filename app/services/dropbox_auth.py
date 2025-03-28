import dropbox
from dropbox import DropboxOAuth2FlowNoRedirect
import webbrowser
import os
from dotenv import load_dotenv, set_key

# Load environment variables
load_dotenv()

# Path to .env file
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")

# Get APP_KEY from environment variables
APP_KEY = os.getenv("DROPBOX_APP_KEY")
APP_SECRET = os.getenv("DROPBOX_APP_SECRET")

def update_env_file(key, value):
    """Update a key-value pair in the .env file"""
    if not os.path.exists(ENV_PATH):
        print(f".env file not found at {ENV_PATH}")
        return False
    
    set_key(ENV_PATH, key, value)
    print(f"Updated {key} in .env file")
    return True

def main():
    print("Starting Dropbox authentication flow...")
    
    # Create the OAuth flow
    auth_flow = DropboxOAuth2FlowNoRedirect(
        APP_KEY, 
        consumer_secret=APP_SECRET,
        use_pkce=True, 
        token_access_type='offline'
    )
    
    # Get the authorization URL
    authorize_url = auth_flow.start()
    
    # Open the URL in the browser
    webbrowser.open_new_tab(authorize_url)
    
    print("1. This is the link to start the authentication. In case it will not open, copy and paste it: " + authorize_url)
    print("2. Click \"Allow\" (you might have to log in first).")
    print("3. Copy the authorization code.")
    
    # Get the authorization code from the user
    auth_code = input("Enter the authorization code here: ").strip()
    
    try:
        # Exchange the authorization code for an access token
        oauth_result = auth_flow.finish(auth_code)
        
        # Save the tokens to the .env file
        update_env_file("DROPBOX_AUTH_CODE", auth_code)
        update_env_file("DROPBOX_ACCESS_TOKEN", oauth_result.access_token)
        update_env_file("DROPBOX_REFRESH_TOKEN", oauth_result.refresh_token)
        
        # Create a Dropbox client using the refresh token
        with dropbox.Dropbox(
            oauth2_refresh_token=oauth_result.refresh_token,
            app_key=APP_KEY,
            app_secret=APP_SECRET
        ) as dbx:
            # Test the connection
            account = dbx.users_get_current_account()
            print(f"Successfully connected to Dropbox account: {account.name.display_name}")
            
            # Save account ID
            update_env_file("DROPBOX_ACCOUNT_ID", account.account_id)
            
            print("All tokens have been saved to your .env file.")
            print("You can now use the Dropbox API in your application.")
            
    except Exception as e:
        print(f'Error: {e}')
        exit(1)

if __name__ == "__main__":
    main()