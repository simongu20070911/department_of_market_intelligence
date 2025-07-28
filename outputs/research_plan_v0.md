# ULTRATHINK_QUANTITATIVE Market Alpha
## Research Plan v0.0
## Project: Market Anomaly Detection in High-Volatility Regimes

---

### 1.0 Hypothesis Formulation

**1.1. Primary Hypothesis (H1):**
High-volatility regimes, defined as periods where the VIX index is greater than 30, induce predictable, non-random patterns in S&P 500 sector returns. These patterns deviate significantly from baseline market behavior and are characterized by:
a) Statistically significant outperformance or underperformance of specific GICS sectors.
b) A measurable momentum reversal effect in the days immediately following a volatility spike.

**1.2. Null Hypothesis (H0):**
Sector returns and momentum factors during high-volatility regimes are statistically indistinguishable from those during normal market conditions (VIX <= 30). Any observed performance deviations are attributable to random chance and do not represent a persistent, exploitable anomaly.

**1.3. Secondary Hypothesis (H2):**
Changes in the correlation structure between sectors and abnormal trading volumes can serve as leading indicators for sector rotation during the transition into and within high-volatility regimes.

---

### 2. Data Sourcing and Hygiene Protocols

**2.1. Data Sources:**
- **Stock Data:** Daily OHLCV (Open, High, Low, Close, Volume), and market capitalization for all S&P 500 constituents from 2019-01-01 to 2025-07-28. The start date is extended to 2019 to allow for a baseline "normal" period. Data to be sourced from a reputable financial data provider (e.g., Yahoo Finance, Alpha Vantage).
- **VIX Data:** Daily closing values for the CBOE Volatility Index (VIX) for the same period.
- **Sector Mappings:** GICS (Global Industry Classification Standard) sector classifications for each S&P 500 constituent.

**2.2. Data Hygiene and Pre-processing:**
- **Missing Data:**
    - Any stock with more than 10% of missing data points in the analysis period will be excluded.
    - For remaining stocks, missing price or volume data will be imputed using forward-fill, assuming the last known value is the best estimator for a short period.
    - Missing VIX data will be imputed using linear interpolation.
- **Survivorship Bias:**
    - The list of S&P 500 constituents will be fetched for the beginning of each calendar year (2020, 2021, 2022, 2023, 2024, 2025). The analysis for that year will be performed on the respective constituent list to mitigate survivorship bias.
- **Data Alignment:** All data series will be aligned by date. Non-trading days will be handled consistently across all datasets.
- **Return Calculation:** Daily logarithmic returns will be calculated as `ln(Price_t / Price_{t-1})`.
- **Volatility Regimes:**
    - **High-Volatility:** Days where VIX > 30.
    - **Normal-Volatility:** Days where VIX <= 30.
