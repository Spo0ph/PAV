import pandas as pd
import numpy as np
import requests
from io import StringIO

# Lädt historische Marktdaten von Stooq herunter und gibt sie als DataFrame zurück.
def download_stooq_data(symbol='^spx', interval='d'):
    url = f'https://stooq.com/q/d/l/?s={symbol}&i={interval}'
    response = requests.get(url)
    response.raise_for_status()  # Stoppt das Skript bei fehlerhafter Anfrage
    
    df = pd.read_csv(StringIO(response.text), parse_dates=['Date'])
    df.sort_values('Date', inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

# Erstellt eine Buy & Hold Strategie.
def calculate_buy_hold(df, output_csv):
    df['Signal'] = 'BUY'
    df.set_index('Date', inplace=True)
    df.to_csv(output_csv)
    print(f"Buy & Hold Datei erstellt: {output_csv}")
    return df

# Berechnet SMA-Signale unter Berücksichtigung von Drawdowns.
def calculate_sma_drawdown_signals(df, output_csv, sma_window=375, drawdown_duration=252):
    df['SMA'] = df['Close'].rolling(window=sma_window, min_periods=1).mean()
    all_time_high = -np.inf
    drawdown_end_idx = -1
    df['Signal'] = None
    df['Drawdown%'] = np.nan
    
    for i, close in enumerate(df['Close']):
        all_time_high = max(all_time_high, close)
        drawdown = (close - all_time_high) / all_time_high * 100
        df.loc[i, 'Drawdown%'] = drawdown
        
        if i <= drawdown_end_idx:
            df.loc[i, 'Signal'] = 'BUY'  # Während Drawdown-Phase Buy-Signal
        elif drawdown <= -40:
            drawdown_end_idx = i + drawdown_duration  # 1 Handelsjahr (~252 Tage)
            df.loc[i, 'Signal'] = 'BUY'
        else:
            df.loc[i, 'Signal'] = 'BUY' if close >= df.loc[i, 'SMA'] else 'SELL'
    
    df.set_index('Date', inplace=True)
    df.to_csv(output_csv)
    print(f"SMA & Drawdown Signal-Datei erstellt: {output_csv}")
    return df

# Berechnet nur SMA-Signale ohne Drawdown-Betrachtung.
def calculate_sma_only(df, output_csv, sma_window=375):
    df['SMA'] = df['Close'].rolling(window=sma_window, min_periods=1).mean()
    df['Signal'] = df.apply(lambda row: 'BUY' if row['Close'] >= row['SMA'] else 'SELL', axis=1)
    
    df.set_index('Date', inplace=True)
    df.to_csv(output_csv)
    print(f"SMA Signal-Datei erstellt: {output_csv}")
    return df

# Erhöht den Marktwert um einen bestimmten Faktor für eine gehebelte Strategie.
def apply_leverage(df, factor=2):
    df['Close'] = df['Close'] * factor
    return df

# Hauptfunktion zum Herunterladen der Daten und Berechnung der Strategien.
def main():
    df = download_stooq_data(symbol='^spx')
    
    # Ungehebelte Strategien (x1)
    calculate_buy_hold(df.copy(), "SP500_x1_BH.csv")
    calculate_sma_drawdown_signals(df.copy(), "SP500_x1_SMA_Drawdown.csv")
    calculate_sma_only(df.copy(), "SP500_x1_SMA.csv")
    
    # Gehebelte Strategien (x2)
    df_x2 = apply_leverage(df.copy(), factor=2)
    calculate_buy_hold(df_x2.copy(), "SP500_x2_BH.csv")
    calculate_sma_drawdown_signals(df_x2.copy(), "SP500_x2_SMA_Drawdown.csv")
    calculate_sma_only(df_x2.copy(), "SP500_x2_SMA.csv")

if __name__ == "__main__":
    main()
