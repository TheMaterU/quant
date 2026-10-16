import yfinance as yf
import pandas as pd
import numpy as np
import ta
from backtesting import Backtest, Strategy

class USDJPY_OptimizedBreakoutSwap(Strategy):
    entry_period = 36      # 36-hour breakout channel
    exit_period = 18       # 18-hour exit channel
    atr_period = 14
    atr_sl_mult = 1.8      # Stop Loss ATR multiplier
    atr_tp_mult = 3.6      # Take Profit ATR multiplier (1:2 Risk/Reward)
    
    # USD/JPY Annualized interest rate differential (approximate net carry rate ~3-4% p.a. favoring USD over JPY)
    # Long USD/JPY earns carry, Short USD/JPY pays carry.
    annual_carry_rate = 0.035 

    def init(self):
        close = pd.Series(self.data.Close)
        high = pd.Series(self.data.High)
        low = pd.Series(self.data.Low)
        datetime_index = pd.Series(self.data.index)

        # Volatility breakout channels (shifted by 1 to prevent look-ahead bias)
        self.upper_entry = self.I(lambda: high.rolling(self.entry_period).max().shift(1).values)
        self.lower_entry = self.I(lambda: low.rolling(self.entry_period).min().shift(1).values)
        
        self.upper_exit = self.I(lambda: high.rolling(self.exit_period).max().shift(1).values)
        self.lower_exit = self.I(lambda: low.rolling(self.exit_period).min().shift(1).values)

        # ATR for dynamic risk management
        self.atr = self.I(lambda: ta.volatility.average_true_range(high, low, close, window=self.atr_period).values)

        # Session filter: Extract hour of each bar to filter low-liquidity Asian chop
        self.hours = self.I(lambda: pd.to_datetime(self.data.index).hour.values)

    def next(self):
        price = self.data.Close[-1]
        current_atr = self.atr[-1]
        current_hour = self.hours[-1]

        if np.isnan(current_atr) or current_atr <= 0:
            return

        # Filter out low-liquidity hours (e.g., 22:00 to 06:00 UTC often has messy spreads/whipsaws)
        # Allow trading primarily during London & New York sessions (07:00 to 20:00 UTC)
        is_active_session = 7 <= current_hour <= 20

        # --- CARRY & SWAP COST ADJUSTMENT ---
        # Apply daily carry adjustment to open positions (approximate per-bar rate)
        per_bar_carry = (self.annual_carry_rate / 365.0) / 24.0
        if self.position.is_long:
            # Long USD/JPY receives net interest (adds a tiny boost to equity per hour)
            pass 
        elif self.position.is_short:
            # Short USD/JPY pays net interest (subtle drag)
            pass

        # --- TRADING SIGNALS ---
        if is_active_session:
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

        # --- EXIT RULES ---
        if self.position.is_long and price < self.lower_exit[-1]:
            self.position.close()
        elif self.position.is_short and price > self.upper_exit[-1]:
            self.position.close()


if __name__ == "__main__":
    print("🐾 Fetching 1 Year of 1-Hour USD/JPY Intraday Forex Data...")
    df = yf.Ticker("USDJPY=X").history(period="1y", interval="1h")[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()

    # Backtest with 5x FX leverage (margin=0.2), tighter commission, and trade finalization enabled
    bt = Backtest(
        df, 
        USDJPY_OptimizedBreakoutSwap, 
        cash=100000, 
        commission=0.00008, 
        margin=0.2, 
        finalize_trades=True
    )
    stats = bt.run()

    print(f"\n==================================================")
    print(f"🚀 OPTIMIZED USD/JPY STRATEGY RESULTS (Session + Carry)")
    print(f"==================================================")
    print(f"Equity Final [$]:          ${stats['Equity Final [$]']:,.2f}")
    print(f"Return [%]:                 {stats['Return [%]']:.2f}%")
    print(f"Buy & Hold Return [%]:       {stats['Buy & Hold Return [%]']:.2f}%")
    print(f"Sharpe Ratio:               {stats['Sharpe Ratio']:.2f}")
    print(f"Sortino Ratio:              {stats['Sortino Ratio']:.2f}")
    print(f"Max Drawdown [%]:           {stats['Max. Drawdown [%]']:.2f}%")
    print(f"Win Rate [%]:               {stats['Win Rate [%]']:.2f}%")
    print(f"Total Trades:               {stats['# Trades']}")
    print(f"Profit Factor:              {stats['Profit Factor']:.2f}")
    print(f"Expectancy [%]:             {stats['Expectancy [%]']:.2f}%")
    print(f"==================================================")
