import time
import logging
from typing import Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from ..api.client import AsterDexClient
from ..api.market_data import MarketDataCollector
from ..indicators.technical_indicators import TradingSignals, RiskCalculator


class PositionSide(Enum):
    LONG = "BUY"
    SHORT = "SELL"
    NONE = "NONE"


@dataclass
class Position:
    symbol: str
    side: PositionSide
    entry_price: float
    quantity: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    entry_time: float = 0
    unrealized_pnl: float = 0


@dataclass
class TradingConfig:
    symbol: str
    risk_per_trade: float = 1.0  # % of balance to risk per trade
    min_profit_target: float = 0.1  # minimum % profit to cover fees
    max_position_time: int = 300  # maximum seconds to hold position
    trading_fee: float = 0.035  # % fee per operation
    rsi_period: int = 14
    sma_short: int = 5
    sma_long: int = 10
    min_volume_threshold: float = 1000  # minimum volume for trading
    scalping_mode: bool = True  # scalping mode for high volume
    min_position_size: float = 0.001  # minimum position size
    force_min_order: bool = False  # force use of minimum order
    leverage: int = 10  # leverage to use
    max_margin_per_trade: float = 20.0  # maximum % of total margin per trade
    take_profit_pct: float = 0.8  # % take profit configured by user
    stop_loss_pct: float = 2.0  # % stop loss configured by user


