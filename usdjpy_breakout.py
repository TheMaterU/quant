import yfinance as yf
import pandas as pd
import numpy as np
import ta
from backtesting import Backtest, Strategy

class USDJPY_DonchianChannelBreakout(Strategy):
    entry_period = 48  # 48 hours (~2 days) breakout channel
    exit_period = 24   # 24 hours exit channel
    atr_period = 14
    atr_sl_mult = 2.0
    atr_tp_mult = 4.0  # 1:2 Risk-Reward ratio

    def init(self):
        close = pd.Series(self.data.Close)
        high = pd.Series(self.data.High)
        low = pd.Series(self.data.Low)

        # Channel breakouts (shifted by 1 to prevent look-ahead bias)
        self.upper_entry = self.I(lambda: high.rolling(self.entry_period).max().shift(1).values)
        self.lower_entry = self.I(lambda: low.rolling(self.entry_period).min().shift(1).values)
        
        self.upper_exit = self.I(lambda: high.rolling(self.exit_period).max().shift(1).values)
        self.lower_exit = self.I(lambda: low.rolling(self.exit_period).min().shift(1).values)

        self.atr = self.I(lambda: ta.volatility.average_true_range(high, low, close, window=self.atr_period).values)

    def next(self):
        price = self.data.Close[-1]
        current_atr = self.atr[-1]

        if np.isnan(current_atr) or current_atr <= 0:
            return

        # Long Entry on Upside Breakout
        if price > self.upper_entry[-1]:
            if self.position.is_short:
                self.position.close()
            if not self.position.is_long:
                sl = price - self.atr_sl_mult * current_atr
                tp = price + self.atr_tp_mult * current_atr
                self.buy(sl=sl, tp=tp)

        # Short Entry on Downside Breakout
        elif price < self.lower_entry[-1]:
            if self.position.is_long:
                self.position.close()
            if not self.position.is_short:
                sl = price + self.atr_sl_mult * current_atr
                tp = price - self.atr_tp_mult * current_atr
                self.sell(sl=sl, tp=tp)

        # Trailing / Channel Exit
        elif self.position.is_long and price < self.lower_exit[-1]:
            self.position.close()
        elif self.position.is_short and price > self.upper_exit[-1]:
            self.position.close()


if __name__ == "__main__":
    print("🐾 Fetching 1 Year of 1-Hour USD/JPY Data for Breakout Strategy...")
    df = yf.Ticker("USDJPY=X").history(period="1y", interval="1h")[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()

    bt = Backtest(df, USDJPY_DonchianChannelBreakout, cash=100000, commission=0.0001, margin=0.2)
    stats = bt.run()

    print(f"\n--- Donchian Channel Breakout Results ---")
    print(f"Equity Final [$]:          ${stats['Equity Final [$]']:,.2f}")
    print(f"Return [%]:                 {stats['Return [%]']:.2f}%")
    print(f"Buy & Hold Return [%]:       {stats['Buy & Hold Return [%]']:.2f}%")
    print(f"Sharpe Ratio:               {stats['Sharpe Ratio']:.2f}")
    print(f"Max Drawdown [%]:           {stats['Max. Drawdown [%]']:.2f}%")
    print(f"Win Rate [%]:               {stats['Win Rate [%]']:.2f}%")
    print(f"Total Trades:               {stats['# Trades']}")
    print(f"Profit Factor:              {stats['Profit Factor']:.2f}")
