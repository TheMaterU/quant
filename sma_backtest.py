import yfinance as yf
import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
from backtesting.lib import crossover

# Define simple moving average crossover strategy
class SmaCross(Strategy):
    n1 = 10
    n2 = 50

    def init(self):
        close = self.data.Close
        self.sma1 = self.I(lambda x: pd.Series(x).rolling(self.n1).mean(), close)
        self.sma2 = self.I(lambda x: pd.Series(x).rolling(self.n2).mean(), close)

    def next(self):
        if crossover(self.sma1, self.sma2):
            self.buy()
        elif crossover(self.sma2, self.sma1):
            self.position.close()

if __name__ == "__main__":
    print("Fetching historical data for AAPL...")
    ticker = yf.Ticker("AAPL")
    df = ticker.history(period="1y")

    if not df.empty:
        # Standardize columns for backtesting package
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        bt = Backtest(df, SmaCross, cash=10000, commission=.002)
        stats = bt.run()
        print("\n=== Backtest Results ===")
        print(stats)
    else:
        print("Failed to download data.")
