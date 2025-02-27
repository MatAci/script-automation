import os
import pickle
import base64
import yfinance as yf
from email.mime.text import MIMEText
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv
import sqlite3

# Učitaj varijable iz .env datoteke
load_dotenv()

# Gmail API scope (dozvola za slanje e-mailova)
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

# Nazivi datoteka za autorizaciju
CLIENT_SECRET_FILE = os.getenv("CLIENT_SECRET_FILE", "client_secret.json")
TOKEN_FILE = os.getenv("TOKEN_FILE", "token.pickle")

# Hardkodirani e-mail primatelja
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER", "acingermateo@gmail.com")

# Simbol ETF-a
TICKER = "IUSA.AS"

def get_credentials():
    """Provjerava postoji li token, ako ne postoji traži prijavu preko OAuth-a"""
    creds = None

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)

    return creds

def send_email(to, subject, message_text):
    """Šalje email pomoću Gmail API-ja"""
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

def check_price_alert():
    """Provjerava trenutnu cijenu ETF-a i šalje upozorenje ako je pad od ATH veći od definiranog postotka"""
    etf = yf.Ticker(TICKER)

    # Trenutna cijena
    current_price = etf.history(period="1d")["Close"].iloc[-1]

    # Povijesni podaci za sve vrijeme
    historical_data = etf.history(period="max")

    # Najveća cijena ikada
    all_time_high = historical_data["Close"].max()

    # Provjerava ATH iz baze
    conn = sqlite3.connect("alerts.db")
    cursor = conn.cursor()

    cursor.execute("SELECT ath FROM ath WHERE id = 1")
    ath_record = cursor.fetchone()[0]

    if ath_record == all_time_high:
        # Postotci od 0.25 do 30 s korakom 0.25
        thresholds = [i / 4 for i in range(1, 121)]  # 0.25, 0.50, 0.75, ..., 30.0
        last_sent = None

        drop_percentage = round(((all_time_high - current_price) / all_time_high) * 100, 4)

        for threshold in thresholds:
            if drop_percentage >= threshold:
                cursor.execute("SELECT is_active FROM percentages WHERE id = ?", (threshold,))
                result = cursor.fetchone()
                
                if result is not None and not result[0]:  # Ako is_active postoji i nije aktivan
                    last_sent = threshold  # Pamti posljednji koji će se poslati
                # Ažuriraj sve prethodne na true
                cursor.execute("UPDATE percentages SET is_active = 1 WHERE id = ?", (threshold,))

        # Ako je pronađen posljednji neaktivni postotak
        if last_sent is not None:
            subject = "IUSA Core S&P 500 Price Alert"
            message = (
                f"Cijena ETF-a {TICKER} je pala za {drop_percentage:.4f}% od vrha!\n\n"
                f"Trenutna cijena: {current_price:.4f} EUR\n"
                f"Najveća cijena ikada: {all_time_high:.4f} EUR\n"
            )
            send_email(EMAIL_RECEIVER, subject, message)

    else:
        # Ažuriraj trenutni ATH i resetiraj is_active za sve postotke
        cursor.execute("UPDATE ath SET ath = ? WHERE id = 1", (all_time_high,))
        cursor.execute("UPDATE percentages SET is_active = 0")
        conn.commit()  # Spremi promjene

        print("✅ Ažuriran ATH i resetiran status aktivacije u percentages.")

        # Ponovno provjeri uvjete za slanje emaila
        check_price_alert()  # Ponovni poziv funkcije nakon ažuriranja ATH-a

    conn.commit()
    conn.close()


if __name__ == "__main__":
    check_price_alert()
