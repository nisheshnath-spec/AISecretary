from flask import Flask, session, redirect, url_for
from dotenv import load_dotenv
import os
from parsing import parse_emails
from auth import login, oauth2callback, profile
import json


load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

@app.route("/")
def home():
    return '<a href="/login">Login with Google</a>'

app.add_url_rule('/login', 'login', login)
app.add_url_rule('/oauth2callback', 'oauth2callback', oauth2callback)
app.add_url_rule('/profile', 'profile', profile)

if __name__ == "__main__":
    app.run(debug=True)
