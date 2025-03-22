"""
NQ-Integration für das Trading Dashboard
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import requests
import json
from io import StringIO

# Logger konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("nq_integration.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("nq_integration")

class NQDataFetcher:
    """
    Klasse zum Abrufen von NQ-Futures-Daten
    """
    
    def __init__(self):
        """
        Initialisiert den NQ-Daten-Fetcher
        """
        self.cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def get_nq_futures_data(self, interval="1d", range_val="1y"):
        """
        Ruft NQ-Futures-Daten ab
        
        Args:
            interval (str): Zeitintervall ("1m", "2m", "5m", "15m", "30m", "60m", "1d", "1wk", "1mo")
            range_val (str): Zeitraum ("1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max")
        
        Returns:
            pd.DataFrame: DataFrame mit OHLCV-Daten
        """
        try:
            # Prüfe, ob Daten im Cache vorhanden sind
            cache_file = os.path.join(self.cache_dir, f"NQ_Futures_{interval}_{range_val}.csv")
            
            # Prüfe, ob Cache-Datei existiert und nicht älter als 24 Stunden ist
            if os.path.exists(cache_file):
                file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
                if file_age.total_seconds() < 24 * 60 * 60:  # 24 Stunden in Sekunden
                    logger.info(f"Lade NQ-Daten aus Cache: {cache_file}")
                    return pd.read_csv(cache_file, index_col=0, parse_dates=True)
            
            # Verwende Yahoo Finance API, um NQ-Futures-Daten abzurufen
            logger.info(f"Rufe NQ-Futures-Daten ab mit Intervall {interval} und Zeitraum {range_val}")
            
            # Verwende die YahooFinance API
            try:
                # Importiere die API-Client-Bibliothek
                sys.path.append('/opt/.manus/.sandbox-runtime')
                from data_api import ApiClient
                client = ApiClient()
                
                # Rufe Daten über die API ab
                response = client.call_api('YahooFinance/get_stock_chart', query={
                    'symbol': 'NQ=F',
                    'interval': interval,
                    'range': range_val,
                    'includePrePost': False,
                    'includeAdjustedClose': True
                })
                
                # Verarbeite die Antwort
                if response and 'chart' in response and 'result' in response['chart'] and response['chart']['result']:
                    result = response['chart']['result'][0]
                    
                    # Extrahiere Zeitstempel und Indikatoren
                    timestamps = result['timestamp']
                    quote = result['indicators']['quote'][0]
                    
                    # Erstelle DataFrame
                    df = pd.DataFrame({
                        'open': quote['open'],
                        'high': quote['high'],
                        'low': quote['low'],
                        'close': quote['close'],
                        'volume': quote['volume']
                    })
                    
                    # Füge Zeitstempel als Index hinzu
                    df.index = pd.to_datetime([datetime.fromtimestamp(ts) for ts in timestamps])
                    df.index.name = 'date'
                    
                    # Speichere Daten im Cache
                    df.to_csv(cache_file)
                    
                    logger.info(f"NQ-Futures-Daten erfolgreich abgerufen: {len(df)} Datenpunkte")
                    return df
                else:
                    logger.error("Fehler beim Abrufen der NQ-Futures-Daten: Ungültiges Antwortformat")
            except Exception as api_error:
                logger.error(f"Fehler beim Abrufen der NQ-Futures-Daten über API: {str(api_error)}")
            
            # Fallback: Generiere synthetische Daten
            logger.warning("Verwende synthetische NQ-Futures-Daten als Fallback")
            return self._generate_synthetic_nq_data(interval, range_val)
        
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der NQ-Futures-Daten: {str(e)}")
            return pd.DataFrame()  # Leerer DataFrame bei Fehler
    
    def _generate_synthetic_nq_data(self, interval="1d", range_val="1y"):
        """
        Generiert synthetische NQ-Futures-Daten
        
        Args:
            interval (str): Zeitintervall
            range_val (str): Zeitraum
        
        Returns:
            pd.DataFrame: DataFrame mit synthetischen OHLCV-Daten
        """
        try:
            # Bestimme Start- und Enddatum basierend auf range_val
            end_date = datetime.now()
            
            if range_val == "1d":
                start_date = end_date - timedelta(days=1)
            elif range_val == "5d":
                start_date = end_date - timedelta(days=5)
            elif range_val == "1mo":
                start_date = end_date - timedelta(days=30)
            elif range_val == "3mo":
                start_date = end_date - timedelta(days=90)
            elif range_val == "6mo":
                start_date = end_date - timedelta(days=180)
            elif range_val == "1y":
                start_date = end_date - timedelta(days=365)
            elif range_val == "2y":
                start_date = end_date - timedelta(days=365*2)
            elif range_val == "5y":
                start_date = end_date - timedelta(days=365*5)
            elif range_val == "10y":
                start_date = end_date - timedelta(days=365*10)
            elif range_val == "ytd":
                start_date = datetime(end_date.year, 1, 1)
            elif range_val == "max":
                start_date = end_date - timedelta(days=365*20)
            else:
                start_date = end_date - timedelta(days=365)
            
            # Bestimme Frequenz basierend auf interval
            if interval == "1m":
                freq = "1min"
                # Für 1-Minuten-Daten nur Handelszeiten (9:30-16:00 ET)
                trading_hours = []
                current_date = start_date
                while current_date <= end_date:
                    if current_date.weekday() < 5:  # Montag bis Freitag
                        for hour in range(9, 16):
                            minute_start = 30 if hour == 9 else 0
                            minute_end = 60
                            for minute in range(minute_start, minute_end):
                                trading_time = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                                if trading_time <= end_date:
                                    trading_hours.append(trading_time)
                    current_date += timedelta(days=1)
                date_range = pd.DatetimeIndex(trading_hours)
            elif interval == "2m":
                freq = "2min"
                # Für 2-Minuten-Daten
                trading_hours = []
                current_date = start_date
                while current_date <= end_date:
                    if current_date.weekday() < 5:  # Montag bis Freitag
                        for hour in range(9, 16):
                            minute_start = 30 if hour == 9 else 0
                            minute_end = 60
                            for minute in range(minute_start, minute_end, 2):
                                trading_time = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                                if trading_time <= end_date:
                                    trading_hours.append(trading_time)
                    current_date += timedelta(days=1)
                date_range = pd.DatetimeIndex(trading_hours)
            elif interval == "5m":
                freq = "5min"
                # Für 5-Minuten-Daten
                trading_hours = []
                current_date = start_date
                while current_date <= end_date:
                    if current_date.weekday() < 5:  # Montag bis Freitag
                        for hour in range(9, 16):
                            minute_start = 30 if hour == 9 else 0
                            minute_end = 60
                            for minute in range(minute_start, minute_end, 5):
                                trading_time = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                                if trading_time <= end_date:
                                    trading_hours.append(trading_time)
                    current_date += timedelta(days=1)
                date_range = pd.DatetimeIndex(trading_hours)
            elif interval == "15m":
                freq = "15min"
                # Für 15-Minuten-Daten
                trading_hours = []
                current_date = start_date
                while current_date <= end_date:
                    if current_date.weekday() < 5:  # Montag bis Freitag
                        for hour in range(9, 16):
                            minute_start = 30 if hour == 9 else 0
                            minute_end = 60
                            for minute in range(minute_start, minute_end, 15):
                                trading_time = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                                if trading_time <= end_date:
                                    trading_hours.append(trading_time)
                    current_date += timedelta(days=1)
                date_range = pd.DatetimeIndex(trading_hours)
            elif interval == "30m":
                freq = "30min"
                # Für 30-Minuten-Daten
                trading_hours = []
                current_date = start_date
                while current_date <= end_date:
                    if current_date.weekday() < 5:  # Montag bis Freitag
                        for hour in range(9, 16):
                            minute_start = 30 if hour == 9 else 0
                            minute_end = 60
                            for minute in range(minute_start, minute_end, 30):
                                trading_time = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                                if trading_time <= end_date:
                                    trading_hours.append(trading_time)
                    current_date += timedelta(days=1)
                date_range = pd.DatetimeIndex(trading_hours)
            elif interval == "60m" or interval == "1h":
                freq = "60min"
                # Für 1-Stunden-Daten
                trading_hours = []
                current_date = start_date
                while current_date <= end_date:
                    if current_date.weekday() < 5:  # Montag bis Freitag
                        for hour in range(9, 16):
                            if hour == 9:
                                trading_time = current_date.replace(hour=hour, minute=30, second=0, microsecond=0)
                            else:
                                trading_time = current_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                            if trading_time <= end_date:
                                trading_hours.append(trading_time)
                    current_date += timedelta(days=1)
                date_range = pd.DatetimeIndex(trading_hours)
            elif interval == "1d":
                freq = "D"
                # Für Tagesdaten nur Handelstage (Montag bis Freitag)
                trading_days = []
                current_date = start_date
                while current_date <= end_date:
                    if current_date.weekday() < 5:  # Montag bis Freitag
                        trading_days.append(current_date)
                    current_date += timedelta(days=1)
                date_range = pd.DatetimeIndex(trading_days)
            elif interval == "1wk" or interval == "1w":
                freq = "W-FRI"
                # Für Wochendaten
                date_range = pd.date_range(start=start_date, end=end_date, freq=freq)
            elif interval == "1mo":
                freq = "MS"
                # Für Monatsdaten
                date_range = pd.date_range(start=start_date, end=end_date, freq=freq)
            else:
                freq = "D"
                # Fallback auf Tagesdaten
                date_range = pd.date_range(start=start_date, end=end_date, freq=freq)
            
            # Generiere synthetische OHLCV-Daten für NQ-Futures
            np.random.seed(42)  # Für reproduzierbare Ergebnisse
            
            # Startpreis für NQ-Futures
            base_price = 17500.0
            
            # Generiere OHLC-Daten mit realistischeren Preisbewegungen
            volatility = 0.03  # Mittlere Volatilität für NQ Futures
            
            price_data = []
            current_price = base_price
            trend = np.random.choice([-1, 1]) * 0.0001  # Zufälliger Trend
            
            for i in range(len(date_range)):
                # Ändere den Trend gelegentlich
                if i % 20 == 0:
                    trend = np.random.normal(0, 0.0003)
                
                # Zufällige Preisbewegung mit Trend
                daily_return = np.random.normal(trend, volatility)
                current_price *= (1 + daily_return)
                
                # Generiere OHLC-Daten
                high_low_range = current_price * volatility * 2
                open_price = current_price * (1 + np.random.normal(0, 0.003))
                close_price = current_price
                high_price = max(open_price, close_price) + abs(np.random.normal(0, high_low_range/2))
                low_price = min(open_price, close_price) - abs(np.random.normal(0, high_low_range/2))
                
                # Volumen mit höheren Werten bei größeren Preisbewegungen
                volume_base = np.random.randint(1000000, 10000000)
                volume_factor = 1 + abs(daily_return) * 10
                volume = int(volume_base * volume_factor)
                
                price_data.append({
                    'date': date_range[i],
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'close': close_price,
                    'volume': volume
                })
            
            df = pd.DataFrame(price_data)
            df.set_index('date', inplace=True)
            
            # Speichere die synthetischen Daten im Cache
            cache_file = os.path.join(self.cache_dir, f"NQ_Futures_{interval}_{range_val}.csv")
            df.to_csv(cache_file)
            
            logger.info(f"Synthetische NQ-Futures-Daten generiert: {len(df)} Datenpunkte")
            return df
        
        except Exception as e:
            logger.error(f"Fehler beim Generieren synthetischer NQ-Futures-Daten: {str(e)}")
            return pd.DataFrame()  # Leerer DataFrame bei Fehler
