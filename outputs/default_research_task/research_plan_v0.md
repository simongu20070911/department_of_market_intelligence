# Research Plan V0: Market Anomaly Detection in S&P 500 Stocks

**Researcher:** Chief Researcher, ULTRATHINK_QUANTITATIVE Market Alpha
**Date:** 2025-07-28

## 1. Hypothesis Formulation

**Primary Hypothesis:**
*   H1: During periods of high market volatility (defined as VIX > 30), specific S&P 500 sectors, particularly defensive sectors (e.g., Utilities, Consumer Staples) and technology sectors, exhibit statistically significant abnormal returns compared to their baseline performance in low-volatility periods.

**Secondary Hypotheses:**
*   H2: A short-term momentum reversal effect is observable in individual S&P 500 stocks in the 1-5 trading days following a volatility spike (VIX crossing above 30).
*   H3: Changes in inter-sector correlation and trading volume can act as leading indicators for sector rotation in the days immediately preceding and following a high-volatility event.

## 2. Data Sourcing and Hygiene Protocol

**Data Sources:**
*   **Stock Data:** Daily OHLCV (Open, High, Low, Close, Volume) prices for all S&P 500 constituents from 2019-01-01 to 2025-07-28. Sourcing from a reputable financial data provider API (e.g., Alpha Vantage, Polygon.io, or a local data store).
*   **VIX Data:** Daily closing values for the CBOE Volatility Index (VIX) for the same period.
*   **Sector Mappings:** Historical S&P 500 sector classifications (GICS) for all constituents. This is crucial to handle reclassifications and delistings.
*   **Market Cap Data:** Daily market capitalization for each S&P 500 constituent to allow for value-weighted analysis.
*   **Risk-Free Rate:** Daily US Treasury yields (e.g., 3-month T-bill rate) to calculate excess returns and Sharpe ratios.

**Data Hygiene Protocol:**
1.  **Survivorship Bias Mitigation:** Utilize a historical constituents list for the S&P 500 to ensure the analysis includes stocks that were delisted or removed from the index during the period.
2.  **Data Cleaning:**
    *   Check for and handle missing data points (NaNs) in all time series. Imputation method: forward-fill for prices, interpolation for VIX if necessary, but removal of the day's data is preferred if critical values are missing.
    *   Adjust for stock splits and dividends to ensure accurate return calculations.
    *   Filter out any erroneous data points (e.g., price changes of >50% in a single day without a corporate action).
3.  **Data Structuring:**
    *   Merge all datasets into a single, time-indexed pandas DataFrame.
    *   Clearly define high-volatility periods (VIX > 30) and low-volatility periods (VIX <= 30) using a binary flag.
    *   Calculate daily returns: `(Close_t - Close_{t-1}) / Close_{t-1}`.
    *   Calculate daily log returns for specific statistical tests: `ln(Close_t / Close_{t-1})`.

## 3. Experiments and Statistical Analysis

**Experiment 1: Sector Performance during High Volatility (H1)**
*   **Objective:** Quantify sector-specific abnormal returns.
*   **Methodology:**
    1.  For each sector, create two return series: `Returns_HighVIX` and `Returns_LowVIX`.
    2.  Perform an independent two-sample t-test to determine if the mean daily return for each sector during high-VIX periods is statistically different from the mean return during low-VIX periods.
    3.  Calculate the Sharpe Ratio for each sector in both high-VIX and low-VIX environments.
*   **Statistical Tests:**
    *   **Shapiro-Wilk Test:** To check if the return distributions are normal. If not, use a non-parametric alternative.
    *   **Levene's Test:** To check for equal variances.
    *   **Independent Two-Sample T-test (or Welch's T-test if variances are unequal, Mann-Whitney U test if non-normal):** To compare mean returns.
    *   **Confidence Intervals:** Calculate 95% confidence intervals for the mean returns in each regime.

**Experiment 2: Momentum Reversal Analysis (H2)**
*   **Objective:** Test for evidence of momentum reversal post-volatility spike.
*   **Methodology:**
    1.  Identify all "volatility spike events" where the VIX crosses from <=30 to >30.
    2.  For each event, identify the top 10% (quintile 1) and bottom 10% (quintile 5) of performers in the S&P 500 over the preceding 5 days.
    3.  Track the cumulative returns of these two portfolios over the subsequent `T+1`, `T+3`, and `T+5` trading days.
    4.  Aggregate the results across all events and run a paired t-test to see if the "loser" portfolio significantly outperforms the "winner" portfolio.
*   **Statistical Tests:**
    *   **Paired T-test:** To compare the post-spike returns of the winner and loser portfolios.

**Experiment 3: Leading Indicators for Sector Rotation (H3)**
*   **Objective:** Identify predictors for sector performance shifts around volatility events.
*   **Methodology:**
    1.  **Correlation Analysis:**
        *   Calculate rolling 30-day correlation matrices for all sector returns.
        *   Compare the average correlation matrix during high-VIX periods to the one during low-VIX periods.
        *   Use a t-test to identify statistically significant changes in inter-sector correlations.
    2.  **Predictive Modeling (Vector Autoregression - VAR):**
        *   Create a time series model using variables such as:
            *   Daily returns for each sector.
            *   Daily trading volume for each sector.
            *   The daily VIX value.
        *   Test for stationarity using the Augmented Dickey-Fuller (ADF) test. Difference data as needed.
        *   Fit a VAR model to the stationary data.
        *   Use Granger Causality tests to determine if changes in volume or VIX "Granger-cause" changes in sector returns.
*   **Statistical Tests:**
    *   **Augmented Dickey-Fuller (ADF) Test:** For time-series stationarity.
    *   **Granger Causality Test:** To assess predictive power.

## 4. Required Outputs, Charts, and Metrics

**1. Statistical Summary Table:**
*   A table showing, for each sector:
    *   Mean Daily Return (High VIX vs. Low VIX)
    *   P-value from the t-test/Mann-Whitney U test
    *   95% Confidence Interval for mean returns
    *   Sharpe Ratio (High VIX vs. Low VIX)

**2. Correlation Matrix Heatmaps:**
*   A heatmap visualizing the sector-sector correlation matrix for low-volatility periods.
*   A second heatmap for high-volatility periods.
*   A third heatmap showing the *difference* between the two matrices to highlight changes.

**3. Momentum Reversal Chart:**
*   A line chart showing the aggregated cumulative returns of the "winner" and "loser" portfolios in the 5 days following volatility spikes. Error bands (standard error) should be included.

**4. Predictive Model Output:**
*   A summary of the VAR model coefficients.
*   A table of the Granger Causality test results, showing p-values for the predictive relationships between VIX, volume, and sector returns.

**5. Backtesting Report (Synthetic Strategy):**
*   Based on the findings, construct a simple, rules-based strategy (e.g., "rotate into Sector X when VIX > 30").
*   Backtest this strategy from 2020-2024.
*   Report key performance indicators:
    *   Cumulative Return
    *   Annualized Sharpe Ratio
    *   Maximum Drawdown (MDD)
    *   Calmar Ratio (Annualized Return / MDD)

**6. Final Written Report:**
*   A comprehensive document summarizing the methodology, findings, and conclusions, referencing all the outputs listed above. The report will explicitly state whether each hypothesis was supported or refuted by the evidence.
