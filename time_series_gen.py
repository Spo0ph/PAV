#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulation einer privaten Altersvorsorge über 34 Jahre (Start 1970) mit zwei Konten:
- ETF-Depot
- Tagesgeldkonto

Datenquelle: sp500_with_signals.csv (Spalten: Date,index,Open,High,Low,Close,Volume,
SMA_375,AllTimeHigh,Drawdown%,Signal)

Tägliche Einzahlung: 25 € (1 Tag = 1 Handelstag)

Tagesablauf:
  1. Marktupdate:
     - Liegt das Vermögen im ETF-Depot, wird es anhand der täglichen Kursänderung (Close)
       angepasst und der anteilige TER (0,6 % p.a. über 200 Handelstage) abgezogen.
     - Liegt das Geld auf dem Tagesgeldkonto, ändert sich dessen Wert nicht.
     
  2. Jahressteuer:
     - Am letzten Handelstag eines Kalenderjahres werden realisierte Gewinne (aus Verkäufen)
       versteuert. Es gilt ein Freibetrag von 30 %; auf den steuerpflichtigen Anteil (70 % des Gewinns)
       wird mit 30,5 % Steuern erhoben. Der Steuerabzug erfolgt vom Tagesgeldkonto.
     
  3. Tägliche Einzahlung (Sparplan):
     - Täglich werden 25 € eingezahlt. Liegt der Sparplan im ETF, so wird der Betrag abzüglich
       einer Transaktionsgebühr von 1 € (falls der einzuzahlende Betrag unter 250 € liegt) in das ETF-Depot
       investiert und erhöht gleichzeitig die Kostenbasis.
     - Liegt das Geld auf dem Tagesgeldkonto, wird der Betrag ohne Gebühren gutgeschrieben.
     
  4. Signalentscheidung:
     - BUY_2X: Liegt das gesamte Vermögen (inklusive des heutigen Beitrags) auf dem Tagesgeldkonto,
       wird dieses vollständig in das ETF-Depot transferiert. Ist der zu transferierende Betrag unter 250 €,
       wird vor Transfer 1 € Gebühr abgezogen. Anschließend wird der Sparplan (25 €/Tag) künftig im ETF
       ausgeführt.
     - SELL:  Liegt das Vermögen im ETF, wird das Depot vollständig liquidiert – der Verkaufserlös wird
       auf das Tagesgeldkonto überwiesen, der realisierte Gewinn erfasst und später versteuert. Danach
       wird der Sparplan auf das Tagesgeldkonto umgestellt.
       
