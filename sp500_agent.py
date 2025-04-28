# sp500_agent.py
import os
import logging
from logging.handlers import RotatingFileHandler

import pandas as pd
from ibind import IbkrClient
from ibind.client.ibkr_utils import Answers  # für Order-Responses
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

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
# ------------------------------

# Umgebungsvariablen
IBKR_USER = os.getenv("IBKR_USER")
IBKR_PASS = os.getenv("IBKR_PASS")
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = os.getenv("API_PORT", "4001")
UPRO_CONID = os.getenv("UPRO_CONID")

def main():
    logger.info("Starte sp500_agent")

    try:
        # 1) Signale laden
        df = pd.read_csv("sp500_signals.csv", index_col=0, parse_dates=True)
        last_signal = df.iloc[-1]["SMA_DD_Signal"]
        price = float(df.iloc[-1]["Close"])
        logger.info(f"Letztes Signal: {last_signal}, Kurs: {price:.2f} USD")

        # 2) IBKR-Client initialisieren & authentifizieren
        client = IbkrClient(
            host=API_HOST,
            port=API_PORT,
            username=IBKR_USER,
            password=IBKR_PASS
        )
        client.check_health()
        client.tickle()

        # 3) Paper-Konto ermitteln
        accounts = client.portfolio_accounts().data.get("accounts", [])
        paper_account = None
        for acct in accounts:
            summary = client.account_summary(acct).data
            if summary.get("accountType", "").lower() == "paper":
                paper_account = acct
                break
        if not paper_account:
            raise RuntimeError("Kein PAPER-Konto gefunden")
        logger.info(f"Verwende PAPER-Konto: {paper_account}")

        # 4) Portfolio-Ledger abfragen
        ledger = client.get_ledger(paper_account).data
        cash = ledger.get("USD", {}).get("cashBalance", 0.0)
        logger.info(f"Cash Balance: {cash:.2f} USD")

        positions = ledger.get("positions", [])
        pos_qty = next(
            (p["position"] for p in positions if str(p.get("conid")) == UPRO_CONID),
            0
        )
        logger.info(f"UPRO Position: {pos_qty} Anteile")

        # 5) Handelslogik
        if last_signal == "BUY" and cash > price:
            qty = int(cash // price)
            if qty > 0:
                logger.info(f"Kaufe {qty} Anteile UPRO")
                order_req = {
                    "conid": int(UPRO_CONID),
                    "secType": "ETF",
                    "orderType": "MKT",
                    "side": "BUY",
                    "quantity": qty
                }
                # leeres Answers-Array, falls keine Fragen auftreten
                client.place_order(order_req, answers=[], account_id=paper_account)
            else:
                logger.info("Nicht genügend Cash für eine Kauforder")
        elif last_signal == "SELL" and pos_qty > 0:
            logger.info(f"Verkaufe alle {pos_qty} Anteile UPRO")
            order_req = {
                "conid": int(UPRO_CONID),
                "secType": "ETF",
                "orderType": "MKT",
                "side": "SELL",
                "quantity": pos_qty
            }
            client.place_order(order_req, answers=[], account_id=paper_account)
        else:
            logger.info("Keine Handelsaktion erforderlich")

        logger.info("sp500_agent erfolgreich abgeschlossen")

    except Exception:
        logger.exception("Fehler im sp500_agent")
        raise

if __name__ == "__main__":
    main()