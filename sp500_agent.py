import os
import logging
from logging.handlers import RotatingFileHandler
import pandas as pd
import requests
import time

# --- Logging-Konfiguration ---
LOG_FILE = os.getenv("PAV_LOGFILE", "sp500_agent.log")
LOG_LEVEL = os.getenv("PAV_LOGLEVEL", "INFO").upper()

logger = logging.getLogger("pav")
logger.setLevel(LOG_LEVEL)

file_handler = RotatingFileHandler(
    LOG_FILE, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8"
)
formatter = logging.Formatter(
    "%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Optional: Ausgabe auch in die Konsole
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
# ------------------------------

# Umgebungsvariablen
IBKR_USER   = os.getenv("IBKR_USER")
IBKR_PASS   = os.getenv("IBKR_PASS")
API_HOST    = os.getenv("API_HOST", "localhost")
API_PORT    = os.getenv("API_PORT", "4001")
UPRO_CONID  = os.getenv("UPRO_CONID")
API_URL     = f"https://{API_HOST}:{API_PORT}"


def authenticate():
    """
    Authentifiziert beim IBKR Client-Portal und gibt eine Session zurück.
    """
    session = requests.Session()
    login_payload = {"user": IBKR_USER, "password": IBKR_PASS}
    url = f"{API_URL}/api/v1/portal/login"
    logger.info("Sende Login-Anfrage an IBKR Client Portal")
    resp = session.post(url, json=login_payload, verify=False)
    resp.raise_for_status()
    logger.info("Erfolgreich authentifiziert")
    return session


def get_account_info(session):
    """
    Liest Kontostand und bestehende UPRO-Position aus.
    Gibt (cash, position_qty) zurück.
    """
    # Kontostand abfragen
    url_cash = f"{API_URL}/api/v1/portfolio/cash"
    resp_cash = session.get(url_cash, verify=False)
    resp_cash.raise_for_status()
    cash = resp_cash.json().get("cashBalance", 0.0)
    logger.info(f"Kontostand: {cash:.2f} USD")

    # Positionen abfragen
    url_pos = f"{API_URL}/api/v1/portfolio/positions"
    resp_pos = session.get(url_pos, verify=False)
    resp_pos.raise_for_status()
    positions = resp_pos.json()
    pos_qty = 0
    for pos in positions:
        if str(pos.get("conid")) == UPRO_CONID:
            pos_qty = pos.get("position", 0)
            break
    logger.info(f"UPRO-Position: {pos_qty} Anteile")
    return cash, pos_qty


def place_order(session, action, qty):
    """
    Führt eine Marktorder (BUY/SELL) für UPRO aus.
    """
    order = {
        "conid": int(UPRO_CONID),
        "secType": "ETF",
        "orderType": "MKT",
        "side": action,
        "quantity": qty,
    }
    url_order = f"{API_URL}/api/v1/trade"
    logger.info(f"Sende Order: {action} {qty} UPRO-Anteile")
    resp = session.post(url_order, json=order, verify=False)
    resp.raise_for_status()
    logger.info("Order erfolgreich platziert")
    return resp.json()


def main():
    logger.info("Starte sp500_agent")
    try:
        # 1) Signale laden
        df = pd.read_csv("sp500_signals.csv", index_col=0, parse_dates=True)
        last_signal = df.iloc[-1]["SMA_DD_Signal"]
        logger.info(f"Letztes Signal: {last_signal}")

        # Aktuellen Preis ermitteln (optional, ersatzweise über CSV-Spalte 'Close')
        price = float(df.iloc[-1]["Close"])
        logger.debug(f"Aktueller UPRO-Kurs: {price:.2f}")

        # 2) Authentifizieren
        session = authenticate()
        time.sleep(1)  # kurz warten, bis Session bereit

        # 3) Konto-Info
        cash, pos_qty = get_account_info(session)

        # 4) Order-Entscheidung
        if last_signal == "BUY" and cash > price:
            qty = int(cash // price)
            if qty > 0:
                logger.info(f"Kaufe {qty} Anteile UPRO")
                place_order(session, "BUY", qty)
            else:
                logger.info("Nicht genügend Cash für eine Kauforder")
        elif last_signal == "SELL" and pos_qty > 0:
            logger.info(f"Verkaufe alle {pos_qty} Anteile UPRO")
            place_order(session, "SELL", pos_qty)
        else:
            logger.info("Keine Handelsaktion erforderlich")

        logger.info("sp500_agent erfolgreich abgeschlossen")
    except Exception:
        logger.exception("Fehler im sp500_agent")
        raise


if __name__ == "__main__":
    main()