import os
import sys
import json
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from io import StringIO

import dash
from dash import dcc, html, Input, Output, State, callback, dash_table, ALL, MATCH
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template, ThemeChangerAIO
from dash_iconify import DashIconify
import dash_mantine_components as dmc

import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Konfiguriere Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Füge den Projektpfad zum Systempfad hinzu
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Importiere die benutzerdefinierten Komponenten
from dashboard.components_module import load_nasdaq_symbols, create_asset_buttons, create_timeframe_buttons

# Importiere die Datenverarbeitungsfunktionen
from data.data_loader_enhanced import load_stock_data, validate_symbol, get_alternative_symbols
from dashboard.chart_utils import create_price_chart, create_volume_chart, create_indicator_chart
from dashboard.chart_callbacks import register_chart_callbacks
from dashboard.error_handler import handle_error

# Initialisiere die Dash-App
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
    ],
    suppress_callback_exceptions=True
)

# Setze den Titel der App
app.title = "Trading Dashboard"

# Lade das Bootstrap-Template
load_figure_template("bootstrap")

# Definiere Farbschema
colors = {
    'background': '#1e222d',
    'card_background': '#252a37',
    'text': '#ffffff',
    'primary': '#0d6efd',
    'secondary': '#6c757d',
    'success': '#198754',
    'danger': '#dc3545',
    'warning': '#ffc107',
    'info': '#0dcaf0',
}

# Lade die Nasdaq-Symbole
nasdaq_symbols = load_nasdaq_symbols()

# Definiere Header
header = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                dbc.Row(
                    [
                        dbc.Col(DashIconify(icon="mdi:chart-line", width=30, color=colors['primary'])),
                        dbc.Col(dbc.NavbarBrand("Trading Dashboard Pro", className="ms-2")),
                    ],
                    align="center",
                    className="g-0",
                ),
                href="#",
                style={"textDecoration": "none"},
            ),
            dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            dbc.Collapse(
                dbc.Nav(
                    [
                        dbc.NavItem(dbc.NavLink([DashIconify(icon="mdi:view-dashboard", width=18, className="me-2"), "Dashboard"], href="#")),
                        dbc.NavItem(dbc.NavLink([DashIconify(icon="mdi:strategy", width=18, className="me-2"), "Strategien"], href="#")),
                        dbc.NavItem(dbc.NavLink([DashIconify(icon="mdi:test-tube", width=18, className="me-2"), "Backtesting"], href="#")),
                        dbc.NavItem(dbc.NavLink([DashIconify(icon="mdi:cog", width=18, className="me-2"), "Einstellungen"], href="#")),
                    ],
                    className="ms-auto",
                    navbar=True,
                ),
                id="navbar-collapse",
                navbar=True,
            ),
        ],
        fluid=True,
    ),
    color=colors['background'],
    dark=True,
    className="mb-4",
)

# Erstelle die verbesserten Zeitrahmen-Buttons
timeframe_buttons = create_timeframe_buttons()

