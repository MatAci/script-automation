import os
import pickle
import base64
import sqlite3
import random
from email.mime.text import MIMEText
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Učitaj varijable iz .env datoteke
load_dotenv()

# Postavi Gmail API scope (dozvolu za slanje e-mailova)
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

# Nazivi datoteka za autorizaciju
CLIENT_SECRET_FILE = os.getenv("CLIENT_SECRET_FILE", "client_secret.json")
TOKEN_FILE = os.getenv("TOKEN_FILE", "token.pickle")

def get_credentials():
    """Provjerava postoji li token, ako ne postoji traži prijavu preko OAuth-a"""
    creds = None

    # Ako već imamo spremljeni token, učitaj ga
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)

    # Ako nema valjanih kredencijala, pokreće OAuth prijavu
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            with open(CLIENT_SECRET_FILE, "r") as f:
                client_secret_json = f.read()
                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
                creds = flow.run_local_server(port=0)

        # Spremi token za buduće prijave
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)

    return creds

def send_email(to, subject, message_text):
    """Šalje email pomoću Gmail API-ja"""
    creds = get_credentials()
    service = build("gmail", "v1", credentials=creds)

    # Kreiraj email poruku
    message = MIMEText(message_text)
    message["to"] = to
    message["subject"] = subject
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    body = {"raw": encoded_message}

    # Pošalji e-mail
    try:
        service.users().messages().send(userId="me", body=body).execute()
        print(f"✅ Email poslan na {to}!")
    except Exception as e:
        print(f"❌ Greška prilikom slanja emaila: {e}")

def insert_random_data():
    """Umetni random broj u field1 i prenesi u field2"""
    conn = sqlite3.connect('alerts.db')
    cursor = conn.cursor()

    # Generiraj nasumični broj za field1
    random_value = random.randint(1, 100)  # Možeš prilagoditi raspon

    # Umetni u tablicu
    cursor.execute("INSERT INTO alerts (field1, field2) VALUES (?, ?)", (random_value, None))

    # Prenesi vrijednost iz field1 u field2
    cursor.execute("UPDATE alerts SET field2 = field1 WHERE id = (SELECT MAX(id) FROM alerts)")

    conn.commit()
    conn.close()

# TESTIRANJE
if __name__ == "__main__":
    receiver = os.getenv("EMAIL_RECEIVER", "acingermateo@gmail.com")  # Hardkodirano za test
    insert_random_data()  # Umetni nasumične podatke
    send_email(receiver, "Testni email", "Podaci su uspješno uneseni u bazu.")
