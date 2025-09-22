#!/usr/bin/env python3
"""
Script para testar ordens e ver erros detalhados
"""

import sys
import os
import json
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from asterbot.api.client import AsterDexClient


def test_order_placement(config_path: str):
    """Testar placement de ordens"""

    print("Testando placement de ordens...")
    print("=" * 50)

    try:
        # Carregar configuração
        with open(config_path, 'r') as f:
            config = json.load(f)

        # Criar cliente
        client = AsterDexClient(
            api_key=config['api_key'],
            secret_key=config['secret_key'],
            base_url=config.get('base_url', 'https://fapi.asterdex.com')
        )

        symbol = 'BTCUSDT'

        print("1. Verificando informacoes da conta...")
        account_info = client.get_account_info()
        for asset in account_info.get('assets', []):
            if asset.get('asset') == 'USDT':
                balance = float(asset.get('availableBalance', 0))
                print(f"   Saldo USDT: {balance}")
                break

        print("\n2. Verificando informacoes do simbolo...")
        exchange_info = client.get_exchange_info()
        symbol_info = None
        for s in exchange_info.get('symbols', []):
            if s.get('symbol') == symbol:
                symbol_info = s
                break

        if symbol_info:
            print(f"   Status: {symbol_info.get('status')}")
            print(f"   Filters:")
            for f in symbol_info.get('filters', []):
                print(f"      {f}")

        print("\n3. Verificando posicoes atuais...")
        positions = client.get_position_info(symbol)
        for pos in positions:
            if pos.get('symbol') == symbol:
                amt = float(pos.get('positionAmt', 0))
                if amt != 0:
                    print(f"   Posicao ativa: {amt} @ {pos.get('entryPrice')}")
                else:
                    print(f"   Nenhuma posicao ativa")

        print("\n4. Tentando order de teste usando cliente...")
        try:
            # Usar o cliente corrigido
            order_result = client.place_order(
                symbol=symbol,
                side='BUY',
                order_type='MARKET',
                quantity=0.001
            )

            print(f"   SUCESSO! Resultado: {order_result}")

        except Exception as e:
            print(f"   Erro na ordem: {e}")

        print("\n5. Testando configuracao de leverage usando cliente...")
        try:
            # Usar o cliente corrigido para leverage
            leverage_result = client.change_leverage(symbol, 10)
            print(f"   SUCESSO! Leverage: {leverage_result}")

        except Exception as e:
            print(f"   Erro no leverage: {e}")

    except Exception as e:
        print(f"ERRO: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")


def main():
    if len(sys.argv) < 2:
        print("Uso: python test_order.py <caminho_config>")
        return

    config_path = sys.argv[1]
    if not os.path.exists(config_path):
        print(f"Arquivo nao encontrado: {config_path}")
        return

    test_order_placement(config_path)


if __name__ == "__main__":
    main()