import yfinance as yf
import pandas as pd
import numpy as np
import ta
from backtesting import Backtest, Strategy
from backtesting.lib import crossover

# -------------------------------------------------------------
# Strategy 1: USD/JPY Keltner / Volatility Squeeze Breakout (Long & Short)
# -------------------------------------------------------------
class USDJPY_VolatilityBreakout(Strategy):
    channel_period = 20
    atr_period = 14
    atr_multiplier = 2.0
    risk_reward_ratio = 2.5

    def init(self):
        close = pd.Series(self.data.Close)
        high = pd.Series(self.data.High)
        low = pd.Series(self.data.Low)

        # Upper and Lower Donchian / Channel Breakouts
        self.upper_channel = self.I(lambda: high.rolling(self.channel_period).max().shift(1).values)
        self.lower_channel = self.I(lambda: low.rolling(self.channel_period).min().shift(1).values)

        # ATR for dynamic Volatility SL/TP
        self.atr = self.I(lambda: ta.volatility.average_true_range(high, low, close, window=self.atr_period).values)

    def next(self):
        price = self.data.Close[-1]
        current_atr = self.atr[-1]
        if np.isnan(current_atr) or current_atr <= 0:
            return

        # Bullish Breakout (BUY)
        if price > self.upper_channel[-1]:
            if self.position.is_short:
                self.position.close()
            if not self.position.is_long:
                sl = price - self.atr_multiplier * current_atr
                tp = price + (self.atr_multiplier * self.risk_reward_ratio) * current_atr
                self.buy(sl=sl, tp=tp)

        # Bearish Breakout (SHORT)
        elif price < self.lower_channel[-1]:
            if self.position.is_long:
                self.position.close()
            if not self.position.is_short:
                sl = price + self.atr_multiplier * current_atr
                tp = price - (self.atr_multiplier * self.risk_reward_ratio) * current_atr
                self.sell(sl=sl, tp=tp)


# -------------------------------------------------------------
# Strategy 2: Multi-Factor MACD + RSI + ATR Volatility Strategy (Long & Short)
# -------------------------------------------------------------
class USDJPY_MultiFactorStrategy(Strategy):
    macd_fast = 12
    macd_slow = 26
    macd_signal = 9
    rsi_period = 14
    atr_period = 14

    def init(self):
        close = pd.Series(self.data.Close)
        high = pd.Series(self.data.High)
        low = pd.Series(self.data.Low)

        # MACD
        self.macd = self.I(lambda: ta.trend.macd(close, window_slow=self.macd_slow, window_fast=self.macd_fast).values)
        self.macd_sig = self.I(lambda: ta.trend.macd_signal(close, window_slow=self.macd_slow, window_fast=self.macd_fast, window_sign=self.macd_signal).values)
        self.macd_hist = self.I(lambda: ta.trend.macd_diff(close, window_slow=self.macd_slow, window_fast=self.macd_fast, window_sign=self.macd_signal).values)

        # RSI
        self.rsi = self.I(lambda: ta.momentum.rsi(close, window=self.rsi_period).values)

        # ATR
        self.atr = self.I(lambda: ta.volatility.average_true_range(high, low, close, window=self.atr_period).values)

    def next(self):
        price = self.data.Close[-1]
        current_atr = self.atr[-1]
        if np.isnan(current_atr) or current_atr <= 0:
            return

        # Buy Signal: MACD Crossover ABOVE Signal AND RSI > 50 (momentum)
        if crossover(self.macd, self.macd_sig) and self.rsi[-1] > 50:
            if self.position.is_short:
                self.position.close()
            if not self.position.is_long:
                sl = price - 1.5 * current_atr
                tp = price + 3.0 * current_atr
                self.buy(sl=sl, tp=tp)

        # Short Signal: MACD Crossover BELOW Signal AND RSI < 50 (bearish momentum)
        elif crossover(self.macd_sig, self.macd) and self.rsi[-1] < 50:
            if self.position.is_long:
                self.position.close()
            if not self.position.is_short:
                sl = price + 1.5 * current_atr
                tp = price - 3.0 * current_atr
                self.sell(sl=sl, tp=tp)


if __name__ == "__main__":
    print("🐾 Fetching 1 Year of 1-Hour USD/JPY Intraday Forex Data...")
    ticker = yf.Ticker("USDJPY=X")
    df = ticker.history(period="1y", interval="1h")
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()

    print(f"Data Loaded: {len(df)} 1-hour candles from {df.index[0]} to {df.index[-1]}")

    print("\n------------------------------------------------")
    print("⚡ Strategy 1: USD/JPY Intraday Volatility Breakout (Long & Short)")
    bt1 = Backtest(df, USDJPY_VolatilityBreakout, cash=100000, commission=0.0001, margin=1/20) # 20x leverage typical for FX
    stats1 = bt1.run()
    print(f"Return [%]:               {stats1['Return [%]']:.2f}%")
    print(f"Buy & Hold Return [%]:     {stats1['Buy & Hold Return [%]']:.2f}%")
    print(f"Sharpe Ratio:             {stats1['Sharpe Ratio']:.2f}")
    print(f"Max Drawdown [%]:         {stats1['Max. Drawdown [%]']:.2f}%")
    print(f"Win Rate [%]:             {stats1['Win Rate [%]']:.2f}%")
    print(f"Total Trades:             {stats1['# Trades']}")
    print(f"Profit Factor:            {stats1['Profit Factor']:.2f}")

    print("\n------------------------------------------------")
    print("🎯 Strategy 2: USD/JPY Multi-Factor MACD + RSI Intraday Strategy (Long & Short)")
    bt2 = Backtest(df, USDJPY_MultiFactorStrategy, cash=100000, commission=0.0001, margin=1/20)
    stats2 = bt2.run()
    print(f"Return [%]:               {stats2['Return [%]']:.2f}%")
    print(f"Sharpe Ratio:             {stats2['Sharpe Ratio']:.2f}")
    print(f"Max Drawdown [%]:         {stats2['Max. Drawdown [%]']:.2f}%")
    print(f"Win Rate [%]:             {stats2['Win Rate [%]']:.2f}%")
    print(f"Total Trades:             {stats2['# Trades']}")
    print(f"Profit Factor:            {stats2['Profit Factor']:.2f}")
