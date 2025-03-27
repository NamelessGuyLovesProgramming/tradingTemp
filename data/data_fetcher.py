"""
Unified Data Fetcher Module für Trading Dashboard
Optimierte Version mit integrierten Funktionen aus verschiedenen Datenquellen
"""

import os
import sys
import pandas as pd
import numpy as np
import yfinance as yf
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Union, Dict, List, Tuple, Any

# Konfiguriere Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Versuche, die Manus API zu importieren, falls verfügbar
try:
    sys.path.append('/opt/.manus/.sandbox-runtime')
    from data_api import ApiClient

    # Teste, ob die API tatsächlich funktioniert
    try:
        client = ApiClient()
        test_response = client.call_api('YahooFinance/get_stock_chart', query={
            'symbol': 'AAPL',
            'interval': '1d',
            'range': '5d'
        })
        if test_response and 'chart' in test_response:
            API_AVAILABLE = True
            logger.info("Manus API erfolgreich initialisiert")
        else:
            API_AVAILABLE = False
            logger.warning("Manus API verfügbar, aber Testanfrage fehlgeschlagen. Verwende yfinance als Fallback")
    except Exception as e:
        API_AVAILABLE = False
        logger.warning(f"Manus API-Test fehlgeschlagen: {e}. Verwende yfinance als Fallback")
except ImportError:
    API_AVAILABLE = False
    logger.info("Manus API nicht verfügbar, verwende yfinance als Fallback")

