import pandas as pd

# 1. CSV einlesen und Zeitraum festlegen (z. B. 1970 bis 2003 inkl.)
df = pd.read_csv("sp500_with_signals.csv", parse_dates=["Date"])
start_date = pd.Timestamp("1970-01-01")
end_date = pd.Timestamp("2003-12-31")  # 34 Jahre ab 1970
df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)].copy()
df.sort_values("Date", inplace=True)
df.reset_index(drop=True, inplace=True)

# 2. Tägliche Rendite berechnen (hier wird der Schlusskurs "Close" verwendet)
df["daily_return"] = df["Close"].pct_change().fillna(0)

# 3. Parameter
TER_daily = 0.006 / 200   # Täglicher TER-Abzug (0,6% p.a. über 200 Handelstage)
deposit_amount = 25.0

# 4. Kontostände und weitere Variablen initialisieren
ETF_depot = 0.0           # aktueller Wert im ETF-Depot
cash = 0.0                # aktueller Stand im Tagesgeldkonto
cost_basis = 0.0          # Summe der eingezahlten Beträge (abzüglich Gebühren) im Depot
pending_realized_profit = 0.0  # Gewinne, die bereits realisiert, aber noch nicht versteuert wurden

# 5. Ergebnisliste (für die tägliche Zeitreihe)
results = []

n = len(df)
for i, row in df.iterrows():
    current_date = row["Date"]
    current_year = current_date.year

    # (A) Marktentwicklung & TER-Abzug (nur wenn im ETF investiert)
    if ETF_depot > 0:
        # Tägliche Kursentwicklung anwenden (über den Schlusskurs "Close")
        ETF_depot *= (1 + row["daily_return"])
        # TER-Gebühr abziehen
        ETF_depot *= (1 - TER_daily)

    # (B) Jahressteuer: Am letzten Tag eines Kalenderjahres werden realisierte Gewinne versteuert
    is_last_day_of_year = False
    if i == n - 1:
        is_last_day_of_year = True
    else:
        next_year = df.loc[i+1, "Date"].year
        if next_year != current_year:
            is_last_day_of_year = True

    if is_last_day_of_year:
        # Es wird angenommen, dass nur 70% der realisierten Gewinne steuerpflichtig sind.
        if pending_realized_profit > 0:
            tax = pending_realized_profit * 0.7 * 0.305
            # Steuer wird vom Tagesgeldkonto abgezogen
            cash -= tax
            pending_realized_profit = 0.0

    # (C) Transaktionsentscheidung anhand des Signals
    signal = str(row["Signal"]).strip()  # Signal als String (kann auch leer sein)
    
    if signal == "BUY_2x":
        # Nur wenn aktuell kein ETF-Investment vorhanden ist
        if ETF_depot == 0 and cash > 0:
            # Gesamtes Geld (abzüglich 1€ Gebühr) wird investiert
            transfer_amount = cash - 1.0 if cash > 1.0 else 0.0
            ETF_depot = transfer_amount
            cost_basis = transfer_amount
            cash = 0.0
    elif signal == "SELL":
        # Nur wenn aktuell im ETF investiert
        if ETF_depot > 0:
            sale_proceeds = ETF_depot
            profit = sale_proceeds - cost_basis
            # Nur positive Gewinne führen zu Steuerpflicht
            if profit > 0:
                pending_realized_profit += profit
            # Verkauf: Geld wird dem Tagesgeldkonto gutgeschrieben
            cash += sale_proceeds
            ETF_depot = 0.0
            cost_basis = 0.0
    # Bei einem leeren Signal (HOLD) wird nichts geändert.

    # (D) Tägliche Einzahlung von 25€
    if ETF_depot > 0:
        ETF_depot += deposit_amount
        cost_basis += deposit_amount  # neuer Sparbeitrag wird in die Kostenbasis aufgenommen
    else:
        cash += deposit_amount

    # (E) Gesamtportfolio ermitteln und Tagesschritt speichern
    portfolio_value = ETF_depot + cash
    results.append({
        "Date": current_date,
        "PortfolioValue": portfolio_value,
        "ETF_depot": ETF_depot,
        "Cash": cash
    })

# 6. Ergebnis als CSV abspeichern
results_df = pd.DataFrame(results)
results_df.to_csv("time_series_data.csv", index=False)

print("Simulation abgeschlossen. Ergebnisse in 'time_series_data.csv' gespeichert.")