# Definiere Sidebar für Dateneinstellungen
sidebar = dbc.Card(
    [
        dbc.CardHeader([
            html.H4("Dateneinstellungen", className="card-title mb-0"),
            html.Div([
                DashIconify(icon="mdi:database-cog", width=24, color=colors['primary']),
            ], className="float-end")
        ]),
        dbc.CardBody([
            dbc.Form([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Symbol", html_for="symbol-input", className="mb-1"),
                        dbc.InputGroup([
                            dbc.InputGroupText(DashIconify(icon="mdi:finance", width=18)),
                            dbc.Input(
                                id="symbol-input",
                                type="text",
                                value="AAPL",
                                placeholder="z.B. AAPL, MSFT",
                                className="border-start-0",
                            ),
                        ], className="mb-3"),
                    ]),
                ]),
                
                # Füge die klickbaren Assets hinzu
                create_asset_buttons(nasdaq_symbols),
                
                dbc.Label("Zeitrahmen", className="mb-1"),
                timeframe_buttons,

                dbc.Row([
                    dbc.Col([
                        dbc.Label("Zeitraum", html_for="range-dropdown", className="mb-1"),
                        dbc.InputGroup([
                            dbc.InputGroupText(DashIconify(icon="mdi:calendar-range", width=18)),
                            dbc.Select(
                                id="range-dropdown",
                                options=[
                                    {"label": "1 Tag", "value": "1d"},
                                    {"label": "5 Tage", "value": "5d"},
                                    {"label": "1 Monat", "value": "1mo"},
                                    {"label": "3 Monate", "value": "3mo"},
                                    {"label": "6 Monate", "value": "6mo"},
                                    {"label": "1 Jahr", "value": "1y"},
                                    {"label": "2 Jahre", "value": "2y"},
                                    {"label": "5 Jahre", "value": "5y"},
                                    {"label": "Max", "value": "max"},
                                ],
                                value="1y",
                                className="border-start-0",
                            ),
                        ], className="mb-3"),
                    ]),
                ]),

                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            [DashIconify(icon="mdi:refresh", width=18, className="me-2"), "Daten abrufen"],
                            id="fetch-data-button",
                            color="primary",
                            className="w-100 mb-3",
                        ),
                    ]),
                ]),

                dbc.Row([
                    dbc.Col([
                        dbc.Spinner(
                            html.Div(id="data-info", className="text-center text-muted small"),
                            color="primary",
                            size="sm",
                            spinner_style={"width": "1rem", "height": "1rem"}
                        ),
                    ]),
                ]),
                
                # Füge ein Statusfeld für API-Fehler hinzu
                dbc.Row([
                    dbc.Col([
                        html.Div(id="api-status", className="text-center small mt-2"),
                    ]),
                ]),
            ]),
        ]),
    ],
    className="mb-4 shadow sidebar",
    style={"backgroundColor": colors['card_background']},
)

# Definiere Hauptbereich für Charts
chart_card = dbc.Card(
    [
        dbc.CardHeader([
            html.H4(["Preischart ", html.Span(id="chart-symbol", className="text-primary")], className="card-title mb-0 d-inline"),
            html.Div([
                dbc.ButtonGroup([
                    dbc.Button(id="toggle-sma", className="btn-sm", n_clicks=0),
                    dbc.Button(id="toggle-bb", className="btn-sm", n_clicks=0),
                    dbc.Button(id="toggle-rsi", className="btn-sm", n_clicks=0),
                    dbc.Button(id="toggle-macd", className="btn-sm", n_clicks=0),
                    dbc.Button(id="toggle-volume", className="btn-sm", n_clicks=0),
                ], className="float-end"),
            ], className="float-end"),
        ]),
        dbc.CardBody([
            dcc.Loading(
                dcc.Graph(
                    id="price-chart",
                    config={
                        "displayModeBar": True,
                        "scrollZoom": True,
                        "modeBarButtonsToRemove": [
                            "select2d",
                            "lasso2d",
                            "autoScale2d",
                        ],
                    },
                    style={"height": "500px"},
                ),
                type="default",
                color="#0d6efd",
            ),
        ]),
    ],
    className="mb-4 shadow",
    style={"backgroundColor": colors['card_background']},
)

# Definiere Bereich für Indikatoren
indicators_card = dbc.Card(
    [
        dbc.CardHeader([
            html.H4("Technische Indikatoren", className="card-title mb-0"),
            html.Div([
                DashIconify(icon="mdi:chart-bell-curve", width=24, color=colors['primary']),
            ], className="float-end")
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dcc.Loading(
                        dcc.Graph(
                            id="rsi-chart",
                            config={
                                "displayModeBar": False,
                                "scrollZoom": True,
                            },
                            style={"height": "200px"},
                        ),
                        type="default",
                        color="#0d6efd",
                    ),
                ], width=12, lg=4, className="mb-4"),
                dbc.Col([
                    dcc.Loading(
                        dcc.Graph(
                            id="macd-chart",
                            config={
                                "displayModeBar": False,
                                "scrollZoom": True,
                            },
                            style={"height": "200px"},
                        ),
                        type="default",
                        color="#0d6efd",
                    ),
                ], width=12, lg=4, className="mb-4"),
                dbc.Col([
                    dcc.Loading(
                        dcc.Graph(
                            id="volume-chart",
                            config={
                                "displayModeBar": False,
                                "scrollZoom": True,
                            },
                            style={"height": "200px"},
                        ),
                        type="default",
                        color="#0d6efd",
                    ),
                ], width=12, lg=4, className="mb-4"),
            ]),
        ]),
    ],
    className="mb-4 shadow",
    style={"backgroundColor": colors['card_background']},
)

