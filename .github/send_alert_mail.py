import smtplib
import pandas as pd
import datetime
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# GMX SMTP-Konfiguration
SMTP_SERVER = "smtp.gmx.net"
SMTP_PORT = 587
EMAIL_SENDER = "conradfritsche@gmx.de"
EMAIL_PASSWORD = os.getenv("57rE&RP6jli@xIQY&7ng")  # Passwort aus Umgebungsvariable laden
EMAIL_RECEIVER = EMAIL_SENDER  # Gleiches Sende- und Empfangskonto

LOG_FILE = "trade_log.csv"

# Funktion zum Laden der letzten Fehlermeldungen oder erfolgreichen Trades
def get_latest_trades(status_filter):
    try:
        df = pd.read_csv(LOG_FILE)

        # Filtere nur Meldungen des heutigen Tages
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        df_today = df[df["Timestamp"].dt.strftime("%Y-%m-%d") == today]
        df_filtered = df_today[df_today["Status"] == status_filter]

        if df_filtered.empty:
            return None

        return "\n".join(df_filtered["Message"].tolist())

    except Exception as e:
        return f"Fehler beim Laden des Logs: {e}"

# Funktion zum Senden einer E-Mail
def send_email(subject, body):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        server.quit()
        print(f"E-Mail erfolgreich gesendet: {subject}")
    except Exception as e:
        print(f"Fehler beim Senden der E-Mail: {e}")

# Funktion zum Senden von Fehlerwarnungen
def send_alert():
    errors = get_latest_trades("ERROR")

    if not errors:
        print("Keine Fehler gefunden. Keine Fehler-E-Mail wird gesendet.")
        return

    email_body = f"""
    Hallo Conrad,

    der Trading-Bot hat heute folgende Fehler festgestellt:

    {errors}

    Bitte überprüfe das `trade_log.csv` für weitere Details.

    Mit freundlichen Grüßen,
    Dein Trading-Bot
    """
    send_email("⚠️ Trading-Bot Fehlerwarnung", email_body)

# Funktion zum Senden einer Bestätigungs-E-Mail für erfolgreiche Trades
def send_trade_confirmation():
    successful_trades = get_latest_trades("SUCCESS")

    if not successful_trades:
        print("Keine erfolgreichen Trades heute. Keine Bestätigungs-E-Mail wird gesendet.")
        return

    email_body = f"""
    Hallo Conrad,

    dein Trading-Bot hat heute erfolgreich folgende Transaktionen durchgeführt:

    {successful_trades}

    Die vollständigen Logs findest du in `trade_log.csv`.

    BR!

    Smart Contract PAV
    """
    send_email("✅ Trading-Bot: Erfolgreicher Trade", email_body)

if __name__ == "__main__":
    send_alert()
    send_trade_confirmation()
