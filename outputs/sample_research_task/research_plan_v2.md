# Research Plan v2: Market Anomaly Detection in High-Volatility Periods

**Note on Revisions:** This version (`v2`) is a comprehensive revision that incorporates all mandatory feedback from `senior_critique_v0.md` and `senior_critique_v1.md`. It introduces a programmatic analysis period, sophisticated feature engineering, robust statistical corrections, and critically, benchmark comparisons to validate the economic significance of any findings.

## 1.0 Hypothesis

(Hypotheses remain unchanged from v1)

## 2.0 Data Sourcing and Hygiene Protocol

**Analysis Period:** January 1, 2020 to T-1 (where T is the date of execution). **Correction:** The end date is now defined programmatically to eliminate lookahead bias and ensure reproducibility.

**Data Sources:**
*   **Stock Prices & Volume:** Daily adjusted close prices and trading volumes for S&P 500 constituents.
*   **VIX Data:** Daily close values for the CBOE Volatility Index (VIX) and VIX term structure data (e.g., front-month vs. second-month futures).
*   **Credit & Options Market Data:** Data for the MOVE Index (bond market volatility) and the CBOE Skew Index.
*   **Sector & Constituent Data:** Historical S&P 500 constituent lists and GICS classifications.
*   **Market Capitalization:** Daily market cap data.

**Hygiene Protocol:**
1.  **Survivorship Bias Mitigation:** Unchanged.
2.  **Data Cleaning:** Unchanged.
3.  **Data Segmentation:** Regimes for initial analysis will be defined dynamically (rolling percentile), with subsequent analysis treating volatility as a continuous variable.

### 3.0 Experiment Design & Statistical Analysis

#### 3.1. Preliminary Statistical Validation
- **Experiment 3.1.1:** Test for Normality (Shapiro-Wilk) and Stationarity (ADF).
- **Experiment 3.1.2: Multiple Comparison Correction Framework (New)**
  - **Procedure:** All experiments involving multiple simultaneous statistical tests (e.g., across all 11 GICS sectors) will have their resulting p-values adjusted to mitigate the risk of false positives (Type I errors).
  - **Statistical Method:** We will apply the Benjamini-Hochberg procedure to control the False Discovery Rate (FDR).
  - **Rationale:** This directly addresses the "Multiple Testing Fallacy" critique and is crucial for maintaining statistical rigor.

#### 3.2. Dynamic Market Regime and Volatility Analysis (Revised)
- **Experiment 3.2.1:** Identify High-Volatility Regimes (Dynamic Threshold). This will be used for initial comparative analysis only.
- **Experiment 3.2.2: Volatility as a Continuous Variable (New)**
  - **Procedure:** Instead of a binary classification, we will analyze the relationship between key outcomes (e.g., sector returns) and the VIX level as a continuous variable.
  - **Statistical Test:** Spearman Rank Correlation to measure the strength and direction of the monotonic relationship between the VIX level and sector returns.
  - **Rationale:** This addresses the critique that a binary regime definition is overly simplistic and loses valuable information.

#### 3.3. Sector Performance & Momentum Reversal Analysis
- **Procedure:** Sector performance and momentum reversals will be analyzed using non-parametric tests (Mann-Whitney U, Wilcoxon signed-rank) as established in v1, with p-values adjusted per Experiment 3.1.2.

### 4. Predictive Modeling

#### 4.1. Sector Rotation Model (Revised)
- **Experiment 4.1.1: Advanced Feature Engineering (Revised)**
  - **Procedure:** The feature set will be expanded beyond simple price/volume derivatives to include more sophisticated, orthogonal factors.
  - **Feature Set:**
    - **Market-wide Volatility:** VIX level, 1-month and 3-month changes in VIX.
    - **Volatility Term Structure:** The ratio of front-month to second-month VIX futures (a measure of market contango/backwardation).
    - **Cross-Asset Risk:** The MOVE Index (bond market volatility) to capture systemic risk-off sentiment.
    - **Tail Risk:** The CBOE Skew Index to measure the perceived risk of outlier negative returns.
    - **Internal Momentum & Reversal:** Standard momentum factors will still be included for comparison.
  - **Rationale:** This addresses the "Naive Feature Engineering" critique by exploring factors less likely to be arbitraged away.

- **Experiment 4.1.2:** Model Training and Validation using time-series cross-validation.

### 5.0 Backtesting & Performance

#### 5.1. Strategy & Benchmark Backtesting (Revised)
- **Experiment 5.1.1: Predictive Model Long-Short Strategy**
  - **Procedure:** Simulate a daily rebalanced, market-neutral portfolio that goes long the predicted top-performing sector and short the predicted bottom-performing sector.
  - **Transaction Costs:** All simulated trades will incur a 5 basis point cost per trade.
- **Experiment 5.1.2: Benchmark Strategy Comparison (CRITICAL NEW SECTION)**
  - **Procedure:** To establish the economic value of the predictive model, its performance will be compared against two non-predictive benchmarks.
  - **Benchmark 1: S&P 500 Buy-and-Hold.** Represents the base market return.
  - **Benchmark 2: Static Defensive/Cyclical Portfolio.** A simple strategy that is always long a market-cap weighted basket of defensive sectors (Utilities, Consumer Staples, Health Care) and short cyclical sectors (Consumer Discretionary, Technology, Industrials). This directly tests the primary hypothesis without any predictive timing model.
  - **Rationale:** This addresses the critical "Lack of a Benchmark" flaw. The predictive model is only valuable if it can significantly outperform these simpler, static strategies after costs.

### 6. Required Outputs & Visualizations (Revised)

1.  **Table:** P-values from Normality and Stationarity tests.
2.  **Table:** Adjusted p-values (Benjamini-Hochberg) for all multi-test experiments.
3.  **Table:** Spearman Rank Correlation results for VIX vs. Sector Returns.
4.  **Chart:** Feature importance plot from the Random Forest model, highlighting the contribution of advanced features.
5.  **Table:** Confusion matrix and classification metrics for the Random Forest model.
6.  **Table: Comparative Performance Metrics (Net of Costs).** This table will be the primary output, comparing Cumulative Return, Annualized Sharpe Ratio, Maximum Drawdown (MDD), and Calmar Ratio across:
    -   Predictive Long-Short Strategy
    -   Benchmark 1: S&P 500 Buy-and-Hold
    -   Benchmark 2: Static Defensive/Cyclical Portfolio
7.  **Chart: Comparative Equity Curves.** A single chart plotting the equity curves of the predictive strategy and both benchmark strategies.
8.  **Report:** Final synthesis of all findings, with a clear conclusion on whether the model provides a statistically and economically significant edge over benchmarks.
