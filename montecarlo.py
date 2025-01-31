import pandas as pd
from datetime import datetime, timedelta

def monte_carlo_simulation_from_csv(input_csv='sp500_with_signals.csv', daily_savings=25, start_amount=0, years=34, num_simulations=1000, output_csv='montecarlo_data.csv'):
    """
    Führe eine Monte-Carlo-Simulation für Sparszenarien durch basierend auf einer CSV-Datei mit den relevanten Spalten 'Close' und 'Signal'.
    Inklusive Steuerberechnung, TER, Gebühren und Steuerfreibeträgen.
    
    :param input_csv: Name der Eingabedatei mit den Kursdaten
    :param daily_savings: Tägliche Sparrate in Euro
    :param start_amount: Anfangsbetrag
    :param years: Dauer der Sparphase in Jahren (wird auf 34 Jahre festgelegt)
    :param num_simulations: Anzahl der durchzuführenden Simulationen
    :param output_csv: Name der Ausgabedatei für die CSV
    :return: None
    """
    # Lade die CSV-Datei und stelle sicher, dass das Datumsformat korrekt interpretiert wird
    df = pd.read_csv(input_csv, parse_dates=['Date'])
    df.set_index('Date', inplace=True)
    
    # Überprüfe, ob die relevanten Spalten vorhanden sind
    required_columns = ['Close', 'Signal']
    for column in required_columns:
        if column not in df.columns:
            raise ValueError(f"Die Spalte '{column}' fehlt in der CSV-Datei.")
    
    # Bestimmen des aktuellen Datums und des Startdatums der letzten 34 Jahre
    today = datetime.today()
    start_date = today - timedelta(days=(years + 21) * 365)  # Berechnet das Startdatum für die letzten 34 Jahre plus 21 Jahre
    
    # Filtern der Daten für den Zeitraum
    df_filtered = df[df.index >= pd.to_datetime(start_date)]
    
    # Generiere alle Startdaten innerhalb des Zeitrahmens (zwischen Startdatum und heutigem Datum)
    all_start_dates = pd.date_range(start=start_date, end=today, freq='MS').strftime('%Y-%m-%d').tolist()

    # Berechnung der täglichen TER (0,6% pro Jahr)
    daily_TER = 0.006 / 365  # Tägliche TER in Dezimalform

    # Simulation der Sparszenarien
    results = []
    for simulation in range(num_simulations):
        simulation_results = []
        for start in all_start_dates:
            # Bestimme den Startindex für das Startdatum
            start_date = pd.to_datetime(start)
            if start_date not in df_filtered.index:
                continue  # Falls das Startdatum nicht existiert, überspringe diese Simulation
            
            start_idx = df_filtered.index.get_loc(start_date)
            Depotwert = start_amount
            Tagesgeldwert = 0  # Das Geld, das auf dem Tagesgeldkonto geparkt ist
            total_value = Depotwert
            taxable_gain = 0  # Steuerpflichtiger Gewinn
            total_taxes_paid = 0  # Insgesamt gezahlte Steuern
            purchased_once = False  # Flag, das anzeigt, ob bereits einmal vollständig gekauft wurde
            
            # Simulation für die Sparphase (34 Jahre)
            for day in range(years * 365):
                if start_idx + day < len(df_filtered) - 1:  # Stelle sicher, dass wir einen Folgetag haben
                    # Nächster Kurswert (Close-Preis)
                    close_price_today = df_filtered.iloc[start_idx + day]['Close']
                    close_price_next_day = df_filtered.iloc[start_idx + day + 1]['Close']
                    signal = df_filtered.iloc[start_idx + day]['Signal']
                    
                    # 1. **TER** vor dem Kauf/Verkauf und Steuerberechnung abziehen
                    total_value -= total_value * daily_TER  # Täglicher TER-Abzug nur vom Depotwert

                    # Tägliches Sparen
                    Depotwert += daily_savings
                
                    # Berechne die tägliche Kursänderung (Prozentsatz)
                    daily_change = (close_price_next_day - close_price_today) / close_price_today
                    
                    if pd.notna(signal):
                        if 'BUY' in signal:
                            if not purchased_once and total_value >= 250:
                                # Bei "Kaufen" wird der gesamte Betrag investiert und keine Gebühr abgezogen
                                Depotwert = total_value
                                total_value = Depotwert * (1 + daily_change)  # Kursänderung anwenden
                                purchased_once = True  # Markiert, dass der erste Kauf stattgefunden hat
                            elif total_value < 250:
                                # Wenn der Kaufbetrag unter 250€ liegt, wird nur mit der Sparrate gekauft und 1€ Gebühr abgezogen
                                Depotwert += daily_savings - 1  # 1€ Gebühr für Käufe < 250€
                                total_value = Depotwert * (1 + daily_change)
                        elif 'SELL' in signal:
                            # Bei "Verkaufen" wird die gesamte Position verkauft
                            Tagesgeldwert = total_value
                            total_value = 0  # Geld geparkt, keine Kursänderung
                        
                    # **Depotwert** wächst täglich um den Prozentsatz der Kursänderung, wenn im Depot
                    if total_value > 0 and Tagesgeldwert == 0:  # Wenn im Depot, wird täglich die Kursänderung angewendet
                        total_value *= (1 + daily_change)  # Depotwert wächst oder fällt je nach Kursänderung
                    
                    # Jährliche Steuerberechnung und Gebührenabzug
                    if (start_idx + day) % 365 == 0:  # Jedes Jahr
                        yearly_gain = total_value - Depotwert  # Gewinn im Jahr
                        if yearly_gain > 0:
                            # Steuerpflichtiger Gewinn (70% steuerfrei)
                            taxable_gain = yearly_gain * 0.7
                            # Berechne Abgeltungssteuer (25%)
                            tax = taxable_gain * 0.25  # 25% Abgeltungssteuer
                            solidarity_surcharge = tax * 0.055  # 5,5% Solidaritätszuschlag
                            total_taxes_paid += tax + solidarity_surcharge
                            total_value -= (tax + solidarity_surcharge)  # Steuern abziehen

            simulation_results.append(total_value)
        results.append(simulation_results)

    # Erstelle DataFrame und speichere es als CSV
    df_results = pd.DataFrame(results, columns=all_start_dates)
    df_results.index = [f'Simulation {i+1}' for i in range(num_simulations)]
    df_results.to_csv(output_csv)
    print(f"Monte Carlo Simulation abgeschlossen. Ergebnisse in '{output_csv}' gespeichert.")

# Start der Simulation mit der Eingabedatei 'sp500_with_signals.csv'
monte_carlo_simulation_from_csv(input_csv='sp500_with_signals.csv')