# Definiere Trades-Tabelle
trades_card = dbc.Card(
    [
        dbc.CardHeader([
            html.H4("Trades", className="card-title mb-0"),
            html.Div([
                DashIconify(icon="mdi:swap-horizontal", width=24, color=colors['primary']),
            ], className="float-end")
        ]),
        dbc.CardBody([
            html.Div(id="trades-table-container"),
        ]),
    ],
    className="mb-4 shadow",
    style={"backgroundColor": colors['card_background']},
)

# Definiere das Layout der App
app.layout = dbc.Container(
    [
        dcc.Store(id="stock-data-store"),
        dcc.Store(id="active-timeframe-store", data="1h"),
        
        # Füge einen Store für API-Status hinzu
        dcc.Store(id="api-error-store"),
        
        header,
        dbc.Row(
            [
                # Linke Spalte mit Sidebar
                dbc.Col(
                    [
                        sidebar,
                    ],
                    lg=3,
                    md=12,
                    className="sidebar",
                ),
                
                # Rechte Spalte mit Charts und Tabellen
                dbc.Col(
                    [
                        chart_card,
                        indicators_card,
                        trades_card,
                    ],
                    lg=9,
                    md=12,
                ),
            ],
        ),
        
        # Füge ein Fehler-Toast hinzu
        dbc.Toast(
            id="error-toast",
            header="Fehler",
            is_open=False,
            dismissable=True,
            icon="danger",
            style={"position": "fixed", "top": 10, "right": 10, "width": 350, "zIndex": 1000},
        ),
        
        # Füge ein Info-Toast hinzu
        dbc.Toast(
            id="info-toast",
            header="Information",
            is_open=False,
            dismissable=True,
            icon="info",
            style={"position": "fixed", "top": 10, "right": 10, "width": 350, "zIndex": 1000},
        ),
        
        # Footer
        html.Footer(
            dbc.Container(
                [
                    html.Hr(),
                    dbc.Row(
                        [
                            dbc.Col(
                                html.P("Trading Dashboard Pro v3.0.1 | Server", className="text-muted small"),
                                width="auto",
                            ),
                            dbc.Col(
                                html.Div(
                                    [
                                        html.A(
                                            DashIconify(icon="mdi:github", width=18),
                                            href="#",
                                            className="text-muted me-3",
                                        ),
                                        html.A(
                                            DashIconify(icon="mdi:twitter", width=18),
                                            href="#",
                                            className="text-muted me-3",
                                        ),
                                        html.A(
                                            DashIconify(icon="mdi:linkedin", width=18),
                                            href="#",
                                            className="text-muted me-3",
                                        ),
                                        html.A(
                                            DashIconify(icon="mdi:email", width=18),
                                            href="#",
                                            className="text-muted me-3",
                                        ),
                                        html.A(
                                            DashIconify(icon="mdi:web", width=18),
                                            href="#",
                                            className="text-muted",
                                        ),
                                    ],
                                    className="text-end",
                                ),
                                width="auto",
                                className="ms-auto",
                            ),
                        ],
                        className="align-items-center",
                    ),
                ]
            ),
            className="mt-5",
        ),
    ],
    fluid=True,
    className="bg-dark text-light",
)

# Callback für die Aktualisierung des aktiven Zeitrahmens
@app.callback(
    Output("active-timeframe-store", "data"),
    [Input({"type": "timeframe-button", "index": ALL}, "n_clicks")],
    [State({"type": "timeframe-button", "index": ALL}, "id"),
     State("active-timeframe-store", "data")]
)
def update_active_timeframe(n_clicks, ids, current_timeframe):
    ctx = dash.callback_context
    if not ctx.triggered:
        return current_timeframe
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if not button_id:
        return current_timeframe
    
    try:
        button_id_dict = json.loads(button_id)
        timeframe = button_id_dict["index"]
        return timeframe
    except:
        return current_timeframe

