#!/usr/bin/env python3
"""
Flask Web Application for AsterBot
Web interface for bot configuration and trading control
"""

import sys
import os
import json
import asyncio
import threading
import time
from pathlib import Path
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from asterbot.bot import AsterBot

app = Flask(__name__)
app.config['SECRET_KEY'] = 'asterbot_secret_key_2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global bot state
bot_instance = None
bot_thread = None
bot_running = False

# Default configurations
default_config = {
    "base_url": "https://fapi.asterdex.com",
    "symbols": [
        "BTCUSDT",
        "ETHUSDT",
        "SOLUSDT",
        "BNBUSDT",
        "XRPUSDT",
        "DOGEUSDT"
    ],
    "cycle_interval": 0.5,
    "log_level": "INFO",
    "multi_symbol_settings": {
        "max_concurrent_positions": 3,
        "symbol_rotation_enabled": True,
        "shared_margin_management": True
    },
    "trading_settings": {
        "risk_per_trade": 5.0,
        "min_profit_target": 0.8,
        "max_position_time": 600,
        "trading_fee": 0.035,
        "scalping_mode": True,
        "min_trade_interval": 30,
        "min_position_size": 0.001,
        "force_min_order": True,
        "leverage": 10,
        "max_margin_per_trade": 30.0
    },
    "technical_indicators": {
        "rsi_period": 14,
        "sma_short": 5,
        "sma_long": 10,
        "rsi_oversold": 30,
        "rsi_overbought": 70
    },
    "risk_management": {
        "max_daily_loss": 50.0,
        "max_consecutive_losses": 5,
        "position_size_multiplier": 1.0,
        "emergency_stop": False
    },
    "monitoring": {
        "performance_snapshot_interval": 300,
        "alert_thresholds": {
            "min_win_rate": 40,
            "max_drawdown": 20,
            "min_profit_factor": 1.0
        }
    }
}

@app.route('/')
def index():
    """Main page"""
    # Check if first time
    first_time = not os.path.exists(Path(__file__).parent.parent.parent / 'config' / 'web_config.json')
    return render_template('index.html', first_time=first_time)

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    config = default_config.copy()
    # Remove sensitive keys
    if 'api_key' in config:
        config['api_key'] = '***'
    if 'secret_key' in config:
        config['secret_key'] = '***'
    return jsonify(config)

