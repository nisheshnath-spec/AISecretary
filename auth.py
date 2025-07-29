import os
import flask
from flask import redirect, session, url_for, request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
import json

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

load_dotenv()

# Load from environment
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
REDIRECT_URI = 'http://127.0.0.1:5000/oauth2callback'

# In-memory token store (for dev only)
TOKEN_FILE = 'token.json'

def login():
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        },
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline', include_granted_scopes='true')
    return redirect(auth_url)

def oauth2callback():
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        },
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials

    # Save token to file (for simplicity in dev)
    with open(TOKEN_FILE, 'w') as token:
        token.write(credentials.to_json())

    session['credentials'] = credentials.to_json()
    return redirect(url_for('profile'))

def profile():
    if 'credentials' not in session:
        return redirect(url_for('login'))

    creds = Credentials.from_authorized_user_info(json.loads(session['credentials']), SCOPES)
    service = build('gmail', 'v1', credentials=creds)
    user_info = service.users().getProfile(userId='me').execute()

    return f"You're logged in as: {user_info['emailAddress']}"
