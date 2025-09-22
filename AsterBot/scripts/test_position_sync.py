#!/usr/bin/env python3
"""
Script to test real position synchronization from exchange
"""

import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from asterbot.api.client import AsterDexClient
from asterbot.strategy.trading_strategy import VolumeScalpingStrategy, TradingConfig


def test_position_sync(config_path: str):
    """Test real position synchronization"""

    print("Position Synchronization Test")
    print("=" * 40)

    try:
        # Load configuration
        with open(config_path, 'r') as f:
            config = json.load(f)

        # Create client
        client = AsterDexClient(
            api_key=config['api_key'],
            secret_key=config['secret_key'],
            base_url=config.get('base_url', 'https://fapi.asterdex.com')
        )

        symbols = config.get('symbols', ['BTCUSDT'])
        print(f"Testing synchronization for {len(symbols)} symbols")

        # Check real positions for each symbol
        for symbol in symbols:
            print(f"\n--- Checking {symbol} ---")

            try:
                # Get real positions from exchange
                positions_response = client.get_position_info(symbol)

                if positions_response and isinstance(positions_response, list):
                    active_position = None
                    for pos in positions_response:
                        if pos.get('symbol') == symbol:
                            pos_size = float(pos.get('positionAmt', 0))
                            if abs(pos_size) > 0:  # Active position
                                active_position = pos
                                break

                    if active_position:
                        pos_size = float(active_position.get('positionAmt', 0))
                        entry_price = float(active_position.get('entryPrice', 0))
                        unrealized_pnl = float(active_position.get('unRealizedProfit', 0))
                        side = "LONG" if pos_size > 0 else "SHORT"

                        print(f"  ACTIVE POSITION FOUND:")
                        print(f"    Side: {side}")
                        print(f"    Quantity: {abs(pos_size)}")
                        print(f"    Entry price: {entry_price}")
                        print(f"    Unrealized PnL: {unrealized_pnl:.4f} USDT")

                        # Calculate used margin
                        position_value = abs(pos_size) * entry_price
                        leverage = config.get('trading_settings', {}).get('leverage', 10)
                        margin_used = position_value / leverage

                        print(f"    Position value: {position_value:.2f} USDT")
                        print(f"    Used margin: {margin_used:.2f} USDT")
                    else:
                        print(f"  No active position")
                else:
                    print(f"  Error getting positions")

            except Exception as e:
                print(f"  ERRO: {e}")

        # Complete synchronization test
        print(f"\n=== AUTOMATIC SYNCHRONIZATION TEST ===")

        # Create strategy for test
        trading_settings = config.get('trading_settings', {})
        technical_indicators = config.get('technical_indicators', {})

        trading_config = TradingConfig(
            symbol=symbols[0],  # Test with first symbol
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

        strategy = VolumeScalpingStrategy(client, trading_config)

        print(f"Testing synchronization for {symbols[0]}...")

        # State before synchronization
        print(f"Internal state before: {'POSITION' if strategy.current_position else 'NO POSITION'}")

        # Execute synchronization
        strategy._sync_positions_from_exchange()

        # State after synchronization
        if strategy.current_position:
            pos = strategy.current_position
            print(f"Internal state after: POSITION {pos.side.value} {pos.quantity} @ {pos.entry_price}")
            print(f"  Take Profit: {pos.take_profit}")
            print(f"  Stop Loss: {pos.stop_loss}")
        else:
            print(f"Internal state after: NO POSITION")

        print(f"\n✓ Synchronization test completed")

    except Exception as e:
        print(f"ERRO: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_position_sync.py <config_path>")
        return

    config_path = sys.argv[1]
    if not os.path.exists(config_path):
        print(f"File not found: {config_path}")
        return

    test_position_sync(config_path)


if __name__ == "__main__":
    main()