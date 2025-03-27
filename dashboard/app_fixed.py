import sys
import os
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
from data.data_loader import load_stock_data, validate_symbol, get_alternative_symbols
from dashboard.chart_utils import create_price_chart, create_volume_chart, create_indicator_chart
from dashboard.chart_callbacks import register_chart_callbacks
from dashboard.error_handler import handle_error