# Callback für die Aktualisierung des Symbols durch Klicken auf Asset-Buttons
@app.callback(
    Output("symbol-input", "value"),
    [Input({"type": "asset-button", "index": ALL}, "n_clicks")],
    [State({"type": "asset-button", "index": ALL}, "id"),
     State("symbol-input", "value")]
)
def update_symbol_from_button(n_clicks, ids, current_symbol):
    ctx = dash.callback_context
    if not ctx.triggered:
        return current_symbol
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if not button_id:
        return current_symbol
    
    try:
        button_id_dict = json.loads(button_id)
        symbol = button_id_dict["index"]
        return symbol
    except:
        return current_symbol

# Callback für das Abrufen der Daten
@app.callback(
    [Output("stock-data-store", "data"),
     Output("data-info", "children"),
     Output("chart-symbol", "children"),
     Output("api-status", "children"),
     Output("api-status", "className"),
     Output("error-toast", "is_open"),
     Output("error-toast", "children"),
     Output("info-toast", "is_open"),
     Output("info-toast", "children")],
    [Input("fetch-data-button", "n_clicks")],
    [State("symbol-input", "value"),
     State("active-timeframe-store", "data"),
     State("range-dropdown", "value")]
)
def fetch_data(n_clicks, symbol, timeframe, date_range):
    if n_clicks is None:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, False, "", False, ""
    
    if not symbol:
        return dash.no_update, "Bitte geben Sie ein Symbol ein", dash.no_update, "", "text-center small mt-2", True, "Bitte geben Sie ein Symbol ein", False, ""
    
    try:
        logger.info(f"Daten werden abgerufen für Symbol: {symbol}, Zeitrahmen: {timeframe}, Zeitraum: {date_range}")
        
        # Validiere das Symbol
        if not validate_symbol(symbol):
            alternatives = []
            if symbol.lower() == "nq":
                alternatives = get_alternative_symbols("nasdaq")
            elif symbol.lower() == "sp" or symbol.lower() == "spx":
                alternatives = get_alternative_symbols("sp500")
            
            alternatives_text = ""
            if alternatives:
                alternatives_text = f"Versuchen Sie stattdessen: {', '.join(alternatives)}"
            
            error_msg = f"Ungültiges Symbol: {symbol}. {alternatives_text}"
            return dash.no_update, error_msg, dash.no_update, error_msg, "text-center small mt-2 text-danger", True, error_msg, False, ""
        
        # Lade die Daten mit verbesserter Fehlerbehandlung
        df, status_message = load_stock_data(symbol, timeframe, date_range)
        
        # Überprüfe, ob Daten zurückgegeben wurden
        if df.empty:
            error_msg = f"Keine Daten für {symbol} gefunden. Bitte überprüfen Sie das Symbol oder versuchen Sie es später erneut."
            return dash.no_update, error_msg, dash.no_update, error_msg, "text-center small mt-2 text-danger", True, error_msg, False, ""
        
        # Erstelle eine Info-Nachricht
        start_date = df.index.min().strftime('%d.%m.%Y')
        end_date = df.index.max().strftime('%d.%m.%Y')
        days = (df.index.max() - df.index.min()).days
        info = f"{days} Tage ({start_date} - {end_date})"
        
        # Bereite die Daten für das Speichern vor
        data = {
            'df': df.to_json(date_format='iso', orient='split'),
            'symbol': symbol,
            'timeframe': timeframe,
            'date_range': date_range
        }
        
        # Zeige ein Info-Toast, wenn Fallback-Symbole verwendet wurden
        show_info_toast = "Fallback" in status_message
        info_toast_message = status_message if show_info_toast else ""
        
        return data, info, symbol, status_message, "text-center small mt-2 text-success", False, "", show_info_toast, info_toast_message
    
    except Exception as e:
        error_msg = f"Fehler beim Laden der Daten: {str(e)}"
        logger.error(error_msg)
        return dash.no_update, error_msg, dash.no_update, error_msg, "text-center small mt-2 text-danger", True, error_msg, False, ""

