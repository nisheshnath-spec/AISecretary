#auth.py
import os
import flask
from flask import redirect, session, url_for, request, render_template_string
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
import json
import base64
from parsing import parse_emails
from summarizer import rank, compose_reply, reply_info_question
import email.utils
from email.message import EmailMessage
from googleapiclient.errors import HttpError

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

load_dotenv()

# Load from environment
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
]
REDIRECT_URI = 'http://127.0.0.1:5000/oauth2callback'

# In-memory token store (for dev only)
TOKEN_FILE = 'token.json'

def login():
    # Check if we already have credentials in session
    creds_json = session.get('credentials')
    if creds_json:
        try:
            creds = Credentials.from_authorized_user_info(json.loads(creds_json), SCOPES)
            # If any required scopes are missing, clear session to force re-consent
            if not set(SCOPES).issubset(set(creds.scopes or [])):
                print("⚠️ Scope mismatch — forcing re-consent.")
                session.clear()
        except Exception as e:
            # If creds are corrupt or expired, clear them
            print(f"⚠️ Invalid credentials found: {e}")
            session.clear()

    # Always create a fresh Flow if no valid creds
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

    auth_url, _ = flow.authorization_url(
        prompt='consent',
        access_type='offline',
        include_granted_scopes='true'
    )
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
    # html = ""
    # for email in parsed_emails:
    #     html += f"<h2>Subject:</h2><p>{email['subject']}</p>"
    #     html += f"<h2>Sender:</h2><p>{email['sender']}</p>"
    #     html += f"<h2>Date:</h2><p>{email['date']}</p>"
    #     html += f"<h2>Body:</h2><pre>{email['body']}</pre><hr>"
    #     html += f"<h2>Body_summary:</h2><pre>{email['body_summary']}</pre><hr>"

    ranked_order = rank(parsed_emails)
    emails_by_number = {email['email_id']: email for email in parsed_emails}
    html = ""
    for num in ranked_order:
        email = emails_by_number.get(num)
        html += f"<h2>Reply Code: {email['reply_code']}</h2>"
        html += f"<h2>Email {num}</h2>"
        html += f"<p>{email['body_summary']}</p><hr>"
        #html += f"<p>{email['reply']}</p>"
        if email['reply_code'] > 0:
            html += f'<div><a href="/reply/{email["email_id"]}">Draft a reply</a></div>'
            html += "<hr>"

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


def reply_email(email_id):
    if 'credentials' not in session:
        return redirect(url_for('login'))
    
    creds = Credentials.from_authorized_user_info(json.loads(session['credentials']), SCOPES)
    service = build('gmail', 'v1', credentials=creds)
    emails = parse_emails(creds, max_results = 1)
    by_id = {e['email_id']: e for e in emails}
    e = by_id.get(email_id)
    if not e:
        return "Email not found", 404
    
    if e['reply_code'] == 0:
        return "No reply necessary"
    
    # Which button did the user press?
    action = request.form.get('action', '').lower()

    if request.method == 'POST' and action == 'generate':
        user_info = request.form.get('user_info', '').strip()
        # Correct arg order: (subject, sender, summary, user_input)
        draft = compose_reply(e['subject'], e['sender'], e['body_summary'], user_info)
        return render_template_string("""
            <h2>Reply to: {{ subj }}</h2>
            <p><b>From:</b> {{ sender }}</p>
            <p>{{ summary }}</p>
            <hr/>
            <form method="post">
                <p><b>Edit your email before sending:</b></p>
                <textarea name="final_body" rows="12" cols="80">{{ draft }}</textarea><br/><br/>
                <input type="hidden" name="action" value="send" />
                <button type="submit">Send</button>
            </form>
            <br/>
            <a href="/profile">Back</a>
        """, subj=e['subject'], sender=e['sender'], summary=e['body_summary'], draft=draft)
    
    if request.method == 'POST' and action == 'send':
        final_body = request.form.get('final_body', '').strip()
        if not final_body:
            return render_template_string("""
                <p>No content to send.</p>
                <a href="/profile">Back</a>
            """)
        try:
            # e['sender'] typically contains "Name <email@domain>". Extract just the email.
            import re
            m = re.search(r'<([^>]+)>', e['sender'])
            to_addr = m.group(1) if m else e['sender']

            resp = send_gmail_reply(
                service=service,
                to_addr=to_addr,
                subject=e['subject'],
                body_text=final_body,
                thread_id=e.get('thread_id')
            )
            return render_template_string("""
                <h2>✅ Sent!</h2>
                <p>Your reply has been sent.</p>
                <p><small>Message ID: {{ mid }}</small></p>
                <a href="/profile">Back</a>
            """, mid=resp.get('id', 'unknown'))
        except HttpError as err:
            # Common case: missing gmail.send scope -> 403
            return render_template_string("""
                <h2>❌ Could not send</h2>
                <pre>{{ error }}</pre>
                <p>If this says you're missing the gmail.send scope, please log out and log back in so we can request it.</p>
                <a href="/profile">Back</a>
            """, error=str(err))

    # Default GET: ask your info question, then generate
    question = reply_info_question(e['sender'], e['subject'], e['body_summary'])
    return render_template_string("""
        <h2>Reply to: {{ subj }}</h2>
        <p><b>From:</b> {{ sender }}</p>
        <p>{{ summary }}</p>
        <hr/>
        <p><b>Question:</b> {{ question }}</p>
        <form method="post">
            <textarea name="user_info" rows="6" cols="60" placeholder="Type your answer here..."></textarea><br/><br/>
            <input type="hidden" name="action" value="generate" />
            <button type="submit">Generate Draft</button>
        </form>
        <a href="/profile">Back</a>
    """, subj=e['subject'], sender=e['sender'], summary=e['body_summary'], question=question)

def send_gmail_reply(service, to_addr, subject, body_text, thread_id = None):
    final_subject = subject if subject.lower().startswith("re:") else f"Re: {subject}"
    msg = EmailMessage()
    msg['To'] = to_addr
    msg['Subject'] = final_subject
    msg.set_content(body_text)
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
    body = {"raw": raw}
    if thread_id:
        body['thread_id'] = thread_id
        
    return service.users().messages().send(userId='me', body=body).execute()


