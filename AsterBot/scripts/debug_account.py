#!/usr/bin/env python3
"""
Script de debug para verificar informações da conta e saldo
"""

import sys
import os
import json
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from asterbot.api.client import AsterDexClient


def debug_account_info(config_path: str):
    """Debug das informações da conta"""

    print("Debug - Informacoes da Conta Aster Dex")
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

        print("1. Testando informacoes da conta...")
        account_info = client.get_account_info()

        print(f"\nInformacoes gerais:")
        print(f"   Total Wallet Balance: {account_info.get('totalWalletBalance', 'N/A')}")
        print(f"   Total Unrealized PnL: {account_info.get('totalUnrealizedPnL', 'N/A')}")
        print(f"   Total Margin Balance: {account_info.get('totalMarginBalance', 'N/A')}")
        print(f"   Available Balance: {account_info.get('availableBalance', 'N/A')}")

        print(f"\nAssets na conta:")
        assets = account_info.get('assets', [])
        for asset in assets:
            asset_name = asset.get('asset', 'N/A')
            wallet_balance = asset.get('walletBalance', '0')
            unrealized_pnl = asset.get('unrealizedPnL', '0')
            margin_balance = asset.get('marginBalance', '0')
            available_balance = asset.get('availableBalance', '0')

            if float(wallet_balance) > 0 or float(margin_balance) > 0:
                print(f"   {asset_name}:")
                print(f"      Wallet Balance: {wallet_balance}")
                print(f"      Margin Balance: {margin_balance}")
                print(f"      Available Balance: {available_balance}")
                print(f"      Unrealized PnL: {unrealized_pnl}")

        print(f"\n2. Testando posicoes abertas...")
        positions = client.get_position_info()

        active_positions = [pos for pos in positions if float(pos.get('positionAmt', 0)) != 0]

        if active_positions:
            print(f"   Posicoes ativas encontradas: {len(active_positions)}")
            for pos in active_positions:
                symbol = pos.get('symbol', 'N/A')
                position_amt = pos.get('positionAmt', '0')
                entry_price = pos.get('entryPrice', '0')
                pnl = pos.get('unRealizedPnL', '0')
                print(f"      {symbol}: {position_amt} @ {entry_price} (PnL: {pnl})")
        else:
            print("   Nenhuma posicao ativa")

        print(f"\n3. Calculando saldo disponivel para USDT...")
        usdt_balance = 0.0
        for asset in assets:
            if asset.get('asset') == 'USDT':
                usdt_balance = float(asset.get('availableBalance', 0))
                break

        print(f"   Saldo USDT disponivel: {usdt_balance}")

        if usdt_balance > 0:
            # Testar cálculo de tamanho de posição
            print(f"\n4. Simulando calculo de posicao...")
            risk_per_trade = 1.0  # 1%
            entry_price = 115000  # Exemplo
            stop_loss_price = 114000  # Exemplo com 1000 USDT de diferença

            risk_amount = usdt_balance * (risk_per_trade / 100)
            risk_per_unit = abs(entry_price - stop_loss_price)
            position_size = risk_amount / risk_per_unit if risk_per_unit > 0 else 0

            print(f"   Saldo: {usdt_balance} USDT")
            print(f"   Risco por trade: {risk_per_trade}% = {risk_amount} USDT")
            print(f"   Preco entrada: {entry_price}")
            print(f"   Stop loss: {stop_loss_price}")
            print(f"   Risco por unidade: {risk_per_unit} USDT")
            print(f"   Tamanho calculado: {position_size:.6f} BTC")
            print(f"   Valor da posicao: {position_size * entry_price:.2f} USDT")
        else:
            print("   AVISO: Saldo USDT zero ou nao encontrado!")

        print(f"\n5. Verificando limites de trading...")
        exchange_info = client.get_exchange_info()
        btc_symbol = None

        for symbol_info in exchange_info.get('symbols', []):
            if symbol_info.get('symbol') == 'BTCUSDT':
                btc_symbol = symbol_info
                break

        if btc_symbol:
            filters = btc_symbol.get('filters', [])
            for filter_info in filters:
                filter_type = filter_info.get('filterType')
                if filter_type == 'LOT_SIZE':
                    min_qty = filter_info.get('minQty', '0')
                    step_size = filter_info.get('stepSize', '0')
                    print(f"   Quantidade minima: {min_qty} BTC")
                    print(f"   Step size: {step_size} BTC")
                elif filter_type == 'MIN_NOTIONAL':
                    notional = filter_info.get('notional', '0')
                    print(f"   Valor minimo da ordem: {notional} USDT")

        return True

    except Exception as e:
        print(f"ERRO: {e}")
        import traceback
        print(f"Detalhes: {traceback.format_exc()}")
        return False


def main():
    if len(sys.argv) < 2:
        print("Uso: python debug_account.py <caminho_config>")
        return

    config_path = sys.argv[1]
    if not os.path.exists(config_path):
        print(f"Arquivo nao encontrado: {config_path}")
        return

    debug_account_info(config_path)


if __name__ == "__main__":
    main()