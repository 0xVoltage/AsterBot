import pandas as pd
import time
from typing import Dict, List, Any, Optional
from .client import AsterDexClient
import logging


class MarketDataCollector:
    def __init__(self, client: AsterDexClient, symbol: str):
        self.client = client
        self.symbol = symbol
        self.price_history = pd.DataFrame()
        self.last_update = 0
        self.update_interval = 1  # segundos
        self.logger = logging.getLogger(__name__)

    def get_current_price(self) -> Optional[float]:
        try:
            ticker = self.client.get_24hr_ticker(self.symbol)
            if isinstance(ticker, list):
                ticker = ticker[0]
            return float(ticker.get('lastPrice', 0))
        except Exception as e:
            self.logger.error(f"Erro ao obter preço atual: {e}")
            return None

    def get_orderbook(self, limit: int = 10) -> Optional[Dict[str, Any]]:
        try:
            return self.client.get_orderbook(self.symbol, limit)
        except Exception as e:
            self.logger.error(f"Erro ao obter orderbook: {e}")
            return None

    def get_klines_data(self, interval: str = '1m', limit: int = 100) -> Optional[pd.DataFrame]:
        try:
            klines = self.client.get_klines(self.symbol, interval, limit)

            if not klines:
                return None

            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])

            # Converter tipos de dados
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)

            return df[numeric_columns]

        except Exception as e:
            self.logger.error(f"Erro ao obter dados de klines: {e}")
            return None

    def update_price_history(self, interval: str = '1m', limit: int = 100):
        current_time = time.time()

        if current_time - self.last_update < self.update_interval:
            return

        try:
            new_data = self.get_klines_data(interval, limit)
            if new_data is not None and not new_data.empty:
                self.price_history = new_data
                self.last_update = current_time
                self.logger.info(f"Dados de preço atualizados para {self.symbol}")
        except Exception as e:
            self.logger.error(f"Erro ao atualizar histórico de preços: {e}")

    def get_latest_prices(self, count: int = 20) -> Optional[pd.Series]:
        if self.price_history.empty:
            self.update_price_history()

        if not self.price_history.empty:
            return self.price_history['close'].tail(count)
        return None

    def get_price_data_for_indicators(self, period: int = 50) -> Optional[Dict[str, pd.Series]]:
        if self.price_history.empty:
            self.update_price_history()

        if len(self.price_history) < period:
            self.update_price_history(limit=period + 20)

        if len(self.price_history) >= period:
            data = self.price_history.tail(period)
            return {
                'close': data['close'],
                'high': data['high'],
                'low': data['low'],
                'volume': data['volume']
            }
        return None

    def get_market_info(self) -> Dict[str, Any]:
        try:
            current_price = self.get_current_price()
            orderbook = self.get_orderbook(5)

            info = {
                'symbol': self.symbol,
                'current_price': current_price,
                'timestamp': time.time()
            }

            if orderbook:
                bids = orderbook.get('bids', [])
                asks = orderbook.get('asks', [])

                if bids and asks:
                    info.update({
                        'best_bid': float(bids[0][0]) if bids else None,
                        'best_ask': float(asks[0][0]) if asks else None,
                        'spread': float(asks[0][0]) - float(bids[0][0]) if bids and asks else None
                    })

            return info

        except Exception as e:
            self.logger.error(f"Erro ao obter informações de mercado: {e}")
            return {'symbol': self.symbol, 'error': str(e)}


class MultiSymbolDataCollector:
    def __init__(self, client: AsterDexClient, symbols: List[str]):
        self.client = client
        self.symbols = symbols
        self.collectors = {}
        self.logger = logging.getLogger(__name__)

        for symbol in symbols:
            self.collectors[symbol] = MarketDataCollector(client, symbol)

    def update_all_data(self):
        for symbol, collector in self.collectors.items():
            try:
                collector.update_price_history()
            except Exception as e:
                self.logger.error(f"Erro ao atualizar dados para {symbol}: {e}")

    def get_all_current_prices(self) -> Dict[str, float]:
        prices = {}
        for symbol, collector in self.collectors.items():
            price = collector.get_current_price()
            if price is not None:
                prices[symbol] = price
        return prices

    def get_collector(self, symbol: str) -> Optional[MarketDataCollector]:
        return self.collectors.get(symbol)