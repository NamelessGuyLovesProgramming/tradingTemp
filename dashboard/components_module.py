import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import json
import os

# Lade die Nasdaq-Symbole aus der JSON-Datei
def load_nasdaq_symbols():
    try:
        with open(os.path.join(os.path.dirname(__file__), 'assets', 'nasdaq_symbols.json'), 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Fehler beim Laden der Nasdaq-Symbole: {e}")
        return {"popular_symbols": [], "indices": []}

# Erstelle klickbare Asset-Buttons
def create_asset_buttons(symbols_data):
    popular_symbols = symbols_data.get("popular_symbols", [])
    indices = symbols_data.get("indices", [])
    
    popular_buttons = [
        html.Button(
            symbol["symbol"],
            id={"type": "asset-button", "symbol": symbol["symbol"]},
            className="asset-button",
            title=symbol["name"]
        ) for symbol in popular_symbols
    ]
    
    indices_buttons = [
        html.Button(
            symbol["symbol"],
            id={"type": "asset-button", "symbol": symbol["symbol"]},
            className="asset-button index-button",
            title=symbol["name"]
        ) for symbol in indices
    ]
    
    return html.Div([
        html.H6("Beliebte Aktien", className="asset-category-title"),
        html.Div(popular_buttons, className="asset-buttons-container"),
        html.H6("Indizes", className="asset-category-title mt-3"),
        html.Div(indices_buttons, className="asset-buttons-container"),
    ], className="asset-selection-container")

# Erstelle verbesserte Zeitrahmen-Buttons
def create_timeframe_buttons():
    timeframes = [
        {"label": "1min", "value": "1m", "id": "tf-1min"},
        {"label": "2min", "value": "2m", "id": "tf-2min"},
        {"label": "3min", "value": "3m", "id": "tf-3min"},
        {"label": "5min", "value": "5m", "id": "tf-5m"},
        {"label": "15min", "value": "15m", "id": "tf-15m"},
        {"label": "30min", "value": "30m", "id": "tf-30m"},
        {"label": "1h", "value": "60m", "id": "tf-1h"},
        {"label": "4h", "value": "4h", "id": "tf-4h"},
    ]
    
    buttons = [
        html.Button(
            tf["label"],
            id=tf["id"],
            className="timeframe-button",
            **{"data-value": tf["value"]}
        ) for tf in timeframes
    ]
    
    return html.Div(buttons, className="timeframe-buttons")

# CSS für die neuen Komponenten
asset_selection_css = """
.asset-selection-container {
    margin-bottom: 20px;
}

.asset-category-title {
    font-size: 0.9rem;
    font-weight: 600;
    margin-bottom: 8px;
    color: #6c757d;
}

.asset-buttons-container {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.asset-button {
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    padding: 6px 12px;
    font-size: 0.85rem;
    cursor: pointer;
    transition: all 0.2s ease;
}

.asset-button:hover {
    background-color: #e9ecef;
}

.asset-button.active {
    background-color: #0d6efd;
    color: white;
    border-color: #0d6efd;
}

.index-button {
    background-color: #f0f7ff;
    border-color: #cfe2ff;
}

.index-button:hover {
    background-color: #e0efff;
}

.index-button.active {
    background-color: #0d6efd;
    color: white;
    border-color: #0d6efd;
}

.timeframe-button {
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 0.85rem;
    cursor: pointer;
    transition: all 0.2s ease;
    margin-right: 4px;
    margin-bottom: 8px;
}

.timeframe-button:hover {
    background-color: #e9ecef;
}

.timeframe-button.active {
    background-color: #0d6efd;
    color: white;
    border-color: #0d6efd;
}
"""
