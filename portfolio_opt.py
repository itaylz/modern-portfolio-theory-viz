import yfinance as yf
import pandas as pd
import cvxpy as cp
import numpy as np
import matplotlib.pyplot as plt



def get_prices(tickers, start="2024-01-01", end="2025-09-27"):
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
    rf_daily = rf / 252

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
        raise ValueError("optimization failed")
    
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


def main():
    #example stocks: apple, microsoft, amazon, google, bitcoin, tesla 
    tickers = ["AAPL", "MSFT", "AMZN", "GOOGL","BTC-USD","TSLA"]
    prices = get_prices(tickers)

    rf = 0.02  # risk-free rate

    #calculate returns
    returns = prices.pct_change().dropna()
    optimized = max_sharpe_ratio(returns, rf)
    min_var = minimun_variance(returns)

    print(returns.head())
    print(optimized)

    expected_returns = returns.mean().values * 252
    cov_mat = returns.cov().values * 252

    # Monte Carlo 
    rand_risks, rand_rets, rand_sharpes = random_portfolios(returns)

    # Plot individual stock returns
    returns.plot(figsize=(10,5))
    plt.title("Daily Returns of Stocks")
    plt.show()


    risks, rets = efficient_frontier(returns, n_points=100)
    sorted_idx = np.argsort(risks)
    risks, rets = risks[sorted_idx], rets[sorted_idx]

    plt.figure(figsize=(10,6))
    plt.plot(risks, rets, 'b-', lw=2, label="Efficient Frontier")
    #monte carlo plot with random portfolios
    scatter = plt.scatter(rand_risks, rand_rets, c=rand_sharpes, cmap='viridis', 
                          s=10, alpha=0.8, label="Random Portfolios", zorder=1)
    plt.colorbar(scatter, label='Sharpe Ratio')  # Add color scale

    #Max Sharpe
    port_return = np.dot(optimized, expected_returns)
    port_risk = np.sqrt(np.dot(optimized, cov_mat @ optimized))
    plt.scatter(port_risk, port_return, c='r', marker='.', s=200, label="Max Sharpe Ratio", zorder=4)

    #Minimum Volatility
    min_return = np.dot(min_var, expected_returns)
    min_risk = np.sqrt(np.dot(min_var, cov_mat @ min_var))
    plt.scatter(min_risk, min_return, c='r', marker='.', s=200, label="Min Volatility", zorder=3)

    #Capital Market Line
    cml_x = np.linspace(min_risk, max(risks)*1.1, 100)
    cml_y = rf + ((port_return - rf) / port_risk) * cml_x
    plt.plot(cml_x, cml_y, color='black', linewidth=2, linestyle='--', label="Capital Market Line", zorder=2)

    #Optimal Weights
    weights_text = "\n".join([f"{ticker}: {w:.2%}" for ticker, w in zip(tickers, optimized)])
    plt.gcf().text(0.87, 0.65, f"Optimal Weights:\n{weights_text}", fontsize=10, ha='left')

    plt.xlabel("Risk (Std Dev)")
    plt.ylabel("Expected Return")
    plt.title("Efficient Frontier with Max Sharpe Portfolio")
    plt.legend()
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main()
