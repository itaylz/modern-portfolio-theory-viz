# 📈 Portfolio Optimization with Modern Portfolio Theory & Black–Litterman

This project implements **portfolio optimization** using **Modern Portfolio Theory (MPT)** and extends it with the **Black–Litterman model** for more robust and realistic results.  
It combines theory from quantitative finance with real market data fetched via `yfinance`.

---

## 🧠 Overview

The project demonstrates how to:
- Construct and visualize the **efficient frontier**
- Compute the **optimal risk-return tradeoff** portfolio
- Integrate **real stock data** into optimization
- Apply **Ledoit–Wolf covariance shrinkage** for numerical stability
- Incorporate **investor views** using the **Black–Litterman model**

---

## ⚙️ Features

| Module | Description |
|---------|-------------|
| **Data Fetching** | Downloads adjusted close prices from Yahoo Finance |
| **Return Estimation** | Computes log returns and expected returns |
| **Covariance Estimation** | Uses Ledoit–Wolf shrinkage estimator for robust covariance |
| **Optimization** | Solves for weights that maximize the Sharpe ratio or minimize risk |
| **Efficient Frontier Plot** | Visualizes the efficient frontier, random portfolios, and optimal portfolio |
| **Black–Litterman Integration** | Blends equilibrium market returns with investor-specific views |
| **Capital Market Line (CML)** | Plots the tangency portfolio and theoretical CML line |

---

## 🧩 Dependencies

Make sure you have the following Python packages installed:

```bash
pip install yfinance numpy pandas matplotlib cvxpy scikit-learn PyPortfolioOpt

