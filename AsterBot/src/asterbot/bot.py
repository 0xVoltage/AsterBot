import asyncio
import logging
import time
import json
from typing import Dict, Any, Optional
from dataclasses import asdict
from .api.client import AsterDexClient
from .strategy.trading_strategy import VolumeScalpingStrategy, TradingConfig
from .utils.logger import setup_logger


class AsterBot:
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.client = None
        self.strategies = {}  # Dict[symbol, strategy]
        self.logger = None
        self.running = False
        self.shared_margin_tracker = 0.0  # Track total margin usage across all symbols
        self.stats = {
            'start_time': 0,
            'uptime': 0,
            'cycles_completed': 0,
            'errors_count': 0,
            'last_error': None,
            'active_symbols': []
        }

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise Exception(f"Error loading configuration: {e}")

    def _validate_config(self) -> bool:
        required_fields = ['api_key', 'secret_key', 'symbols']
        for field in required_fields:
            if field not in self.config:
                self.logger.error(f"Required field missing in configuration: {field}")
                return False

        # Validate symbols is a list and not empty
        if not isinstance(self.config['symbols'], list) or len(self.config['symbols']) == 0:
            self.logger.error("Field 'symbols' must be a non-empty list")
            return False

        return True

    def initialize(self) -> bool:
        try:
            # Setup logger
            log_level = self.config.get('log_level', 'INFO')
            self.logger = setup_logger('asterbot', log_level)

            self.logger.info("Initializing AsterBot...")

            # Validate configuration
            if not self._validate_config():
                return False

            # Initialize API client
            self.client = AsterDexClient(
                api_key=self.config['api_key'],
                secret_key=self.config['secret_key'],
                base_url=self.config.get('base_url', 'https://fapi.asterdex.com')
            )

            # Test connection
            server_time = self.client.get_server_time()
            self.logger.info(f"Connected to server. Server time: {server_time}")

            # Create strategies for all symbols
            trading_settings = self.config.get('trading_settings', {})
            technical_indicators = self.config.get('technical_indicators', {})
            multi_symbol_settings = self.config.get('multi_symbol_settings', {})

            max_concurrent = multi_symbol_settings.get('max_concurrent_positions', 3)
            self.logger.info(f"Configuring bot for {len(self.config['symbols'])} symbols, maximum {max_concurrent} simultaneous positions")

            # Create strategy for each symbol
            for symbol in self.config['symbols']:
                trading_config = TradingConfig(
                    symbol=symbol,
                    risk_per_trade=trading_settings.get('risk_per_trade', 1.0),
                    min_profit_target=trading_settings.get('min_profit_target', 0.1),
                    max_position_time=trading_settings.get('max_position_time', 300),
                    trading_fee=trading_settings.get('trading_fee', 0.035),
                    rsi_period=technical_indicators.get('rsi_period', 14),
                    sma_short=technical_indicators.get('sma_short', 5),
                    sma_long=technical_indicators.get('sma_long', 10),
                    scalping_mode=trading_settings.get('scalping_mode', True),
                    min_position_size=trading_settings.get('min_position_size', 0.001),
                    force_min_order=trading_settings.get('force_min_order', False),
                    leverage=trading_settings.get('leverage', 10),
                    max_margin_per_trade=trading_settings.get('max_margin_per_trade', 20.0),
                    take_profit_pct=self.config.get('take_profit_pct', 0.8),
                    stop_loss_pct=self.config.get('stop_loss_pct', 2.0)
                )

                # Inicializar estratégia para este símbolo
                strategy = VolumeScalpingStrategy(self.client, trading_config)
                self.strategies[symbol] = strategy
                self.stats['active_symbols'].append(symbol)

                self.logger.info(f"Strategy initialized for {symbol}")

            self.logger.info("AsterBot initialized successfully!")
            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"Initialization error: {e}")
            else:
                print(f"Initialization error: {e}")
            return False

    def get_total_margin_usage(self) -> float:
        """Calcular margem total em uso obtendo posições reais da exchange"""
        total_margin = 0.0

        try:
            # Obter posições reais de todos os símbolos
            for symbol, strategy in self.strategies.items():
                positions_response = strategy.client.get_position_info(symbol)

                if positions_response and isinstance(positions_response, list):
                    for pos in positions_response:
                        if pos.get('symbol') == symbol:
                            pos_size = float(pos.get('positionAmt', 0))
                            if abs(pos_size) > 0:  # Active position
                                entry_price = float(pos.get('entryPrice', 0))
                                position_value = abs(pos_size) * entry_price
                                margin_used = position_value / strategy.config.leverage
                                total_margin += margin_used
                                break
        except Exception as e:
            # Fallback to calculation based on internal positions
            self.logger.warning(f"Error getting real positions, using fallback: {e}")
            for symbol, strategy in self.strategies.items():
                if strategy.current_position:
                    position_value = strategy.current_position.quantity * strategy.current_position.entry_price
                    margin_used = position_value / strategy.config.leverage
                    total_margin += margin_used

        return total_margin

    def _count_real_active_positions(self) -> int:
        """Count real active positions on exchange"""
        active_count = 0

        try:
            for symbol, strategy in self.strategies.items():
                positions_response = strategy.client.get_position_info(symbol)

                if positions_response and isinstance(positions_response, list):
                    for pos in positions_response:
                        if pos.get('symbol') == symbol:
                            pos_size = float(pos.get('positionAmt', 0))
                            if abs(pos_size) > 0:  # Active position
                                active_count += 1
                                break
        except Exception as e:
            # Fallback to counting based on internal positions
            self.logger.warning(f"Error counting real positions, using fallback: {e}")
            active_count = sum(1 for strategy in self.strategies.values() if strategy.current_position)

        return active_count

    def get_available_margin_percentage(self) -> float:
        """Calculate available margin percentage"""
        # Get balance from any strategy (all share the same client)
        if not self.strategies:
            return 0.0

        first_strategy = next(iter(self.strategies.values()))
        total_balance = first_strategy.get_account_balance()

        if total_balance <= 0:
            return 0.0

        used_margin = self.get_total_margin_usage()
        used_percentage = (used_margin / total_balance) * 100
        return 100.0 - used_percentage

    async def run_cycle(self) -> Dict[str, Any]:
        try:
            cycle_start = time.time()

            # Multi-symbol settings
            multi_symbol_settings = self.config.get('multi_symbol_settings', {})
            max_concurrent = multi_symbol_settings.get('max_concurrent_positions', 3)

            # Count real active positions from exchange
            active_positions = self._count_real_active_positions()

            # Cycle results
            cycle_results = {
                'cycle_number': self.stats['cycles_completed'] + 1,
                'active_positions': active_positions,
                'available_margin_percentage': self.get_available_margin_percentage(),
                'symbol_results': {},
                'total_performance': {
                    'trades_count': 0,
                    'total_volume': 0.0,
                    'total_pnl': 0.0
                }
            }

            # PRIORITIZATION: Separate symbols with and without active positions
            symbols_with_positions = []
            symbols_without_positions = []

            for symbol, strategy in self.strategies.items():
                if strategy.current_position:
                    symbols_with_positions.append((symbol, strategy))
                else:
                    symbols_without_positions.append((symbol, strategy))

            # EXECUTE SYMBOLS WITH ACTIVE POSITIONS FIRST (maximum priority)
            all_strategies = symbols_with_positions + symbols_without_positions

            self.logger.debug(f"Prioritization: {len(symbols_with_positions)} active positions first, {len(symbols_without_positions)} without positions after")

            # Execute strategies in priority order
            for symbol, strategy in all_strategies:
                try:
                    # Check if can open new position
                    can_open_new = (active_positions < max_concurrent and
                                   self.get_available_margin_percentage() > 25.0)

                    # Execute strategy cycle
                    # ALWAYS execute if has position (priority), or if can open new
                    if strategy.current_position or can_open_new:
                        # Pass available margin to strategy
                        available_margin = self.get_available_margin_percentage()

                        # Priority execution log
                        if strategy.current_position:
                            self.logger.debug(f"PRIORITY: Checking active position in {symbol}")

                        result = strategy.run_strategy_cycle(available_margin)
                        cycle_results['symbol_results'][symbol] = result

                        # Aggregate performance
                        if 'performance' in result and isinstance(result['performance'], dict):
                            cycle_results['total_performance']['trades_count'] += result['performance'].get('trades_count', 0)
                            cycle_results['total_performance']['total_volume'] += result['performance'].get('total_volume', 0.0)
                            cycle_results['total_performance']['total_pnl'] += result['performance'].get('total_pnl', 0.0)

                        # Atualizar contador de posições ativas se mudou
                        new_active_count = self._count_real_active_positions()
                        if new_active_count != active_positions:
                            active_positions = new_active_count
                            cycle_results['active_positions'] = active_positions

                    else:
                        cycle_results['symbol_results'][symbol] = {
                            'status': 'WAITING',
                            'reason': f'Max concurrent positions ({max_concurrent}) reached or insufficient margin'
                        }

                except Exception as e:
                    cycle_results['symbol_results'][symbol] = {
                        'error': str(e)
                    }
                    self.logger.error(f"Error in strategy {symbol}: {e}")

            cycle_time = time.time() - cycle_start
            self.stats['cycles_completed'] += 1

            # Log de performance periódico
            if self.stats['cycles_completed'] % 10 == 0:
                self.logger.info(f"Cycle {self.stats['cycles_completed']}: "
                               f"Active positions: {active_positions}/{max_concurrent}, "
                               f"Available margin: {cycle_results['available_margin_percentage']:.1f}%, "
                               f"Total trades: {cycle_results['total_performance']['trades_count']}, "
                               f"PnL total: {cycle_results['total_performance']['total_pnl']:.4f}")

            cycle_results['cycle_time'] = cycle_time

            return cycle_results

        except Exception as e:
            self.stats['errors_count'] += 1
            self.stats['last_error'] = str(e)
            self.logger.error(f"Error in bot cycle: {e}")
            return {'error': str(e)}

    async def run(self):
        if not self.initialize():
            return

        self.running = True
        self.stats['start_time'] = time.time()
        # Intervalo ultra-rápido para detecção de take profit
        cycle_interval = self.config.get('cycle_interval', 0.5)  # 500ms para máxima responsividade

        self.logger.info(f"Starting trading bot for {len(self.config['symbols'])} symbols: {', '.join(self.config['symbols'])}")
        self.logger.info(f"Interval between cycles: {cycle_interval}s")

        try:
            while self.running:
                cycle_result = await self.run_cycle()

                # Aguardar próximo ciclo
                await asyncio.sleep(cycle_interval)

                # Atualizar uptime
                self.stats['uptime'] = time.time() - self.stats['start_time']

        except KeyboardInterrupt:
            self.logger.info("Interruption received, stopping bot...")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
        finally:
            await self.shutdown()

    def stop(self):
        """Parar o bot de forma controlada"""
        self.logger.info("Stop command received...")
        self.running = False

    async def shutdown(self):
        self.logger.info("Shutting down AsterBot...")
        self.running = False

        # Fechar todas as posições abertas
        closed_positions = 0
        for symbol, strategy in self.strategies.items():
            if strategy.current_position:
                try:
                    current_price = strategy.market_data.get_current_price()
                    if current_price:
                        strategy.close_position(current_price, "SHUTDOWN")
                        closed_positions += 1
                        self.logger.info(f"Position {symbol} closed due to shutdown")
                except Exception as e:
                    self.logger.error(f"Error closing position {symbol} on shutdown: {e}")

        if closed_positions > 0:
            self.logger.info(f"Total of {closed_positions} positions closed on shutdown")

        # Log de estatísticas finais
        final_stats = self.get_stats()
        self.logger.info(f"Final statistics: {json.dumps(final_stats, indent=2)}")

    def get_stats(self) -> Dict[str, Any]:
        uptime_minutes = self.stats['uptime'] / 60

        # Agregar estatísticas de todas as estratégias
        total_trades = 0
        total_volume = 0.0
        total_pnl = 0.0
        active_positions = 0

        strategy_stats_by_symbol = {}

        for symbol, strategy in self.strategies.items():
            stats = strategy.get_strategy_stats()
            strategy_stats_by_symbol[symbol] = stats

            # Agregar totais
            if 'trades_count' in stats:
                total_trades += stats['trades_count']
            if 'total_volume' in stats:
                total_volume += stats['total_volume']
            if 'total_pnl' in stats:
                total_pnl += stats['total_pnl']
            if strategy.current_position:
                active_positions += 1

        return {
            'bot_stats': {
                'uptime_minutes': round(uptime_minutes, 2),
                'cycles_completed': self.stats['cycles_completed'],
                'errors_count': self.stats['errors_count'],
                'last_error': self.stats['last_error'],
                'cycles_per_minute': round(self.stats['cycles_completed'] / max(uptime_minutes, 1), 2),
                'active_positions': active_positions,
                'total_margin_usage': self.get_total_margin_usage(),
                'available_margin_percentage': self.get_available_margin_percentage()
            },
            'aggregated_performance': {
                'total_trades': total_trades,
                'total_volume': total_volume,
                'total_pnl': total_pnl
            },
            'strategy_stats_by_symbol': strategy_stats_by_symbol,
            'config': {
                'symbols': self.config.get('symbols', []),
                'cycle_interval': self.config.get('cycle_interval', 5),
                'max_concurrent_positions': self.config.get('multi_symbol_settings', {}).get('max_concurrent_positions', 3)
            }
        }

    def force_close_position(self, symbol: Optional[str] = None) -> Dict[str, bool]:
        """Fechar posições manualmente. Se symbol for None, fecha todas."""
        results = {}

        if symbol:
            # Fechar posição específica
            if symbol in self.strategies and self.strategies[symbol].current_position:
                try:
                    strategy = self.strategies[symbol]
                    current_price = strategy.market_data.get_current_price()
                    if current_price:
                        success = strategy.close_position(current_price, "MANUAL_CLOSE")
                        results[symbol] = success
                        if success:
                            self.logger.info(f"Position {symbol} closed manually")
                    else:
                        results[symbol] = False
                except Exception as e:
                    self.logger.error(f"Error closing position {symbol} manually: {e}")
                    results[symbol] = False
            else:
                results[symbol] = False
        else:
            # Fechar todas as posições
            for sym, strategy in self.strategies.items():
                if strategy.current_position:
                    try:
                        current_price = strategy.market_data.get_current_price()
                        if current_price:
                            success = strategy.close_position(current_price, "MANUAL_CLOSE")
                            results[sym] = success
                            if success:
                                self.logger.info(f"Position {sym} closed manually")
                        else:
                            results[sym] = False
                    except Exception as e:
                        self.logger.error(f"Error closing position {sym} manually: {e}")
                        results[sym] = False

        return results

    def get_current_positions(self) -> Dict[str, Dict[str, Any]]:
        """Obter todas as posições ativas"""
        positions = {}

        for symbol, strategy in self.strategies.items():
            if strategy.current_position:
                position = strategy.current_position
                positions[symbol] = {
                    'symbol': position.symbol,
                    'side': position.side.value,
                    'entry_price': position.entry_price,
                    'quantity': position.quantity,
                    'stop_loss': position.stop_loss,
                    'take_profit': position.take_profit,
                    'unrealized_pnl': position.unrealized_pnl,
                    'position_age_seconds': time.time() - position.entry_time
                }

        return positions


# Função principal para executar o bot
async def main():
    import sys
    import os

    if len(sys.argv) < 2:
        print("Usage: python -m asterbot.bot <path_to_config.json>")
        return

    config_path = sys.argv[1]
    if not os.path.exists(config_path):
        print(f"Configuration file not found: {config_path}")
        return

    bot = AsterBot(config_path)
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())