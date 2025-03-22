# Trading Dashboard

Ein interaktives Dashboard für Trading-Strategien, Backtesting und Analyse von Finanzdaten.

## Funktionen

- **Interaktive Charts**: TradingView-ähnliche Charts mit Drag-Navigation, Zoom und Zeichenwerkzeugen
- **Asset-Auswahl**: Dropdown mit verschiedenen Assets (Aktien, Krypto, Forex, Futures)
- **Zeitrahmen-Auswahl**: Buttons für verschiedene Zeitrahmen (1m, 2m, 5m, 15m, 30m, 1h, 1d, 1w, 1mo)
- **Trading-Strategien**: Implementierung und Backtesting verschiedener Strategien (MA Crossover, RSI)
- **Backtesting**: Analyse der Performance von Strategien mit detaillierten Metriken
- **Fehlerbehandlung**: Robuste Fehlerbehandlung mit Fallback-Mechanismen

## Installation

1. Klonen Sie das Repository:
```bash
git clone https://github.com/yourusername/trading.git
cd trading
```

2. Installieren Sie die erforderlichen Abhängigkeiten:
```bash
pip install -r requirements.txt
```

3. Starten Sie die Anwendung:
```bash
python run.py
```

4. Öffnen Sie die Anwendung in Ihrem Browser:
```
http://localhost:8050
```

## Projektstruktur

```
trading/
├── core/                  # Kernlogik (Strategien, Backtesting-Engine)
├── dashboard/             # UI-Komponenten (Chart, Navigation, Forms)
│   ├── assets/            # CSS, JavaScript und andere statische Dateien
│   ├── app.py             # Hauptanwendung
│   ├── components.py      # UI-Komponenten
│   ├── chart_utils.py     # Chart-Hilfsfunktionen
│   ├── chart_callbacks.py # Chart-Callbacks
│   └── error_handler.py   # Fehlerbehandlung
├── data/                  # Daten-Handling (APIs, CSV-Loader, Datenbank)
│   ├── cache/             # Cache-Verzeichnis für Daten
│   ├── data_source.py     # Datenquellen-Abstraktion
│   └── nq_integration.py  # NQ-Futures-Integration
├── utils/                 # Hilfsfunktionen
│   └── helpers.py         # Allgemeine Hilfsfunktionen
├── tests/                 # Tests
│   └── test_trading_dashboard.py # Testskript
├── docs/                  # Dokumentation
│   ├── changes.md         # Änderungsdokumentation
│   └── error_analysis.md  # Fehleranalyse
├── run.py                 # Startskript
└── requirements.txt       # Abhängigkeiten
```

## Verwendung

### Navigation

Die Anwendung verfügt über drei Hauptbereiche, die über die Tabs in der oberen Navigationsleiste zugänglich sind:

1. **Strategien**: Konfiguration und Ausführung von Trading-Strategien
2. **Backtesting**: Analyse der Performance von Strategien
3. **Einstellung**: Konfiguration der Anwendung

### Chart-Interaktion

Der Chart bietet folgende Interaktionsmöglichkeiten:

- **Verschieben**: Klicken und Ziehen im Chart-Bereich
- **Zoomen**: Mausrad für Zoom auf beide Achsen
- **Asset-Auswahl**: Dropdown-Menü über dem Chart
- **Zeitrahmen-Auswahl**: Buttons für verschiedene Zeitrahmen
- **Zeichenwerkzeuge**: Buttons für Trendlinien, horizontale Levels, Fibonacci-Retracements und Rechtecke

### Strategien

Folgende Strategien sind implementiert:

1. **Moving Average Crossover**: Kauft, wenn der schnelle MA den langsamen MA von unten kreuzt, und verkauft, wenn er ihn von oben kreuzt.
2. **RSI**: Kauft, wenn der RSI unter den überverkauften Bereich fällt, und verkauft, wenn er über den überkauften Bereich steigt.

## Entwicklung

### Neue Strategien hinzufügen

Um eine neue Strategie hinzuzufügen:

1. Erstellen Sie eine neue Klasse in `core/strategy.py`, die von `Strategy` erbt
2. Implementieren Sie die Methoden `generate_signals` und `backtest`
3. Fügen Sie die Strategie zur `StrategyFactory` hinzu

### Neue Datenquellen hinzufügen

Um eine neue Datenquelle hinzuzufügen:

1. Erstellen Sie eine neue Klasse in `data/data_source.py`, die von `DataSource` erbt
2. Implementieren Sie die Methoden `get_data`, `get_available_symbols` und `get_available_timeframes`
3. Fügen Sie die Datenquelle zur `DataSourceFactory` hinzu

## Tests

Um die Tests auszuführen:

```bash
python -m tests.test_trading_dashboard
```

## Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert - siehe die [LICENSE](LICENSE) Datei für Details.
