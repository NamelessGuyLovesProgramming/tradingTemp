import pandas as pd
import numpy as np
import yfinance as yf
import logging
import time
from datetime import datetime, timedelta

# Konfiguriere Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Konstanten für Fallback und Wiederholungsversuche
MAX_RETRIES = 3
RETRY_DELAY = 2  # Sekunden
FALLBACK_SYMBOLS = {
    'NQ': ['NQ=F', 'QQQ'],  # Fallback-Symbole für Nasdaq
    'QQQ': ['QQQ', 'QQQM', 'TQQQ'],  # Fallback-Symbole für QQQ
}

def load_stock_data(symbol, timeframe, date_range):
    """
    Lädt Aktiendaten von Yahoo Finance mit verbesserter Fehlerbehandlung
    
    Args:
        symbol (str): Das Aktiensymbol (z.B. 'AAPL')
        timeframe (str): Der Zeitrahmen ('1m', '5m', '15m', '30m', '60m', '1h', '4h', '1d')
        date_range (str): Der Datumsbereich ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max')
        
    Returns:
        tuple: (pd.DataFrame, str) - DataFrame mit den Aktiendaten und Status-Nachricht
    """
    # Konvertiere Zeitrahmen in yfinance-Format
    if timeframe == '60m' or timeframe == '1h':
        interval = '1h'
    else:
        interval = timeframe
    
    # Initialisiere Variablen
    data = None
    status_message = ""
    symbols_to_try = [symbol]
    
    # Füge Fallback-Symbole hinzu, wenn verfügbar
    if symbol in FALLBACK_SYMBOLS:
        symbols_to_try = FALLBACK_SYMBOLS[symbol]
        if symbol not in symbols_to_try:
            symbols_to_try.insert(0, symbol)
    
    # Versuche, Daten für jedes Symbol zu laden
    for current_symbol in symbols_to_try:
        logger.info(f"Versuche, Daten für Symbol {current_symbol} zu laden...")
        
        for attempt in range(MAX_RETRIES):
            try:
                # Lade die Daten
                data = yf.download(
                    current_symbol,
                    period=date_range,
                    interval=interval,
                    auto_adjust=True,
                    progress=False
                )
                
                # Überprüfe, ob Daten zurückgegeben wurden
                if data.empty:
                    logger.warning(f"Keine Daten für {current_symbol} gefunden (Versuch {attempt+1}/{MAX_RETRIES})")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY)
                        continue
                else:
                    # Daten erfolgreich geladen
                    logger.info(f"Daten für {current_symbol} erfolgreich geladen: {len(data)} Einträge")
                    status_message = f"Daten für {current_symbol} erfolgreich geladen"
                    
                    # Füge technische Indikatoren hinzu
                    try:
                        data = add_technical_indicators(data)
                        return data, status_message
                    except Exception as e:
                        logger.error(f"Fehler beim Hinzufügen von Indikatoren: {str(e)}")
                        status_message = f"Fehler beim Hinzufügen von Indikatoren: {str(e)}"
                        return data, status_message
            
            except Exception as e:
                logger.error(f"Fehler beim Laden von {current_symbol} (Versuch {attempt+1}/{MAX_RETRIES}): {str(e)}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                    continue
    
    # Wenn wir hier ankommen, konnten keine Daten geladen werden
    if data is None or data.empty:
        logger.error(f"Konnte keine Daten für {symbol} oder Fallback-Symbole laden")
        status_message = f"Keine Daten für {symbol} gefunden. Bitte überprüfen Sie das Symbol oder versuchen Sie es später erneut."
        # Erstelle einen leeren DataFrame mit der richtigen Struktur
        data = create_empty_dataframe()
    
    return data, status_message

def create_empty_dataframe():
    """
    Erstellt einen leeren DataFrame mit der richtigen Struktur für Fehlerszenarien
    
    Returns:
        pd.DataFrame: Leerer DataFrame mit OHLCV-Struktur
    """
    # Erstelle einen leeren DataFrame mit den erforderlichen Spalten
    columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Splits']
    df = pd.DataFrame(columns=columns)
    
    # Setze den Index als DatetimeIndex
    df.index = pd.DatetimeIndex([])
    
    return df

def add_technical_indicators(df):
    """
    Fügt technische Indikatoren zum DataFrame hinzu mit verbesserter Fehlerbehandlung
    
    Args:
        df (pd.DataFrame): DataFrame mit OHLCV-Daten
        
    Returns:
        pd.DataFrame: DataFrame mit hinzugefügten Indikatoren
    """
    try:
        # Überprüfe, ob der DataFrame leer ist
        if df.empty:
            logger.warning("Leerer DataFrame, keine Indikatoren hinzugefügt")
            return df
        
        # Überprüfe, ob die erforderlichen Spalten vorhanden sind
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_columns:
            if col not in df.columns:
                logger.error(f"Spalte {col} fehlt im DataFrame")
                raise ValueError(f"Spalte {col} fehlt im DataFrame")
        
        # Kopiere den DataFrame, um Warnungen zu vermeiden
        df = df.copy()
        
        # Berechne SMA
        df['sma_20'] = df['Close'].rolling(window=20).mean()
        df['sma_50'] = df['Close'].rolling(window=50).mean()
        df['sma_200'] = df['Close'].rolling(window=200).mean()
        
        # Berechne Bollinger Bands
        df['bb_middle'] = df['sma_20']
        df['bb_std'] = df['Close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + 2 * df['bb_std']
        df['bb_lower'] = df['bb_middle'] - 2 * df['bb_std']
        
        # Berechne RSI mit Fehlerbehandlung
        try:
            delta = df['Close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            
            # Vermeide Division durch Null
            avg_loss = avg_loss.replace(0, np.nan)
            rs = avg_gain / avg_loss
            df['rsi_14'] = 100 - (100 / (1 + rs))
        except Exception as e:
            logger.warning(f"Fehler bei RSI-Berechnung: {str(e)}")
            df['rsi_14'] = np.nan
        
        # Berechne MACD
        try:
            ema_12 = df['Close'].ewm(span=12, adjust=False).mean()
            ema_26 = df['Close'].ewm(span=26, adjust=False).mean()
            df['macd'] = ema_12 - ema_26
            df['macdsignal'] = df['macd'].ewm(span=9, adjust=False).mean()
            df['macdhist'] = df['macd'] - df['macdsignal']
        except Exception as e:
            logger.warning(f"Fehler bei MACD-Berechnung: {str(e)}")
            df['macd'] = np.nan
            df['macdsignal'] = np.nan
            df['macdhist'] = np.nan
        
        # Fülle NaN-Werte
        df = df.fillna(method='ffill').fillna(method='bfill').fillna(0)
        
        return df
    
    except Exception as e:
        logger.error(f"Fehler beim Hinzufügen von Indikatoren: {str(e)}")
        # Gib den ursprünglichen DataFrame zurück, wenn ein Fehler auftritt
        return df

def get_symbol_info(symbol):
    """
    Holt Informationen zu einem Symbol
    
    Args:
        symbol (str): Das Aktiensymbol
        
    Returns:
        dict: Informationen zum Symbol oder None bei Fehler
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return info
    except Exception as e:
        logger.error(f"Fehler beim Abrufen von Informationen für {symbol}: {str(e)}")
        return None

def validate_symbol(symbol):
    """
    Überprüft, ob ein Symbol gültig ist
    
    Args:
        symbol (str): Das zu überprüfende Symbol
        
    Returns:
        bool: True, wenn das Symbol gültig ist, sonst False
    """
    try:
        info = get_symbol_info(symbol)
        if info and 'regularMarketPrice' in info and info['regularMarketPrice'] is not None:
            return True
        return False
    except:
        return False

def get_alternative_symbols(symbol_type):
    """
    Gibt alternative Symbole für einen bestimmten Typ zurück
    
    Args:
        symbol_type (str): Der Symboltyp (z.B. 'nasdaq', 'sp500')
        
    Returns:
        list: Liste von alternativen Symbolen
    """
    alternatives = {
        'nasdaq': ['QQQ', 'ONEQ', 'QQQM', 'TQQQ', 'NQ=F'],
        'sp500': ['SPY', 'VOO', 'IVV', 'SPLG', 'ES=F'],
        'dow': ['DIA', 'DDM', 'UDOW', 'YM=F'],
        'russell': ['IWM', 'VTWO', 'URTY', 'TF=F']
    }
    
    return alternatives.get(symbol_type.lower(), [])
