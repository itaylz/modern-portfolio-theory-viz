import React, { useState } from "react";
import { PieChart, Pie, Cell, Tooltip, Legend, 
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, ResponsiveContainer
} from "recharts";

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#AA336A"];

export default function PortfolioOptimizer() {
  // 1. STATE MANAGEMENT
  const [tickers, setTickers] = useState("AAPL,MSFT,GOOG,AMZN,TSLA");
  
  // New: Date Pickers (Default to last year)
  const [startDate, setStartDate] = useState("2024-01-01");
  const [endDate, setEndDate] = useState("2025-01-01");
  
  // New: Loading & Error States
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const [data, setData] = useState([]);
  const [stats, setStats] = useState(null);

  //efficient frontier graph
  const [frontierData, setFrontierData] = useState([]);
  //efficient frontier curve
  const [curveData, setCurveData] = useState([]);

  const handleOptimize = async () => {
    // Reset states before starting
    setLoading(true);
    setError(null);
    setData([]);
    setStats(null);

    const tickerArray = tickers.split(",").map(t => t.trim());
    
    // 2. USE DYNAMIC DATES IN REQUEST
    const body = {
      tickers: tickerArray,
      start: startDate,
      end: endDate,
      rf: 0.02
    };

    try {
      const res = await fetch("http://localhost:8080/api/optimise", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });

      // Handle Server Errors (e.g., Bad Ticker)
      if (!res.ok) {
        throw new Error("Failed to optimize. Check tickers or try different dates.");
      }

      const json = await res.json();
      setFrontierData(json.frontier_data);
      setCurveData(json.frontier_curve);

      const chartData = Object.entries(json.weights).map(([ticker, weight]) => ({
        name: ticker,
        value: weight
      }));

      setData(chartData);
      setStats({
        expectedReturn: json.expected_return,
        volatility: json.volatility,
        sharpe: json.sharpe_ratio
      });

    } catch (err) {
      console.error(err);
      setError(err.message); // Show error to user
    } finally {
      setLoading(false); // Stop loading no matter what
    }
  };

  return (
    <div style={{ padding: "40px", fontFamily: "Arial, sans-serif" }}>
      <h1>Portfolio Optimizer</h1>

      {/* INPUT SECTION */}
      <div style={{ display: "flex", gap: "10px", marginBottom: "20px", alignItems: "center" }}>
        <div>
            <label style={{display:"block", fontSize:"12px"}}>Tickers:</label>
            <input
            type="text"
            value={tickers}
            onChange={(e) => setTickers(e.target.value)}
            style={{ width: "300px", padding: "8px" }}
            placeholder="AAPL, MSFT, ..."
            />
        </div>

        <div>
            <label style={{display:"block", fontSize:"12px"}}>Start Date:</label>
            <input 
                type="date" 
                value={startDate} 
                onChange={(e) => setStartDate(e.target.value)}
                style={{ padding: "8px" }}
            />
        </div>
        
        <div>
            <label style={{display:"block", fontSize:"12px"}}>End Date:</label>
            <input 
                type="date" 
                value={endDate} 
                onChange={(e) => setEndDate(e.target.value)}
                style={{ padding: "8px" }}
            />
        </div>

        <button 
            onClick={handleOptimize} 
            disabled={loading} // Disable button while loading
            style={{ 
                padding: "10px 20px", 
                backgroundColor: loading ? "#ccc" : "#007BFF", 
                color: "white", 
                border: "none", 
                cursor: loading ? "not-allowed" : "pointer",
                marginTop: "15px"
            }}
        >
            {loading ? "Optimizing..." : "Optimize"}
        </button>
      </div>

      {/* ERROR MESSAGE */}
      {error && <div style={{ color: "red", marginTop: "10px" }}>⚠️ {error}</div>}

      {/* RESULTS SECTION */}
      {data.length > 0 && (
        <div style={{ marginTop: "30px", display:"flex", gap:"50px" }}>
          <div>
            <h2>Allocation</h2>
            <PieChart width={400} height={400}>
                <Pie
                data={data}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={120}
                label={(entry) => `${entry.name}: ${(entry.value * 100).toFixed(1)}%`}
                >
                {data.map((_, index) => (
                    <Cell key={index} fill={COLORS[index % COLORS.length]} />
                ))}
                </Pie>
                <Tooltip formatter={(value) => `${(value * 100).toFixed(1)}%`} />
                <Legend />
            </PieChart>
          </div>

          <div>
            <h2>Stats</h2>
            <div style={{ fontSize: "18px", lineHeight: "1.6" }}>
                <p><strong>Expected Return:</strong> {(stats.expectedReturn * 100).toFixed(2)}%</p>
                <p><strong>Volatility:</strong> {(stats.volatility * 100).toFixed(2)}%</p>
                <p><strong>Sharpe Ratio:</strong> {stats.sharpe.toFixed(2)}</p>
            </div>
          </div>
        </div>
      )}

      {/* EFFICIENT FRONTIER GRAPH */}
      {frontierData.length > 0 && (
        <div style={{ marginTop: "50px" }}>
          <h2>Efficient Frontier (Monte Carlo)</h2>
          <div style={{ width: "100%", height: 400 }}>
            <ResponsiveContainer>
              <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <CartesianGrid />
                <XAxis 
                  type="number" 
                  dataKey="volatility" 
                  name="Risk" 
                  unit="" 
                  domain={['auto', 'auto']} 
                  label={{ value: 'Risk (Volatility)', position: 'insideBottom', offset: -10 }}
                />
                <YAxis 
                  type="number" 
                  dataKey="return" 
                  name="Return" 
                  unit="" 
                  domain={['auto', 'auto']} 
                  label={{ value: 'Expected Return', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip cursor={{ strokeDasharray: '3 3' }} />

                {/* 1. The Cloud (Random Portfolios) */}
                <Scatter name="Random Portfolios" data={frontierData} fill="#8884d8" fillOpacity={0.5} />

                {/* 2. The Efficient Frontier (The Line) */}
                <Scatter 
                  name="Efficient Frontier" 
                  data={curveData} 
                  fill="none"       // No dots fill
                  line={{ stroke: "#82ca9d", strokeWidth: 3 }} // The Line style
                  shape={() => null} // Hide the dots on the line itself
                />

                {/* 3. The Optimal Portfolio (Star) */}
                <Scatter 
                  name="Optimal" 
                  data={[{ volatility: stats.volatility, return: stats.expectedReturn }]} 
                  fill="#FF0000" 
                  shape="star" 
                  iconSize={200} 
                />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}