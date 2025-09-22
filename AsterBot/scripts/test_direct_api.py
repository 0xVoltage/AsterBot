#!/usr/bin/env python3
"""
Teste direto da API usando exatamente o método que funcionou
"""

import sys
import os
import json
import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode
from pathlib import Path


def test_direct_api(config_path: str):
    """Teste direto usando o método que sabemos que funciona"""

    print("Teste Direto da API")
    print("=" * 30)

    try:
        # Carregar configuração
        with open(config_path, 'r') as f:
            config = json.load(f)

        api_key = config['api_key']
        secret_key = config['secret_key']
        base_url = config.get('base_url', 'https://fapi.asterdex.com')

        print(f"Testando com API: {api_key[:10]}...")

        # Método que funcionou no debug
        timestamp = int(time.time() * 1000)
        recv_window = 5000

        params = {
            'recvWindow': recv_window,
            'timestamp': timestamp
        }

        query_string = urlencode(sorted(params.items()))
        signature = hmac.new(
            secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        headers = {'X-MBX-APIKEY': api_key}
        url = f"{base_url}/fapi/v2/account?{query_string}&signature={signature}"

        print(f"URL: {url}")

        response = requests.get(url, headers=headers)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Sucesso! Saldo USDT: {next((asset['availableBalance'] for asset in data['assets'] if asset['asset'] == 'USDT'), 'Nao encontrado')}")

            # Agora testar uma ordem
            print("\nTestando ordem...")

            order_params = {
                'symbol': 'BTCUSDT',
                'side': 'BUY',
                'type': 'MARKET',
                'quantity': '0.001',
                'timestamp': int(time.time() * 1000),
                'recvWindow': recv_window
            }

            order_query = urlencode(sorted(order_params.items()))
            order_signature = hmac.new(
                secret_key.encode('utf-8'),
                order_query.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            order_url = f"{base_url}/fapi/v1/order?{order_query}&signature={order_signature}"

            print(f"Order URL: {order_url}")

            order_response = requests.post(order_url, headers=headers)
            print(f"Order Status: {order_response.status_code}")
            print(f"Order Response: {order_response.text}")

            if order_response.status_code == 200:
                print("ORDEM EXECUTADA COM SUCESSO!")
            else:
                print("Erro na ordem")

        else:
            print(f"Erro: {response.text}")

    except Exception as e:
        print(f"ERRO: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")


def main():
    if len(sys.argv) < 2:
        print("Uso: python test_direct_api.py <caminho_config>")
        return

    config_path = sys.argv[1]
    if not os.path.exists(config_path):
        print(f"Arquivo nao encontrado: {config_path}")
        return

    test_direct_api(config_path)


if __name__ == "__main__":
    main()