class DataFetcher:
    """
    Optimierte Klasse zum Abrufen und Verwalten von Handelsdaten
    Kombiniert Funktionalität aus verschiedenen Datenquellen
    """
    def __init__(self, cache_dir=None):
        """
        Initialisiert den DataFetcher

        Args:
            cache_dir (str, optional): Verzeichnis für den Daten-Cache
        """
        if cache_dir is None:
            self.cache_dir = Path(os.path.dirname(os.path.abspath(__file__))) / 'cache'
        else:
            self.cache_dir = Path(cache_dir)

        # Stelle sicher, dass das Cache-Verzeichnis existiert
        os.makedirs(self.cache_dir, exist_ok=True)

        # Initialisiere API-Client, wenn verfügbar
        if API_AVAILABLE:
            self.client = ApiClient()

        # Konstanten für Fallback und Wiederholungsversuche
        self.max_retries = 3
        self.retry_delay = 2  # Sekunden
        self.fallback_symbols = {
            'NQ': ['NQ=F', 'QQQ'],  # Fallback-Symbole für Nasdaq
            'QQQ': ['QQQ', 'QQQM', 'TQQQ'],  # Fallback-Symbole für QQQ
        }

    def get_stock_data(self, symbol: str, interval: str = '1d', range_val: str = '1y',
                      use_cache: bool = True, force_refresh: bool = False) -> pd.DataFrame:
        """
        Ruft Aktiendaten für ein bestimmtes Symbol ab

        Args:
            symbol: Das Aktiensymbol (z.B. 'AAPL')
            interval: Zeitintervall ('1m', '2m', '5m', '15m', '30m', '60m', '1h', '1d', '1wk', '1mo')
            range_val: Zeitraum ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            use_cache: Ob der Cache verwendet werden soll
            force_refresh: Ob die Daten unabhängig vom Cache neu abgerufen werden sollen

        Returns:
            pandas.DataFrame: DataFrame mit den Aktiendaten
        """
        # Spezialbehandlung für NQ Futures
        if symbol.upper() in ['NQ', 'NQ=F']:
            return self.get_nq_futures_data(interval, range_val, use_cache, force_refresh)

        cache_file = self.cache_dir / f"{symbol}_{interval}_{range_val}.csv"

        # Prüfe, ob Cache verwendet werden soll und Datei existiert
        if use_cache and cache_file.exists() and not force_refresh:
            cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if interval in ['1d', '1wk', '1mo'] and cache_age.days < 1:
                logger.info(f"Verwende gecachte Daten für {symbol}")
                return pd.read_csv(cache_file, index_col=0, parse_dates=True)
            elif interval.endswith('m') and cache_age.seconds < 3600:  # Für Minutendaten: 1 Stunde Cache
                logger.info(f"Verwende gecachte Daten für {symbol}")
                return pd.read_csv(cache_file, index_col=0, parse_dates=True)

        # Daten abrufen
        # Erste Priorität: Manus API, wenn verfügbar
        if API_AVAILABLE:
            try:
                data = self._fetch_data_from_api(symbol, interval, range_val)
                if data is not None and not data.empty:
                    # Speichere Daten im Cache
                    if use_cache:
                        data.to_csv(cache_file)
                    return data
            except Exception as e:
                logger.error(f"Fehler beim Abrufen der Daten über API: {e}")
                logger.info("Verwende yfinance als Fallback...")

        # Zweite Priorität: yfinance mit Fallbacks
        symbols_to_try = [symbol]

        # Füge Fallback-Symbole hinzu, wenn verfügbar
        if symbol in self.fallback_symbols:
            symbols_to_try = self.fallback_symbols[symbol]
            if symbol not in symbols_to_try:
                symbols_to_try.insert(0, symbol)

        # Versuche, Daten für jedes Symbol zu laden
        for current_symbol in symbols_to_try:
            logger.info(f"Versuche, Daten für Symbol {current_symbol} zu laden...")

            for attempt in range(self.max_retries):
                try:
                    data = self._fetch_data_from_yfinance(current_symbol, interval, range_val)

                    # Überprüfe, ob Daten zurückgegeben wurden
                    if data.empty:
                        logger.warning(f"Keine Daten für {current_symbol} gefunden (Versuch {attempt+1}/{self.max_retries})")
                        if attempt < self.max_retries - 1:
                            time.sleep(self.retry_delay)
                            continue
                    else:
                        # Daten erfolgreich geladen
                        logger.info(f"Daten für {current_symbol} erfolgreich geladen: {len(data)} Einträge")

                        # Füge technische Indikatoren hinzu
                        data = self.add_technical_indicators(data)

                        # Speichere Daten im Cache
                        if use_cache:
                            data.to_csv(cache_file)

                        return data

                except Exception as e:
                    logger.error(f"Fehler beim Laden von {current_symbol} (Versuch {attempt+1}/{self.max_retries}): {str(e)}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)

        # Wenn alle Versuche fehlschlagen, erstelle einen leeren DataFrame mit der richtigen Struktur
        logger.error(f"Konnte keine Daten für {symbol} oder Fallback-Symbole laden")
        return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Splits'])

    def _fetch_data_from_api(self, symbol: str, interval: str, range_val: str) -> pd.DataFrame:
        """
        Ruft Daten über die Manus API ab
        """
        try:
            # Verwende die YahooFinance API über den Manus API-Client
            response = self.client.call_api('YahooFinance/get_stock_chart', query={
                'symbol': symbol,
                'interval': interval,
                'range': range_val,
                'includeAdjustedClose': True
            })

            if response and 'chart' in response and 'result' in response['chart'] and response['chart']['result']:
                result = response['chart']['result'][0]

                # Extrahiere Zeitstempel und Indikatoren
                timestamps = result.get('timestamp', [])
                indicators = result.get('indicators', {})

                # Extrahiere Preisdaten
                quote = indicators.get('quote', [{}])[0]
                adjclose = indicators.get('adjclose', [{}])[0].get('adjclose', [])

                # Erstelle DataFrame
                data = {
                    'Open': quote.get('open', []),
                    'High': quote.get('high', []),
                    'Low': quote.get('low', []),
                    'Close': quote.get('close', []),
                    'Volume': quote.get('volume', []),
                    'Adj Close': adjclose
                }

                # Konvertiere Zeitstempel zu Datetime
                # Behebe das tzinfo-Problem durch explizite Konvertierung ohne Zeitzoneninformation
                index = pd.to_datetime([datetime.fromtimestamp(ts).replace(tzinfo=None) for ts in timestamps])

                # Erstelle DataFrame und entferne Zeilen mit NaN-Werten
                df = pd.DataFrame(data, index=index).dropna()

                return df

            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Daten über API: {e}")
            return pd.DataFrame()

    def _fetch_data_from_yfinance(self, symbol: str, interval: str, range_val: str) -> pd.DataFrame:
        """
        Ruft Daten über yfinance ab (Fallback)
        """
        try:
            # Konvertiere Intervall für yfinance (1h statt 60m)
            yf_interval = '1h' if interval == '60m' else interval

            # Verwende yfinance als Fallback
            ticker = yf.Ticker(symbol)

            # Rufe Historiendaten ab
            df = ticker.history(period=range_val, interval=yf_interval)

            # Wenn keine Daten zurückgegeben wurden, versuche es mit einem anderen Ansatz
            if df.empty:
                logger.info(f"Keine Daten für {symbol} mit period={range_val}, interval={yf_interval}. Versuche direkten Download...")
                # Bestimme das Startdatum basierend auf dem angegebenen Bereich
                end_date = datetime.now()

                # Bestimme das Startdatum basierend auf dem angegebenen Bereich
                if range_val == '1d':
                    start_date = end_date - timedelta(days=1)
                elif range_val == '5d':
                    start_date = end_date - timedelta(days=5)
                elif range_val == '1mo':
                    start_date = end_date - timedelta(days=30)
                elif range_val == '3mo':
                    start_date = end_date - timedelta(days=90)
                elif range_val == '6mo':
                    start_date = end_date - timedelta(days=180)
                elif range_val == '1y':
                    start_date = end_date - timedelta(days=365)
                elif range_val == '2y':
                    start_date = end_date - timedelta(days=730)
                elif range_val == '5y':
                    start_date = end_date - timedelta(days=1825)
                elif range_val == '10y':
                    start_date = end_date - timedelta(days=3650)
                elif range_val == 'ytd':
                    start_date = datetime(end_date.year, 1, 1)
                else:  # 'max'
                    start_date = end_date - timedelta(days=3650)  # Default to 10 years

                # Formatiere Daten für yfinance
                start_str = start_date.strftime('%Y-%m-%d')
                end_str = end_date.strftime('%Y-%m-%d')

                # Versuche den direkten Download
                df = yf.download(symbol, start=start_str, end=end_str, interval=yf_interval, progress=False)

            # Standardisiere Spaltennamen und stelle sicher, dass sie großgeschrieben sind
            if not df.empty:
                # Benenne die Spalten um, falls sie kleingeschrieben sind
                column_mapping = {col: col.title() for col in df.columns}
                df = df.rename(columns=column_mapping)

                # Stelle sicher, dass die Grundspalten vorhanden sind
                required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                for col in required_columns:
                    if col not in df.columns:
                        df[col] = np.nan

                # Standardisiere die Namen der Splits- und Dividendenspalten
                if 'Stock Splits' in df.columns:
                    df = df.rename(columns={'Stock Splits': 'Splits'})
                elif 'Splits' not in df.columns:
                    df['Splits'] = 0.0

                if 'Dividends' not in df.columns:
                    df['Dividends'] = 0.0

                # Füge Adj Close hinzu, falls es fehlt
                if 'Adj Close' not in df.columns and 'Close' in df.columns:
                    df['Adj Close'] = df['Close']

            return df

        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Daten über yfinance: {e}")
            # Erstelle einen leeren DataFrame mit den erwarteten Spalten
            return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close', 'Dividends', 'Splits'])

    def get_multiple_stocks(self, symbols: List[str], interval: str = '1d', range_val: str = '1y',
                           use_cache: bool = True) -> Dict[str, pd.DataFrame]:
        """
        Ruft Daten für mehrere Aktien ab

        Args:
            symbols: Liste von Aktiensymbolen
            interval: Zeitintervall
            range_val: Zeitraum
            use_cache: Ob der Cache verwendet werden soll

        Returns:
            Dict[str, pd.DataFrame]: Dictionary mit Symbol als Schlüssel und DataFrame als Wert
        """
        result = {}
        for symbol in symbols:
            result[symbol] = self.get_stock_data(symbol, interval, range_val, use_cache)
        return result

    def get_technical_indicators(self, symbol: str, interval: str = '1d', range_val: str = '1y') -> Dict[str, Any]:
        """
        Ruft technische Indikatoren für ein Symbol ab

        Args:
            symbol: Das Aktiensymbol
            interval: Zeitintervall
            range_val: Zeitraum

        Returns:
            Dict[str, Any]: Dictionary mit technischen Indikatoren
        """
        if not API_AVAILABLE:
            logger.warning("Technische Indikatoren sind nur über die Manus API verfügbar")
            return {}

        try:
            # Verwende die YahooFinance API über den Manus API-Client
            response = self.client.call_api('YahooFinance/get_stock_insights', query={
                'symbol': symbol
            })

            if response and 'finance' in response and 'result' in response['finance']:
                result = response['finance']['result']

                # Extrahiere technische Indikatoren
                if 'instrumentInfo' in result and 'technicalEvents' in result['instrumentInfo']:
                    return result['instrumentInfo']['technicalEvents']

                # Extrahiere Stop-Loss und Widerstand
                if 'instrumentInfo' in result and 'keyTechnicals' in result['instrumentInfo']:
                    return result['instrumentInfo']['keyTechnicals']

            return {}

        except Exception as e:
            logger.error(f"Fehler beim Abrufen der technischen Indikatoren: {e}")
            return {}

    def get_nq_futures_data(self, interval: str = '1d', range_val: str = '1y',
                           use_cache: bool = True, force_refresh: bool = False) -> pd.DataFrame:
        """
        Ruft NQ Futures Daten für ein bestimmtes Zeitintervall ab

        Args:
            interval: Zeitintervall
            range_val: Zeitraum
            use_cache: Ob der Cache verwendet werden soll
            force_refresh: Ob die Daten unabhängig vom Cache neu abgerufen werden sollen

        Returns:
            pd.DataFrame: DataFrame mit NQ Futures Daten
        """
        # Standardmäßig verwenden wir das generische NQ Futures Symbol
        symbol = "NQ=F"

        cache_file = self.cache_dir / f"NQ_Futures_{interval}_{range_val}.csv"

        # Prüfe, ob Cache verwendet werden soll und Datei existiert
        if use_cache and cache_file.exists() and not force_refresh:
            cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if interval in ['1d', '1wk', '1mo'] and cache_age.days < 1:
                logger.info("Verwende gecachte NQ Futures Daten")
                return pd.read_csv(cache_file, index_col=0, parse_dates=True)
            elif interval.endswith('m') and cache_age.seconds < 3600:  # Für Minutendaten: 1 Stunde Cache
                logger.info("Verwende gecachte NQ Futures Daten")
                return pd.read_csv(cache_file, index_col=0, parse_dates=True)

        # Versuche Daten über yfinance zu laden
        logger.info("Rufe NQ Futures Daten über yfinance ab...")
        try:
            df = self._fetch_data_from_yfinance(symbol, interval, range_val)

            if not df.empty:
                # Speichere Daten im Cache
                if use_cache:
                    df.to_csv(cache_file)
                logger.info(f"Erfolgreich NQ Futures Daten abgerufen, {len(df)} Datenpunkte")
                return df
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der NQ Futures Daten über yfinance: {e}")

        # Wenn yfinance fehlschlägt, versuche über die Manus API
        if API_AVAILABLE:
            try:
                logger.info("Versuche NQ Futures Daten über Manus API abzurufen...")
                df = self._fetch_data_from_api(symbol, interval, range_val)

                if not df.empty:
                    # Speichere Daten im Cache
                    if use_cache:
                        df.to_csv(cache_file)
                    logger.info(f"Erfolgreich NQ Futures Daten über API abgerufen, {len(df)} Datenpunkte")
                    return df
            except Exception as e:
                logger.error(f"Fehler beim Abrufen der NQ Futures Daten über API: {e}")

        # Wenn alle Versuche fehlschlagen, erstelle einen leeren DataFrame
        logger.error("Alle Versuche, NQ Futures Daten abzurufen, sind fehlgeschlagen.")
        return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close'])

    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fügt technische Indikatoren zu einem DataFrame hinzu

        Args:
            df: DataFrame mit OHLCV-Daten

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
                    return df

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

    def validate_symbol(self, symbol: str) -> bool:
        """
        Überprüft, ob ein Symbol gültig ist

        Args:
            symbol: Das zu überprüfende Symbol

        Returns:
            bool: True, wenn das Symbol gültig ist, sonst False
        """
        try:
            # Versuche, Daten für das Symbol abzurufen (Minimal-Anfrage)
            df = self.get_stock_data(symbol, interval='1d', range_val='5d', use_cache=False)
            return not df.empty
        except:
            return False

    def get_alternative_symbols(self, symbol_type: str) -> List[str]:
        """
        Gibt alternative Symbole für einen bestimmten Typ zurück

        Args:
            symbol_type: Der Symboltyp (z.B. 'nasdaq', 'sp500')

        Returns:
            List[str]: Liste von alternativen Symbolen
        """
        alternatives = {
            'nasdaq': ['QQQ', 'ONEQ', 'QQQM', 'TQQQ', 'NQ=F'],
            'sp500': ['SPY', 'VOO', 'IVV', 'SPLG', 'ES=F'],
            'dow': ['DIA', 'DDM', 'UDOW', 'YM=F'],
            'russell': ['IWM', 'VTWO', 'URTY', 'TF=F']
        }

        return alternatives.get(symbol_type.lower(), [])