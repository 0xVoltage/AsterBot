# 🤖 AsterBot - Automated Trading Bot

**Trading bot for Aster Dex perpetuals with intuitive web interface**

## 🚀 Super Simple Installation

⚠️ **IMPORTANTE**: Use o arquivo `INSTALL.bat`, não o `install.py`!

### For Windows (Double Click)
1. **Download the project** from GitHub
2. **Double click `INSTALL.bat`** ⭐ - Installs everything automatically
3. **Double click `START_ASTERBOT.bat`** - Opens the interface
4. **Access** `http://localhost:5000` in your browser

> 💡 **Tip**: If you click on `install.py` it only opens the code. Always use `INSTALL.bat`!

### Manual Installation (Optional)
```bash
# 1. Clone repository
git clone https://github.com/seu-usuario/AsterBot.git
cd AsterBot

# 2. Install dependencies
pip install -r requirements_web.txt

# 3. Start interface
python run_web.py
```

## 📱 How to Use

### 1️⃣ First Setup
- Open `http://localhost:5000`
- Enter your **Aster Dex keys**
- Configure **margin per trade** (10-50%)
- Adjust **Take Profit** and **Stop Loss**
- Click **"Save Configuration""

### 2️⃣ Start Trading
- Click **"Start Bot"**
- Follow the **real-time dashboard**
- Monitor the **activity logs"

### 3️⃣ Stop Bot
- Click **"Stop Bot"** when you want to stop

## ⚡ Features

✅ **Intuitive Web Interface** - Full browser control
✅ **6 Trading Pairs** - BTC, ETH, SOL, BNB, XRP, DOGE
✅ **10x Leverage** - Automatic on all trades
✅ **Smart Scalping** - High frequency with risk management
✅ **Real-time Dashboard** - Live positions, margin and P&L
✅ **Synchronization** - Detects manually opened positions
✅ **Automatic Installation** - Zero complications

## 🎯 Settings

### Margin per Trade
- **10%** - Conservative
- **20%** - Moderate
- **30%** - Balanced (default)
- **40%** - Aggressive
- **50%** - Very aggressive

### Take Profit / Stop Loss
- **Default TP**: 0.8% (covers fees + profit)
- **Default SL**: 2.0% (protection against losses)

## ⚠️ Important Warnings

🚨 **TRADING INVOLVES RISKS** 🚨

- Only use capital you can afford to lose
- Always test with small amounts first
- Monitor the bot regularly
- Keep your API keys secure
- Don't leave running unsupervised for long periods

## 📂 File Structure

```
AsterBot/
├── 📄 START_ASTERBOT.bat    ← CLICK HERE TO START
├── 🔧 INSTALL.bat            ← CLICK HERE TO INSTALL (first time)
├── 📖 README.md               ← This file
├── 📋 HOW_TO_USE.txt           ← Super simple instructions
├── 🌐 run_web.py              ← Web interface
├── ⚙️ config/                 ← Configurations
├── 🧠 src/                    ← Bot code
└── 📊 logs/                   ← System logs
```

## 🆘 Common Problems

### Bot doesn't start
- ✅ Check if Python is installed
- ✅ Run `install.py` again
- ✅ Check your API keys

### Interface doesn't load
- ✅ Wait a few seconds
- ✅ Access `http://localhost:5000`
- ✅ Close and open the `.bat` again

### API key error
- ✅ Check if the keys are correct
- ✅ Confirm that the API is active on Aster Dex
- ✅ Check trading permissions

## 🔧 Technical Support

- 📋 Check the **logs in the web interface**
- 📖 Read the **complete documentation** in `WEB_README.md`
- 🐛 Report bugs on **GitHub Issues**

## 📊 Bot Statistics

- **Leverage**: 10x fixed
- **Frequency**: ~12 checks per minute
- **Maximum Margin**: Configurable (10-50%)
- **Minimum Profit**: 0.8% guaranteed
- **Simultaneous Positions**: Up to 3
- **Timeframe**: Scalping (seconds/minutes)

---

## 🎉 Ready to Start!

1. **Click `INSTALL.bat`** (first time only)
2. **Click `START_ASTERBOT.bat`**
3. **Configure and start** at `http://localhost:5000`

**Happy Trading! 🚀**
