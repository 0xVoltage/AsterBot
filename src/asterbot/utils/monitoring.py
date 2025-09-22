import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import csv
import os


@dataclass
class TradeRecord:
    timestamp: float
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    reason: str
    duration_seconds: float


@dataclass
class PerformanceMetrics:
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_volume: float = 0.0
    total_pnl: float = 0.0
    max_profit: float = 0.0
    max_loss: float = 0.0
    win_rate: float = 0.0
    average_profit: float = 0.0
    average_loss: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0


class TradingMonitor:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.trade_history: List[TradeRecord] = []
        self.session_start = time.time()
        self.performance_history: List[PerformanceMetrics] = []
        self.last_snapshot = time.time()
        self.snapshot_interval = 300  # 5 minutos

    def record_trade(self, side: str, entry_price: float, exit_price: float,
                    quantity: float, pnl: float, reason: str, duration: float):
        trade = TradeRecord(
            timestamp=time.time(),
            symbol=self.symbol,
            side=side,
            entry_price=entry_price,
            exit_price=exit_price,
            quantity=quantity,
            pnl=pnl,
            reason=reason,
            duration_seconds=duration
        )
        self.trade_history.append(trade)

    def calculate_metrics(self, period_hours: Optional[int] = None) -> PerformanceMetrics:
        trades = self.trade_history

        # Filtrar por período se especificado
        if period_hours:
            cutoff_time = time.time() - (period_hours * 3600)
            trades = [t for t in trades if t.timestamp >= cutoff_time]

        if not trades:
            return PerformanceMetrics()

        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.pnl > 0])
        losing_trades = len([t for t in trades if t.pnl < 0])
        total_volume = sum(t.quantity * t.entry_price for t in trades)
        total_pnl = sum(t.pnl for t in trades)

        profits = [t.pnl for t in trades if t.pnl > 0]
        losses = [t.pnl for t in trades if t.pnl < 0]

        max_profit = max(profits) if profits else 0.0
        max_loss = min(losses) if losses else 0.0
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
        average_profit = sum(profits) / len(profits) if profits else 0.0
        average_loss = abs(sum(losses) / len(losses)) if losses else 0.0

        # Profit Factor = Gross Profit / Gross Loss
        gross_profit = sum(profits) if profits else 0.0
        gross_loss = abs(sum(losses)) if losses else 0.0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf') if gross_profit > 0 else 0.0

        # Sharpe Ratio simplificado (retornos / volatilidade)
        returns = [t.pnl for t in trades]
        if len(returns) > 1:
            mean_return = sum(returns) / len(returns)
            variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
            std_dev = variance ** 0.5
            sharpe_ratio = mean_return / std_dev if std_dev > 0 else 0.0
        else:
            sharpe_ratio = 0.0

        return PerformanceMetrics(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            total_volume=total_volume,
            total_pnl=total_pnl,
            max_profit=max_profit,
            max_loss=max_loss,
            win_rate=win_rate,
            average_profit=average_profit,
            average_loss=average_loss,
            profit_factor=profit_factor,
            sharpe_ratio=sharpe_ratio
        )

    def take_performance_snapshot(self):
        current_time = time.time()
        if current_time - self.last_snapshot >= self.snapshot_interval:
            metrics = self.calculate_metrics()
            self.performance_history.append(metrics)
            self.last_snapshot = current_time

    def get_session_summary(self) -> Dict[str, Any]:
        session_duration = time.time() - self.session_start
        session_metrics = self.calculate_metrics()

        # Métricas da última hora
        last_hour_metrics = self.calculate_metrics(1)

        return {
            'session_info': {
                'symbol': self.symbol,
                'start_time': datetime.fromtimestamp(self.session_start).isoformat(),
                'duration_hours': round(session_duration / 3600, 2),
                'total_trades': len(self.trade_history)
            },
            'session_performance': asdict(session_metrics),
            'last_hour_performance': asdict(last_hour_metrics),
            'recent_trades': [asdict(t) for t in self.trade_history[-5:]]  # Últimas 5 trades
        }

    def export_trades_to_csv(self, filename: Optional[str] = None) -> str:
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'trades_{self.symbol}_{timestamp}.csv'

        reports_dir = 'logs/reports'
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)

        filepath = os.path.join(reports_dir, filename)

        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['timestamp', 'datetime', 'symbol', 'side', 'entry_price',
                         'exit_price', 'quantity', 'pnl', 'reason', 'duration_seconds']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for trade in self.trade_history:
                row = asdict(trade)
                row['datetime'] = datetime.fromtimestamp(trade.timestamp).isoformat()
                writer.writerow(row)

        return filepath

    def export_performance_report(self, filename: Optional[str] = None) -> str:
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'performance_report_{self.symbol}_{timestamp}.json'

        reports_dir = 'logs/reports'
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)

        filepath = os.path.join(reports_dir, filename)

        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': self.get_session_summary(),
            'performance_snapshots': [asdict(p) for p in self.performance_history],
            'detailed_trades': [asdict(t) for t in self.trade_history]
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return filepath

    def get_risk_alerts(self) -> List[str]:
        alerts = []
        metrics = self.calculate_metrics()

        # Alertas baseados em performance
        if metrics.total_trades >= 10:
            if metrics.win_rate < 40:
                alerts.append(f"Taxa de vitória baixa: {metrics.win_rate:.1f}%")

            if metrics.profit_factor < 1.0:
                alerts.append(f"Profit Factor negativo: {metrics.profit_factor:.2f}")

            # Sequência de perdas
            recent_trades = self.trade_history[-5:]
            if len(recent_trades) >= 3:
                recent_losses = sum(1 for t in recent_trades if t.pnl < 0)
                if recent_losses >= 3:
                    alerts.append(f"Sequência de {recent_losses} perdas nas últimas trades")

        # Alerta de PnL total negativo
        if metrics.total_pnl < -100:  # Ajustar threshold conforme necessário
            alerts.append(f"PnL total negativo: {metrics.total_pnl:.2f}")

        return alerts

    def get_trading_frequency_stats(self) -> Dict[str, Any]:
        if len(self.trade_history) < 2:
            return {'error': 'Histórico insuficiente'}

        # Calcular intervalos entre trades
        intervals = []
        for i in range(1, len(self.trade_history)):
            interval = self.trade_history[i].timestamp - self.trade_history[i-1].timestamp
            intervals.append(interval)

        avg_interval = sum(intervals) / len(intervals)
        session_duration = time.time() - self.session_start
        trades_per_hour = len(self.trade_history) / (session_duration / 3600)

        return {
            'total_trades': len(self.trade_history),
            'session_duration_hours': round(session_duration / 3600, 2),
            'trades_per_hour': round(trades_per_hour, 2),
            'average_interval_minutes': round(avg_interval / 60, 2),
            'min_interval_seconds': min(intervals),
            'max_interval_seconds': max(intervals)
        }