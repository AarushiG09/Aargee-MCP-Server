import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Scopes needed for writing to Google Docs and composing/creating drafts in Gmail.
SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/gmail.compose'
]

# Resolve paths relative to the directory where auth.py is located.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH = os.path.join(BASE_DIR, 'token.json')
CREDENTIALS_PATH = os.path.join(BASE_DIR, 'credentials.json')

def get_credentials():
    """
    Retrieves, refreshes, or initiates the Google OAuth2 flow to obtain credentials.
    Supports reading credentials and tokens from environment variables for headless deployment.
    """
    creds = None
    
    # 1. Try loading existing token from environment variable first
    env_token = os.getenv("GOOGLE_TOKEN_JSON")
    if env_token:
        try:
            token_info = json.loads(env_token)
            creds = Credentials.from_authorized_user_info(token_info, SCOPES)
        except Exception as e:
            print(f"Warning: Failed to load credentials from GOOGLE_TOKEN_JSON environment variable: {e}")
            
    # Fallback to local token.json if env variable wasn't present or failed
    if not creds and os.path.exists(TOKEN_PATH):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        except Exception as e:
            print(f"Warning: Failed to load cached token from {TOKEN_PATH}: {e}")

    # 2. If no valid credentials, login/refresh
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Warning: Failed to refresh token: {e}")
                creds = None

        # If refresh failed or token wasn't valid, start local browser OAuth
        if not creds:
            env_credentials = os.getenv("GOOGLE_CREDENTIALS_JSON")
            if env_credentials:
                try:
                    client_config = json.loads(env_credentials)
                    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                except Exception as e:
                    raise ValueError(f"Failed to parse GOOGLE_CREDENTIALS_JSON from environment: {e}")
            else:
                if not os.path.exists(CREDENTIALS_PATH):
                    raise FileNotFoundError(
                        f"'{CREDENTIALS_PATH}' not found in {BASE_DIR} and GOOGLE_CREDENTIALS_JSON environment variable is not set. "
                        "Please download OAuth Client ID credentials from Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            
            # This requires browser access; it will raise an error in headless/production environments
            creds = flow.run_local_server(port=0)
            
        # 3. Save credentials for future execution
        try:
            with open(TOKEN_PATH, 'w') as token_file:
                token_file.write(creds.to_json())
        except Exception as e:
            print(f"Warning: Failed to write token.json to disk (common in read-only filesystems): {e}")

    return creds
