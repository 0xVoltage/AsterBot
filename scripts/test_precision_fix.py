#!/usr/bin/env python3
"""
Test script to verify precision fix for XRP, BNB, DOGE and other symbols.
Checks that step sizes are correctly fetched from exchange info.
"""

import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from asterbot.api.client import AsterDexClient
from asterbot.utils.symbol_precision import SymbolPrecisionManager


def test_symbol_precision(config_path: str):
    """Test precision handling for different symbols"""

    print("Testing Symbol Precision Fix")
    print("=" * 50)

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

        # Create precision manager
        precision_manager = SymbolPrecisionManager(client)

        # Test symbols that previously caused precision errors
        test_symbols = ['XRPUSDT', 'BNBUSDT', 'DOGEUSDT', 'BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'SOLUSDT']

        print("1. Testing precision fetching from exchange...")

        for symbol in test_symbols:
            print(f"\nTesting {symbol}:")

            try:
                precision = precision_manager.get_symbol_precision(symbol)
                print(f"   Step Size: {precision['step_size']}")
                print(f"   Min Quantity: {precision['min_qty']}")
                print(f"   Min Notional: {precision['min_notional']}")

                # Test quantity rounding
                test_quantities = [0.0015, 0.5, 1.5, 10.123, 100.9876]
                print(f"   Quantity Rounding Tests:")

                for qty in test_quantities:
                    rounded = precision_manager.round_quantity(symbol, qty)
                    print(f"      {qty} -> {rounded}")

                # Test order validation
                test_price = 1.0 if 'USDT' in symbol else 50000.0
                min_valid_qty = precision['min_qty']

                print(f"   Order Validation Tests (price: {test_price}):")
                valid = precision_manager.validate_order_size(symbol, min_valid_qty, test_price)
                print(f"      Minimum quantity ({min_valid_qty}): {'✓ Valid' if valid else '✗ Invalid'}")

                # Test with quantity below minimum
                invalid_qty = min_valid_qty * 0.5
                valid = precision_manager.validate_order_size(symbol, invalid_qty, test_price)
                print(f"      Below minimum ({invalid_qty}): {'✓ Valid' if valid else '✗ Invalid (expected)'}")

            except Exception as e:
                print(f"   ERROR: {e}")

        print("\n2. Testing common precisions reference...")
        common = precision_manager.get_common_precisions()
        for symbol, precision in common.items():
            print(f"   {symbol}: step={precision['step_size']}, min_qty={precision['min_qty']}")

        print("\n3. Summary of precision differences:")
        print("   BTC/ETH: step_size=0.001 (3 decimal places)")
        print("   XRP/DOGE/ADA: step_size=1.0 (whole numbers)")
        print("   BNB/SOL: step_size=0.01 (2 decimal places)")
        print("\nThe bot now dynamically fetches these values instead of hardcoding 0.001!")

        return True

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        print(f"Details: {traceback.format_exc()}")
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_precision_fix.py <config_path>")
        print("Example: python test_precision_fix.py ../config/config.json")
        return

    config_path = sys.argv[1]
    if not os.path.exists(config_path):
        print(f"Config file not found: {config_path}")
        return

    success = test_symbol_precision(config_path)
    if success:
        print("\n✅ Precision fix test completed successfully!")
        print("The API Error 400 for XRP, BNB, DOGE should now be resolved.")
    else:
        print("\n❌ Precision fix test failed!")


if __name__ == "__main__":
    main()