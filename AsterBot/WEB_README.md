# AsterBot - Web Interface

Web interface for AsterBot that allows configuration and control through the browser.

## 🚀 How to Use

### 1. Install Dependencies
```bash
pip install -r requirements_web.txt
```

### 2. Start Web Interface
```bash
python run_web.py
```

### 3. Access in Browser
Open your browser and go to: **http://localhost:5000**

## 🔧 Features

### ⚙️ Configuration
- **API Key**: Enter your Aster Dex API key
- **Secret Key**: Enter your Aster Dex secret key
- **Maximum Margin**: Choose between 10%, 20%, 30%, 40% or 50% of total margin per trade
- **Take Profit**: Set minimum profit (default: 0.8%)
- **Stop Loss**: Set maximum loss (default: 2.0%)

### 🎮 Bot Control
- **Start Bot**: Start automated trading
- **Stop Bot**: Stop bot and close all positions
- **Real-time Status**: Visual status indicator (running/stopped)

### 📊 Real-time Dashboard
- **Active Positions**: Number of open positions
- **Margin Used**: Percentage of total margin in use
- **Total P&L**: Accumulated profit/loss
- **Uptime**: Time the bot has been running

### 📝 System Logs
- **Real-time Logs**: Monitor bot actions in real time
- **Different Types**: INFO (blue), SUCCESS (green), WARNING (yellow), ERROR (red)
- **Clear Button**: Clear logs when needed

## 🔐 Security

- API keys are masked after being entered
- Keys are stored only in memory during execution
- Configuration is saved to local temporary file

## 📋 Supported Symbols

The bot automatically operates on the main perpetual pairs from Aster Dex:
- BTCUSDT
- ETHUSDT
- SOLUSDT
- BNBUSDT
- XRPUSDT
- DOGEUSDT

## ⚡ Technical Features

- **Leverage**: 10x on all trades
- **Scalping Mode**: Fast operations with high frequency
- **Risk Management**: Automatic margin control
- **Synchronization**: Syncs with real exchange positions
- **Multi-Symbol**: Operates multiple pairs simultaneously
- **WebSocket**: Real-time updates via WebSocket

## 🛠️ Created Files

```
src/web/
├── app.py              # Main Flask application
├── templates/
│   └── index.html      # Web interface
requirements_web.txt    # Web interface dependencies
run_web.py             # Script to start the interface
```

## 🔧 Advanced Settings

Technical settings (indicators, intervals, etc.) use optimized default values:

- **RSI**: Period 14, oversold 30, overbought 70
- **Moving Averages**: SMA 5 and 10 periods
- **Cycle Interval**: 5 seconds
- **Minimum Profit**: 0.8% (to cover fees)
- **Trading Fee**: 0.035% per side
- **Simultaneous Positions**: Maximum 3

## ⚠️ Important

1. **Test First**: Always test with small amounts
2. **Monitor**: Follow logs and performance
3. **Backup**: Keep backup of important settings
4. **Risk**: Automated trading involves risks - only use capital you can afford to lose

## 📞 Support

For issues or questions, check the system logs in the web interface.