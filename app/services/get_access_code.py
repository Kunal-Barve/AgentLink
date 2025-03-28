import webbrowser
import os
from dotenv import load_dotenv
import sys

# Get the absolute path to the .env file
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
print(f"Loading .env from: {env_path}")

# Force reload the .env file
load_dotenv(env_path, override=True)

DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
print(f"App Key from env: '{DROPBOX_APP_KEY}'")

# Manually set the key if needed for testing
# DROPBOX_APP_KEY = "tdql4adyxfghhlk"

# Ensure the app key is properly formatted (strip any whitespace)
DROPBOX_APP_KEY = DROPBOX_APP_KEY.strip() if DROPBOX_APP_KEY else ""
print(f"App Key after strip: '{DROPBOX_APP_KEY}'")

url = f'https://www.dropbox.com/oauth2/authorize?client_id={DROPBOX_APP_KEY}&' \
      f'response_type=code&token_access_type=offline'

# Print the full URL for debugging
print(f"Authorization URL: {url}")

# Open the URL in the browser
webbrowser.open(url)