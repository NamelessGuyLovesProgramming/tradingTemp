"""
Refaktorisierte App-Datei mit verbesserten Funktionen und Fehlerbehandlung
"""

import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import os
import sys
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Importiere Komponenten und Utilities
from dashboard.components import (
    create_header,
    create_strategy_sidebar,
    create_chart_card,
    create_results_card,
    create_trades_card,
    create_backtesting_content,
    create_settings_content,
)

# Importiere Chart-Utilities und Callbacks
from dashboard.chart_utils import (
    generate_mock_data,
    create_interactive_chart,
    get_available_assets,
    get_available_timeframes,
)

# Importiere Fehlerbehandlung
from dashboard.error_handler import ErrorHandler

# Logger konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("dashboard.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("trading_dashboard")

# Initialisiere die Dash-App
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
    ],
)

app.title = "Trading Dashboard Pro"

# App-Layout
app.layout = html.Div(
    [
        # URL-Routing
        dcc.Location(id="url", refresh=False),
        
        # Header mit Tab-Navigation
        create_header(),
        
        # Hauptinhalt
        dbc.Container(
            [
                # Fehlerbenachrichtigungen
                html.Div(id="error-notification", className="mb-3"),
                
                # Seiteninhalt basierend auf URL
                html.Div(id="page-content"),
            ],
            fluid=True,
            className="py-3",
        ),
        
        # Speicher für den aktiven Tab
        dcc.Store(id="active-tab-store", data="strategien"),
        
        # Speicher für das aktive Zeichenwerkzeug
        dcc.Store(id="active-drawing-tool-store", data=None),
        
        # Speicher für Zeichnungsdaten
        dcc.Store(id="drawing-data-store", data=[]),
        
        # Speicher für den aktiven Zeitrahmen
        dcc.Store(id="active-timeframe-store", data="1d"),
    ],
    className="bg-dark text-light min-vh-100",
)

# Callback für URL-Routing
@callback(
    Output("page-content", "children"),
    Output("tab-strategien", "active"),
    Output("tab-backtesting", "active"),
    Output("tab-einstellung", "active"),
    Output("active-tab-store", "data"),
    Input("url", "pathname"),
    State("active-tab-store", "data"),
)
def render_page_content(pathname, active_tab):
    """
    Rendert den Seiteninhalt basierend auf der URL
    """
    try:
        # Standardmäßig aktiver Tab
        strategien_active = True
        backtesting_active = False
        einstellung_active = False
        new_active_tab = "strategien"
        
        # Bestimme den aktiven Tab basierend auf der URL
        if pathname == "/backtesting":
            strategien_active = False
            backtesting_active = True
            einstellung_active = False
            new_active_tab = "backtesting"
        elif pathname == "/einstellung":
            strategien_active = False
            backtesting_active = False
            einstellung_active = True
            new_active_tab = "einstellung"
        
        # Rendere den entsprechenden Inhalt
        if new_active_tab == "backtesting":
            return create_backtesting_content(), strategien_active, backtesting_active, einstellung_active, new_active_tab
        elif new_active_tab == "einstellung":
            return create_settings_content(), strategien_active, backtesting_active, einstellung_active, new_active_tab
        else:
            # Strategien-Tab (Standard)
            return html.Div(
                [
                    dbc.Row(
                        [
                            # Sidebar
                            dbc.Col(
                                create_strategy_sidebar(),
                                md=3,
                                sm=12,
                            ),
                            # Hauptbereich
                            dbc.Col(
                                [
                                    create_chart_card(),
                                    create_results_card(),
                                    create_trades_card(),
                                ],
                                md=9,
                                sm=12,
                            ),
                        ],
                        className="g-4",
                    ),
                ]
            ), strategien_active, backtesting_active, einstellung_active, new_active_tab
    
    except Exception as e:
        logger.error(f"Fehler beim Rendern des Seiteninhalts: {str(e)}")
        
        # Zeige Fehlermeldung
        error_content = html.Div(
            [
                html.H3("Fehler beim Laden der Seite", className="text-danger"),
                html.P(f"Ein unerwarteter Fehler ist aufgetreten: {str(e)}"),
                html.P("Bitte aktualisieren Sie die Seite oder versuchen Sie es später erneut."),
                dbc.Button(
                    "Seite neu laden",
                    color="primary",
                    href="/",
                    className="mt-3",
                ),
            ],
            className="text-center p-5",
        )
        
        return error_content, strategien_active, backtesting_active, einstellung_active, active_tab

