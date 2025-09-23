"""
Symbol precision utility for handling different cryptocurrency precision requirements.
Solves API Error 400: "Precision is over the maximum defined for this asset" for XRP, BNB, DOGE, etc.
"""

from typing import Dict, Any, Optional
import logging
from ..api.client import AsterDexClient


class SymbolPrecisionManager:
    """Manages symbol-specific precision data from exchange info"""

    def __init__(self, client: AsterDexClient):
        self.client = client
        self.logger = logging.getLogger(__name__)
        self._precision_cache: Dict[str, Dict[str, float]] = {}

    def get_symbol_precision(self, symbol: str) -> Dict[str, float]:
        """
        Get precision data for a symbol
        Returns: {'step_size': float, 'min_qty': float, 'min_notional': float}
        """
        if symbol in self._precision_cache:
            return self._precision_cache[symbol]

        try:
            exchange_info = self.client.get_exchange_info()
            symbols = exchange_info.get('symbols', [])

            for symbol_info in symbols:
                if symbol_info.get('symbol') == symbol:
                    precision_data = self._extract_precision_data(symbol_info)
                    self._precision_cache[symbol] = precision_data
                    return precision_data

            # Symbol not found
            self.logger.warning(f"Symbol {symbol} not found in exchange info")
            return self._get_default_precision()

        except Exception as e:
            self.logger.error(f"Error fetching precision for {symbol}: {e}")
            return self._get_default_precision()

    def _extract_precision_data(self, symbol_info: Dict[str, Any]) -> Dict[str, float]:
        """Extract precision data from symbol info"""
        precision = {
            'step_size': 0.001,  # Default for BTC
            'min_qty': 0.001,
            'min_notional': 5.0
        }

        filters = symbol_info.get('filters', [])
        for filter_info in filters:
            filter_type = filter_info.get('filterType')

            if filter_type == 'LOT_SIZE':
                precision['step_size'] = float(filter_info.get('stepSize', '0.001'))
                precision['min_qty'] = float(filter_info.get('minQty', '0.001'))

            elif filter_type == 'MIN_NOTIONAL':
                precision['min_notional'] = float(filter_info.get('notional', '5.0'))

        return precision

    def _get_default_precision(self) -> Dict[str, float]:
        """Return safe default precision values"""
        return {
            'step_size': 0.001,
            'min_qty': 0.001,
            'min_notional': 5.0
        }

    def round_quantity(self, symbol: str, quantity: float) -> float:
        """Round quantity to symbol's step size"""
        precision = self.get_symbol_precision(symbol)
        step_size = precision['step_size']

        # Round down to respect precision limits
        rounded = int(quantity / step_size) * step_size

        # Ensure it meets minimum quantity
        min_qty = precision['min_qty']
        if rounded < min_qty:
            rounded = min_qty

        return rounded

    def validate_order_size(self, symbol: str, quantity: float, price: float) -> bool:
        """Validate if order meets exchange requirements"""
        precision = self.get_symbol_precision(symbol)

        # Check minimum quantity
        if quantity < precision['min_qty']:
            self.logger.warning(f"Quantity {quantity} below minimum {precision['min_qty']} for {symbol}")
            return False

        # Check minimum notional value
        notional_value = quantity * price
        if notional_value < precision['min_notional']:
            self.logger.warning(f"Order value {notional_value} below minimum {precision['min_notional']} for {symbol}")
            return False

        return True

    def get_common_precisions(self) -> Dict[str, Dict[str, float]]:
        """Get common cryptocurrency precisions for quick reference"""
        return {
            'BTCUSDT': {'step_size': 0.001, 'min_qty': 0.001, 'min_notional': 5.0},
            'ETHUSDT': {'step_size': 0.001, 'min_qty': 0.001, 'min_notional': 5.0},
            'XRPUSDT': {'step_size': 1.0, 'min_qty': 1.0, 'min_notional': 5.0},
            'BNBUSDT': {'step_size': 0.01, 'min_qty': 0.01, 'min_notional': 5.0},
            'DOGEUSDT': {'step_size': 1.0, 'min_qty': 1.0, 'min_notional': 5.0},
            'ADAUSDT': {'step_size': 1.0, 'min_qty': 1.0, 'min_notional': 5.0},
            'SOLUSDT': {'step_size': 0.01, 'min_qty': 0.01, 'min_notional': 5.0},
            'MATICUSDT': {'step_size': 1.0, 'min_qty': 1.0, 'min_notional': 5.0}
        }