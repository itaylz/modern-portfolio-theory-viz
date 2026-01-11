import sys
import json
import yfinance as yf
import pandas as pd
import cvxpy as cp
import numpy as np
import matplotlib.pyplot as plt
from datetime import date


'''
NOTE:
Start and End dates can be adjusted for better accuracy.
Efficient Frontier plot can be made more accurate by using better ticker
options however as a default example use pre chosen tickers.
Black-Litterman to be implemented
'''

today = date.today()

def get_prices(tickers, start="2024-01-01", end=today):
    """
    Download adjusted close prices for given tickers.
    Works for both single and multiple tickers.
    """
    data = yf.download(
        tickers, start=start, end=end,
        auto_adjust=True,   # already adjusted, no "Adj Close"
        progress=False
    )
    
    # If multiple tickers, we get columns like ("Close", "AAPL")
    if isinstance(data.columns, pd.MultiIndex):
        prices = data["Close"]  # take the "Close" level
    else:
        prices = data["Close"].to_frame(name=tickers if isinstance(tickers, str) else tickers[0])
    
    return prices.dropna()

def max_sharpe_ratio(returns, rf):
    expected_returns = returns.mean().values * 252
    cov_mat = returns.cov().values * 252
    n = len(expected_returns)

    best_sharpe = -np.inf
    best_weights = None

    # Sweep over lambda values (trade-off between risk and return)
    for lam in np.logspace(-3, 3, 100):
        w = cp.Variable(n)
        risk = cp.quad_form(w, cov_mat)
        ret = expected_returns @ w

        prob = cp.Problem(cp.Minimize(risk - lam * ret),
                          [cp.sum(w) == 1, w >= 0])
        prob.solve(solver=cp.SCS, verbose=False)

        if w.value is not None:
            port_ret = expected_returns @ w.value
            port_risk = np.sqrt(w.value.T @ cov_mat @ w.value)
            sharpe = (port_ret - rf) / port_risk
            if sharpe > best_sharpe:
                best_sharpe = sharpe
                best_weights = w.value

    #check valid weights
    if best_weights is None:
        raise ValueError("Optimisation failed: No valid portfolio found (e.g., flat returns or solver error)")

    weights = np.maximum(best_weights, 0)
    weights /= weights.sum()

    return weights

def minimun_variance(returns):
    #expected annual returns (252 trading days)
    expected_returns = returns.mean().values * 252
    #covariance matrix 
    cov_mat = returns.cov().values * 252
    n = len(expected_returns)
    #w is our unknown weights variable 
    w = cp.Variable(n)
    risk = cp.quad_form(w, cov_mat)

    #using cvxpy to solve quadratic programming under constraints of
    #sum of weights == 1 and non-negative weights
    #results of which will yield max sharpe ratio
    prob = cp.Problem(cp.Minimize(risk), [cp.sum(w) == 1, w >= 0])
    prob.solve()

    if w.value is None:
        raise ValueError("optimisation failed")
    
    weights = np.round(w.value, 4)
    weights[weights < 1e-4] = 0
    weights = weights / weights.sum()

    return weights

def efficient_frontier(returns, n_points=50):
    """
    Compute the efficient frontier.
    returns: DataFrame of daily returns
    n_points: number of portfolios along the frontier
    """
    expected_returns = returns.mean().values * 252 # annualized expected returns
    cov_mat = returns.cov().values * 252 #annualized covariance
    n = len(expected_returns)

    target_returns = np.linspace(expected_returns.min(), expected_returns.max(), n_points)
    risks, rets = [], []

    for R in target_returns:
        w = cp.Variable(n)
        risk = cp.quad_form(w, cov_mat)
        constraints = [cp.sum(w) == 1, w >= 0, expected_returns @ w >= R]
        prob = cp.Problem(cp.Minimize(risk), constraints)
        prob.solve()
        
        if w.value is not None:
            risks.append(np.sqrt(risk.value))
            rets.append(expected_returns @ w.value)

    return np.array(risks), np.array(rets)

# -----------------------------
# Monte Carlo Simulation
# -----------------------------
def random_portfolios(returns, n_portfolios=5000):
    expected_returns = returns.mean().values * 252
    cov_mat = returns.cov().values * 252
    n = len(expected_returns)

    risks, rets, sharpes = [], [], []
    for _ in range(n_portfolios):
        w = np.random.rand(n)
        w /= w.sum()
        ret = expected_returns @ w
        risk = np.sqrt(w.T @ cov_mat @ w)
        sharpe = (ret - 0.02)/risk #assuming risk-free rate of 2%
        rets.append(ret)
        risks.append(risk)
        sharpes.append(sharpe)
    return np.array(risks), np.array(rets), np.array(sharpes)