# Callback für Strategie-Parameter
@callback(
    Output("strategy-params", "children"),
    Input("strategy-select", "value"),
)
def update_strategy_params(strategy):
    """
    Aktualisiert die Strategie-Parameter basierend auf der ausgewählten Strategie
    """
    try:
        if strategy == "ma_crossover":
            return html.Div(
                [
                    html.Label("Schneller MA", className="form-label"),
                    dbc.Input(
                        id="fast-ma-input",
                        type="number",
                        value=20,
                        min=1,
                        max=200,
                        step=1,
                        className="mb-2",
                    ),
                    html.Label("Langsamer MA", className="form-label"),
                    dbc.Input(
                        id="slow-ma-input",
                        type="number",
                        value=50,
                        min=1,
                        max=200,
                        step=1,
                        className="mb-2",
                    ),
                    html.Label("Stop Loss (%)", className="form-label"),
                    dbc.Input(
                        id="sl-input",
                        type="number",
                        value=2,
                        min=0.1,
                        max=10,
                        step=0.1,
                        className="mb-2",
                    ),
                    html.Label("Take Profit (%)", className="form-label"),
                    dbc.Input(
                        id="tp-input",
                        type="number",
                        value=4,
                        min=0.1,
                        max=20,
                        step=0.1,
                        className="mb-2",
                    ),
                ]
            )
        elif strategy == "rsi":
            return html.Div(
                [
                    html.Label("RSI Periode", className="form-label"),
                    dbc.Input(
                        id="rsi-period-input",
                        type="number",
                        value=14,
                        min=1,
                        max=50,
                        step=1,
                        className="mb-2",
                    ),
                    html.Label("Überkauft", className="form-label"),
                    dbc.Input(
                        id="rsi-overbought-input",
                        type="number",
                        value=70,
                        min=50,
                        max=90,
                        step=1,
                        className="mb-2",
                    ),
                    html.Label("Überverkauft", className="form-label"),
                    dbc.Input(
                        id="rsi-oversold-input",
                        type="number",
                        value=30,
                        min=10,
                        max=50,
                        step=1,
                        className="mb-2",
                    ),
                    html.Label("Stop Loss (%)", className="form-label"),
                    dbc.Input(
                        id="sl-input",
                        type="number",
                        value=2,
                        min=0.1,
                        max=10,
                        step=0.1,
                        className="mb-2",
                    ),
                    html.Label("Take Profit (%)", className="form-label"),
                    dbc.Input(
                        id="tp-input",
                        type="number",
                        value=4,
                        min=0.1,
                        max=20,
                        step=0.1,
                        className="mb-2",
                    ),
                ]
            )
        elif strategy == "macd":
            return html.Div(
                [
                    html.Label("Schneller EMA", className="form-label"),
                    dbc.Input(
                        id="macd-fast-input",
                        type="number",
                        value=12,
                        min=1,
                        max=50,
                        step=1,
                        className="mb-2",
                    ),
                    html.Label("Langsamer EMA", className="form-label"),
                    dbc.Input(
                        id="macd-slow-input",
                        type="number",
                        value=26,
                        min=1,
                        max=50,
                        step=1,
                        className="mb-2",
                    ),
                    html.Label("Signal", className="form-label"),
                    dbc.Input(
                        id="macd-signal-input",
                        type="number",
                        value=9,
                        min=1,
                        max=50,
                        step=1,
                        className="mb-2",
                    ),
                    html.Label("Stop Loss (%)", className="form-label"),
                    dbc.Input(
                        id="sl-input",
                        type="number",
                        value=2,
                        min=0.1,
                        max=10,
                        step=0.1,
                        className="mb-2",
                    ),
                    html.Label("Take Profit (%)", className="form-label"),
                    dbc.Input(
                        id="tp-input",
                        type="number",
                        value=4,
                        min=0.1,
                        max=20,
                        step=0.1,
                        className="mb-2",
                    ),
                ]
            )
        elif strategy == "bollinger":
            return html.Div(
                [
                    html.Label("Periode", className="form-label"),
                    dbc.Input(
                        id="bollinger-period-input",
                        type="number",
                        value=20,
                        min=1,
                        max=50,
                        step=1,
                        className="mb-2",
                    ),
                    html.Label("Standardabweichungen", className="form-label"),
                    dbc.Input(
                        id="bollinger-std-input",
                        type="number",
                        value=2,
                        min=0.5,
                        max=4,
                        step=0.1,
                        className="mb-2",
                    ),
                    html.Label("Stop Loss (%)", className="form-label"),
                    dbc.Input(
                        id="sl-input",
                        type="number",
                        value=2,
                        min=0.1,
                        max=10,
                        step=0.1,
                        className="mb-2",
                    ),
                    html.Label("Take Profit (%)", className="form-label"),
                    dbc.Input(
                        id="tp-input",
                        type="number",
                        value=4,
                        min=0.1,
                        max=20,
                        step=0.1,
                        className="mb-2",
                    ),
                ]
            )
        else:
            return html.Div(
                [
                    html.P("Keine Parameter verfügbar für diese Strategie."),
                ]
            )
    
    except Exception as e:
        logger.error(f"Fehler beim Aktualisieren der Strategie-Parameter: {str(e)}")
        
        # Zeige Fehlermeldung
        return html.Div(
            [
                html.P(f"Fehler beim Laden der Strategie-Parameter: {str(e)}", className="text-danger"),
            ]
        )

