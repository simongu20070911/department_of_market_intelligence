# Research Plan: Market Anomaly Detection in High-Volatility Periods

**Version:** 0.1
**Date:** 2025-07-28
**Author:** ULTRATHINK_QUANTITATIVE Market Alpha Department

## 1. Hypothesis

**Primary Hypothesis:** Specific S&P 500 sectors, particularly defensive sectors (e.g., Utilities, Consumer Staples) and cyclical sectors (e.g., Technology, Consumer Discretionary), exhibit statistically significant, divergent return patterns during periods of high market volatility (VIX > 30) compared to periods of low volatility. We expect defensive sectors to outperform, and cyclical sectors to underperform, on a risk-adjusted basis.

**Secondary Hypothesis:** A short-term momentum reversal effect is observable in individual S&P 500 stocks in the 1-5 trading days following a volatility spike (VIX > 30). Specifically, stocks with high positive momentum in the preceding period will show negative returns, and vice-versa.

## 2. Data Sourcing and Hygiene Protocol

**Data Sources:**
*   **Stock Data:** yfinance library for daily OHLCV (Open, High, Low, Close, Volume) data for all S&P 500 constituents.
*   **VIX Data:** yfinance library for daily VIX close data.
*   **Sector Data:** A reliable source (e.g., a public financial data API or a static file from a reputable provider) for GICS sector classifications for each S&P 500 constituent.
*   **Market Capitalization:** yfinance library for daily market cap data.

**Data Hygiene Protocol:**
1.  **Data Collection:**
    *   Download daily data for all current S&P 500 constituents from 2019-01-01 to 2024-12-31. This includes a buffer year for momentum calculations.
    *   Download daily VIX data for the same period.
    *   Obtain a list of historical S&P 500 constituents to mitigate survivorship bias.
2.  **Data Cleaning:**
    *   Check for and handle missing data (e.g., using forward-fill or back-fill, with a maximum of 3 consecutive missing days).
    *   Adjust for stock splits and dividends using adjusted close prices.
    *   Merge datasets on the date field.
3.  **Feature Engineering:**
    *   Calculate daily returns for each stock.
    *   Calculate daily log returns.
    *   Create a binary 'High Volatility' indicator (1 if VIX > 30, 0 otherwise).

## 3. Experiments and Statistical Tests

**Experiment 1: Sector Performance Analysis**
*   **Objective:** Test the primary hypothesis.
*   **Methodology:**
    1.  Group stocks by sector.
    2.  Calculate daily, weekly, and monthly returns for each sector, both equally-weighted and market-cap weighted.
    3.  Separate the data into 'High Volatility' and 'Low Volatility' periods.
    4.  Perform a two-sample t-test to compare the mean returns of each sector in high vs. low volatility periods.
    5.  Calculate Sharpe ratios for each sector in both periods.
*   **Statistical Tests:** Two-sample t-test, Sharpe ratio calculation.

**Experiment 2: Momentum Reversal Analysis**
*   **Objective:** Test the secondary hypothesis.
*   **Methodology:**
    1.  For each stock, calculate a 30-day rolling momentum score.
    2.  Identify all days where the 'High Volatility' indicator is triggered.
    3.  For each trigger day, analyze the returns of the top and bottom quintiles of stocks (based on momentum) over the next 1, 3, and 5 trading days.
    4.  Perform a paired t-test to compare the returns of the high-momentum and low-momentum portfolios in the post-spike period.
*   **Statistical Tests:** Paired t-test.

**Experiment 3: Sector Correlation Analysis**
*   **Objective:** Analyze changes in inter-sector relationships.
*   **Methodology:**
    1.  Calculate the daily returns for each sector.
    2.  Create two correlation matrices of sector returns: one for 'High Volatility' periods and one for 'Low Volatility' periods.
    3.  Analyze the differences in the correlation matrices.
*   **Statistical Tests:** Pearson correlation coefficient.

**Experiment 4: Predictive Modeling for Sector Rotation**
*   **Objective:** Identify leading indicators for sector rotation.
*   **Methodology:**
    1.  Develop a logistic regression model to predict which sector will be the top performer in the next month.
    2.  Potential features for the model:
        *   VIX level and recent changes.
        *   Moving averages of sector returns.
        *   Relative strength of sectors.
        *   Macroeconomic indicators (e.g., interest rates, inflation).
    3.  Use proper cross-validation techniques (e.g., time-series cross-validation) to evaluate the model's performance.
*   **Statistical Tests:** Logistic regression, AUC-ROC score.

**Experiment 5: Backtesting**
*   **Objective:** Evaluate the profitability of a strategy based on the findings.
*   **Methodology:**
    1.  Develop a simple trading strategy (e.g., long defensive sectors, short cyclical sectors during high volatility).
    2.  Backtest the strategy from 2020-2024.
    3.  Calculate performance metrics: Sharpe ratio, maximum drawdown, cumulative returns.
*   **Statistical Tests:** Sharpe ratio, Sortino ratio.

## 4. Required Outputs, Charts, and Metrics

1.  **Data Summary:**
    *   Table of descriptive statistics for all data sources.
2.  **Sector Performance:**
    *   Table of t-test results for sector returns in high vs. low volatility periods.
    *   Bar chart comparing Sharpe ratios of sectors in both periods.
3.  **Momentum Reversal:**
    *   Table of t-test results for momentum reversal portfolios.
    *   Line chart showing cumulative returns of high-momentum and low-momentum portfolios after a volatility spike.
4.  **Correlation Analysis:**
    *   Heatmaps of the sector correlation matrices for both periods.
5.  **Predictive Model:**
    *   Table of logistic regression coefficients and their significance.
    *   ROC curve for the model.
6.  **Backtesting:**
    *   Equity curve of the backtested strategy.
    *   Table of performance metrics (Sharpe ratio, max drawdown, etc.).
7.  **Final Report:**
    *   A comprehensive report summarizing the findings, with clear visualizations and interpretations of the results.

## 5. Secondary Relationships

*   **VIX Term Structure:** Investigate if the shape of the VIX futures curve (contango vs. backwardation) has any predictive power for sector performance.
*   **Small-Cap vs. Large-Cap:** Compare the performance of small-cap and large-cap stocks during high-volatility periods.
*   **Interest Rate Sensitivity:** Analyze how different sectors' sensitivity to interest rate changes is affected by high volatility.