# -----------------------------
# Black-Litterman Portfolio Optimization
# -----------------------------
def black_litterman(returns, cov_mat, market_weights, P, Q, tau=0.05, rf=0.02):
    """
    Pure numpy Black – Litterman model.
    Uses your already computed:
        - returns DataFrame
        - Ledoit-Wolf covariance (cov_mat)
        - expected returns from CAPM or historical data
        - market_weights (vector of w_m)
    """

    # === 1. Compute equilibrium returns (Pi) ===
    # Pi = delta * cov * w_m
    # Use delta=2.5 if not provided elsewhere
    delta = 2.5  
    pi = delta * cov_mat @ market_weights

    # === 2. Compute posterior expected returns ===
    # μ_BL = [ (τΣ)^(-1) + PᵀΩ⁻¹P ]⁻¹ [ (τΣ)^(-1)π + PᵀΩ⁻¹Q ]

    tau_sigma = tau * cov_mat
    tau_sigma_inv = np.linalg.inv(tau_sigma)

    # Uncertainty of views: Ω = diag(diag(P Σ Pᵀ))
    omega = np.diag(np.diag(P @ cov_mat @ P.T))

    omega_inv = np.linalg.inv(omega)

    A = tau_sigma_inv + P.T @ omega_inv @ P
    b = tau_sigma_inv @ pi + P.T @ omega_inv @ Q

    mu_bl = np.linalg.inv(A) @ b   # posterior expected returns

    # === 3. Max Sharpe Ratio Optimization ===
    n = len(mu_bl)
    w = cp.Variable(n)

    # Objective: maximize excess return
    objective = cp.Maximize((mu_bl - rf) @ w)

    # Constraint: risk <= 1 (unit variance)
    constraints = [cp.quad_form(w, cov_mat) <= 1, w >= 0]

    problem = cp.Problem(objective, constraints)
    problem.solve()

    # Normalize weights to sum to 1 (direction is max-sharpe)
    weights = np.maximum(w.value, 0)
    weights /= weights.sum()

    return weights, mu_bl

def run_optimiser(tickers, start, end, views=None):
    """
    Main logic handler that can be called by API or CLI.
    """
    # Defaults
    if views is None:
         views = {"AAPL": 1, "AMZN": -1} # Example default views

    prices = get_prices(tickers, start=start, end=end)
    
    # [Check if data was returned]
    if prices.empty:
        return {"error": "No data found for tickers"}

    rf = 0.02
    returns = prices.pct_change().dropna()
    
    # 1. Optimizations
    optimized = max_sharpe_ratio(returns, rf)
    min_var = minimun_variance(returns)
    expected_returns = returns.mean().values * 252
    cov_mat = returns.cov().values * 252

    # 2. Monte Carlo
    rand_risks, rand_rets, rand_sharpes = random_portfolios(returns)

    # 3. Black-Litterman Setup
    # Filter views to only include tickers we actually have
    valid_views = {t: v for t, v in views.items() if t in tickers}
    
    P = np.zeros((1, len(tickers)))
    Q = []
    
    # Construct P matrix based on valid_views
    for ticker, view in valid_views.items():
        if ticker in tickers:
            P[0, tickers.index(ticker)] = view
            Q.append(0.02)

    Q = np.array(Q)
    market_weights = np.array([1/len(tickers)] * len(tickers))

    if len(Q) == 0:
        bl_weights = market_weights
        bl_returns = np.zeros(len(tickers))
        bl_risk = 0
        bl_return = 0
    else:
        bl_weights, bl_returns = black_litterman(
            returns, cov_mat, market_weights, P, Q, tau=0.05, rf=rf
        )
        bl_return = np.dot(bl_weights, expected_returns)
        bl_risk   = np.sqrt(np.dot(bl_weights, cov_mat @ bl_weights))

    # 4. Prepare Results
    risks, rets = efficient_frontier(returns, n_points=100)
    sorted_idx = np.argsort(risks)
    risks, rets = risks[sorted_idx], rets[sorted_idx]

    port_return = np.dot(optimized, expected_returns)
    port_risk = np.sqrt(np.dot(optimized, cov_mat @ optimized))

    min_return = np.dot(min_var, expected_returns)
    min_risk = np.sqrt(np.dot(min_var, cov_mat @ min_var))

    cml_x = np.linspace(min_risk, max(risks)*1.1, 100)
    cml_y = rf + ((port_return - rf) / port_risk) * cml_x

    return {
        "meta": {"tickers": tickers, "start": start, "end": end},
        "efficient_frontier": {"risk": risks.tolist(), "return": rets.tolist()},
        "max_sharpe": {
            "risk": float(port_risk),
            "return": float(port_return),
            "weights": {t: float(w) for t, w in zip(tickers, optimized)}
        },
        "monte_carlo": {
            "risk": rand_risks.tolist(), 
            "return": rand_rets.tolist(), 
            "sharpe": rand_sharpes.tolist()
        },
        "min_variance": {
            "risk": float(min_risk), 
            "return": float(min_return), 
            "weights": {t: float(w) for t, w in zip(tickers, min_var)}
        },
        "capital_market_line": {
            "risk": cml_x.tolist(), 
            "return": cml_y.tolist(), 
            "risk_free_rate": float(rf)
        },
        "black_litterman": {
            "risk": float(bl_risk),
            "return": float(bl_return),
            "weights": {t: float(w) for t, w in zip(tickers, bl_weights)},
            "expected_returns": bl_returns.tolist()
        }
    }

def main():
    if len(sys.argv) < 4:
        print(json.dumps({"error": "Not enough arguments"}))
        return
        
    tickers = sys.argv[1].split(",")
    start = sys.argv[2]
    end = sys.argv[3]
    
    result = run_optimiser(tickers, start, end)
    print(json.dumps(result))

if __name__ == "__main__":
    main()