# Callback für die Aktualisierung der Chart-Steuerelemente
@app.callback(
    [Output("toggle-sma", "children"),
     Output("toggle-sma", "color"),
     Output("toggle-bb", "children"),
     Output("toggle-bb", "color"),
     Output("toggle-rsi", "children"),
     Output("toggle-rsi", "color"),
     Output("toggle-macd", "children"),
     Output("toggle-macd", "color"),
     Output("toggle-volume", "children"),
     Output("toggle-volume", "color")],
    [Input("toggle-sma", "n_clicks"),
     Input("toggle-bb", "n_clicks"),
     Input("toggle-rsi", "n_clicks"),
     Input("toggle-macd", "n_clicks"),
     Input("toggle-volume", "n_clicks")]
)
def update_chart_controls(n_sma, n_bb, n_rsi, n_macd, n_volume):
    # Standardwerte
    sma_active = n_sma % 2 == 1 if n_sma else False
    bb_active = n_bb % 2 == 1 if n_bb else False
    rsi_active = n_rsi % 2 == 1 if n_rsi else True
    macd_active = n_macd % 2 == 1 if n_macd else True
    volume_active = n_volume % 2 == 1 if n_volume else True
    
    # Erstelle die Button-Inhalte
    sma_content = [DashIconify(icon="mdi:chart-line", width=16), " SMA"]
    bb_content = [DashIconify(icon="mdi:chart-bell-curve-cumulative", width=16), " BB"]
    rsi_content = [DashIconify(icon="mdi:chart-line-variant", width=16), " RSI"]
    macd_content = [DashIconify(icon="mdi:chart-timeline-variant", width=16), " MACD"]
    volume_content = [DashIconify(icon="mdi:chart-histogram", width=16), " VOL"]
    
    # Setze die Button-Farben
    sma_color = "primary" if sma_active else "outline-primary"
    bb_color = "primary" if bb_active else "outline-primary"
    rsi_color = "primary" if rsi_active else "outline-primary"
    macd_color = "primary" if macd_active else "outline-primary"
    volume_color = "primary" if volume_active else "outline-primary"
    
    return sma_content, sma_color, bb_content, bb_color, rsi_content, rsi_color, macd_content, macd_color, volume_content, volume_color

# Callback für die Aktualisierung der Charts
@app.callback(
    [Output("price-chart", "figure"),
     Output("rsi-chart", "figure"),
     Output("macd-chart", "figure"),
     Output("volume-chart", "figure")],
    [Input("stock-data-store", "data"),
     Input("toggle-sma", "n_clicks"),
     Input("toggle-bb", "n_clicks"),
     Input("toggle-rsi", "n_clicks"),
     Input("toggle-macd", "n_clicks"),
     Input("toggle-volume", "n_clicks")]
)
def update_chart(data, n_sma, n_bb, n_rsi, n_macd, n_volume):
    # Überprüfe, ob Daten vorhanden sind
    if data is None:
        # Erstelle leere Charts
        empty_price_chart = go.Figure()
        empty_price_chart.update_layout(
            template="plotly_dark",
            paper_bgcolor=colors['card_background'],
            plot_bgcolor=colors['card_background'],
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=False, zeroline=False),
        )
        
        return empty_price_chart, empty_price_chart, empty_price_chart, empty_price_chart
    
    try:
        # Lade die Daten aus dem Store
        df = pd.read_json(StringIO(data['df']), orient='split')
        symbol = data['symbol']
        
        # Setze den Index als DatetimeIndex
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        
        # Überprüfe, ob der DataFrame leer ist
        if df.empty:
            logger.warning(f"Leerer DataFrame für Symbol {symbol}")
            # Erstelle leere Charts
            empty_price_chart = go.Figure()
            empty_price_chart.update_layout(
                template="plotly_dark",
                paper_bgcolor=colors['card_background'],
                plot_bgcolor=colors['card_background'],
                margin=dict(l=0, r=0, t=0, b=0),
                xaxis=dict(showgrid=False, zeroline=False),
                yaxis=dict(showgrid=False, zeroline=False),
            )
            
            return empty_price_chart, empty_price_chart, empty_price_chart, empty_price_chart
        
        # Überprüfe, ob NaN-Werte vorhanden sind
        if df.isna().any().any():
            logger.warning(f"{df.isna().sum().sum()} NaN-Werte gefunden, werden gefüllt...")
            df = df.fillna(method='ffill').fillna(method='bfill').fillna(0)
        
        # Bestimme die aktiven Indikatoren
        show_sma = n_sma % 2 == 1 if n_sma else False
        show_bb = n_bb % 2 == 1 if n_bb else False
        show_rsi = n_rsi % 2 == 1 if n_rsi else True
        show_macd = n_macd % 2 == 1 if n_macd else True
        show_volume = n_volume % 2 == 1 if n_volume else True
        
        # Erstelle die Charts
        price_chart = create_price_chart(df, symbol, show_sma=show_sma, show_bb=show_bb, show_volume=show_volume)
        rsi_chart = create_indicator_chart(df, 'rsi') if show_rsi else go.Figure()
        macd_chart = create_indicator_chart(df, 'macd') if show_macd else go.Figure()
        volume_chart = create_volume_chart(df) if show_volume else go.Figure()
        
        # Aktualisiere die Layouts
        for chart in [rsi_chart, macd_chart, volume_chart]:
            chart.update_layout(
                template="plotly_dark",
                paper_bgcolor=colors['card_background'],
                plot_bgcolor=colors['card_background'],
                margin=dict(l=0, r=0, t=30, b=0),
                height=200,
            )
        
        price_chart.update_layout(
            template="plotly_dark",
            paper_bgcolor=colors['card_background'],
            plot_bgcolor=colors['card_background'],
            margin=dict(l=0, r=0, t=0, b=0),
        )
        
        return price_chart, rsi_chart, macd_chart, volume_chart
    
    except Exception as e:
        logger.error(f"Fehler beim Aktualisieren der Charts: {str(e)}")
        # Erstelle leere Charts im Fehlerfall
        empty_price_chart = go.Figure()
        empty_price_chart.update_layout(
            template="plotly_dark",
            paper_bgcolor=colors['card_background'],
            plot_bgcolor=colors['card_background'],
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=False, zeroline=False),
        )
        
        return empty_price_chart, empty_price_chart, empty_price_chart, empty_price_chart

