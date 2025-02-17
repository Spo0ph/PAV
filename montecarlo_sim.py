import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# CSV-Datei einlesen
df = pd.read_csv("time_series_data.csv")

# Berechnung des arithmetischen Mittelwerts für jede Periode
mean_growth = df.mean(axis=1)

# Berechnung der Standardabweichung für jede Periode
std_dev = df.std(axis=1)

# Berechnung der mittleren Standardabweichung über alle Perioden hinweg
mean_std_dev = std_dev.mean()

# Plot der individuellen Zeitreihen
plt.figure(figsize=(10, 6))
for col in df.columns:
    plt.plot(df.index, df[col], alpha=0.2, color="gray")  # Transparente Linien für Einzelverläufe

# Plot des mittleren Wachstums
plt.plot(df.index, mean_growth, label="Arithmetischer Mittelwert", color="blue", linewidth=2)

# Konfidenzintervall hinzufügen (Mittelwert ± eine Standardabweichung)
plt.fill_between(df.index, mean_growth - std_dev, mean_growth + std_dev, color="blue", alpha=0.2, label="1σ-Bereich")

# Labels & Titel
plt.xlabel("Zeit")
plt.ylabel("Vermögen")
plt.title("Durchschnittliche Wachstumsentwicklung mit Unsicherheitsbereich")
plt.legend()
plt.grid(True)

# Speichern des Plots
plt.savefig("growth_plot.png", dpi=300)
plt.show()

# Ergebnisse speichern
summary_df = pd.DataFrame({
    "Zeit": df.index,
    "Mittelwert": mean_growth,
    "Standardabweichung": std_dev
})
summary_df.to_csv("montecarlo_sim.csv", index=False)

# Ausgabe der mittleren Standardabweichung
print(f"Mittlere Standardabweichung über alle Perioden: {mean_std_dev:.4f}")