# Callback für Fehlerbenachrichtigungen
@callback(
    Output("error-notification", "children"),
    Input("url", "pathname"),
)
def check_system_status(pathname):
    """
    Überprüft den Systemstatus und zeigt Fehlerbenachrichtigungen an
    """
    try:
        # Prüfe, ob Fehler vorliegen
        error_log_path = "dashboard_errors.log"
        if os.path.exists(error_log_path):
            # Prüfe, ob neue Fehler in den letzten 5 Minuten aufgetreten sind
            file_mod_time = datetime.fromtimestamp(os.path.getmtime(error_log_path))
            if datetime.now() - file_mod_time < timedelta(minutes=5):
                # Lese die letzten Fehler
                with open(error_log_path, "r") as f:
                    last_errors = f.readlines()[-5:]  # Letzte 5 Zeilen
                
                # Zeige Fehlerbenachrichtigung
                return dbc.Alert(
                    [
                        html.H4("Systemfehler erkannt", className="alert-heading"),
                        html.P(
                            "Es wurden kürzlich Fehler im System erkannt. "
                            "Die Anwendung läuft im Fallback-Modus mit eingeschränkter Funktionalität."
                        ),
                        html.Hr(),
                        html.P(
                            "Bitte aktualisieren Sie die Seite oder versuchen Sie es später erneut. "
                            "Wenn das Problem weiterhin besteht, wenden Sie sich an den Support.",
                            className="mb-0",
                        ),
                    ],
                    color="warning",
                    dismissable=True,
                )
        
        # Keine Fehler
        return None
    
    except Exception as e:
        logger.error(f"Fehler beim Überprüfen des Systemstatus: {str(e)}")
        return None

