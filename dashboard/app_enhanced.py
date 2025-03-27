import os
import sys
import json
import pandas as pd
import numpy as np
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

# Füge den Projektpfad zum Systempfad hinzu
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Importiere die benutzerdefinierten Komponenten
from components import load_nasdaq_symbols, create_asset_buttons, create_timeframe_buttons

# Importiere die Datenverarbeitungsfunktionen
from data.data_loader import load_stock_data
from chart_utils import create_price_chart, create_volume_chart, create_indicator_chart
from chart_callbacks import register_chart_callbacks
from error_handler import handle_error

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
                        "modeBarButtonsToRemove": ["lasso2d", "select2d"],
                    },
                    style={"height": "500px"},
                ),
                type="default",
            ),
            html.Div(id="chart-indicators", className="mt-2"),
        ]),
    ],
    className="mb-4 shadow",
    style={"backgroundColor": colors['card_background']},
)

# Definiere Bereich für Backtest-Ergebnisse
results_card = dbc.Card(
    [
        dbc.CardHeader([
            html.H4("Backtest-Ergebnisse", className="card-title mb-0"),
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Gesamtrendite", className="card-title text-center"),
                            html.H3(id="total-return", className="text-center mb-0"),
                        ]),
                    ], className="mb-3 shadow-sm"),
                ], width=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Win-Rate", className="card-title text-center"),
                            html.H3(id="win-rate", className="text-center mb-0"),
                        ]),
                    ], className="mb-3 shadow-sm"),
                ], width=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Profit-Faktor", className="card-title text-center"),
                            html.H3(id="profit-factor", className="text-center mb-0"),
                        ]),
                    ], className="mb-3 shadow-sm"),
                ], width=4),
            ]),
            dbc.Row([
                dbc.Col([
                    dcc.Loading(
                        dcc.Graph(
                            id="equity-curve",
                            config={"displayModeBar": False},
                            style={"height": "300px"},
                        ),
                        type="default",
                    ),
                ]),
            ]),
        ]),
    ],
    className="mb-4 shadow",
    style={"backgroundColor": colors['card_background']},
)

# Definiere Bereich für Trade-Liste
trades_card = dbc.Card(
    [
        dbc.CardHeader([
            html.H4("Trade-Liste", className="card-title mb-0"),
        ]),
        dbc.CardBody([
            dcc.Loading(
                dash_table.DataTable(
                    id="trades-table",
                    columns=[
                        {"name": "Datum", "id": "date"},
                        {"name": "Typ", "id": "type"},
                        {"name": "Preis", "id": "price"},
                        {"name": "Menge", "id": "quantity"},
                        {"name": "P/L", "id": "pnl"},
                    ],
                    style_header={
                        "backgroundColor": colors['background'],
                        "color": colors['text'],
                        "fontWeight": "bold",
                        "textAlign": "center",
                    },
                    style_cell={
                        "backgroundColor": colors['card_background'],
                        "color": colors['text'],
                        "textAlign": "center",
                    },
                    style_data_conditional=[
                        {
                            "if": {"filter_query": "{type} = 'BUY'"},
                            "backgroundColor": "rgba(25, 135, 84, 0.1)",
                        },
                        {
                            "if": {"filter_query": "{type} = 'SELL'"},
                            "backgroundColor": "rgba(220, 53, 69, 0.1)",
                        },
                        {
                            "if": {"filter_query": "{pnl} > 0"},
                            "color": colors['success'],
                        },
                        {
                            "if": {"filter_query": "{pnl} < 0"},
                            "color": colors['danger'],
                        },
                    ],
                    page_size=10,
                ),
                type="default",
            ),
        ]),
    ],
    className="mb-4 shadow",
    style={"backgroundColor": colors['card_background']},
)

