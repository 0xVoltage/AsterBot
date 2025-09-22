#!/usr/bin/env python3
"""
Script para testar os novos cálculos de margem e alavancagem
"""

import sys
import os
import json
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from asterbot.api.client import AsterDexClient
from asterbot.strategy.trading_strategy import VolumeScalpingStrategy, TradingConfig


def test_margin_calculations(config_path: str):
    """Testar os novos cálculos de margem"""

    print("Teste dos Novos Cálculos de Margem")
    print("=" * 40)

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

        # Teste multi-símbolo
        symbols = config.get('symbols', [config.get('symbol', 'BTCUSDT')])
        if not isinstance(symbols, list):
            symbols = [symbols]

        print(f"Símbolos configurados: {symbols}")

        # Criar estratégias para todos os símbolos
        strategies = {}
        trading_settings = config.get('trading_settings', {})
        technical_indicators = config.get('technical_indicators', {})

        for symbol in symbols:
            trading_config = TradingConfig(
                symbol=symbol,
                risk_per_trade=trading_settings.get('risk_per_trade', 5.0),
                min_profit_target=trading_settings.get('min_profit_target', 0.15),
                max_position_time=trading_settings.get('max_position_time', 600),
                trading_fee=trading_settings.get('trading_fee', 0.035),
                rsi_period=technical_indicators.get('rsi_period', 14),
                sma_short=technical_indicators.get('sma_short', 5),
                sma_long=technical_indicators.get('sma_long', 10),
                scalping_mode=trading_settings.get('scalping_mode', True),
                min_position_size=trading_settings.get('min_position_size', 0.001),
                force_min_order=trading_settings.get('force_min_order', False),
                leverage=trading_settings.get('leverage', 10),
                max_margin_per_trade=trading_settings.get('max_margin_per_trade', 20.0)
            )

            # Criar estratégia para este símbolo
            strategy = VolumeScalpingStrategy(client, trading_config)
            strategies[symbol] = strategy

        print(f"Estratégias criadas para {len(strategies)} símbolos")

        print(f"Configuração:")
        print(f"  Leverage: {trading_config.leverage}x")
        print(f"  Max margin per trade: {trading_config.max_margin_per_trade}%")
        print(f"  Min position size: {trading_config.min_position_size}")

        # Obter saldo atual
        first_strategy = next(iter(strategies.values()))
        balance = first_strategy.get_account_balance()
        print(f"\nSaldo atual: {balance:.2f} USDT")

        # Configurações multi-símbolo
        multi_symbol_settings = config.get('multi_symbol_settings', {})
        max_concurrent = multi_symbol_settings.get('max_concurrent_positions', 3)
        print(f"Max posições simultâneas: {max_concurrent}")

        # Simular cenário multi-símbolo
        print(f"\n=== TESTE MULTI-SÍMBOLO ===")

        # Preços de teste para diferentes símbolos
        test_prices = {
            'BTCUSDT': 115000,
            'ETHUSDT': 4000,
            'ASTERUSDT': 0.05,
            'SOLUSDT': 250,
            'BNBUSDT': 700,
            'XRPUSDT': 2.5,
            'DOGEUSDT': 0.4,
            'SUIUSDT': 4.5,
            'FARTUSDT': 0.001
        }

        total_margin_used = 0.0
        simulated_positions = 0

        for symbol in symbols:
            if simulated_positions >= max_concurrent:
                print(f"\n--- {symbol}: AGUARDANDO (max posições atingido) ---")
                continue

            price = test_prices.get(symbol, 100)  # preço padrão se não encontrado
            print(f"\n--- Teste {symbol}: {price:,} USDT ---")

            # Calcular margem disponível considerando outras posições
            used_percentage = (total_margin_used / balance) * 100
            available_percentage = 100.0 - used_percentage

            # Calcular posição considerando margem compartilhada
            strategy = strategies[symbol]
            stop_loss = price * 0.998  # 0.2% abaixo

            quantity = strategy.calculate_position_size(price, stop_loss, available_percentage)

            if quantity > 0:
                position_value = quantity * price
                margin_needed = position_value / trading_config.leverage
                margin_percentage = (margin_needed / balance) * 100

                print(f"  Quantidade: {quantity:.6f} {symbol.replace('USDT', '')}")
                print(f"  Valor da posição: {position_value:,.2f} USDT")
                print(f"  Margem necessária: {margin_needed:.2f} USDT ({margin_percentage:.1f}% do saldo)")
                print(f"  Margem total usada: {total_margin_used + margin_needed:.2f} USDT")

                # Verificar se pode abrir a posição
                total_margin_percentage = ((total_margin_used + margin_needed) / balance) * 100

                if total_margin_percentage <= 80:  # limite de segurança de 80%
                    print(f"  OK - POSICAO APROVADA")
                    total_margin_used += margin_needed
                    simulated_positions += 1
                else:
                    print(f"  ERRO - POSICAO REJEITADA - Excederia limite total de margem")

            else:
                print(f"  ERRO - Nao e possivel calcular posicao")

        print(f"\n=== RESUMO FINAL ===")
        print(f"Posições simuladas: {simulated_positions}/{max_concurrent}")
        print(f"Margem total utilizada: {total_margin_used:.2f} USDT ({(total_margin_used/balance)*100:.1f}%)")
        print(f"Margem disponível: {balance - total_margin_used:.2f} USDT ({((balance - total_margin_used)/balance)*100:.1f}%)")
        print(f"Proteção: Cada operação limitada a {trading_config.max_margin_per_trade}% do saldo")

    except Exception as e:
        print(f"ERRO: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")


def main():
    if len(sys.argv) < 2:
        print("Uso: python test_margin_calculation.py <caminho_config>")
        return

    config_path = sys.argv[1]
    if not os.path.exists(config_path):
        print(f"Arquivo não encontrado: {config_path}")
        return

    test_margin_calculations(config_path)


if __name__ == "__main__":
    main()