import yfinance as yf
import pandas as pd
import numpy as np
import ta
from backtesting import Backtest, Strategy

class USDJPY_ProQuantStrategy(Strategy):
    # Parameters
    ema_trend_period = 200    # Master Trend Filter (200 EMA)
    rsi_period = 14
    rsi_buy_level = 42        # RSI pullback entry in uptrend
    rsi_short_level = 58      # RSI rally entry in downtrend
    atr_period = 14
    atr_sl_mult = 1.2         # Dynamic ATR Stop Loss
    atr_tp_mult = 2.4         # Dynamic ATR Take Profit (1:2 Risk-Reward)

    def init(self):
        close = pd.Series(self.data.Close)
        high = pd.Series(self.data.High)
        low = pd.Series(self.data.Low)

        # 200 EMA for Macro Trend Regime
        self.ema200 = self.I(lambda: ta.trend.ema_indicator(close, window=self.ema_trend_period).values)

        # RSI Momentum Oscillator
        self.rsi = self.I(lambda: ta.momentum.rsi(close, window=self.rsi_period).values)

        # ATR Volatility
        self.atr = self.I(lambda: ta.volatility.average_true_range(high, low, close, window=self.atr_period).values)

    def next(self):
        price = self.data.Close[-1]
        current_ema = self.ema200[-1]
        current_rsi = self.rsi[-1]
        current_atr = self.atr[-1]

        if np.isnan(current_ema) or np.isnan(current_rsi) or np.isnan(current_atr) or current_atr <= 0:
            return

        # -------------------------------------------------------------
        # LONG CONDITION: Price > 200 EMA (Uptrend) AND RSI dips below 42 (Pullback)
        # -------------------------------------------------------------
        if price > current_ema and current_rsi < self.rsi_buy_level:
            if self.position.is_short:
                self.position.close()
            if not self.position.is_long:
                sl = price - self.atr_sl_mult * current_atr
                tp = price + self.atr_tp_mult * current_atr
                self.buy(sl=sl, tp=tp)

        # -------------------------------------------------------------
        # SHORT CONDITION: Price < 200 EMA (Downtrend) AND RSI spikes above 58 (Rally)
        # -------------------------------------------------------------
        elif price < current_ema and current_rsi > self.rsi_short_level:
            if self.position.is_long:
                self.position.close()
            if not self.position.is_short:
                sl = price + self.atr_sl_mult * current_atr
                tp = price - self.atr_tp_mult * current_atr
                self.sell(sl=sl, tp=tp)


if __name__ == "__main__":
    print("🐾 Fetching 1 Year of 1-Hour USD/JPY Intraday Forex Data...")
    df = yf.Ticker("USDJPY=X").history(period="1y", interval="1h")[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()

    print("\n------------------------------------------------")
    print("🚀 Backtesting USD/JPY 200-EMA Trend Pullback Strategy (Long & Short)...")
    # Using 5x leverage (margin=0.2)
    bt = Backtest(df, USDJPY_ProQuantStrategy, cash=100000, commission=0.0001, margin=0.2)
    stats = bt.run()

    print(f"Equity Final [$]:          ${stats['Equity Final [$]']:,.2f}")
    print(f"Return [%]:                 {stats['Return [%]']:.2f}%")
    print(f"Buy & Hold Return [%]:       {stats['Buy & Hold Return [%]']:.2f}%")
    print(f"Sharpe Ratio:               {stats['Sharpe Ratio']:.2f}")
    print(f"Max Drawdown [%]:           {stats['Max. Drawdown [%]']:.2f}%")
    print(f"Win Rate [%]:               {stats['Win Rate [%]']:.2f}%")
    print(f"Total Trades:               {stats['# Trades']}")
    print(f"Profit Factor:              {stats['Profit Factor']:.2f}")