# Definiere das Layout der App
app.layout = html.Div(
    [
        # Versteckte Div-Elemente für Datenspeicherung
        dcc.Store(id="stock-data-store"),
        dcc.Store(id="backtest-results-store"),
        dcc.Store(id="active-timeframe-store", data="1h"),  # Standardmäßig 1h

        # Header
        header,

        # Hauptinhalt
        dbc.Container(
            [
                dbc.Row(
                    [
                        # Linke Spalte mit Sidebar
                        dbc.Col(
                            [
                                sidebar,
                                strategy_card,
                            ],
                            lg=3,
                            md=12,
                            className="sidebar",
                        ),

                        # Rechte Spalte mit Charts und Ergebnissen
                        dbc.Col(
                            [
                                chart_card,
                                results_card,
                                trades_card,
                            ],
                            lg=9,
                            md=12,
                        ),
                    ]
                ),
            ],
            fluid=True,
            className="mb-4",
        ),

        # Footer
        dbc.Container(
            dbc.Row(
                dbc.Col(
                    html.P(
                        [
                            "Trading Dashboard Pro v3.0.1 | ",
                            html.Span(id="server-status", className="text-success"),
                            html.I(className="fas fa-circle text-success ms-1"),
                        ],
                        className="text-center text-muted small",
                    ),
                    className="py-3",
                ),
            ),
            fluid=True,
        ),

        # Debug-Bereich
        dbc.Container(
            dbc.Row(
                dbc.Col(
                    dbc.ButtonGroup(
                        [
                            dbc.Button(
                                [html.I(className="fas fa-exclamation-triangle me-1"), "Errors"],
                                id="error-button",
                                color="danger",
                                outline=True,
                                size="sm",
                                className="me-1",
                            ),
                            dbc.Button(
                                [html.I(className="fas fa-code me-1"), "Callbacks"],
                                id="callback-button",
                                color="primary",
                                outline=True,
                                size="sm",
                            ),
                        ],
                        className="float-end mb-3",
                    ),
                ),
            ),
            fluid=True,
        ),
    ],
    style={"backgroundColor": colors['background'], "color": colors['text'], "minHeight": "100vh"},
)

# Callback für die Asset-Buttons
@app.callback(
    [Output("symbol-input", "value"),
     Output({"type": "asset-button", "symbol": ALL}, "className")],
    [Input({"type": "asset-button", "symbol": ALL}, "n_clicks")],
    [State({"type": "asset-button", "symbol": ALL}, "id"),
     State({"type": "asset-button", "symbol": ALL}, "className")]
)
def update_symbol_from_button(n_clicks, ids, classes):
    ctx = dash.callback_context
    
    # Wenn kein Button geklickt wurde, keine Änderung
    if not ctx.triggered:
        button_classes = []
        for cls in classes:
            if "index-button" in cls:
                button_classes.append("asset-button index-button")
            else:
                button_classes.append("asset-button")
        return dash.no_update, button_classes
    
    # Finde den geklickten Button
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    button_data = json.loads(button_id)
    clicked_symbol = button_data['symbol']
    
    # Aktualisiere die Button-Klassen
    button_classes = []
    for i, id_obj in enumerate(ids):
        symbol = id_obj['symbol']
        is_index = "index-button" in classes[i]
        
        if symbol == clicked_symbol:
            if is_index:
                button_classes.append("asset-button index-button active")
            else:
                button_classes.append("asset-button active")
        else:
            if is_index:
                button_classes.append("asset-button index-button")
            else:
                button_classes.append("asset-button")
    
    return clicked_symbol, button_classes

# Callback für die Zeitrahmen-Buttons
@app.callback(
    [Output("active-timeframe-store", "data"),
     Output("tf-1min", "className"),
     Output("tf-2min", "className"),
     Output("tf-3min", "className"),
     Output("tf-5m", "className"),
     Output("tf-15m", "className"),
     Output("tf-30m", "className"),
     Output("tf-1h", "className"),
     Output("tf-4h", "className")],
    [Input("tf-1min", "n_clicks"),
     Input("tf-2min", "n_clicks"),
     Input("tf-3min", "n_clicks"),
     Input("tf-5m", "n_clicks"),
     Input("tf-15m", "n_clicks"),
     Input("tf-30m", "n_clicks"),
     Input("tf-1h", "n_clicks"),
     Input("tf-4h", "n_clicks")],
    [State("active-timeframe-store", "data")]
)
def update_active_timeframe(n1, n2, n3, n5, n15, n30, n1h, n4h, current_tf):
    ctx = dash.callback_context
    
    # Wenn kein Button geklickt wurde, behalte den aktuellen Zeitrahmen
    if not ctx.triggered:
        return update_timeframe_classes(current_tf)
    
    # Finde den geklickten Button
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Ordne den Button-ID dem entsprechenden Zeitrahmen zu
    timeframe_map = {
        "tf-1min": "1m",
        "tf-2min": "2m",
        "tf-3min": "3m",
        "tf-5m": "5m",
        "tf-15m": "15m",
        "tf-30m": "30m",
        "tf-1h": "60m",
        "tf-4h": "4h"
    }
    
    # Setze den neuen Zeitrahmen
    new_timeframe = timeframe_map.get(button_id, current_tf)
    
    # Aktualisiere die Button-Klassen basierend auf dem neuen Zeitrahmen
    return update_timeframe_classes(new_timeframe)

