# Event-Driven Option Backtester

This is a custom-built, event-driven backtesting engine designed specifically for **Options and Equities**.

Unlike vector-based backtesters (which calculate everything at once), this engine steps through time bar-by-bar. This allows for realistic handling of option-specific complexities like auto-expiration, assignment, and modifying positions based on current market depth.

## 🤝 Transparency & Development Process

I believe in being open about how this code was written. This project is a collaboration between human intent and AI assistance (Google Gemini Pro).

* **The AI:** Used as a heavy lifter for boilerplate generation, identifying edge cases in option logic, and drafting initial class structures.
* **The Human:** Responsible for the system architecture, creative problem solving, rigorous prompt engineering, debugging, and verifying the financial logic.

While an AI helped write the lines, the design choices, strategy implementation, and final code validation are my own.

## 🔄 How It Works: The "Lifecycle of a Tick"

To understand this engine, you just need to follow what happens in a single time step. Every time the loop runs (e.g., every minute), the `Engine` orchestrates this specific sequence:

1.  **Time Advances:** The `DataHandler` yields the next bar of data (Price, Bid, Ask) for all subscribed symbols.
2.  **Exchange Cleanup:** Before any trading happens, the `OptionExchange` checks if any options in the portfolio have expired.
    * *ITM (In-The-Money):* Auto-exercised (Option removed, Stock added).
    * *OTM (Out-Of-The-Money):* Expired worthless.
3.  **Mark-to-Market:** The `Portfolio` looks at the new prices and updates the current equity and unrealized PnL.
4.  **Strategy Scan:** The `Strategy` analyzes the new data. If a condition is met (e.g., Price > SMA), it emits a **Signal**.
5.  **Execution:** The `Broker` receives the signal. It checks liquidity, calculates commissions (e.g., $0.65/contract), and converts the signal into a **Fill** (a completed trade).
6.  **Update:** The filled trade is written to the `Portfolio`, updating cash and position counts.

## 🚀 Key Features

* **Multi-Asset & Multi-Ticker:** Designed to handle **Stocks and Options** simultaneously across multiple symbols. You can run strategies that hedge an equity portfolio with options, or trade volatility across diverse tickers without synchronization issues.
* **Pluggable Execution Models:** The architecture separates strategy logic from execution logic, allowing you to stress-test fills under different assumptions.
    * *Default:* **Worst-Case Scenario (WCS)** — Buys at Ask, Sells at Bid (Safety First).
    * *Flexible:* Easily extensible to support Mid-Point (MPS), Best-Case (BCS), or random-walk slippage models to simulate varying liquidity conditions.
* **Event-Driven Accuracy:** Eliminates look-ahead bias by processing data tick-by-tick. The engine adheres to strict chronological ordering, ensuring your strategy only reacts to data that would have historically been available at that exact second.

## 📂 Project Structure

```text
.
├── data/                   # Raw CSVs and processed .arrow files
├── src/
│   ├── data/               # ETL and Time synchronization
│   ├── execution/          # Broker simulation & Option Expiration logic
│   ├── portfolio/          # Position tracking & Mark-to-Market math
│   ├── strategy/           # Logic for entering/exiting trades
│   ├── engine.py           # The main event loop described above
│   └── events.py           # Data classes (Signal, Order, Fill)
├── tests/                  # Pytest suite
└── main.py                 # Entry point