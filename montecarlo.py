import pandas as pd

def monte_carlo_simulation_from_csv(input_csv='sp500_with_signals.csv', daily_savings=25, start_amount=0, years=34, num_simulations=1000, output_csv='montecarlo_sp500_data.csv'):
    """
    Führe eine Monte-Carlo-Simulation für Sparszenarien durch basierend auf einer CSV-Datei mit den relevanten Spalten 'Close' und 'Signal'.
    
    :param input_csv: Name der Eingabedatei mit den Kursdaten
    :param daily_savings: Tägliche Sparrate in Euro
    :param start_amount: Anfangsbetrag
    :param years: Dauer der Sparphase in Jahren
    :param num_simulations: Anzahl der durchzuführenden Simulationen
    :param output_csv: Name der Ausgabedatei für die CSV
    :return: None
    """
    # Lade die CSV-Datei
    df = pd.read_csv(input_csv, parse_dates=['Date'])
    df.set_index('Date', inplace=True)
    
    # Überprüfe, ob die relevanten Spalten vorhanden sind
    required_columns = ['Close', 'Signal']
    for column in required_columns:
        if column not in df.columns:
            raise ValueError(f"Die Spalte '{column}' fehlt in der CSV-Datei.")
    
    # Generiere alle Startmonate zwischen 1970 und 1990
    start_year = 1970
    end_year = 1990
    all_start_dates = pd.date_range(start=f'{start_year}-01-01', end=f'{end_year}-12-31', freq='MS').strftime('%Y-%m-%d').tolist()

    # Simulation der Sparszenarien
    results = []
    for simulation in range(num_simulations):
        simulation_results = []
        for start in all_start_dates:
            # Bestimme den Startindex für das Startdatum
            start_date = pd.to_datetime(start)
            if start_date not in df.index:
                continue  # Falls das Startdatum nicht existiert, überspringe diese Simulation
            
            start_idx = df.index.get_loc(start_date)
            total_savings = start_amount
            days_in_savings_period = years * 365
            cash_held = 0  # Variable für das geparkte Geld bei "SELL"-Signal
            
            # Simulation für die Sparphase
            for day in range(days_in_savings_period):
                if start_idx + day < len(df) - 1:  # Stelle sicher, dass wir einen Folgetag haben
                    # Nächster Kurswert (Close-Preis)
                    close_price_today = df.iloc[start_idx + day]['Close']
                    close_price_next_day = df.iloc[start_idx + day + 1]['Close']
                    signal = df.iloc[start_idx + day]['Signal']
                    
                    # Tägliches Sparen
                    total_savings += daily_savings
                
                    # Berechne die tägliche Kursänderung (Prozentsatz)
                    daily_change = (close_price_next_day - close_price_today) / close_price_today
                    
                    if pd.notna(signal):
                        if 'BUY' in signal:
                            # Bei "Kaufen" wird der Wert basierend auf der Tagesänderung angepasst
                            total_savings *= (1 + daily_change)
                        elif 'SELL' in signal:
                            # Bei "Verkaufen" wird das Geld geparkt (keine Kursänderung)
                            cash_held = total_savings
                            total_savings = 0  # Das Geld wird auf dem Tagesgeldkonto geparkt
                        
                        # Wieder „Kaufen“-Signal - Wir setzen das geparkte Geld zu gleichen Anteilen wieder ein
                        if 'BUY' in signal and cash_held > 0:
                            total_savings = cash_held
                            cash_held = 0  # Das Geld wird wieder investiert und ist nicht mehr geparkt
                            total_savings *= (1 + daily_change)  # Wieder von der Kursänderung betroffen

            simulation_results.append(total_savings)
        results.append(simulation_results)

    # Erstelle DataFrame und speichere es als CSV
    df_results = pd.DataFrame(results, columns=all_start_dates)
    df_results.index = [f'Simulation {i+1}' for i in range(num_simulations)]
    df_results.to_csv(output_csv)
    print(f"Monte Carlo Simulation abgeschlossen. Ergebnisse in '{output_csv}' gespeichert.")

# Start der Simulation mit der Eingabedatei 'sp500_with_signals.csv'
monte_carlo_simulation_from_csv(input_csv='sp500_with_signals.csv')