@app.route('/api/config', methods=['POST'])
def update_config():
    """Update configuration"""
    try:
        data = request.json

        # Validate required keys
        if not data.get('api_key') or not data.get('secret_key'):
            return jsonify({'error': 'API Key and Secret Key are required'}), 400

        # Create complete configuration
        config = default_config.copy()
        config['api_key'] = data['api_key']
        config['secret_key'] = data['secret_key']

        # Update specific configurations
        if 'max_margin_per_trade' in data:
            config['trading_settings']['max_margin_per_trade'] = float(data['max_margin_per_trade'])

        if 'take_profit_pct' in data:
            config['take_profit_pct'] = float(data['take_profit_pct'])

        if 'stop_loss_pct' in data:
            config['stop_loss_pct'] = float(data['stop_loss_pct'])

        if 'take_profit_pct' in data:
            config['take_profit_pct'] = float(data['take_profit_pct'])

        # Save configuration to temporary file
        config_path = Path(__file__).parent.parent.parent / 'config' / 'web_config.json'
        config_path.parent.mkdir(exist_ok=True)

        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        session['config_path'] = str(config_path)

        return jsonify({'success': True, 'message': 'Configuration updated successfully'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bot/start', methods=['POST'])
def start_bot():
    """Start the bot"""
    global bot_instance, bot_thread, bot_running

    try:
        if bot_running:
            return jsonify({'error': 'Bot is already running'}), 400

        config_path = session.get('config_path')
        if not config_path or not os.path.exists(config_path):
            return jsonify({'error': 'Configuration not found. Configure first.'}), 400

        def run_bot():
            global bot_instance, bot_running
            try:
                bot_instance = AsterBot(config_path)
                asyncio.run(bot_instance.run())
            except Exception as e:
                logging.error(f"Error running bot: {e}")
                bot_running = False
                socketio.emit('bot_error', {'error': str(e)})

        bot_thread = threading.Thread(target=run_bot)
        bot_thread.daemon = True
        bot_thread.start()
        bot_running = True

        socketio.emit('bot_status', {'status': 'running'})

        return jsonify({'success': True, 'message': 'Bot started successfully'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bot/stop', methods=['POST'])
def stop_bot():
    """Stop the bot"""
    global bot_instance, bot_running

    try:
        if not bot_running:
            return jsonify({'error': 'Bot is not running'}), 400

        bot_running = False
        if bot_instance:
            bot_instance.stop()

        socketio.emit('bot_status', {'status': 'stopped'})

        return jsonify({'success': True, 'message': 'Bot stopped successfully'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bot/status', methods=['GET'])
def get_bot_status():
    """Get bot status"""
    status = {
        'running': bot_running,
        'active_positions': 0,
        'total_profit': 0.0,
        'margin_usage': 0.0,
        'margin_usage_percentage': 0.0,
        'timestamp': int(time.time())
    }

    if bot_instance:
        try:
            # Get detailed bot information
            stats = bot_instance.get_stats()

            # Real active positions
            status['active_positions'] = stats.get('bot_stats', {}).get('active_positions', 0)

            # Total aggregated PnL
            status['total_profit'] = stats.get('aggregated_performance', {}).get('total_pnl', 0.0)

            # Margin used in absolute value and percentage
            status['margin_usage'] = stats.get('bot_stats', {}).get('total_margin_usage', 0.0)

            # Calculate margin usage percentage
            available_margin_pct = stats.get('bot_stats', {}).get('available_margin_percentage', 100.0)
            status['margin_usage_percentage'] = max(0.0, 100.0 - available_margin_pct)

            # Debug log
            print(f"Bot status: positions={status['active_positions']}, PnL={status['total_profit']:.4f}, margin={status['margin_usage_percentage']:.1f}%")

        except Exception as e:
            # Detailed error log
            print(f"Error getting bot status: {e}")
            import traceback
            traceback.print_exc()
            # Keep default values in case of error
            pass

    return jsonify(status)

@socketio.on('connect')
def handle_connect():
    """Client connected"""
    emit('connected', {'message': 'Connected to AsterBot'})

@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected"""
    print('Client disconnected')

def emit_trading_log(level, message, symbol=None):
    """Emit trading log to frontend"""
    try:
        log_data = {
            'level': level,  # info, success, warning, error
            'message': message,
            'symbol': symbol,
            'timestamp': time.time()
        }
        socketio.emit('trading_log', log_data)
    except Exception as e:
        print(f"Error emitting log: {e}")

# Make function globally available to the bot
import sys
sys.modules[__name__].emit_trading_log = emit_trading_log

# Real-time data emitter
def emit_real_time_data():
    """Emit real-time data to frontend"""
    while True:
        if bot_running and bot_instance:
            try:
                # Get complete statistics
                stats = bot_instance.get_stats()

                status = {
                    'running': True,
                    'active_positions': stats.get('bot_stats', {}).get('active_positions', 0),
                    'total_profit': stats.get('aggregated_performance', {}).get('total_pnl', 0.0),
                    'margin_usage': stats.get('bot_stats', {}).get('total_margin_usage', 0.0),
                    'margin_usage_percentage': max(0.0, 100.0 - stats.get('bot_stats', {}).get('available_margin_percentage', 100.0)),
                    'timestamp': int(time.time())
                }
                socketio.emit('real_time_update', status)

                # Detailed debug log
                print(f"WebSocket sent: positions={status['active_positions']}, PnL={status['total_profit']:.4f}, margin={status['margin_usage_percentage']:.1f}%")

            except Exception as e:
                print(f"Error emitting real-time data: {e}")
                import traceback
                traceback.print_exc()

        socketio.sleep(1)  # Update every 1 second for maximum responsiveness

if __name__ == '__main__':
    import time

    # Start thread for real-time data
    real_time_thread = threading.Thread(target=emit_real_time_data)
    real_time_thread.daemon = True
    real_time_thread.start()

    print("🚀 AsterBot Web Interface started!")
    print("📱 Access: http://localhost:5000")

    socketio.run(app, host='0.0.0.0', port=5000, debug=False)