# Callback für die Aktualisierung der Trades-Tabelle
@app.callback(
    Output("trades-table-container", "children"),
    [Input("stock-data-store", "data")]
)
def update_trades_table(data):
    if data is None:
        return html.Div("Keine Daten verfügbar", className="text-center text-muted py-5")
    
    try:
        # Erstelle eine Beispiel-Tabelle für Trades
        trades_data = [
            {"Datum": "2023-01-15", "Typ": "Kauf", "Preis": "$150.25", "Menge": "10", "Wert": "$1,502.50"},
            {"Datum": "2023-02-22", "Typ": "Verkauf", "Preis": "$165.75", "Menge": "5", "Wert": "$828.75"},
            {"Datum": "2023-03-10", "Typ": "Kauf", "Preis": "$145.30", "Menge": "8", "Wert": "$1,162.40"},
            {"Datum": "2023-04-05", "Typ": "Verkauf", "Preis": "$170.20", "Menge": "13", "Wert": "$2,212.60"},
        ]
        
        table = dash_table.DataTable(
            data=trades_data,
            columns=[{"name": col, "id": col} for col in trades_data[0].keys()],
            style_header={
                "backgroundColor": colors['background'],
                "color": colors['text'],
                "fontWeight": "bold",
                "border": f"1px solid {colors['secondary']}",
            },
            style_cell={
                "backgroundColor": colors['card_background'],
                "color": colors['text'],
                "border": f"1px solid {colors['secondary']}",
                "padding": "10px",
                "textAlign": "left",
            },
            style_data_conditional=[
                {
                    "if": {"column_id": "Typ", "filter_query": "{Typ} eq 'Kauf'"},
                    "color": colors['success'],
                },
                {
                    "if": {"column_id": "Typ", "filter_query": "{Typ} eq 'Verkauf'"},
                    "color": colors['danger'],
                },
            ],
            page_size=10,
        )
        
        return table
    
    except Exception as e:
        logger.error(f"Fehler beim Aktualisieren der Trades-Tabelle: {str(e)}")
        return html.Div(f"Fehler beim Laden der Trades: {str(e)}", className="text-center text-danger py-5")

# Starte die App
if __name__ == "__main__":
    # Melde erfolgreiche Initialisierung
    logger.info("Manus API erfolgreich initialisiert")
    print("Starte Trading Dashboard auf http://localhost:8050")
    app.run_server(debug=True, host="0.0.0.0", port=8050)
