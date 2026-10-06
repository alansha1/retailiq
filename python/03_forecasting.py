"""
RetailIQ — Revenue Forecasting
================================
Fits multiple forecasting models to monthly revenue and evaluates
them: Linear Trend, ARIMA, and a seasonal decomposition approach.
Outputs a 6-month forward forecast with confidence intervals.

Output:  outputs/forecast/

Usage:
    pip install statsmodels scikit-learn
    python python/03_forecasting.py
"""

import os
import warnings
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import PolynomialFeatures

try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.seasonal import seasonal_decompose
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    print("  ⚠  statsmodels not found — ARIMA skipped. "
          "Install with: pip install statsmodels")

warnings.filterwarnings("ignore")

OUT_DIR = "outputs/forecast"
os.makedirs(OUT_DIR, exist_ok=True)


# ── Prepare monthly series ────────────────────────────────────────────────────
def build_monthly_series(txn: pd.DataFrame) -> pd.Series:
    clean  = txn.loc[txn["is_returned"] == 0].copy()
    monthly = (clean.set_index("transaction_date")["revenue"]
                    .resample("MS")          # Month Start
                    .sum())
    return monthly


# ── Evaluation ────────────────────────────────────────────────────────────────
def evaluate(actual: np.ndarray, predicted: np.ndarray) -> dict:
    mae  = mean_absolute_error(actual, predicted)
    rmse = np.sqrt(mean_squared_error(actual, predicted))
    mape = np.mean(np.abs((actual - predicted) / np.clip(actual, 1e-9, None))) * 100
    return {"MAE": round(mae, 2), "RMSE": round(rmse, 2), "MAPE%": round(mape, 2)}


# ── Model 1: Linear Regression (with time index) ──────────────────────────────
def fit_linear(series: pd.Series, forecast_months=6):
    n = len(series)
    X = np.arange(n).reshape(-1, 1)
    y = series.values

    split = int(n * 0.8)
    model = LinearRegression()
    model.fit(X[:split], y[:split])

    fitted      = model.predict(X)
    test_pred   = model.predict(X[split:])
    metrics     = evaluate(y[split:], test_pred)

    # Forecast
    X_future  = np.arange(n, n + forecast_months).reshape(-1, 1)
    forecast  = model.predict(X_future)
    last_date = series.index[-1]
    fut_dates = pd.date_range(last_date + pd.offsets.MonthBegin(1),
                              periods=forecast_months, freq="MS")

    return {
        "name": "Linear Trend",
        "fitted": pd.Series(fitted, index=series.index),
        "forecast_dates": fut_dates,
        "forecast_values": forecast,
        "split_idx": split,
        "metrics": metrics,
    }


# ── Model 2: Polynomial Regression ───────────────────────────────────────────
def fit_polynomial(series: pd.Series, degree=3, forecast_months=6):
    n   = len(series)
    X   = np.arange(n).reshape(-1, 1)
    y   = series.values
    poly = PolynomialFeatures(degree=degree)
    Xp  = poly.fit_transform(X)
    split = int(n * 0.8)

    model = LinearRegression()
    model.fit(Xp[:split], y[:split])
    fitted    = model.predict(Xp)
    test_pred = model.predict(Xp[split:])
    metrics   = evaluate(y[split:], test_pred)

    X_future  = poly.transform(np.arange(n, n + forecast_months).reshape(-1, 1))
    forecast  = model.predict(X_future)
    last_date = series.index[-1]
    fut_dates = pd.date_range(last_date + pd.offsets.MonthBegin(1),
                              periods=forecast_months, freq="MS")
    return {
        "name": f"Polynomial (deg={degree})",
        "fitted": pd.Series(fitted, index=series.index),
        "forecast_dates": fut_dates,
        "forecast_values": forecast,
        "split_idx": split,
        "metrics": metrics,
    }


# ── Model 3: ARIMA ────────────────────────────────────────────────────────────
def fit_arima(series: pd.Series, order=(1, 1, 1), forecast_months=6):
    if not HAS_STATSMODELS:
        return None
    n     = len(series)
    split = int(n * 0.8)
    train = series.iloc[:split]
    test  = series.iloc[split:]

    try:
        model  = ARIMA(train, order=order)
        result = model.fit()

        # In-sample fit
        fitted = result.fittedvalues

        # Forecast over test period
        test_fc = result.forecast(steps=len(test))
        metrics = evaluate(test.values, test_fc.values)

        # Refit on full series for final forecast
        full_model  = ARIMA(series, order=order).fit()
        fc_result   = full_model.get_forecast(steps=forecast_months)
        forecast    = fc_result.predicted_mean
        ci          = fc_result.conf_int()

        return {
            "name": f"ARIMA{order}",
            "fitted": fitted,
            "forecast_dates": forecast.index,
            "forecast_values": forecast.values,
            "ci_lower": ci.iloc[:, 0].values,
            "ci_upper": ci.iloc[:, 1].values,
            "split_idx": split,
            "metrics": metrics,
        }
    except Exception as e:
        print(f"  ⚠  ARIMA failed: {e}")
        return None


