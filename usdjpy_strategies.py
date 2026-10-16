import yfinance as yf
import pandas as pd
import numpy as np
import ta
from backtesting import Backtest, Strategy
from backtesting.lib import crossover

# -------------------------------------------------------------
# Strategy 1: USD/JPY Dual EMA + ADX Trend Strategy (Long & Short)
# -------------------------------------------------------------
class USDJPY_EMATrendStrategy(Strategy):
    fast_period = 12
    slow_period = 34
    adx_period = 14
    adx_threshold = 20
    atr_mult = 2.0

    def init(self):
        close = pd.Series(self.data.Close)
        high = pd.Series(self.data.High)
        low = pd.Series(self.data.Low)

        # Exponential Moving Averages
        self.fast_ema = self.I(lambda: ta.trend.ema_indicator(close, window=self.fast_period).values)
        self.slow_ema = self.I(lambda: ta.trend.ema_indicator(close, window=self.slow_period).values)

        # ADX for trend strength filter
        self.adx = self.I(lambda: ta.trend.adx(high, low, close, window=self.adx_period).values)

        # ATR for dynamic risk management
        self.atr = self.I(lambda: ta.volatility.average_true_range(high, low, close, window=14).values)

    def next(self):
        price = self.data.Close[-1]
        current_atr = self.atr[-1] if not np.isnan(self.atr[-1]) else 1.0

        # Long Signal: Fast EMA crosses above Slow EMA AND ADX shows trend
        if crossover(self.fast_ema, self.slow_ema) and self.adx[-1] > self.adx_threshold:
            if self.position.is_short:
                self.position.close()
            if not self.position.is_long:
                sl = price - self.atr_mult * current_atr
                tp = price + (self.atr_mult * 2.0) * current_atr
                self.buy(sl=sl, tp=tp)

        # Short Signal: Fast EMA crosses below Slow EMA AND ADX shows trend
        elif crossover(self.slow_ema, self.fast_ema) and self.adx[-1] > self.adx_threshold:
            if self.position.is_long:
                self.position.close()
            if not self.position.is_short:
                sl = price + self.atr_mult * current_atr
                tp = price - (self.atr_mult * 2.0) * current_atr
                self.sell(sl=sl, tp=tp)


# -------------------------------------------------------------
# Strategy 2: USD/JPY Bollinger Bands + RSI Reversion Strategy (Long & Short)
# -------------------------------------------------------------
class USDJPY_MeanReversionStrategy(Strategy):
    bb_window = 20
    bb_std = 2.0
    rsi_window = 14
    rsi_oversold = 35
    rsi_overbought = 65

    def init(self):
        close = pd.Series(self.data.Close)

        # Bollinger Bands
        self.bb_upper = self.I(lambda: ta.volatility.bollinger_hband(close, window=self.bb_window, window_dev=self.bb_std).values)
        self.bb_lower = self.I(lambda: ta.volatility.bollinger_lband(close, window=self.bb_window, window_dev=self.bb_std).values)

        # RSI Indicator
        self.rsi = self.I(lambda: ta.momentum.rsi(close, window=self.rsi_window).values)

    def next(self):
        price = self.data.Close[-1]

        # Long Signal: Price breaks below lower Bollinger Band AND RSI is oversold
        if price < self.bb_lower[-1] and self.rsi[-1] < self.rsi_oversold:
            if self.position.is_short:
                self.position.close()
            if not self.position.is_long:
                self.buy(sl=price * 0.985, tp=price * 1.025)

        # Short Signal: Price breaks above upper Bollinger Band AND RSI is overbought
        elif price > self.bb_upper[-1] and self.rsi[-1] > self.rsi_overbought:
            if self.position.is_long:
                self.position.close()
            if not self.position.is_short:
                self.sell(sl=price * 1.015, tp=price * 0.975)


if __name__ == "__main__":
    print("🐾 Fetching 2 years of daily USD/JPY data...")
    ticker = yf.Ticker("USDJPY=X")
    df = ticker.history(period="2y")
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()

    print(f"Data loaded: {len(df)} candles from {df.index[0].date()} to {df.index[-1].date()}")

    print("\n------------------------------------------------")
    print("📈 Running Strategy 1: USD/JPY EMA + ADX Trend Strategy (Long & Short)...")
    bt1 = Backtest(df, USDJPY_EMATrendStrategy, cash=100000, commission=0.0002)
    stats1 = bt1.run()
    print(f"Return [%]:               {stats1['Return [%]']:.2f}%")
    print(f"Buy & Hold Return [%]:     {stats1['Buy & Hold Return [%]']:.2f}%")
    print(f"Sharpe Ratio:             {stats1['Sharpe Ratio']:.2f}")
    print(f"Max Drawdown [%]:         {stats1['Max Drawdown [%]']:.2f}%")
    print(f"Win Rate [%]:             {stats1['Win Rate [%]']:.2f}%")
    print(f"Total Trades:             {stats1['# Trades']}")

    print("\n------------------------------------------------")
    print("📉 Running Strategy 2: USD/JPY Bollinger + RSI Reversion Strategy (Long & Short)...")
    bt2 = Backtest(df, USDJPY_MeanReversionStrategy, cash=100000, commission=0.0002)
    stats2 = bt2.run()
    print(f"Return [%]:               {stats2['Return [%]']:.2f}%")
    print(f"Sharpe Ratio:             {stats2['Sharpe Ratio']:.2f}")
    print(f"Max Drawdown [%]:         {stats2['Max Drawdown [%]']:.2f}%")
    print(f"Win Rate [%]:             {stats2['Win Rate [%]']:.2f}%")
    print(f"Total Trades:             {stats2['# Trades']}")
