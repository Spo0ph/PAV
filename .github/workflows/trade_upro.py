import time
import datetime
import subprocess
import pandas as pd
import os
from ib_insync import IB, MarketOrder, Stock

# Konfiguration
IB_GATEWAY_PORT = 4002
MAX_RETRIES = 10
SLEEP_TIME = 10
SYMBOL = "UPRO"
DAILY_BUDGET = 25
LOG_FILE = "trade_log.csv"

# Funktion zum Speichern von Logs
def log_trade(status, message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {"Timestamp": timestamp, "Status": status, "Message": message}
    
    if not os.path.exists(LOG_FILE):
        df = pd.DataFrame([log_entry])
        df.to_csv(LOG_FILE, index=False)
    else:
        df = pd.read_csv(LOG_FILE)
        df = df.append(log_entry, ignore_index=True)
        df.to_csv(LOG_FILE, index=False)
    
    print(f"LOG: {status} - {message}")

# Funktion zur Prüfung, ob heute ein Handelstag ist
def is_trading_day():
    df = pd.read_csv("SP500_x2_SMA.csv")
    df['Date'] = pd.to_datetime(df['Date'])
    today = datetime.datetime.today().date()
    return today in df['Date'].dt.date.values

# Funktion, um verbleibende Handelstage im Monat zu berechnen
def get_remaining_trading_days():
    df = pd.read_csv("SP500_x2_SMA.csv")
    df['Date'] = pd.to_datetime(df['Date'])
    today = datetime.datetime.today().date()
    remaining_days = df[df['Date'].dt.date >= today].shape[0]
    return remaining_days

# Funktion für den Kauf
def execute_buy(ib):
    available_funds = get_available_funds(ib)
    remaining_days = get_remaining_trading_days()
    reserve = remaining_days * DAILY_BUDGET  # Puffer für restliche Handelstage
    
    if available_funds >= reserve:
        invest_amount = available_funds - reserve
        log_trade("INFO", f"Investiere gesamtes verfügbares Kapital (abzüglich Reserve): {invest_amount} USD")
    else:
        invest_amount = DAILY_BUDGET
        log_trade("INFO", f"Nur täglicher Kauf möglich: {DAILY_BUDGET} USD")
    
    price = get_latest_price(ib, SYMBOL)
    if not price:
        log_trade("ERROR", "Kein gültiger Marktpreis verfügbar. Trade abgebrochen.")
        return False
    
    qty = round(invest_amount / price, 4)
    if qty < 0.01:
        log_trade("WARNING", "Mindestmenge für Fractional Buys nicht erreicht. Trade nicht ausgeführt.")
        return False
    
    contract = Stock(SYMBOL, 'SMART', 'USD', primaryExchange="NYSE")
    order = MarketOrder("BUY", qty)
    trade = ib.placeOrder(contract, order)
    
    ib.sleep(3)
    if trade.orderStatus.status == "Filled":
        log_trade("SUCCESS", f"Trade erfolgreich: Kauf von {qty} Anteilen")
        return True
    else:
        log_trade("ERROR", "Trade fehlgeschlagen.")
        return False

# Hauptablauf
if __name__ == "__main__":
    if not is_trading_day():
        log_trade("INFO", "Heute ist kein Handelstag (laut CSV). Kein Trade durchgeführt.")
        exit(0)
    
    start_ib_gateway()
    ib = wait_for_gateway()
    signal = get_trading_signal()
    trade_success = False
    
    if signal == "BUY":
        trade_success = execute_buy(ib)
    elif signal == "SELL":
        trade_success = execute_sell(ib)
    else:
        log_trade("INFO", "Kein gültiges Signal gefunden. Kein Trade heute.")
    
    ib.disconnect()
    
    if not trade_success:
        log_trade("ERROR", "Kein erfolgreicher Trade heute, obwohl ein Signal vorhanden war!")
        exit(1)
