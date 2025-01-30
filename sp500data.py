import pandas as pd 
import numpy as np
import requests
from io import StringIO
import sys

def download_stooq_data(symbol='^spx', interval='d'):
    """
    Lädt historische Kursdaten von Stooq herunter.
    
    :param symbol: Börsensymbol, Standard ist '^spx' für den S&P 500 Index
    :param interval: Zeitintervall, 'd' für täglich
    :return: pandas DataFrame mit den Kursdaten
    """
    url = f'https://stooq.com/q/d/l/?s={symbol}&i={interval}'
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Fehler beim Herunterladen der Daten: {e}")
        sys.exit(1)
    
    # Lesen der CSV-Daten direkt aus dem Response
    data = StringIO(response.text)
    df = pd.read_csv(data, parse_dates=['Date'])
    
    # Sortieren nach Datum aufsteigend
    df.sort_values('Date', inplace=True)
    df.reset_index(drop=True, inplace=True)
    
    return df

def calculate_signals(
    df,
    output_csv="sp500_with_signals.csv",
    sma_window=375
):
    """
    Kombiniert eine SMA-basierte Strategie (375 Tage) 
    mit einer Drawdown-Strategie, die Vorrang hat.
    
    :param df: pandas DataFrame mit den Kursdaten (muss 'Close' enthalten)
    :param output_csv: Name der Ausgabedatei
    :param sma_window: Fenstergröße für den gleitenden Durchschnitt
    :return: DataFrame mit berechneten Signalen
    """
    # 2) SMA 375 berechnen
    df["SMA_375"] = df["Close"].rolling(window=sma_window, min_periods=1).mean()

    # Drawdown-Einstellungen für Handelstage
    # 1,65 Jahre => ca. 1.65 * 252 => 416 Bars
    # 0,85 Jahre => ca. 0.85 * 252 => 214 Bars
    dd_30_bars = 416
    dd_40_bars = 214

    # Variablen für die Schleife
    all_time_high = -np.inf
    drawdown_end_idx = -1

    # Index resetten, damit wir tagweise iterieren können
    df.reset_index(inplace=True)  # => df.index = 0..N, "Date" => extra Spalte
    df["AllTimeHigh"] = np.nan
    df["Drawdown%"] = np.nan
    df["Signal"] = None

    # 3) Tag-für-Tag durchgehen
    for i in range(len(df)):
        close_i = df.loc[i, "Close"]
        # All-Time-High updaten
        if close_i > all_time_high:
            all_time_high = close_i

        # Drawdown in %
        drawdown_i = (close_i - all_time_high) / all_time_high * 100
        df.loc[i, "AllTimeHigh"] = all_time_high
        df.loc[i, "Drawdown%"] = drawdown_i

        # Prüfen, ob wir noch in einer laufenden Drawdown-Phase sind
        if i <= drawdown_end_idx:
            # => Aktive Drawdown-Phase
            # Prüfen, ob wir <= -40% fallen => bricht alte -30%-Phase ab, 
            # starte NEU 0,85-Jahre-Phase
            if drawdown_i <= -40:
                drawdown_end_idx = i + dd_40_bars
            signal = "BUY_2X_DRAWDOWN"

        else:
            # => Keine aktive Phase
            # Check, ob wir jetzt <= -40% oder -30% sind
            if drawdown_i <= -40:
                drawdown_end_idx = i + dd_40_bars
                signal = "BUY_2X_DRAWDOWN"
            elif drawdown_i <= -30:
                drawdown_end_idx = i + dd_30_bars
                signal = "BUY_2X_DRAWDOWN"
            else:
                # => Normal: SMA-Logik
                sma_val = df.loc[i, "SMA_375"]
                if pd.isna(sma_val):
                    # Noch nicht genug Daten für 375 Tage
                    signal = None
                else:
                    # "Close >= SMA_375 => BUY_2X, sonst SELL"
                    if close_i >= sma_val:
                        signal = "BUY_2X"
                    else:
                        signal = "SELL"

        df.loc[i, "Signal"] = signal

    # Datum wieder als Index herstellen
    df.set_index("Date", inplace=True)
    df.index.name = "Date"

    # 4) Ergebnis speichern
    df.to_csv(output_csv)
    print(f"Signal-Datei erstellt/aktualisiert: {output_csv}")

    # Letzten Tag ausgeben
    last_row = df.iloc[-1]
    print("--------------------------------------------------")
    print(f"Letztes Datum: {last_row.name.date()}")
    print(f"Close: {last_row['Close']:.2f}")
    print(f"AllTimeHigh: {last_row['AllTimeHigh']:.2f}")
    print(f"Drawdown%: {last_row['Drawdown%']:.2f}%")
    print(f"SMA_375: {last_row['SMA_375']:.2f}")
    print(f"Signal: {last_row['Signal']}")

    return df  # Rückgabe des DataFrames für weitere Nutzung

def main():
    # Schritt 1: Daten herunterladen
    symbol = '^spx'
    print(f"Lade Daten für {symbol} von Stooq herunter...")
    df = download_stooq_data(symbol=symbol)
    print("Daten erfolgreich heruntergeladen.")
    
    # Schritt 2: Signale berechnen
    print("Berechne Signale basierend auf der SMA- und Drawdown-Strategie...")
    calculate_signals(df)

if __name__ == "__main__":
    main()
