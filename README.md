# 📈 Full-Stack Portfolio Optimiser

A financial engineering tool that leverages **Modern Portfolio Theory (MPT)** to construct the optimal portfolio for any set of stock tickers. The application performs a Monte Carlo simulation to visualise the risk/return landscape and uses the Critical Line Algorithm (CLA) to mathematically identify the Efficient Frontier.

## 🚀 Features
* **Dynamic Optimisation:** Fetches real-time market data (via Yahoo Finance) for any custom date range.
* **Monte Carlo Simulation:** Generates 2,000+ random portfolio combinations to visualise the feasible set.
* **Efficient Frontier:** Mathematically calculates the "Perfect Line" (Maximum return for minimal risk) using the Critical Line Algorithm.
* **Interactive Visualisation:**
    * **Pie Chart:** Exact asset allocation weights.
    * **Scatter Plot:** Visual comparison of the "Cloud" (random portfolios) vs. the "Star" (optimal portfolio).
* **Robust Architecture:** Fully Dockerized microservices ensuring isolation and easy deployment.

## 📐 Manual Maths Verification
**"Trust, but Verify."**
To ensure the Python "Black Box" optimisation is accurate, this project includes a dedicated manual verification file which manually calculates some of the features using CVXPY (`/optimiser`).

* **Process:** The covariance matrices, expected returns, and Sharpe Ratios calculated by the Python algorithms were cross-referenced against manual matrix multiplication in Excel/Spreadsheets.
* **Result:** The automated engine produces results within a <0.01% margin of error compared to the manual derivation, confirming the integrity of the maths models.

## 🛠 Tech Stack

### **Frontend**
* **React.js:** Dynamic UI and state management.
* **Recharts:** Complex data visualisation (Scatter plots, Pie charts).

### **Backend (Financial Engine)**
* **Python (FastAPI):** High-performance API handling.
* **PyPortfolioOpt:** The core library for convex optimisation and CLA.
* **NumPy:** Vectorised calculations for Monte Carlo simulations.
* **yFinance:** Market data ingestion.

### **Infrastructure**
* **Docker & Docker Compose:** Containerisation of both services and internal networking.

## ⚡️ Getting Started

### Prerequisites
* Docker & Docker Desktop installed.

### Installation
1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/itay/modern-portfolio-theory-viz.git](https://github.com/itaylz/modern-portfolio-theory-viz.git)
    cd YOUR_REPO
    ```

2.  **Build and Run via Docker:**
    The entire app handles its own dependencies inside the containers.
    ```bash
    docker-compose up --build
    ```
    NOTE: If app start-up is too slow comment out the frontend section in the docker-compose.yml and run the react service      locally using:
    ```bash
     npm start
    ```

4.  **Access the App:**
    * **Frontend:** Open `http://localhost:3000`
    * **Backend API:** Running on `http://localhost:8080`

## 🧠 How It Works (The Maths)
1.  **User Input:** Tickers (e.g., `AAPL, TSLA`) and Date Range are sent to the backend.
2.  **Data Ingestion:** Historical adjusted closing prices are downloaded.
3.  **Statistical Analysis:**
    * Calculates **Expected Returns** (Mean historical return).
    * Calculates **Covariance Matrix** (Risk correlation between assets).
4.  **Optimisation (convex):**
    * Solves for weights $w$ that maximise $\frac{R_p - R_f}{\sigma_p}$ (Sharpe Ratio).
5.  **Simulation:**
    * Randomly assigns weights 2,000 times to map the volatility surface.

