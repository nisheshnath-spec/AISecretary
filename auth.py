import os
import flask
from flask import redirect, session, url_for, request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
import json
import base64
from parsing import parse_emails

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
    parsed_emails = parse_emails(creds)
    #print out in html for now
    html = ""
    for email in parsed_emails:
        html += f"<h2>Subject:</h2><p>{email['subject']}</p>"
        html += f"<h2>Sender:</h2><p>{email['sender']}</p>"
        html += f"<h2>Date:</h2><p>{email['date']}</p>"
        html += f"<h2>Body:</h2><pre>{email['body']}</pre><hr>"
        html += f"<h2>Body_summary:</h2><pre>{email['body_summary']}</pre><hr>"
    return html



    # messages = service.users().messages().list(userId='me', maxResults=5).execute()
    # message_id = messages['messages'][0]['id']
    # msg = service.users().messages().get(userId='me', id=message_id).execute()

    # headers = msg['payload'].get('headers', [])
    # for header in headers:
    #     if header['name'] == 'Subject':
    #         subject = header['value']
    #         break
    # parts = msg['payload'].get('parts', [])
    # body_data = None
    # for part in parts:
    #     if part.get('mimeType') == 'text/plain':
    #         body_data = part['body'].get('data')
    #         continue
    # if not body_data:
    #     return "no plain text body found"
    
    # decoded_bytes = base64.urlsafe_b64decode(body_data + '==')
    # decoded_text = decoded_bytes.decode('utf-8')
    # return f"<h2>Subject:</h2><p>{subject}</p><h2>Body:</h2><pre>{decoded_text}</pre>"