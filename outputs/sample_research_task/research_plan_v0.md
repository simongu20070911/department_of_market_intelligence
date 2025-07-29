# Research Plan v0: Market Anomaly Detection in High-Volatility Periods

## 1.0 Hypothesis

### Primary Hypothesis
The returns and volatility of S&P 500 sectors exhibit statistically significant, non-random patterns during periods of high market volatility (defined as VIX > 30) compared to periods of normal volatility. Specifically, we hypothesize that defensive sectors (e.g., Utilities, Consumer Staples) will outperform cyclical sectors (e.g., Consumer Discretionary, Technology) during these high-stress periods.

### Secondary Hypothesis
1.  **Momentum Reversal:** We hypothesize that stocks exhibiting strong positive momentum in the 5-10 trading days preceding a high-volatility event will experience a statistically significant negative return (reversal) in the 5-10 trading days following the event.
2.  **Correlation Shift:** We hypothesize that inter-sector and intra-sector correlations will increase significantly during high-volatility periods, reducing the benefits of diversification.

## 2.0 Data Sourcing and Hygiene Protocol

**Analysis Period:** January 1, 2020 - December 31, 2024. This period is selected to capture recent market dynamics and ends before the current date.

**Data Sources:**
*   **Stock Prices & Volume:** Daily adjusted close prices and trading volumes for S&P 500 constituents. Source: A reliable financial data provider API (e.g., yfinance, Polygon.io, Alpha Vantage).
*   **VIX Data:** Daily close values for the CBOE Volatility Index (VIX). Source: Same as above, or directly from the CBOE website/data provider.
*   **Sector & Constituent Data:** Historical S&P 500 constituent lists and their corresponding GICS sector classifications.
*   **Market Capitalization:** Daily market cap data for each constituent to enable value-weighted analysis.

**Hygiene Protocol:**
1.  **Survivorship Bias Mitigation:** We will source historical S&P 500 constituent lists for each quarter within the analysis period. The analysis for any given date will use the constituent list that was active at that time. This prevents the bias of only analyzing the companies that survived in the index until the end of the period.
2.  **Data Cleaning:**
    *   Forward-fill and then back-fill any missing daily price/volume data for up to 2 consecutive days. Any stock with more than 2 consecutive missing data points will be excluded from the analysis for that specific period.
    *   Verify and align all data to a common trading calendar.
    *   Calculate daily log returns: `log_return = ln(Price_t / Price_{t-1})`.
3.  **Data Segmentation:** Create a binary indicator variable `is_high_vol` which is `1` if `VIX > 30` and `0` otherwise. This will be used to partition the dataset into "High Volatility" and "Normal Volatility" regimes.
### 3. Experiment Design & Statistical Analysis

#### 3.1. Sector Performance Analysis
- **Experiment 3.1.1:** Identify High-Volatility Regimes.
  - **Procedure:** Filter the entire dataset for periods where the daily VIX close is greater than 30. These periods will be defined as "stressed." All other periods will be "normal."
  - **Statistical Test:** None. This is a filtering step.
- **Experiment 3.1.2:** Calculate Sector-Level Returns.
  - **Procedure:** For both "stressed" and "normal" periods, calculate the market-cap weighted daily returns for each GICS sector.
  - **Statistical Test:** Welch's t-test to determine if the mean daily return of each sector during "stressed" periods is significantly different from "normal" periods. A p-value < 0.05 will be considered significant.
  - **Output:** Table of t-statistics and p-values for each sector.

#### 3.2. Momentum Reversal Analysis
- **Experiment 3.2.1:** Identify Volatility Spikes.
  - **Procedure:** Define a "volatility spike" as a day where the VIX closes above 30, and the previous day it was below 30.
  - **Statistical Test:** None. This is an event definition step.
- **Experiment 3.2.2:** Analyze Post-Spike Returns.
  - **Procedure:** For each stock, calculate the cumulative return over the T+1, T+3, and T+5 trading days following each volatility spike. Compare these returns to the stock's average return over the entire period.
  - **Statistical Test:** Paired t-test to compare post-spike returns to baseline average returns.
  - **Output:** Analysis of returns for top/bottom decile performers in the 30 days preceding the spike.

#### 3.3. Inter-Sector Relationships
- **Experiment 3.3.1:** Correlation Matrix Analysis.
  - **Procedure:** Calculate the Pearson correlation matrix of daily sector returns during "normal" periods and "stressed" periods separately.
  - **Statistical Test:** Fisher's Z-transform to test if the change in correlation coefficients between the two periods is statistically significant.
  - **Output:** Two correlation matrix heatmaps (Normal vs. Stressed) and a matrix of p-values for the change in correlations.

### 4. Predictive Modeling

#### 4.1. Sector Rotation Model
- **Experiment 4.1.1:** Feature Engineering.
  - **Procedure:** For each day, create features that could predict next-day sector performance. Potential features include:
    - VIX level and 5-day change.
    - 5-day and 20-day moving averages of sector returns.
    - 5-day and 20-day moving averages of trading volume.
    - Cross-sector return correlations.
- **Experiment 4.1.2:** Model Training and Validation.
  - **Procedure:** Train a Random Forest classifier to predict which sector will be the top performer the next day. Use time-series cross-validation (e.g., walk-forward validation) to prevent lookahead bias.
  - **Metrics:** Classification accuracy, precision, recall, and F1-score.

### 5. Backtesting & Performance

#### 5.1. Strategy Backtest
- **Experiment 5.1.1:** Long-Short Sector Strategy.
  - **Procedure:** Based on the predictive model, simulate a daily long position in the predicted top-performing sector and a short position in the predicted bottom-performing sector.
  - **Metrics:**
    - Cumulative Return
    - Annualized Sharpe Ratio
    - Maximum Drawdown (MDD)
    - Calmar Ratio (Annualized Return / MDD)

### 6. Required Outputs & Visualizations

1.  **Table:** Summary statistics of VIX index (2020-2024).
2.  **Table:** T-test results for sector returns (Stressed vs. Normal).
3.  **Chart:** Heatmaps of sector correlation matrices (Normal vs. Stressed).
4.  **Chart:** Time-series plot of the VIX with high-volatility periods highlighted.
5.  **Table:** Confusion matrix and classification metrics for the Random Forest model.
6.  **Chart:** Equity curve of the backtested long-short strategy.
7.  **Table:** Key performance metrics of the backtest (Sharpe Ratio, MDD, etc.).
8.  **Report:** Final synthesis of all findings in a structured research report.
