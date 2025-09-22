import logging
import os
from datetime import datetime
from typing import Optional


def setup_logger(name: str, level: str = 'INFO', log_file: Optional[str] = None) -> logging.Logger:
    # Criar diretório de logs se não existir
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Configurar logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Evitar handlers duplicados
    if logger.handlers:
        logger.handlers.clear()

    # Formato das mensagens
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    if log_file is None:
        log_file = f"{log_dir}/asterbot_{datetime.now().strftime('%Y%m%d')}.log"

    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)  # Arquivo sempre com nível DEBUG
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


class TradingLogger:
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def log_trade_signal(self, symbol: str, action: str, confidence: float, price: float, analysis: dict):
        self.logger.info(f"SIGNAL | {symbol} | {action} | Confidence: {confidence:.2f} | Price: {price}")
        self.logger.debug(f"Signal Analysis: {analysis}")

    def log_position_opened(self, symbol: str, side: str, quantity: float, entry_price: float,
                          stop_loss: float, take_profit: float):
        self.logger.info(f"POSITION_OPEN | {symbol} | {side} | Qty: {quantity} | "
                        f"Entry: {entry_price} | SL: {stop_loss} | TP: {take_profit}")

    def log_position_closed(self, symbol: str, side: str, quantity: float, entry_price: float,
                          exit_price: float, pnl: float, reason: str):
        self.logger.info(f"POSITION_CLOSE | {symbol} | {side} | Qty: {quantity} | "
                        f"Entry: {entry_price} | Exit: {exit_price} | PnL: {pnl:.4f} | Reason: {reason}")

    def log_error(self, error_type: str, message: str, details: str = ""):
        self.logger.error(f"ERROR | {error_type} | {message}")
        if details:
            self.logger.debug(f"Error Details: {details}")

    def log_performance(self, trades_count: int, total_volume: float, total_pnl: float,
                       success_rate: float = 0):
        self.logger.info(f"PERFORMANCE | Trades: {trades_count} | Volume: {total_volume:.2f} | "
                        f"PnL: {total_pnl:.4f} | Success Rate: {success_rate:.1f}%")

    def log_market_data(self, symbol: str, price: float, volume: float, spread: float = None):
        spread_info = f" | Spread: {spread:.4f}" if spread else ""
        self.logger.debug(f"MARKET | {symbol} | Price: {price} | Volume: {volume:.2f}{spread_info}")

    def log_risk_management(self, action: str, details: str):
        self.logger.warning(f"RISK_MGMT | {action} | {details}")


def get_trading_logger(name: str = 'trading', level: str = 'INFO') -> TradingLogger:
    base_logger = setup_logger(name, level)
    return TradingLogger(base_logger)