# Callback für Zeichnungsdaten
@callback(
    Output("drawing-data-store", "data"),
    Input("price-chart", "clickData"),
    Input("active-drawing-tool-store", "data"),
    State("drawing-data-store", "data"),
)
def update_drawing_data(click_data, active_tool, drawing_data):
    """
    Aktualisiert die Zeichnungsdaten basierend auf Klicks im Chart
    """
    try:
        if not click_data or not active_tool:
            raise PreventUpdate
        
        # Extrahiere Klickposition
        x = click_data["points"][0]["x"]
        y = click_data["points"][0]["y"]
        
        # Wenn das Lösch-Werkzeug aktiv ist, entferne Zeichnungen in der Nähe
        if active_tool == "delete":
            # Filtere Zeichnungen, die nicht in der Nähe des Klicks sind
            new_drawing_data = []
            for drawing in drawing_data:
                # Prüfe, ob der Klick in der Nähe der Zeichnung ist
                if drawing["type"] == "trendline":
                    # Für Trendlinien prüfe, ob der Klick in der Nähe der Linie ist
                    # Vereinfachte Implementierung: Prüfe, ob der Klick in der Nähe der Endpunkte ist
                    if (abs(pd.Timestamp(x) - pd.Timestamp(drawing["x0"])).total_seconds() > 86400 and
                        abs(pd.Timestamp(x) - pd.Timestamp(drawing["x1"])).total_seconds() > 86400) or \
                       (abs(y - drawing["y0"]) > 0.01 * drawing["y0"] and
                        abs(y - drawing["y1"]) > 0.01 * drawing["y1"]):
                        new_drawing_data.append(drawing)
                elif drawing["type"] == "horizontal":
                    # Für horizontale Linien prüfe, ob der Klick in der Nähe der Linie ist
                    if abs(y - drawing["y0"]) > 0.01 * drawing["y0"]:
                        new_drawing_data.append(drawing)
                elif drawing["type"] == "rectangle":
                    # Für Rechtecke prüfe, ob der Klick innerhalb des Rechtecks ist
                    if not (pd.Timestamp(drawing["x0"]) <= pd.Timestamp(x) <= pd.Timestamp(drawing["x1"]) and
                            min(drawing["y0"], drawing["y1"]) <= y <= max(drawing["y0"], drawing["y1"])):
                        new_drawing_data.append(drawing)
                elif drawing["type"] == "fibonacci":
                    # Für Fibonacci-Retracements prüfe, ob der Klick in der Nähe der Linie ist
                    if (abs(pd.Timestamp(x) - pd.Timestamp(drawing["x0"])).total_seconds() > 86400 and
                        abs(pd.Timestamp(x) - pd.Timestamp(drawing["x1"])).total_seconds() > 86400) or \
                       (abs(y - drawing["y0"]) > 0.01 * drawing["y0"] and
                        abs(y - drawing["y1"]) > 0.01 * drawing["y1"]):
                        new_drawing_data.append(drawing)
            
            return new_drawing_data
        
        # Füge neue Zeichnung hinzu
        if active_tool == "trendline":
            # Für Trendlinien benötigen wir zwei Klicks
            if len(drawing_data) > 0 and drawing_data[-1].get("type") == "trendline" and "x1" not in drawing_data[-1]:
                # Zweiter Klick für Trendlinie
                drawing_data[-1]["x1"] = x
                drawing_data[-1]["y1"] = y
                return drawing_data
            else:
                # Erster Klick für Trendlinie
                drawing_data.append({
                    "type": "trendline",
                    "x0": x,
                    "y0": y,
                })
                return drawing_data
        elif active_tool == "horizontal":
            # Für horizontale Linien benötigen wir nur einen Klick
            drawing_data.append({
                "type": "horizontal",
                "y0": y,
            })
            return drawing_data
        elif active_tool == "rectangle":
            # Für Rechtecke benötigen wir zwei Klicks
            if len(drawing_data) > 0 and drawing_data[-1].get("type") == "rectangle" and "x1" not in drawing_data[-1]:
                # Zweiter Klick für Rechteck
                drawing_data[-1]["x1"] = x
                drawing_data[-1]["y1"] = y
                return drawing_data
            else:
                # Erster Klick für Rechteck
                drawing_data.append({
                    "type": "rectangle",
                    "x0": x,
                    "y0": y,
                })
                return drawing_data
        elif active_tool == "fibonacci":
            # Für Fibonacci-Retracements benötigen wir zwei Klicks
            if len(drawing_data) > 0 and drawing_data[-1].get("type") == "fibonacci" and "x1" not in drawing_data[-1]:
                # Zweiter Klick für Fibonacci
                drawing_data[-1]["x1"] = x
                drawing_data[-1]["y1"] = y
                return drawing_data
            else:
                # Erster Klick für Fibonacci
                drawing_data.append({
                    "type": "fibonacci",
                    "x0": x,
                    "y0": y,
                })
                return drawing_data
        
        # Fallback: Keine Änderung
        return drawing_data
    
    except Exception as e:
        logger.error(f"Fehler beim Aktualisieren der Zeichnungsdaten: {str(e)}")
        return drawing_data

# Importiere Chart-Callbacks
from dashboard.chart_callbacks import (
    update_interactive_chart,
    update_drawing_tool_buttons,
    update_asset_options,
    update_timeframe_buttons,
    handle_timeframe_button_click,
)

# Server für WSGI-Deployment
server = app.server

if __name__ == "__main__":
    try:
        # Starte die App
        app.run_server(debug=True, host="0.0.0.0")
    except Exception as e:
        logger.error(f"Fehler beim Starten der App: {str(e)}")
