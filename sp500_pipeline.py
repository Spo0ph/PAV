import pandas as pd

# 1. Daten einlesen
url = 'https://stooq.com/q/d/l/?s=^spx&i=d'
df = pd.read_csv(
    url,
    parse_dates=['Date'],
    index_col='Date'
)

# 2. Buy & Hold-Signal (jeder Tag 'BUY')
df['B&H'] = 'BUY'

# 3. SMA375 berechnen
window = 375  # Fenstergröße in Handelstagen
df['SMA375'] = df['Close'].rolling(window=window, min_periods=1).mean()

# 4. SMA-Signal: BUY wenn Close > SMA375, sonst SELL
df['SMA_Signal'] = df.apply(
    lambda row: 'BUY' if row['Close'] > row['SMA375'] else 'SELL',
    axis=1
)

# 5. Drawdown-Berechnung
#   ATH = All Time High bis zum aktuellen Datum
df['ATH'] = df['Close'].cummax()
#   Verhältnis zum ATH
df['DD_Ratio'] = df['Close'] / df['ATH']

# 6. SMA+DD-Signal und Countdown
signals = []
countdowns = []
countdown = 0

for dd_ratio, sma_signal in zip(df['DD_Ratio'], df['SMA_Signal']):
    if countdown > 0:
        signals.append('BUY')
        countdown -= 1
        countdowns.append(countdown)
    elif dd_ratio < 0.7:
        countdown = 425
        signals.append('BUY')
        countdown -= 1
        countdowns.append(countdown)
    else:
        signals.append(sma_signal)
        countdowns.append(0)

df['SMA_DD_Signal'] = signals
df['DD_Countdown'] = countdowns

# 7. Hebel simulieren: Close x3
#    neuer Wert, um dreifachen Hebel zu imitieren und auf 2 Nachkommastellen runden
df['Close_x3'] = (df['Close'] * 3).round(2)

# 8. Hilfsgrößen auf 2 Nachkommastellen runden
df['Volume'] = df['Volume'].round(2)
df['SMA375'] = df['SMA375'].round(2)
df['ATH'] = df['ATH'].round(2)
df['DD_Ratio'] = df['DD_Ratio'].round(2)

# 9. CSV exportieren
output_file = 'sp500_signals.csv'
df.to_csv(output_file)

print(f"Fertig! CSV mit gerundeten Signalen und Hebel-Spalte unter '{output_file}' abgelegt.")