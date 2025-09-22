import hashlib
import hmac
import time
import json
from typing import Dict, Any, Optional
import requests
from urllib.parse import urlencode


class AsterDexClient:
    def __init__(self, api_key: str, secret_key: str, base_url: str = "https://fapi.asterdex.com"):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = base_url
        self.recv_window = 5000

    def _generate_signature(self, query_string: str) -> str:
        return hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def _prepare_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        timestamp = int(time.time() * 1000)
        params['timestamp'] = timestamp
        params['recvWindow'] = self.recv_window
        return params

    def _make_request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None, signed: bool = False) -> Dict[str, Any]:
        headers = {
            'X-MBX-APIKEY': self.api_key
        }

        if params is None:
            params = {}

        if signed:
            params = self._prepare_params(params)
            query_string = urlencode(sorted(params.items()))
            signature = self._generate_signature(query_string)

            # Para requisições assinadas, sempre usar URL com query string
            full_url = f"{self.base_url}{endpoint}?{query_string}&signature={signature}"
        else:
            full_url = f"{self.base_url}{endpoint}"

        try:
            if method.upper() == 'GET':
                if signed:
                    response = requests.get(full_url, headers=headers, timeout=30)
                else:
                    response = requests.get(full_url, headers=headers, params=params, timeout=30)
            elif method.upper() == 'POST':
                if signed:
                    response = requests.post(full_url, headers=headers, timeout=30)
                else:
                    response = requests.post(full_url, headers=headers, data=params, timeout=30)
            elif method.upper() == 'PUT':
                if signed:
                    response = requests.put(full_url, headers=headers, timeout=30)
                else:
                    response = requests.put(full_url, headers=headers, data=params, timeout=30)
            elif method.upper() == 'DELETE':
                if signed:
                    response = requests.delete(full_url, headers=headers, timeout=30)
                else:
                    response = requests.delete(full_url, headers=headers, params=params, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                print(f"API Error {e.response.status_code}: {e.response.text}")
            raise Exception(f"API request failed: {str(e)}")

    def get_server_time(self) -> Dict[str, Any]:
        return self._make_request('GET', '/fapi/v1/time')

    def get_exchange_info(self) -> Dict[str, Any]:
        return self._make_request('GET', '/fapi/v1/exchangeInfo')

    def get_orderbook(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        params = {'symbol': symbol, 'limit': limit}
        return self._make_request('GET', '/fapi/v1/depth', params)

    def get_recent_trades(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        params = {'symbol': symbol, 'limit': limit}
        return self._make_request('GET', '/fapi/v1/trades', params)

    def get_klines(self, symbol: str, interval: str, limit: int = 100) -> Dict[str, Any]:
        params = {'symbol': symbol, 'interval': interval, 'limit': limit}
        return self._make_request('GET', '/fapi/v1/klines', params)

    def get_24hr_ticker(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        params = {'symbol': symbol} if symbol else {}
        return self._make_request('GET', '/fapi/v1/ticker/24hr', params)

    def get_mark_price(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        params = {'symbol': symbol} if symbol else {}
        return self._make_request('GET', '/fapi/v1/premiumIndex', params)

    def get_account_info(self) -> Dict[str, Any]:
        return self._make_request('GET', '/fapi/v2/account', signed=True)

    def get_position_info(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        params = {'symbol': symbol} if symbol else {}
        return self._make_request('GET', '/fapi/v2/positionRisk', params, signed=True)

    def place_order(self, symbol: str, side: str, order_type: str, quantity: float,
                   price: Optional[float] = None, time_in_force: str = 'GTC',
                   reduce_only: bool = False, close_position: bool = False) -> Dict[str, Any]:
        params = {
            'symbol': symbol,
            'side': side.upper(),
            'type': order_type.upper(),
            'quantity': str(quantity)  # Converter para string
        }

        # Adicionar timeInForce apenas para ordens que precisam
        if order_type.upper() in ['LIMIT', 'STOP_MARKET', 'TAKE_PROFIT_MARKET']:
            params['timeInForce'] = time_in_force

        # Adicionar preço apenas se necessário
        if price is not None and order_type.upper() in ['LIMIT', 'STOP', 'TAKE_PROFIT']:
            params['price'] = str(price)

        # Adicionar flags opcionais apenas se True
        if reduce_only:
            params['reduceOnly'] = 'true'

        if close_position:
            params['closePosition'] = 'true'

        return self._make_request('POST', '/fapi/v1/order', params, signed=True)

    def cancel_order(self, symbol: str, order_id: Optional[int] = None,
                    orig_client_order_id: Optional[str] = None) -> Dict[str, Any]:
        params = {'symbol': symbol}
        if order_id:
            params['orderId'] = order_id
        if orig_client_order_id:
            params['origClientOrderId'] = orig_client_order_id

        return self._make_request('DELETE', '/fapi/v1/order', params, signed=True)

    def cancel_all_orders(self, symbol: str) -> Dict[str, Any]:
        params = {'symbol': symbol}
        return self._make_request('DELETE', '/fapi/v1/allOpenOrders', params, signed=True)

    def get_open_orders(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        params = {'symbol': symbol} if symbol else {}
        return self._make_request('GET', '/fapi/v1/openOrders', params, signed=True)

    def get_order_history(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        params = {'symbol': symbol, 'limit': limit}
        return self._make_request('GET', '/fapi/v1/allOrders', params, signed=True)

    def change_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """Alterar alavancagem para um símbolo"""
        params = {'symbol': symbol, 'leverage': leverage}
        return self._make_request('POST', '/fapi/v1/leverage', params, signed=True)

    def change_margin_type(self, symbol: str, margin_type: str = 'ISOLATED') -> Dict[str, Any]:
        """Alterar tipo de margem (ISOLATED ou CROSSED)"""
        params = {'symbol': symbol, 'marginType': margin_type}
        return self._make_request('POST', '/fapi/v1/marginType', params, signed=True)

    def get_leverage_bracket(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Obter informações de alavancagem e brackets"""
        params = {'symbol': symbol} if symbol else {}
        return self._make_request('GET', '/fapi/v1/leverageBracket', params, signed=True)