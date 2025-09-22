#!/usr/bin/env python3
"""
Script para debugar problemas de assinatura da API Aster Dex
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

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_signature_methods(config_path: str):
    """Testar diferentes métodos de assinatura"""

    print("Debug de Assinatura - Aster Dex API")
    print("=" * 50)

    try:
        # Carregar configuração
        with open(config_path, 'r') as f:
            config = json.load(f)

        api_key = config['api_key']
        secret_key = config['secret_key']
        base_url = config.get('base_url', 'https://fapi.asterdex.com')

        print(f"API Key: {api_key[:10]}...")
        print(f"Secret Key: {secret_key[:10]}...")
        print(f"Base URL: {base_url}")

        # Teste 1: Verificar server time
        print("\n1. Testando server time (sem autenticacao)...")
        response = requests.get(f"{base_url}/fapi/v1/time")
        server_time_data = response.json()
        server_time = server_time_data['serverTime']
        print(f"   Server time: {server_time}")

        # Teste 2: Account info com diferentes métodos de assinatura
        print("\n2. Testando account info com diferentes assinaturas...")

        timestamp = int(time.time() * 1000)
        recv_window = 5000

        # Método 1: Parâmetros ordenados alfabeticamente
        print("\n   Método 1: Parâmetros ordenados alfabeticamente")
        params_1 = {
            'recvWindow': recv_window,
            'timestamp': timestamp
        }

        query_string_1 = urlencode(sorted(params_1.items()))
        signature_1 = hmac.new(
            secret_key.encode('utf-8'),
            query_string_1.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        print(f"   Query string: {query_string_1}")
        print(f"   Signature: {signature_1}")

        headers = {'X-MBX-APIKEY': api_key}
        url_1 = f"{base_url}/fapi/v2/account?{query_string_1}&signature={signature_1}"

        response_1 = requests.get(url_1, headers=headers)
        print(f"   Status: {response_1.status_code}")
        print(f"   Response: {response_1.text[:200]}...")

        # Método 2: Usar form data em POST
        print("\n   Método 2: POST com form data")
        params_2 = {
            'timestamp': timestamp,
            'recvWindow': recv_window
        }

        query_string_2 = urlencode(params_2)
        signature_2 = hmac.new(
            secret_key.encode('utf-8'),
            query_string_2.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        params_2['signature'] = signature_2

        print(f"   Params: {params_2}")

        response_2 = requests.post(f"{base_url}/fapi/v2/account", headers=headers, data=params_2)
        print(f"   Status: {response_2.status_code}")
        print(f"   Response: {response_2.text[:200]}...")

        # Método 3: Usar timestamp do servidor
        print("\n   Método 3: Usando timestamp do servidor")
        params_3 = {
            'timestamp': server_time,
            'recvWindow': recv_window
        }

        query_string_3 = urlencode(sorted(params_3.items()))
        signature_3 = hmac.new(
            secret_key.encode('utf-8'),
            query_string_3.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        params_3['signature'] = signature_3

        print(f"   Server timestamp: {server_time}")
        print(f"   Query string: {query_string_3}")

        response_3 = requests.post(f"{base_url}/fapi/v2/account", headers=headers, data=params_3)
        print(f"   Status: {response_3.status_code}")
        print(f"   Response: {response_3.text[:200]}...")

        # Teste 3: Testar uma ordem simples
        print("\n3. Testando ordem de teste...")

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

        order_params['signature'] = order_signature

        print(f"   Order params: {order_params}")

        # Tentar com POST
        response_order = requests.post(f"{base_url}/fapi/v1/order", headers=headers, data=order_params)
        print(f"   Order Status: {response_order.status_code}")
        print(f"   Order Response: {response_order.text}")

        # Teste 4: Verificar se a API aceita outros endpoints
        print("\n4. Testando outros endpoints...")

        # Exchange info (não autenticado)
        exchange_response = requests.get(f"{base_url}/fapi/v1/exchangeInfo")
        print(f"   Exchange info status: {exchange_response.status_code}")

        # Ticker (não autenticado)
        ticker_response = requests.get(f"{base_url}/fapi/v1/ticker/24hr?symbol=BTCUSDT")
        print(f"   Ticker status: {ticker_response.status_code}")

    except Exception as e:
        print(f"ERRO: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")


def main():
    if len(sys.argv) < 2:
        print("Uso: python debug_signature.py <caminho_config>")
        return

    config_path = sys.argv[1]
    if not os.path.exists(config_path):
        print(f"Arquivo nao encontrado: {config_path}")
        return

    test_signature_methods(config_path)


if __name__ == "__main__":
    main()