class VolumeScalpingStrategy:
    def __init__(self, client: AsterDexClient, config: TradingConfig):
        self.client = client
        self.config = config
        self.market_data = MarketDataCollector(client, config.symbol)
        self.signals = TradingSignals(config.rsi_period, config.sma_short, config.sma_long)
        self.current_position: Optional[Position] = None
        self.logger = logging.getLogger(__name__)
        self.trades_count = 0
        self.total_volume = 0.0
        self.total_pnl = 0.0
        self.last_trade_time = 0
        self.min_trade_interval = 15  # reduzido para 15s para maior responsividade

        # Multi-symbol support
        self.available_margin_percentage: Optional[float] = None

        # Configurar alavancagem na inicialização
        self._setup_leverage()

    def _emit_web_log(self, level: str, message: str):
        """Emitir log para interface web"""
        try:
            # Tentar importar e usar a função de log da web
            import sys
            web_module = sys.modules.get('src.web.app')
            if web_module and hasattr(web_module, 'emit_trading_log'):
                web_module.emit_trading_log(level, message, self.config.symbol)
        except Exception:
            # Se não conseguir emitir para web, apenas continuar
            pass

    def _sync_positions_from_exchange(self):
        """Sincronizar posições reais da exchange com o estado interno do bot"""
        try:
            # Obter posições reais da exchange
            positions_response = self.client.get_position_info(self.config.symbol)

            if not positions_response or not isinstance(positions_response, list):
                return

            # Search for active position for this symbol
            active_position = None
            for pos in positions_response:
                if pos.get('symbol') == self.config.symbol:
                    pos_size = float(pos.get('positionAmt', 0))
                    if abs(pos_size) > 0:  # Active position
                        active_position = pos
                        break

            if active_position:
                # Real position exists on exchange
                pos_size = float(active_position.get('positionAmt', 0))
                entry_price = float(active_position.get('entryPrice', 0))
                unrealized_pnl = float(active_position.get('unRealizedProfit', 0))

                if not self.current_position:
                    # Bot didn't know about position - synchronize
                    side = PositionSide.LONG if pos_size > 0 else PositionSide.SHORT

                    # Calculate net unrealized PnL considering fees
                    current_price = self.market_data.get_current_price() or entry_price
                    net_unrealized_pnl = RiskCalculator.calculate_profit_loss(
                        entry_price, current_price, abs(pos_size), side.value, self.config.trading_fee
                    )

                    self.current_position = Position(
                        symbol=self.config.symbol,
                        side=side,
                        entry_price=entry_price,
                        quantity=abs(pos_size),
                        stop_loss=0,  # Será recalculado
                        take_profit=0,  # Será recalculado
                        entry_time=time.time(),
                        unrealized_pnl=net_unrealized_pnl  # Usar PnL líquido
                    )

                    # Recalcular targets
                    take_profit, stop_loss = self.calculate_scalping_targets(entry_price, side)
                    self.current_position.take_profit = take_profit
                    self.current_position.stop_loss = stop_loss

                    self.logger.info(f"SYNCHRONIZED: Position detected on exchange - {side.value} {abs(pos_size)} @ {entry_price}")
                else:
                    # Update existing position PnL with net calculation
                    current_price = self.market_data.get_current_price()
                    if current_price:
                        self.current_position.unrealized_pnl = RiskCalculator.calculate_profit_loss(
                            self.current_position.entry_price,
                            current_price,
                            self.current_position.quantity,
                            self.current_position.side.value,
                            self.config.trading_fee
                        )
            else:
                # No real position exists on exchange
                if self.current_position:
                    # Bot thought it had position but doesn't - clear
                    self.logger.info(f"SYNCHRONIZED: Position {self.current_position.side.value} was closed externally")
                    self.current_position = None

        except Exception as e:
            self.logger.warning(f"Error synchronizing exchange positions: {e}")

    def _setup_leverage(self):
        """Configure leverage and margin type"""
        try:
            # Configurar alavancagem
            result = self.client.change_leverage(self.config.symbol, self.config.leverage)
            self.logger.info(f"Alavancagem configurada para {self.config.leverage}x: {result}")

            # Configure isolated margin (safer for scalping)
            margin_result = self.client.change_margin_type(self.config.symbol, 'ISOLATED')
            self.logger.info(f"Isolated margin configured: {margin_result}")

        except Exception as e:
            self.logger.warning(f"Error configuring leverage: {e}")

    def get_account_balance(self) -> float:
        try:
            account_info = self.client.get_account_info()
            balance = 0.0
            for asset in account_info.get('assets', []):
                if asset.get('asset') == 'USDT':
                    # Use availableBalance instead of walletBalance for trading
                    balance = float(asset.get('availableBalance', 0))
                    break
            return balance
        except Exception as e:
            self.logger.error(f"Error getting account balance: {e}")
            return 0.0

    def calculate_position_size(self, entry_price: float, stop_loss_price: float, available_margin_percentage: Optional[float] = None) -> float:
        balance = self.get_account_balance()
        if balance <= 0:
            return 0

        # NEW LOGIC: Ensure 10x leverage and maximum 20% of total margin
        # Consider margin already in use by other positions (multi-symbol)

        # 1. Determine maximum available margin
        if available_margin_percentage is not None:
            # Usar margem disponível real (considerando outras posições)
            available_margin = balance * (available_margin_percentage / 100)
            # Limitar ao máximo de 20% por trade
            max_margin_per_trade = min(available_margin, balance * (self.config.max_margin_per_trade / 100))
        else:
            # Fallback to original logic (single symbol)
            max_margin_per_trade = balance * (self.config.max_margin_per_trade / 100)

        # 2. With 10x leverage, calculate maximum position value
        max_position_value_by_margin = max_margin_per_trade * self.config.leverage
        max_quantity_by_margin = max_position_value_by_margin / entry_price

        # 3. Check exchange minimum quantity
        min_order_size = getattr(self.config, 'min_position_size', 0.001)
        min_order_value = min_order_size * entry_price
        min_margin_required = min_order_value / self.config.leverage

        if max_margin_per_trade < min_margin_required:
            self.logger.warning(f"Maximum margin per trade ({max_margin_per_trade:.2f} USDT) less than minimum required ({min_margin_required:.2f} USDT)")
            return 0

        # 4. Use the quantity that respects the 20% margin limit
        final_quantity = max_quantity_by_margin

        # 5. Ensure it meets exchange minimum
        if final_quantity < min_order_size:
            # If calculated quantity is less than minimum, use minimum
            # but check if it doesn't exceed margin limit
            test_margin = (min_order_size * entry_price) / self.config.leverage
            if test_margin <= max_margin_per_trade:
                final_quantity = min_order_size
                self.logger.info(f"Using exchange minimum quantity: {min_order_size}")
            else:
                self.logger.warning(f"Minimum quantity ({min_order_size}) would exceed margin limit. Trade cancelled.")
                return 0

        # 6. Check if it doesn't exceed total available margin
        final_margin_needed = (final_quantity * entry_price) / self.config.leverage

        if final_margin_needed > balance:
            self.logger.warning(f"Required margin ({final_margin_needed:.2f}) exceeds balance ({balance:.2f})")
            return 0

        # 7. Round to exchange step size (0.001) - ALWAYS DOWN to respect limit
        step_size = 0.001
        final_quantity = int(final_quantity / step_size) * step_size  # Round down

        self.logger.info(f"Calculated position: "
                        f"balance={balance:.2f} USDT, "
                        f"max_margin_per_trade={max_margin_per_trade:.2f} USDT ({self.config.max_margin_per_trade}%), "
                        f"leverage={self.config.leverage}x, "
                        f"position_value={final_quantity * entry_price:.2f} USDT, "
                        f"margin_needed={final_margin_needed:.2f} USDT, "
                        f"quantity={final_quantity:.3f} BTC")

        return final_quantity

    def calculate_scalping_targets(self, entry_price: float, side: PositionSide) -> Tuple[float, float]:
        # Use user settings for TP and SL
        take_profit_pct = self.config.take_profit_pct / 100  # Convert % to decimal
        stop_loss_pct = self.config.stop_loss_pct / 100  # Convert % to decimal

        # ENSURE MINIMUM PROFIT TO COVER FEES
        fee_cost = (self.config.trading_fee / 100) * 2  # opening + closing
        min_profit_for_fees = 0.5 / 100  # 0.5% minimum to cover fees

        # ALWAYS use exact user configuration (don't override for fees)
        # User is responsible for configuring an adequate value
        min_profit_needed = take_profit_pct

        if side == PositionSide.LONG:
            # LONG: use user configuration
            take_profit = entry_price * (1 + min_profit_needed)
            stop_loss = entry_price * (1 - stop_loss_pct)
        else:
            # SHORT: use user configuration
            take_profit = entry_price * (1 - min_profit_needed)
            stop_loss = entry_price * (1 + stop_loss_pct)

        # Log calculated target
        profit_pct = min_profit_needed * 100
        sl_pct = stop_loss_pct * 100
        self.logger.info(f"Calculated targets: TP={profit_pct:.2f}%, SL={sl_pct:.2f}%, Entry={entry_price}, TP={take_profit:.2f}, SL={stop_loss:.2f}")

        return take_profit, stop_loss

    def calculate_current_profit_percentage(self, current_price: float) -> float:
        """Calculate real ROE% considering leverage"""
        if not self.current_position:
            return 0.0

        entry_price = self.current_position.entry_price

        if self.current_position.side == PositionSide.LONG:
            # LONG: lucro quando preço sobe
            price_change_pct = ((current_price - entry_price) / entry_price) * 100
        else:
            # SHORT: lucro quando preço desce
            price_change_pct = ((entry_price - current_price) / entry_price) * 100

        # ROE% = Price change × Leverage
        roe_pct = price_change_pct * self.config.leverage

        return roe_pct

    def check_existing_positions(self) -> Optional[Position]:
        """Check if there are existing positions in account"""
        try:
            positions = self.client.get_position_info(self.config.symbol)
            for pos in positions:
                position_amt = float(pos.get('positionAmt', 0))
                if position_amt != 0:
                    side = PositionSide.LONG if position_amt > 0 else PositionSide.SHORT
                    entry_price = float(pos.get('entryPrice', 0))

                    # Calculate targets for existing position
                    take_profit, stop_loss = self.calculate_scalping_targets(entry_price, side)

                    return Position(
                        symbol=self.config.symbol,
                        side=side,
                        entry_price=entry_price,
                        quantity=abs(position_amt),
                        stop_loss=stop_loss,
                        take_profit=take_profit,
                        entry_time=time.time()  # Approximation
                    )
        except Exception as e:
            self.logger.error(f"Error checking existing positions: {e}")
        return None

    def should_enter_trade(self, signal_data: Dict[str, Any]) -> Tuple[bool, PositionSide]:
        if 'error' in signal_data:
            return False, PositionSide.NONE

        # Evitar trades muito frequentes
        if time.time() - self.last_trade_time < self.min_trade_interval:
            return False, PositionSide.NONE

        # Check if we already have open position in bot
        if self.current_position is not None:
            return False, PositionSide.NONE

        # Check if there are existing positions in account
        existing_position = self.check_existing_positions()
        if existing_position:
            self.current_position = existing_position
            self.logger.info(f"Existing position detected: {existing_position.side.value} {existing_position.quantity} @ {existing_position.entry_price}")
            return False, PositionSide.NONE

        action = signal_data.get('action', 'HOLD')
        confidence = signal_data.get('confidence', 0)

        # For scalping, accept signals with lower confidence to generate more volume
        min_confidence = 0.3 if self.config.scalping_mode else 0.6

        if action == 'BUY' and confidence >= min_confidence:
            return True, PositionSide.LONG
        elif action == 'SELL' and confidence >= min_confidence:
            return True, PositionSide.SHORT

        return False, PositionSide.NONE

    def enter_position(self, side: PositionSide, entry_price: float) -> bool:
        try:
            take_profit, stop_loss = self.calculate_scalping_targets(entry_price, side)
            quantity = self.calculate_position_size(entry_price, stop_loss, self.available_margin_percentage)

            if quantity <= 0:
                self.logger.warning("Invalid calculated quantity for new position")
                return False

            # Execute market order for fast entry
            # Round quantity to step size (0.001)
            step_size = 0.001
            rounded_quantity = round(quantity / step_size) * step_size

            self.logger.info(f"Trying to open order: {side.value} {rounded_quantity} {self.config.symbol} @ market")

            order_result = self.client.place_order(
                symbol=self.config.symbol,
                side=side.value,
                order_type='MARKET',
                quantity=rounded_quantity
            )

            if order_result:
                self.current_position = Position(
                    symbol=self.config.symbol,
                    side=side,
                    entry_price=entry_price,
                    quantity=quantity,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    entry_time=time.time()
                )

                self.trades_count += 1
                self.total_volume += quantity * entry_price
                self.last_trade_time = time.time()

                # Detailed log of position opening with ROE%
                log_msg = f"✅ POSITION OPENED: {side.value} {quantity:.3f} @ ${entry_price:.2f} | TP: {self.config.take_profit_pct}% ROE | SL: {self.config.stop_loss_pct}% ROE | Leverage: {self.config.leverage}x"
                self.logger.info(log_msg)
                self._emit_web_log('success', log_msg)
                return True

        except Exception as e:
            self.logger.error(f"Error opening position: {e}")

        return False

    def should_close_position(self, current_price: float) -> Tuple[bool, str]:
        if self.current_position is None:
            return False, ""

        # PRIORIDADE MÁXIMA: Verificar take profit PRIMEIRO
        if self.current_position.side == PositionSide.LONG:
            if current_price >= self.current_position.take_profit:
                return True, "TAKE_PROFIT"
        else:
            if current_price <= self.current_position.take_profit:
                return True, "TAKE_PROFIT"

        # SEGUNDA PRIORIDADE: Verificar stop loss
        if self.current_position.side == PositionSide.LONG:
            if current_price <= self.current_position.stop_loss:
                return True, "STOP_LOSS"
        else:
            if current_price >= self.current_position.stop_loss:
                return True, "STOP_LOSS"

        # TERCEIRA PRIORIDADE: Verificar tempo máximo da posição (importante para scalping)
        position_age = time.time() - self.current_position.entry_time
        if position_age > self.config.max_position_time:
            # CORRECTION: Only close by time if loss is not too big
            current_pnl_pct = ((current_price - self.current_position.entry_price) / self.current_position.entry_price) * 100
            if self.current_position.side == PositionSide.SHORT:
                current_pnl_pct = -current_pnl_pct

            # Only force closure if loss < 2% or if too much time passed (10 min)
            max_timeout_loss = 2.0  # 2% maximum loss by timeout
            absolute_max_time = self.config.max_position_time * 2  # 10 minutes absolute

            if current_pnl_pct > -max_timeout_loss or position_age > absolute_max_time:
                return True, "MAX_TIME_REACHED"
            else:
                self.logger.warning(f"Position with {current_pnl_pct:.2f}% loss - waiting for recovery (age: {position_age:.0f}s)")
                return False, ""

        return False, ""

    def close_position(self, current_price: float, reason: str) -> bool:
        if self.current_position is None:
            return False

        try:
            # Market order for fast closure
            close_side = "SELL" if self.current_position.side == PositionSide.LONG else "BUY"

            order_result = self.client.place_order(
                symbol=self.config.symbol,
                side=close_side,
                order_type='MARKET',
                quantity=self.current_position.quantity,
                reduce_only=True
            )

            if order_result:
                # Calculate net PnL (deducting fees)
                pnl = RiskCalculator.calculate_profit_loss(
                    self.current_position.entry_price,
                    current_price,
                    self.current_position.quantity,
                    self.current_position.side.value,
                    self.config.trading_fee  # Pass configured trading fee
                )

                # Calculate profit/loss percentage
                pnl_pct = ((current_price - self.current_position.entry_price) / self.current_position.entry_price) * 100
                if self.current_position.side == PositionSide.SHORT:
                    pnl_pct = -pnl_pct

                self.total_pnl += pnl
                self.total_volume += self.current_position.quantity * current_price

                # Detailed log of position closure
                pnl_symbol = "💰" if pnl > 0 else "📉"
                log_msg = f"{pnl_symbol} POSITION CLOSED: {self.current_position.side.value} {self.current_position.quantity:.3f} @ ${current_price:.2f} | Reason: {reason} | PnL: ${pnl:.4f} ({pnl_pct:+.2f}%)"

                log_level = 'success' if pnl > 0 else 'warning' if pnl >= -0.001 else 'error'
                self.logger.info(log_msg)
                self._emit_web_log(log_level, log_msg)

                self.current_position = None
                return True

        except Exception as e:
            self.logger.error(f"Error closing position: {e}")

        return False

    def update_position_pnl(self, current_price: float):
        if self.current_position:
            # Calcular unrealized PnL líquido (descontando taxas)
            self.current_position.unrealized_pnl = RiskCalculator.calculate_profit_loss(
                self.current_position.entry_price,
                current_price,
                self.current_position.quantity,
                self.current_position.side.value,
                self.config.trading_fee  # Incluir taxas no cálculo do unrealized PnL
            )

    def run_strategy_cycle(self, available_margin_percentage: Optional[float] = None) -> Dict[str, Any]:
        try:
            # Update available margin for this cycle
            self.available_margin_percentage = available_margin_percentage

            # SUPER PRIORITY: If there's active position, check closure IMMEDIATELY
            if self.current_position:
                # Get current price first for closure verification
                current_price = self.market_data.get_current_price()
                if current_price:
                    # ULTRA-PRIORITY VERIFICATION: Use real ROE% with leverage
                    current_roe_pct = self.calculate_current_profit_percentage(current_price)
                    target_tp = self.config.take_profit_pct  # TP configured by user
                    target_sl = -self.config.stop_loss_pct   # SL configured by user (negative)

                    # Detailed log for debug
                    self.logger.debug(f"ROE Check: {current_roe_pct:.3f}% | TP: {target_tp}% | SL: {target_sl}% | Price: {self.current_position.entry_price:.2f} -> {current_price:.2f}")

                    # TAKE PROFIT: ROE% reached positive target
                    if current_roe_pct >= target_tp:
                        priority_msg = f"🎯 TAKE PROFIT: ROE {current_roe_pct:.2f}% >= {target_tp}% (Leverage {self.config.leverage}x)"
                        self.logger.info(priority_msg)
                        self._emit_web_log('success', priority_msg)
                        self.close_position(current_price, "TAKE_PROFIT_ROE")
                        return {
                            'timestamp': time.time(),
                            'current_price': current_price,
                            'action': 'TAKE_PROFIT_EXECUTED',
                            'roe_pct': current_roe_pct,
                            'target_tp': target_tp,
                            'position': {'active': False},
                            'performance': {
                                'trades_count': self.trades_count,
                                'total_volume': self.total_volume,
                                'total_pnl': self.total_pnl
                            }
                        }

                    # STOP LOSS: ROE% reached negative target
                    if current_roe_pct <= target_sl:
                        priority_msg = f"🛑 STOP LOSS: ROE {current_roe_pct:.2f}% <= {target_sl}% (Leverage {self.config.leverage}x)"
                        self.logger.warning(priority_msg)
                        self._emit_web_log('warning', priority_msg)
                        self.close_position(current_price, "STOP_LOSS_ROE")
                        return {
                            'timestamp': time.time(),
                            'current_price': current_price,
                            'action': 'STOP_LOSS_EXECUTED',
                            'roe_pct': current_roe_pct,
                            'target_sl': target_sl,
                            'position': {'active': False},
                            'performance': {
                                'trades_count': self.trades_count,
                                'total_volume': self.total_volume,
                                'total_pnl': self.total_pnl
                            }
                        }

            # Synchronize real positions from exchange
            self._sync_positions_from_exchange()

            # Update market data
            self.market_data.update_price_history()

            # Get current price (again, for cases where there was no position before)
            current_price = self.market_data.get_current_price()
            if current_price is None:
                return {'error': 'Could not get current price'}

            # Update current position PnL
            self.update_position_pnl(current_price)

            # Check if should close existing position (secondary checks)
            if self.current_position:
                # Check position timeout (only additional verification needed)
                position_age = time.time() - self.current_position.entry_time
                if position_age > self.config.max_position_time:
                    timeout_msg = f"⏰ TIMEOUT: Position open for {position_age:.0f}s (maximum {self.config.max_position_time}s)"
                    self.logger.info(timeout_msg)
                    self._emit_web_log('info', timeout_msg)
                    self.close_position(current_price, "TIMEOUT")

            # If no position, check entry
            if self.current_position is None:
                price_data = self.market_data.get_price_data_for_indicators()
                if price_data:
                    analysis = self.signals.analyze_price_data(price_data)
                    signal = self.signals.generate_signal(analysis)

                    should_enter, side = self.should_enter_trade(signal)
                    if should_enter:
                        self.enter_position(side, current_price)

            # Return current status
            return {
                'timestamp': time.time(),
                'current_price': current_price,
                'position': {
                    'active': self.current_position is not None,
                    'side': self.current_position.side.value if self.current_position else None,
                    'unrealized_pnl': self.current_position.unrealized_pnl if self.current_position else 0
                },
                'performance': {
                    'trades_count': self.trades_count,
                    'total_volume': self.total_volume,
                    'total_pnl': self.total_pnl
                }
            }

        except Exception as e:
            self.logger.error(f"Error in strategy cycle: {e}")
            return {'error': str(e)}

    def get_strategy_stats(self) -> Dict[str, Any]:
        return {
            'trades_count': self.trades_count,
            'total_volume': self.total_volume,
            'total_pnl': self.total_pnl,
            'active_position': self.current_position is not None,
            'current_position_pnl': self.current_position.unrealized_pnl if self.current_position else 0,
            'strategy_config': {
                'symbol': self.config.symbol,
                'scalping_mode': self.config.scalping_mode,
                'min_profit_target': self.config.min_profit_target,
                'risk_per_trade': self.config.risk_per_trade,
                'take_profit_pct': self.config.take_profit_pct,
                'stop_loss_pct': self.config.stop_loss_pct
            }
        }