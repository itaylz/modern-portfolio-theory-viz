import pytest
import pandas as pd
import numpy as np
import sys
import os

# Ensure we can import from the parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from optimiser import max_sharpe_ratio, minimun_variance, black_litterman

# --- FIXTURES (Setup Synthetic Data) ---

@pytest.fixture
def synthetic_returns():
    """
    Creates a deterministic 2-asset return dataframe.
    Asset A: Low risk, Low return
    Asset B: High risk, High return
    """
    np.random.seed(42) # Crucial for reproducible math tests
    dates = pd.date_range(start="2023-01-01", periods=100)
    
    # Asset A: Mean 0.01, Std 0.01
    asset_a = np.random.normal(0.0005, 0.01, 100)
    # Asset B: Mean 0.03, Std 0.05
    asset_b = np.random.normal(0.0015, 0.05, 100)
    
    df = pd.DataFrame({"Asset_A": asset_a, "Asset_B": asset_b}, index=dates)
    return df

@pytest.fixture
def covariance_matrix(synthetic_returns):
    return synthetic_returns.cov().values * 252

@pytest.fixture
def expected_returns(synthetic_returns):
    return synthetic_returns.mean().values * 252

# --- TESTS ---

def test_max_sharpe_ratio_properties(synthetic_returns):
    """
    Test 1: Do the weights sum to 1?
    Test 2: Are all weights positive? (Long only constraint)
    """
    rf = 0.02
    weights = max_sharpe_ratio(synthetic_returns, rf)
    
    # Check sum is 1.0 (within floating point tolerance)
    np.testing.assert_allclose(np.sum(weights), 1.0, atol=1e-4)
    
    # Check non-negative (allow for tiny solver errors like -1e-10)
    assert np.all(weights >= -1e-4)

def test_minimum_variance_logic(synthetic_returns):
    """
    The Minimum Variance portfolio should theoretically have 
    lower volatility than the Max Sharpe portfolio (usually).
    """
    weights_min_var = minimun_variance(synthetic_returns)
    weights_max_sharpe = max_sharpe_ratio(synthetic_returns, 0.02)
    
    cov = synthetic_returns.cov().values * 252
    
    vol_min_var = np.sqrt(weights_min_var.T @ cov @ weights_min_var)
    vol_max_sharpe = np.sqrt(weights_max_sharpe.T @ cov @ weights_max_sharpe)
    
    # Min Var must be <= Max Sharpe Volatility
    assert vol_min_var <= vol_max_sharpe + 1e-5

def test_black_litterman_shapes(synthetic_returns, covariance_matrix):
    """
    Test that Black-Litterman returns the correct shapes and types
    given specific views.
    """
    n_assets = synthetic_returns.shape[1]
    market_weights = np.array([0.5, 0.5])
    
    # View: Asset A will outperform by 2%
    P = np.array([[1, 0]]) 
    Q = np.array([0.02])
    
    weights, mu_bl = black_litterman(
        synthetic_returns, 
        covariance_matrix, 
        market_weights, 
        P, Q
    )
    
    assert weights.shape == (n_assets,)
    assert mu_bl.shape == (n_assets,)
    np.testing.assert_allclose(np.sum(weights), 1.0, atol=1e-4)

def test_edge_case_flat_returns():
    """
    Test math stability when returns are zero (should handle gracefully or error).
    """
    dates = pd.date_range(start="2023-01-01", periods=10)
    df = pd.DataFrame({"A": [0]*10, "B": [0]*10}, index=dates)
    
    # Depending on implementation, this might raise error or return equal weights
    # We just want to ensure it doesn't crash with a cryptic error
    try:
        max_sharpe_ratio(df, 0.02)
    except Exception as e:
        # Accepting solver errors for edge cases is fine, 
        # but we should know which one.
        assert "optimisation" in str(e).lower() or "singular" in str(e).lower()