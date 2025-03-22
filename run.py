"""
Hauptskript zum Starten des Trading Dashboards
"""

import os
import sys
from pathlib import Path

# Füge den Projektpfad zum Systempfad hinzu
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Importiere die Dashboard-App
from dashboard.app import app

if __name__ == "__main__":
    print("Starte Trading Dashboard auf http://localhost:8050")
    app.run(debug=True, host="0.0.0.0", port=8050)
1) denke über die nachfolgendne aufgaben nach und versuche sie bestmöglich umzusetzen
2) die Straegie Konfiguration hat immernoch "symbol",
3) da ist immernoch eine fehlermeldung: callback error updating trades-table.container.children
4) sind die "NQ-Asset und Zeiteinheiten: NQ-Futures und alle Zeiteinheiten (1m bis 1mo) sind verfügbar" gar nciht auswählbar???
5) MOmentan habe ich rechts im chart etwas über der Y-achse, ich glaube es sind werkzeuge für den chart, kontrolliere das. Packe es an den Linken Rand wie int
tradingview.
6) packe die zeiten wieder hinzu, die wurden vorher wohl entfernt. ich will 1min, 2min, 3min, 5min,15min,30min,1h,4h,1D,1W,1Month
7) packe diese anschließend direkt über den chart wie in tradingview
8) führe das projekt aus und kontrolliere ob fehler vorhanden sind