def update_timeframe_classes(active_tf):
    # Ordne den Zeitrahmen den Button-IDs zu
    timeframe_map = {
        "1m": "tf-1min",
        "2m": "tf-2min",
        "3m": "tf-3min",
        "5m": "tf-5m",
        "15m": "tf-15m",
        "30m": "tf-30m",
        "60m": "tf-1h",
        "4h": "tf-4h"
    }
    
    # Erstelle die Klassen für jeden Button
    classes = {}
    for tf, button_id in timeframe_map.items():
        if tf == active_tf:
            classes[button_id] = "timeframe-button active"
        else:
            classes[button_id] = "timeframe-button"
    
    return [
        active_tf,
        classes["tf-1min"],
        classes["tf-2min"],
        classes["tf-3min"],
        classes["tf-5m"],
        classes["tf-15m"],
        classes["tf-30m"],
        classes["tf-1h"],
        classes["tf-4h"]
    ]

# Callback für das Abrufen von Daten
@app.callback(
    [Output("stock-data-store", "data"),
     Output("data-info", "children"),
     Output("chart-symbol", "children")],
    [Input("fetch-data-button", "n_clicks")],
    [State("symbol-input", "value"),
     State("active-timeframe-store", "data"),
     State("range-dropdown", "value")]
)
def fetch_data(n_clicks, symbol, timeframe, date_range):
    if n_clicks is None:
        return dash.no_update, dash.no_update, dash.no_update
    
    if not symbol:
        return dash.no_update, "Bitte geben Sie ein Symbol ein", dash.no_update
    
    try:
        # Lade die Daten
        df = load_stock_data(symbol, timeframe, date_range)
        
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
        
        return data, info, symbol
    
    except Exception as e:
        error_msg = f"Fehler beim Laden der Daten: {str(e)}"
        return dash.no_update, error_msg, dash.no_update

# Callback für das Aktualisieren des Charts
@app.callback(
    [Output("price-chart", "figure"),
     Output("chart-indicators", "children")],
    [Input("stock-data-store", "data"),
     Input("toggle-sma", "n_clicks"),
     Input("toggle-bb", "n_clicks"),
     Input("toggle-rsi", "n_clicks"),
     Input("toggle-macd", "n_clicks"),
     Input("toggle-volume", "n_clicks")],
    [State("toggle-sma", "className"),
     State("toggle-bb", "className"),
     State("toggle-rsi", "className"),
     State("toggle-macd", "className"),
     State("toggle-volume", "className")]
)
def update_chart(data, n_sma, n_bb, n_rsi, n_macd, n_volume, 
                cls_sma, cls_bb, cls_rsi, cls_macd, cls_volume):
    if data is None:
        # Erstelle ein leeres Chart
        fig = go.Figure()
        fig.update_layout(
            template="bootstrap",
            paper_bgcolor=colors['card_background'],
            plot_bgcolor=colors['card_background'],
            font=dict(color=colors['text']),
            margin=dict(l=0, r=0, t=0, b=0),
            showlegend=False,
        )
        return fig, ""
    
    # Lade die Daten
    df = pd.read_json(data['df'], orient='split')
    
    # Bestimme, welche Indikatoren angezeigt werden sollen
    show_sma = "active" in cls_sma if cls_sma else False
    show_bb = "active" in cls_bb if cls_bb else False
    show_rsi = "active" in cls_rsi if cls_rsi else False
    show_macd = "active" in cls_macd if cls_macd else False
    show_volume = "active" in cls_volume if cls_volume else True
    
    # Erstelle das Chart
    fig = create_price_chart(df, data['symbol'], show_sma, show_bb, show_volume)
    
    # Füge Indikatoren hinzu
    indicators_html = []
    
    if show_sma:
        sma_values = f"SMA(20): {df['sma_20'].iloc[-1]:.2f}"
        indicators_html.append(
            dbc.Badge(sma_values, color="primary", className="me-1 mb-1")
        )
    
    if show_bb:
        bb_values = f"BB(20,2): {df['bb_upper'].iloc[-1]:.2f} / {df['bb_middle'].iloc[-1]:.2f} / {df['bb_lower'].iloc[-1]:.2f}"
        indicators_html.append(
            dbc.Badge(bb_values, color="info", className="me-1 mb-1")
        )
    
    if show_rsi:
        rsi_value = f"RSI(14): {df['rsi_14'].iloc[-1]:.2f}"
        indicators_html.append(
            dbc.Badge(rsi_value, color="warning", className="me-1 mb-1")
        )
    
    if show_macd:
        macd_values = f"MACD(12,26,9): {df['macd'].iloc[-1]:.2f} / {df['macdsignal'].iloc[-1]:.2f}"
        indicators_html.append(
            dbc.Badge(macd_values, color="danger", className="me-1 mb-1")
        )
    
    return fig, indicators_html

