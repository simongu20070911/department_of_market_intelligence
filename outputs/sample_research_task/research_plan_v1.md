# Research Plan v1: Market Anomaly Detection in High-Volatility Periods

## 1.0 Hypothesis

### Primary Hypothesis
The returns and volatility of S&P 500 sectors exhibit statistically significant, non-random patterns during periods of high market volatility compared to periods of normal volatility. We hypothesize that defensive sectors (e.g., Utilities, Consumer Staples) will systematically outperform cyclical sectors (e.g., Consumer Discretionary, Technology) during these high-stress periods.

### Secondary Hypothesis
1.  **Momentum Reversal:** We hypothesize that stocks exhibiting strong positive momentum preceding a high-volatility event will experience a statistically significant negative return (reversal) in the days following the event.
2.  **Correlation Shift:** We hypothesize that inter-sector and intra-sector correlations will increase significantly during high-volatility periods, reducing the benefits of diversification.

## 2.0 Data Sourcing and Hygiene Protocol

**Analysis Period:** January 1, 2020 - July 28, 2025. **Correction:** The end date has been revised to the day prior to the current date to eliminate lookahead bias.

**Data Sources:**
*   **Stock Prices & Volume:** Daily adjusted close prices and trading volumes for S&P 500 constituents. Source: A reliable financial data provider API (e.g., yfinance, Polygon.io, Alpha Vantage).
*   **VIX Data:** Daily close values for the CBOE Volatility Index (VIX). Source: Same as above.
*   **Sector & Constituent Data:** Historical S&P 500 constituent lists and their corresponding GICS sector classifications.
*   **Market Capitalization:** Daily market cap data for each constituent.

**Hygiene Protocol:**
1.  **Survivorship Bias Mitigation:** Source historical S&P 500 constituent lists for each quarter. The analysis for any given date will use the constituent list that was active at that time.
2.  **Data Cleaning:**
    *   Forward-fill and then back-fill any missing daily price/volume data for up to 2 consecutive days.
    *   Verify and align all data to a common trading calendar.
    *   Calculate daily log returns: `log_return = ln(Price_t / Price_{t-1})`.
3.  **Data Segmentation:** Regimes will be defined dynamically based on a rolling percentile of the VIX, as detailed in Experiment 3.1.
### 3.0 Experiment Design & Statistical Analysis

#### 3.1. Preliminary Statistical Validation (New Section)
- **Experiment 3.1.1:** Test for Normality and Stationarity.
  - **Procedure:** Before applying comparative tests, all return series (sector-level and individual stock) will be tested for statistical properties.
  - **Statistical Test:** Shapiro-Wilk test for normality and Augmented Dickey-Fuller (ADF) test for stationarity.
  - **Rationale:** Financial returns are often non-normal and non-stationary. This step ensures that the statistical tests chosen in subsequent sections are appropriate for the data's true distribution, addressing the critique's concern about invalid assumptions.

#### 3.2. Dynamic Market Regime Identification (Revised)
- **Experiment 3.2.1:** Identify High-Volatility Regimes.
  - **Procedure:** Define "high volatility" dynamically. A day is classified as "stressed" if its VIX value is in the top decile (90th percentile) of the VIX values from the preceding 252 trading days (a rolling one-year window). All other periods are "normal."
  - **Rationale:** This approach adapts to changing market conditions, ensuring that "high volatility" is defined relative to the recent market context, rather than a static, arbitrary threshold like `VIX > 30`. It also includes a check to ensure the number of "stressed" days is sufficient for analysis.

#### 3.3. Sector Performance Analysis (Revised)
- **Experiment 3.3.1:** Calculate Sector-Level Returns.
  - **Procedure:** For both "stressed" and "normal" periods, calculate the market-cap weighted daily returns for each GICS sector.
- **Experiment 3.3.2:** Compare Sector Returns.
  - **Statistical Test:** Based on the results of Experiment 3.1.1, we will use the **Mann-Whitney U test** (a non-parametric alternative to the t-test) to determine if the median daily returns of each sector are significantly different between regimes. A p-value < 0.05 will be considered significant.
  - **Rationale:** The Mann-Whitney U test does not assume a normal distribution, making it far more robust for analyzing financial returns.

#### 3.4. Momentum Reversal Analysis (Revised)
- **Experiment 3.4.1:** Identify Volatility Spikes using the dynamic threshold.
- **Experiment 3.4.2:** Analyze Post-Spike Returns using the **Wilcoxon signed-rank test** to compare post-spike returns to a baseline.
  - **Rationale:** This is a non-parametric paired test, making it suitable for non-normal data.

### 4. Predictive Modeling

#### 4.1. Sector Rotation Model
- **Experiment 4.1.1:** Feature Engineering. (No change in procedure).
- **Experiment 4.1.2:** Model Training and Validation.
  - **Procedure:** Train a Random Forest classifier using time-series cross-validation. Crucially, we will ensure that the number of samples in the "stressed" class is sufficient for training a meaningful model. If not, the scope of this experiment will be re-evaluated.

### 5. Backtesting & Performance

#### 5.1. Strategy Backtest (Revised)
- **Experiment 5.1.1:** Long-Short Sector Strategy with Realistic Costs.
  - **Procedure:** Simulate a daily long/short strategy based on the model's predictions.
  - **Transaction Cost Model (New):** All simulated trades will incur a realistic cost assumption (e.g., 5 basis points per trade) to account for slippage and commissions.
  - **Metrics:** All performance metrics (Sharpe Ratio, MDD, etc.) will be calculated on returns **net of transaction costs**.
  - **Rationale:** This provides a far more realistic assessment of the strategy's viability.

### 6. Required Outputs & Visualizations (Revised)

1.  **Table:** P-values from Normality and Stationarity tests.
2.  **Table:** Mann-Whitney U test results for sector returns.
3.  **Chart:** Heatmaps of Spearman Rank correlation matrices (robust to outliers).
4.  **Chart:** Time-series plot of the VIX with dynamically identified high-volatility periods highlighted.
5.  **Table:** Classification metrics for the Random Forest model.
6.  **Chart:** Equity curve of the backtested strategy, explicitly labeled "Net of Transaction Costs."
7.  **Table:** Key performance metrics of the backtest (net returns).
8.  **Report:** Final synthesis of all findings.
