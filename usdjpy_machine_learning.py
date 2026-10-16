import yfinance as yf
import pandas as pd
import numpy as np
import ta
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from backtesting import Backtest, Strategy

class USDJPY_ML_Strategy(Strategy):
    model = None
    scaler_mean = 0
    scaler_std = 1

    def init(self):
        close = pd.Series(self.data.Close)
        high = pd.Series(self.data.High)
        low = pd.Series(self.data.Low)
        volume = pd.Series(self.data.Volume)

        # Feature Engineering for ML Model
        self.rsi = self.I(lambda: ta.momentum.rsi(close, window=14).values)
        self.macd_diff = self.I(lambda: ta.trend.macd_diff(close).values)
        self.atr = self.I(lambda: ta.volatility.average_true_range(high, low, close, window=14).values)
        self.returns_1 = self.I(lambda: close.pct_change(1).values)
        self.returns_5 = self.I(lambda: close.pct_change(5).values)

    def next(self):
        # We need enough historical bars to evaluate
        if len(self.data) < 100:
            return

        price = self.data.Close[-1]
        current_atr = self.atr[-1]
        
        if np.isnan(current_atr) or current_atr <= 0:
            return

        # Build feature vector for current bar
        features = np.array([[
            self.rsi[-1],
            self.macd_diff[-1],
            self.atr[-1],
            self.returns_1[-1],
            self.returns_5[-1]
        ]])

        # Predict using our pre-trained Random Forest model
        # 1 = Bullish/Long, 0 = Bearish/Short
        if USDJPY_ML_Strategy.model is not None:
            pred = USDJPY_ML_Strategy.model.predict(features)[0]

            if pred == 1: # Long Signal
                if self.position.is_short:
                    self.position.close()
                if not self.position.is_long:
                    self.buy(sl=price - 1.8 * current_atr, tp=price + 3.6 * current_atr)
            elif pred == 0: # Short Signal
                if self.position.is_long:
                    self.position.close()
                if not self.position.is_short:
                    self.sell(sl=price + 1.8 * current_atr, tp=price - 3.6 * current_atr)


if __name__ == "__main__":
    print("🐾 Fetching 2 Years of 1-Hour USD/JPY Data for ML Model Training...")
    df = yf.Ticker("USDJPY=X").history(period="2y", interval="1h")[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()

    print("🧠 Engineering Features & Training Random Forest Classifier...")
    # Create dataset for ML training
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    df['MACD_Diff'] = ta.trend.macd_diff(df['Close'])
    df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=14)
    df['Return_1'] = df['Close'].pct_change(1)
    df['Return_5'] = df['Close'].pct_change(5)

    # Define Target: Next 3 periods return > 0 (1 for Up, 0 for Down)
    df['Target'] = np.where(df['Close'].shift(-3) > df['Close'], 1, 0)
    df = df.dropna()

    features = ['RSI', 'MACD_Diff', 'ATR', 'Return_1', 'Return_5']
    X = df[features]
    y = df['Target']

    # Train on first 70%, test on last 30%
    split_idx = int(len(X) * 0.7)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    rf = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    
    train_acc = rf.score(X_train, y_train)
    test_acc = rf.score(X_test, y_test)
    print(f"Model Training Accuracy: {train_acc*100:.2f}% | Test Accuracy: {test_acc*100:.2f}%")

    # Pass trained model to strategy class
    USDJPY_ML_Strategy.model = rf

    # Run Backtest on the test period data
    test_df = df.iloc[split_idx:][['Open', 'High', 'Low', 'Close', 'Volume']]
    
    bt = Backtest(test_df, USDJPY_ML_Strategy, cash=100000, commission=0.00008, margin=0.2, finalize_trades=True)
    stats = bt.run()

    print(f"\n==================================================")
    print(f"🤖 MACHINE LEARNING USD/JPY STRATEGY RESULTS")
    print(f"==================================================")
    print(f"Equity Final [$]:          ${stats['Equity Final [$]']:,.2f}")
    print(f"Return [%]:                 {stats['Return [%]']:.2f}%")
    print(f"Buy & Hold Return [%]:       {stats['Buy & Hold Return [%]']:.2f}%")
    print(f"Sharpe Ratio:               {stats['Sharpe Ratio']:.2f}")
    print(f"Max Drawdown [%]:           {stats['Max. Drawdown [%]']:.2f}%")
    print(f"Win Rate [%]:               {stats['Win Rate [%]']:.2f}%")
    print(f"Total Trades:               {stats['# Trades']}")
    print(f"Profit Factor:              {stats['Profit Factor']:.2f}")
    print(f"==================================================")