# Callback für den Server-Status
@app.callback(
    Output("server-status", "children"),
    Input("interval-component", "n_intervals")
)
def update_server_status(n):
    return "Server"

# Füge ein Interval-Komponente hinzu, um den Server-Status zu aktualisieren
app.layout.children.append(dcc.Interval(
    id='interval-component',
    interval=30*1000,  # in Millisekunden
    n_intervals=0
))

# Definiere die Strategie-Karte
strategy_card = dbc.Card(
    [
        dbc.CardHeader([
            html.H4("Strategie-Einstellungen", className="card-title mb-0"),
            html.Div([
                DashIconify(icon="mdi:strategy", width=24, color=colors['primary']),
            ], className="float-end")
        ]),
        dbc.CardBody([
            dbc.Form([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Strategie", html_for="strategy-dropdown", className="mb-1"),
                        dbc.InputGroup([
                            dbc.InputGroupText(DashIconify(icon="mdi:chart-timeline-variant", width=18)),
                            dbc.Select(
                                id="strategy-dropdown",
                                options=[
                                    {"label": "Moving Average Crossover", "value": "ma_crossover"},
                                    {"label": "RSI Strategy", "value": "rsi_strategy"},
                                    {"label": "MACD Strategy", "value": "macd_strategy"},
                                    {"label": "Bollinger Bands Strategy", "value": "bb_strategy"},
                                ],
                                value="ma_crossover",
                                className="border-start-0",
                            ),
                        ], className="mb-3"),
                    ]),
                ]),

                dbc.Row([
                    dbc.Col([
                        dbc.Label("Startkapital (€)", html_for="capital-input", className="mb-1"),
                        dbc.InputGroup([
                            dbc.InputGroupText("€"),
                            dbc.Input(
                                id="capital-input",
                                type="number",
                                value=5000,
                                min=1000,
                                step=1000,
                            ),
                        ], className="mb-3"),
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Kommission (%)", html_for="commission-input", className="mb-1"),
                        dbc.InputGroup([
                            dbc.InputGroupText("%"),
                            dbc.Input(
                                id="commission-input",
                                type="number",
                                value=0.1,
                                min=0,
                                max=5,
                                step=0.1,
                            ),
                        ], className="mb-3"),
                    ], width=6),
                ]),

                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            [DashIconify(icon="mdi:play", width=18, className="me-2"), "Backtest durchführen"],
                            id="run-backtest-button",
                            color="success",
                            className="w-100 mb-3",
                        ),
                    ]),
                ]),
            ]),
        ]),
    ],
    className="mb-4 shadow",
    style={"backgroundColor": colors['card_background']},
)

# Starte den Server
if __name__ == "__main__":
    print("Manus API erfolgreich initialisiert")
    print("Starte Trading Dashboard auf http://localhost:8050")
    app.run(debug=True, host="0.0.0.0", port=8050)
