import pandas as pd
import numpy as np
from typing import Optional, Tuple


class TechnicalIndicators:
    @staticmethod
    def simple_moving_average(prices: pd.Series, period: int) -> pd.Series:
        return prices.rolling(window=period).mean()

    @staticmethod
    def exponential_moving_average(prices: pd.Series, period: int) -> pd.Series:
        return prices.ewm(span=period).mean()

    @staticmethod
    def rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def bollinger_bands(prices: pd.Series, period: int = 20, std_dev: int = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        sma = TechnicalIndicators.simple_moving_average(prices, period)
        std = prices.rolling(window=period).std()

        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)

        return upper_band, sma, lower_band

    @staticmethod
    def macd(prices: pd.Series, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        ema_fast = TechnicalIndicators.exponential_moving_average(prices, fast_period)
        ema_slow = TechnicalIndicators.exponential_moving_average(prices, slow_period)

        macd_line = ema_fast - ema_slow
        signal_line = TechnicalIndicators.exponential_moving_average(macd_line, signal_period)
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    @staticmethod
    def stochastic_oscillator(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()

        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()

        return k_percent, d_percent


class TradingSignals:
    def __init__(self, rsi_period: int = 14, sma_short: int = 10, sma_long: int = 20):
        self.rsi_period = rsi_period
        self.sma_short = sma_short
        self.sma_long = sma_long
        self.rsi_oversold = 30
        self.rsi_overbought = 70

    def analyze_price_data(self, data: dict) -> dict:
        if not data or 'close' not in data:
            return {'error': 'Dados de preço insuficientes'}

        close_prices = data['close']

        if len(close_prices) < max(self.sma_long, self.rsi_period):
            return {'error': f'Histórico insuficiente. Necessário pelo menos {max(self.sma_long, self.rsi_period)} períodos'}

        # Calcular indicadores
        rsi = TechnicalIndicators.rsi(close_prices, self.rsi_period)
        sma_short = TechnicalIndicators.simple_moving_average(close_prices, self.sma_short)
        sma_long = TechnicalIndicators.simple_moving_average(close_prices, self.sma_long)

        # Valores atuais
        current_price = close_prices.iloc[-1]
        current_rsi = rsi.iloc[-1]
        current_sma_short = sma_short.iloc[-1]
        current_sma_long = sma_long.iloc[-1]

        # Valores anteriores para detectar cruzamentos
        prev_sma_short = sma_short.iloc[-2] if len(sma_short) > 1 else current_sma_short
        prev_sma_long = sma_long.iloc[-2] if len(sma_long) > 1 else current_sma_long

        analysis = {
            'current_price': current_price,
            'rsi': current_rsi,
            'sma_short': current_sma_short,
            'sma_long': current_sma_long,
            'indicators': {
                'rsi_oversold': current_rsi < self.rsi_oversold,
                'rsi_overbought': current_rsi > self.rsi_overbought,
                'sma_bullish_cross': prev_sma_short <= prev_sma_long and current_sma_short > current_sma_long,
                'sma_bearish_cross': prev_sma_short >= prev_sma_long and current_sma_short < current_sma_long,
                'price_above_sma_short': current_price > current_sma_short,
                'price_above_sma_long': current_price > current_sma_long
            }
        }

        return analysis

    def generate_signal(self, analysis: dict) -> dict:
        if 'error' in analysis:
            return analysis

        indicators = analysis['indicators']

        # Sinais de compra
        buy_signals = []
        if indicators['rsi_oversold']:
            buy_signals.append('RSI_OVERSOLD')
        if indicators['sma_bullish_cross']:
            buy_signals.append('SMA_BULLISH_CROSS')

        # Sinais de venda
        sell_signals = []
        if indicators['rsi_overbought']:
            sell_signals.append('RSI_OVERBOUGHT')
        if indicators['sma_bearish_cross']:
            sell_signals.append('SMA_BEARISH_CROSS')

        # Determinar ação recomendada
        action = 'HOLD'
        confidence = 0.0

        if buy_signals and not sell_signals:
            action = 'BUY'
            confidence = len(buy_signals) * 0.5
        elif sell_signals and not buy_signals:
            action = 'SELL'
            confidence = len(sell_signals) * 0.5
        elif buy_signals and sell_signals:
            action = 'HOLD'
            confidence = 0.0

        # Aumentar confiança baseado na tendência das médias
        if indicators['price_above_sma_short'] and indicators['price_above_sma_long'] and action == 'BUY':
            confidence += 0.2
        elif not indicators['price_above_sma_short'] and not indicators['price_above_sma_long'] and action == 'SELL':
            confidence += 0.2

        confidence = min(confidence, 1.0)

        return {
            'action': action,
            'confidence': confidence,
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'analysis': analysis
        }


class RiskCalculator:
    @staticmethod
    def calculate_position_size(account_balance: float, risk_percentage: float,
                              entry_price: float, stop_loss_price: float) -> float:
        risk_amount = account_balance * (risk_percentage / 100)
        risk_per_unit = abs(entry_price - stop_loss_price)

        if risk_per_unit == 0:
            return 0

        position_size = risk_amount / risk_per_unit
        return position_size

    @staticmethod
    def calculate_stop_loss(entry_price: float, atr: float, multiplier: float = 2.0, side: str = 'BUY') -> float:
        if side.upper() == 'BUY':
            return entry_price - (atr * multiplier)
        else:
            return entry_price + (atr * multiplier)

    @staticmethod
    def calculate_take_profit(entry_price: float, stop_loss_price: float,
                            risk_reward_ratio: float = 2.0, side: str = 'BUY') -> float:
        risk = abs(entry_price - stop_loss_price)

        if side.upper() == 'BUY':
            return entry_price + (risk * risk_reward_ratio)
        else:
            return entry_price - (risk * risk_reward_ratio)

    @staticmethod
    def calculate_profit_loss(entry_price: float, current_price: float,
                            quantity: float, side: str = 'BUY', trading_fee_pct: float = 0.035) -> float:
        """
        Calcular PnL real descontando as taxas de trading

        Args:
            entry_price: Preço de entrada
            current_price: Preço atual/saída
            quantity: Quantidade da posição
            side: 'BUY' para long, 'SELL' para short
            trading_fee_pct: Taxa de trading em % (padrão 0.035%)

        Returns:
            PnL líquido após descontar taxas de abertura e fechamento
        """
        # Calcular PnL bruto
        if side.upper() == 'BUY':
            gross_pnl = (current_price - entry_price) * quantity
        else:
            gross_pnl = (entry_price - current_price) * quantity

        # Calcular taxas
        # Taxa de abertura: trading_fee_pct sobre valor da entrada
        entry_value = entry_price * quantity
        entry_fee = entry_value * (trading_fee_pct / 100)

        # Taxa de fechamento: trading_fee_pct sobre valor da saída
        exit_value = current_price * quantity
        exit_fee = exit_value * (trading_fee_pct / 100)

        # PnL líquido = PnL bruto - taxas de abertura - taxas de fechamento
        net_pnl = gross_pnl - entry_fee - exit_fee

        return net_pnl