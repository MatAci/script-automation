import os
import pickle
import base64
import json
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def get_credentials():
    """Dohvaća kredencijale iz GitHub Secrets i vraća autorizirani objekt."""
    client_secret_json = os.getenv("CLIENT_SECRET_JSON")
    client_secrets = json.loads(client_secret_json)

    token_b64 = os.getenv("TOKEN_PICKLE")
    token_data = base64.b64decode(token_b64)
    creds = pickle.loads(token_data)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise Exception("Token nije valjan ili nije moguće osvježiti!")

    return creds

def send_email(to, subject, message_text):
    """Šalje e-mail pomoću Gmail API-ja"""
    creds = get_credentials()
    service = build("gmail", "v1", credentials=creds)

    message = MIMEText(message_text)
    message["to"] = to
    message["subject"] = subject
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    body = {"raw": encoded_message}

    try:
        service.users().messages().send(userId="me", body=body).execute()
        print(f"✅ Email poslan na {to}!")
    except Exception as e:
        print(f"❌ Greška prilikom slanja emaila: {e}")

# Hardkodirani e-mail prijamnik
if __name__ == "__main__":
    receiver = "acingermateo@gmail.com"  # Zamijeni s pravom e-mail adresom
    send_email(receiver, "Testni email", "Ovo je test poruka poslana iz GitHub Actions!")