# ── Plot all models together ──────────────────────────────────────────────────
def plot_forecasts(series: pd.Series, models: list):
    fig, axes = plt.subplots(len(models), 1, figsize=(14, 5 * len(models)),
                             sharex=False)
    if len(models) == 1:
        axes = [axes]

    for ax, m in zip(axes, models):
        if m is None:
            continue
        split_idx = m["split_idx"]

        # Actual
        ax.plot(series.index, series.values, color="#212F3C",
                linewidth=2, label="Actual", zorder=3)

        # Fitted
        ax.plot(m["fitted"].index, m["fitted"].values, color="#2E86C1",
                linewidth=1.5, linestyle="--", label="Fitted", alpha=0.85)

        # Train/test split line
        ax.axvline(series.index[split_idx], color="#E74C3C", linewidth=1.2,
                   linestyle=":", label="Train/Test Split")

        # Forecast
        ax.plot(m["forecast_dates"], m["forecast_values"], color="#E67E22",
                linewidth=2.5, marker="o", markersize=5, label="Forecast")

        # Confidence interval (ARIMA only)
        if "ci_lower" in m:
            ax.fill_between(m["forecast_dates"],
                            m["ci_lower"], m["ci_upper"],
                            alpha=0.2, color="#E67E22", label="95% CI")

        ax.set_title(
            f"{m['name']}  —  "
            f"MAE: €{m['metrics']['MAE']:,.0f}  |  "
            f"RMSE: €{m['metrics']['RMSE']:,.0f}  |  "
            f"MAPE: {m['metrics']['MAPE%']:.1f}%",
            fontsize=13
        )
        ax.set_ylabel("Monthly Revenue (€)")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"€{x:,.0f}"))
        ax.legend(loc="upper left", fontsize=10)
        ax.grid(axis="y", alpha=0.4)

    plt.suptitle("RetailIQ — Revenue Forecasting Models", fontsize=16, y=1.005)
    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/01_forecast_comparison.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  ✓ 01_forecast_comparison.png")


def plot_seasonal_decomposition(series: pd.Series):
    if not HAS_STATSMODELS or len(series) < 24:
        return
    result = seasonal_decompose(series, model="additive", period=12)
    fig, axes = plt.subplots(4, 1, figsize=(14, 10), sharex=True)

    for ax, data, label in zip(
        axes,
        [result.observed, result.trend, result.seasonal, result.resid],
        ["Observed", "Trend", "Seasonal", "Residual"]
    ):
        ax.plot(data.index, data.values, color="#1A5276", linewidth=1.5)
        ax.set_ylabel(label)
        ax.axhline(0, color="#AAA", linewidth=0.8, linestyle="--")
        ax.grid(axis="y", alpha=0.35)

    plt.suptitle("RetailIQ — Seasonal Decomposition (Additive, period=12)",
                 fontsize=14, y=1.005)
    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/02_seasonal_decomposition.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  ✓ 02_seasonal_decomposition.png")


def export_forecast_csv(models: list, series: pd.Series):
    rows = []
    for m in models:
        if m is None:
            continue
        for d, v in zip(m["forecast_dates"], m["forecast_values"]):
            rows.append({"model": m["name"], "month": d.strftime("%Y-%m"),
                         "forecast_revenue": round(float(v), 2)})
    pd.DataFrame(rows).to_csv(f"{OUT_DIR}/forecast_values.csv", index=False)

    # Model comparison table
    comp = pd.DataFrame([m["metrics"] | {"Model": m["name"]}
                         for m in models if m is not None])
    comp = comp[["Model", "MAE", "RMSE", "MAPE%"]].set_index("Model")
    comp.to_csv(f"{OUT_DIR}/model_comparison.csv")
    print("  ✓ forecast_values.csv")
    print("  ✓ model_comparison.csv")
    print("\n  ── Model Comparison ──")
    print(comp.to_string())


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("\nRetailIQ — Revenue Forecasting")
    print("=" * 40)

    txn = pd.read_csv("data/raw/transactions.csv", parse_dates=["transaction_date"])
    series = build_monthly_series(txn)
    print(f"  Monthly observations: {len(series)} ({series.index[0].date()} → {series.index[-1].date()})")

    print("\nFitting models...")
    models = [
        fit_linear(series),
        fit_polynomial(series, degree=3),
        fit_arima(series, order=(2, 1, 1)),
    ]
    models = [m for m in models if m is not None]

    print("\nGenerating charts...")
    plot_forecasts(series, models)
    plot_seasonal_decomposition(series)
    export_forecast_csv(models, series)

    print(f"\nAll outputs saved to {OUT_DIR}/")


if __name__ == "__main__":
    main()