Ergebnis: Zeitreihe der Vermögensentwicklung in Tagesschritten, ausgegeben als "time_series_data.csv".
"""

import pandas as pd

# ---------------------------
# Parameter der Simulation
# ---------------------------
START_DATE = pd.Timestamp("1970-01-01")
YEARS = 34
DAILY_DEPOSIT = 25.0

TER_ANNUAL = 0.006                # 0,6 % p.a.
TRADING_DAYS_PER_YEAR = 200       # angenommene Handelstage pro Jahr
TER_DAILY = TER_ANNUAL / TRADING_DAYS_PER_YEAR

MIN_INVESTMENT = 250.0            # Mindesteinsatz: bei Beträgen < 250 € fällt eine Gebühr an
PURCHASE_FEE = 1.0                # 1 € Gebühr pro Transaktion, wenn Betrag < 250 €

# Steuerparameter (auf realisierte Gewinne bei Verkäufen)
TAX_FREE_ALLOWANCE = 0.30         # 30 % Freibetrag
TAX_RATE = 0.305                # 30,5 % Steuersatz auf den steuerpflichtigen Anteil (70 % des Gewinns)

# ---------------------------
# CSV einlesen und Simulationszeitraum festlegen
# ---------------------------
df = pd.read_csv("sp500_with_signals.csv", parse_dates=["Date"])
df.sort_values("Date", inplace=True)

# Zeitraum: Start 1970, Dauer 34 Jahre
end_date = START_DATE + pd.DateOffset(years=YEARS)
df_sim = df[(df["Date"] >= START_DATE) & (df["Date"] < end_date)].reset_index(drop=True)

# ---------------------------
# Initialisierung der Konten und weiterer Variablen
# ---------------------------
etf_value = 0.0       # Aktueller Wert im ETF-Depot
etf_cost_basis = 0.0  # Kumulierte Investitionskosten im ETF (zur Gewinnberechnung)
tagesgeld = 0.0       # Kontostand des Tagesgeldkontos

# Start: Sparplan läuft auf dem Tagesgeldkonto
current_mode = "Tagesgeld"  # Mögliche Werte: "Tagesgeld" oder "ETF"

# Puffer für realisierte, aber noch nicht versteuerte Gewinne (aus Verkäufen)
realized_gain_buffer = 0.0

prev_close = None  # Für die Berechnung der täglichen Kursänderung

# Liste zur Protokollierung der Tagesergebnisse
results = []

# ---------------------------
# Simulation – Tag für Tag
# ---------------------------
for i, row in df_sim.iterrows():
    date = row["Date"]
    close = row["Close"]
    # Signal aus der CSV; falls kein Signal angegeben, wird ein leerer String verwendet
    signal = str(row["Signal"]).strip().upper() if pd.notnull(row["Signal"]) else ""
    
    # 1. Marktupdate & TER (nur bei ETF-Investition):
    if current_mode == "ETF" and prev_close is not None:
        daily_return = (close / prev_close) - 1
        etf_value *= (1 + daily_return)
        etf_value *= (1 - TER_DAILY)
    # Liegt das Geld auf dem Tagesgeldkonto, bleibt dessen Wert unverändert.

    # 2. Jahressteuer: (am letzten Handelstag eines Kalenderjahres)
    is_year_end = False
    if i == len(df_sim) - 1:
        is_year_end = True
    else:
        next_date = df_sim.loc[i + 1, "Date"]
        if next_date.year != date.year:
            is_year_end = True

    if is_year_end:
        if realized_gain_buffer > 0:
            taxable_gain = realized_gain_buffer * (1 - TAX_FREE_ALLOWANCE)  # 70 % des Gewinns
            tax = taxable_gain * TAX_RATE
            tagesgeld -= tax  # Steuerabzug erfolgt vom Tagesgeldkonto
        realized_gain_buffer = 0.0  # Puffer zurücksetzen

    # 3. Tägliche Einzahlung (Sparplan):
    if current_mode == "ETF":
        # Für den Sparplan im ETF wird, falls der einzuzahlende Betrag unter 250 € liegt, eine Gebühr von 1 € abgezogen.
        deposit_net = DAILY_DEPOSIT - PURCHASE_FEE if DAILY_DEPOSIT < MIN_INVESTMENT else DAILY_DEPOSIT
        etf_value += deposit_net
        etf_cost_basis += deposit_net
    else:  # current_mode == "Tagesgeld"
        tagesgeld += DAILY_DEPOSIT

    # 4. Signalentscheidung:
    if signal == "BUY_2X":
        # Liegt das gesamte Vermögen (inklusive der heutigen Einzahlung) auf dem Tagesgeldkonto,
        # wird es vollständig in das ETF-Depot investiert.
        if current_mode == "Tagesgeld" and tagesgeld > 0:
            transfer_amount = tagesgeld
            if transfer_amount < MIN_INVESTMENT:
                transfer_amount -= PURCHASE_FEE
            etf_value += transfer_amount
            etf_cost_basis += transfer_amount
            tagesgeld = 0.0
            current_mode = "ETF"  # Sparplan wechselt auf ETF
    elif signal == "SELL":
        # Liegt das Vermögen im ETF, wird das Depot vollständig liquidiert.
        if current_mode == "ETF" and etf_value > 0:
            sale_proceeds = etf_value
            # Realisierter Gewinn: Verkaufserlös minus bisherige Investitionskosten
            realized_gain = sale_proceeds - etf_cost_basis
            realized_gain_buffer += realized_gain
            tagesgeld += sale_proceeds  # Erlös wird auf das Tagesgeldkonto überwiesen
            # Depot zurücksetzen:
            etf_value = 0.0
            etf_cost_basis = 0.0
            current_mode = "Tagesgeld"  # Sparplan wechselt auf Tagesgeld

    # 5. Tagesprotokollierung:
    total_value = etf_value + tagesgeld
    results.append({
        "Date": date,
        "ETF_value": etf_value,
        "Tagesgeld": tagesgeld,
        "Total_value": total_value,
        "Signal": signal,
        "Mode": current_mode
    })
    
    # Update: speichere den aktuellen Close für die Berechnung der nächsten Tagesrendite
    prev_close = close

# ---------------------------
# Ergebnisse als CSV speichern
# ---------------------------
result_df = pd.DataFrame(results)
result_df.to_csv("time_series_data.csv", index=False)

print("Simulation abgeschlossen. Ergebnisse wurden in 'time_series_data.csv' gespeichert.")

