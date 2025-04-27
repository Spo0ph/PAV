import os
import logging
from logging.handlers import RotatingFileHandler
import pandas as pd
import requests
from datetime import datetime

# --- Logging-Konfiguration ---
LOG_FILE = os.getenv("PAV_LOGFILE", "pav_pipeline.log")
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

STOOQ_URL = "https://stooq.com/q/d/l/"
SYMBOL = "^spx"
SMA_WINDOW = 375
DD_COUNTDOWN_RESET = 425
LEVERAGE = 3
OUTPUT_CSV = "sp500_signals.csv"


def load_data():
    """Lädt historische S&P 500-Daten von Stooq.com."""
    params = {"s": SYMBOL, "i": "d"}
    logger.info(f"Lade Daten für {SYMBOL} von Stooq")
    resp = requests.get(STOOQ_URL, params=params)
    resp.raise_for_status()
    df = pd.read_csv(pd.compat.StringIO(resp.text), parse_dates=["Date"], index_col="Date")
    logger.info(f"Daten geladen: {len(df)} Zeilen von {df.index.min().date()} bis {df.index.max().date()}")
    return df


def compute_signals(df):
    """Berechnet SMA, Drawdown-Regeln und Hebel."""
    logger.info(f"Berechne {SMA_WINDOW}-Tag-SMA")
    df['SMA'] = df['Close'].rolling(window=SMA_WINDOW).mean()
    df['SMA_Signal'] = df['Close'] > df['SMA']
    df['SMA_Signal'] = df['SMA_Signal'].map({True: 'BUY', False: 'SELL'})

    logger.info("Bestimme All-Time-High und Drawdown")
    df['ATH'] = df['Close'].cummax()
    df['DD_Ratio'] = df['Close'] / df['ATH']

    # Countdown-Mechanismus
    logger.info("Wende Drawdown-Countdown-Regel an")
    countdown = 0
    signals = []
    for dd in df['DD_Ratio']:
        if dd < 0.7:
            countdown = DD_COUNTDOWN_RESET
        else:
            countdown = max(countdown - 1, 0)
        signals.append('BUY' if countdown > 0 else None)
    df['DD_Signal'] = signals

    # Kombiniertes Signal
    df['Signal'] = df['DD_Signal'].fillna(df['SMA_Signal'])

    # Hebel-Spalte
    df['Close_x3'] = (df['Close'] * LEVERAGE).round(2)

    logger.info(f"Signale berechnet für {len(df)} Datenpunkte")
    return df


def save_csv(df):
    """Speichert das Ergebnis als CSV."""
    df_out = df[['Close', 'SMA', 'SMA_Signal', 'ATH', 'DD_Ratio', 'Signal', 'Close_x3']]
    df_out.to_csv(OUTPUT_CSV)
    logger.info(f"Ergebnisse in {OUTPUT_CSV} geschrieben")


def main():
    logger.info("Starte sp500_pipeline")
    try:
        df = load_data()
        df = compute_signals(df)
        save_csv(df)
        logger.info("Pipeline erfolgreich abgeschlossen")
    except Exception:
        logger.exception("Fehler in der Pipeline")
        raise


if __name__ == '__main__':
    main()