from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yfinance as yf

# Import the local modules we built earlier
from market_data import get_options_chain
from trading_engine import execute_order, get_portfolio
from database import get_cash

app = FastAPI(title="Options Simulator API")

# Enable CORS so your frontend can communicate with the backend in Codespaces
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the expected JSON structure for incoming trades
class TradeRequest(BaseModel):
    ticker: str
    strike: float
    option_type: str
    expiry: str
    action: str
    quantity: int
    price: float

@app.get("/portfolio")
def portfolio_status():
    """Returns the current cash balance and all open positions."""
    return {
        "cash": round(get_cash(), 2),
        "positions": get_portfolio()
    }

@app.get("/options/{ticker}")
def options_chain(ticker: str, expiry: str):
    """Fetches the options chain and calculates Greeks."""
    try:
        return get_options_chain(ticker, expiry)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch options: {str(e)}")

@app.post("/trade")
def trade(req: TradeRequest):
    """Executes a buy or sell order."""
    result = execute_order(
        req.ticker, req.strike, req.option_type, 
        req.expiry, req.action, req.quantity, req.price
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@app.get("/history/{ticker}")
def historical_data(ticker: str, period: str = "3mo", interval: str = "1d"):
    """Fetches OHLC data specifically formatted for frontend Candlestick charts."""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval=interval)
        
        # Format the data cleanly for a library like Lightweight Charts
        chart_data = []
        for date, row in hist.iterrows():
            chart_data.append({
                "time": date.strftime("%Y-%m-%d"),
                "open": round(row["Open"], 2),
                "high": round(row["High"], 2),
                "low": round(row["Low"], 2),
                "close": round(row["Close"], 2)
            })
        return chart_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch history: {str(e)}")


# --- SERVER STARTUP ---
# This block allows you to run the file directly using `python app.py`
if __name__ == "__main__":
    import uvicorn
    # Use 0.0.0.0 so Codespaces can expose the port correctly
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    import uvicorn
    # 0.0.0.0 is required in Codespaces to expose the port outside the container
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)