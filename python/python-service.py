from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import traceback 
import yfinance as yf 
from pypfopt import EfficientFrontier, risk_models, expected_returns, CLA
import numpy as np 

app = FastAPI(title="Portfolio Optimizer API")

class OptimizeRequest(BaseModel):
    tickers: List[str]
    start: Optional[str] = "2024-01-01"
    end: Optional[str] = None
    rf: Optional[float] = 0.02
    view: Optional[dict] = None

import traceback # Make sure this is imported at the top

@app.post("/optimize")
def optimize_portfolio(request: OptimizeRequest):
    print(f"\n\n--- STARTED OPTIMIZATION FOR: {request.tickers} ---", flush=True)
    
    try:
        # 1. Validation
        if not request.tickers or len(request.tickers) < 2:
            raise ValueError("Need at least 2 stocks to optimize.")

        # 2. Download Data
        print("Step 1: Downloading data from Yahoo...", flush=True)
        data = yf.download(request.tickers, start = request.start, end = request.end, auto_adjust=True)['Close']
        
        if data.empty or data.shape[1] == 0:
            print("CRITICAL ERROR: Yahoo returned no data.", flush=True)
            raise ValueError("Yahoo Finance returned empty data. Check internet connection.")
            
        print(f"Step 2: Data downloaded. Shape: {data.shape}", flush=True)

       # 3. Calculate Returns
        print("Step 3: Calculating returns...", flush=True)
        
        #expected_returns (module) . mean_historical_return (function)
        mu = expected_returns.mean_historical_return(data)
        
        #risk_models (module) . sample_cov (function)
        S = risk_models.sample_cov(data)

        # 4. Optimization
        print("Step 4: Running Convex Optimizer...", flush=True)
        ef = EfficientFrontier(mu, S)

        # Calculate the raw weights
        ef.max_sharpe() 
        cleaned_weights = ef.clean_weights()
        # --------------------------

        # --- 5. MONTE CARLO SIMULATION (The Cloud) ---
        print("Step 5: Running Monte Carlo Simulation...", flush=True)
        num_simulations = 2000
        simulation_results = []
        
        # Convert to numpy for fast math
        mu_np = mu.to_numpy()
        S_np = S.to_numpy()
        n_assets = len(mu)

        for _ in range(num_simulations):
            # Generate random weights
            w = np.random.random(n_assets)
            w /= np.sum(w) # Normalize so they sum to 1
            
            # Calculate Risk & Return for this random portfolio
            p_ret = np.sum(mu_np * w)
            p_vol = np.sqrt(np.dot(w.T, np.dot(S_np, w)))
            
            simulation_results.append({
                "volatility": float(p_vol), 
                "return": float(p_ret)
            })

        # --- 6. CALCULATE THE ACTUAL FRONTIER CURVE (The Line) ---
        print("Step 6: Calculating Efficient Frontier Curve...", flush=True)
        cla = CLA(mu, S)
        (cla_mu, cla_sigma, cla_weights) = cla.efficient_frontier()

        # Format for frontend: List of { volatility, return }
        # cla_sigma is risk (x-axis), cla_mu is return (y-axis)
        frontier_curve = []
        for r, v in zip(cla_mu, cla_sigma):
            frontier_curve.append({
                "return": float(r),
                "volatility": float(v)
        })

        performance = ef.portfolio_performance(verbose=False)
        
        print("--- SUCCESS! Returning results. ---\n\n", flush=True)

        return {
            "weights": cleaned_weights,
            "expected_return": performance[0],
            "volatility": performance[1],
            "sharpe_ratio": performance[2],
            "frontier_data": simulation_results,
            "frontier_curve": frontier_curve
        }

    except Exception as e:
        # THIS IS THE PART THAT WILL SHOW US THE ERROR
        print("\n\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", flush=True)
        print("PYTHON CRASHED HERE:", flush=True)
        print(f"Error Message: {str(e)}", flush=True)
        print("Traceback:", flush=True)
        traceback.print_exc()
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n\n", flush=True)
        
        # Send a helpful message back to Java/React
        raise HTTPException(status_code=500, detail=f"Python Error: {str(e)}")

@app.get("/health")
def health():
    return {"status": "ok"}