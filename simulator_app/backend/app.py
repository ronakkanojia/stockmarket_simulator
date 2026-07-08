from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import yfinance as yf

from market_data import (
    get_options_chain,
    get_available_expiries,
    OptionsDataError,
)

from trading_engine import (
    execute_order,
    get_portfolio,
)

from database import get_cash


# ==========================================
# FastAPI App
# ==========================================

app = FastAPI(
    title="NIFTY Options Simulator API",
    version="2.0.0"
)


# ==========================================
# CORS
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# Request Models
# ==========================================

class TradeRequest(BaseModel):
    ticker: str
    strike: float
    option_type: str
    expiry: str
    action: str
    quantity: int
    price: float


# ==========================================
# Portfolio
# ==========================================

@app.get("/portfolio")
def portfolio_status():

    return {
        "cash": round(get_cash(), 2),
        "positions": get_portfolio()
    }


# ==========================================
# Available Expiries
# ==========================================

@app.get("/options/{ticker}/expiries")
def options_expiries(ticker: str):

    try:

        symbol_map = {
            "NIFTY": "^NSEI",
            "BANKNIFTY": "^NSEBANK",
            "^NSEI": "^NSEI",
            "^NSEBANK": "^NSEBANK"
        }

        ticker = symbol_map.get(
            ticker.upper(),
            ticker.upper()
        )

        return {
            "ticker": ticker,
            "expiries": get_available_expiries(ticker)
        }

    except OptionsDataError as e:

        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch expiries: {e}"
        )


# ==========================================
# Options Chain
# ==========================================

@app.get("/options/{ticker}")
def options_chain(
    ticker: str,
    expiry: str
):

    try:

        symbol_map = {
            "NIFTY": "^NSEI",
            "BANKNIFTY": "^NSEBANK",
            "^NSEI": "^NSEI",
            "^NSEBANK": "^NSEBANK"
        }

        ticker = symbol_map.get(
            ticker.upper(),
            ticker.upper()
        )

        return get_options_chain(
            ticker,
            expiry
        )

    except OptionsDataError as e:

        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch options: {e}"
        )
    # ==========================================
# Execute Trade
# ==========================================

@app.post("/trade")
def trade(req: TradeRequest):

    result = execute_order(
        ticker=req.ticker,
        strike=req.strike,
        option_type=req.option_type,
        expiry=req.expiry,
        action=req.action,
        quantity=req.quantity,
        price=req.price
    )

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result["message"]
        )

    return result


# ==========================================
# Historical Chart Data
# ==========================================

@app.get("/history/{ticker}")
def historical_data(
    ticker: str,
    period: str = "1mo",
    interval: str = "1d"
):
    """
    Returns OHLC data formatted for Lightweight Charts.
    Supports aliases like NIFTY and BANKNIFTY.
    """

    try:

        symbol_map = {
    "NIFTY": "^NSEI",
    "^NSEI": "^NSEI",

    "BANKNIFTY": "^NSEBANK",
    "^NSEBANK": "^NSEBANK",

    "FINNIFTY": "NIFTY_FIN_SERVICE.NS",

    "MIDCPNIFTY": "NIFTY_MID_SELECT.NS"
}
        print("Yahoo Symbol:", ticker)

        ticker = symbol_map.get(
            ticker.upper(),
            ticker.upper()
        )

        stock = yf.Ticker(ticker)

        hist = stock.history(
            period=period,
            interval=interval,
            auto_adjust=False,
            prepost=False
        )

        if hist.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No historical data found for {ticker}"
            )

        chart_data = []

        for date, row in hist.iterrows():

            if interval.endswith(("m", "h")):
                candle_time = int(date.timestamp())
            else:
                candle_time = date.strftime("%Y-%m-%d")

            chart_data.append({
                "time": candle_time,
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2)
            })

        return chart_data

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ==========================================
# Serve Frontend
# ==========================================

app.mount(
    "/",
    StaticFiles(
        directory="../frontend",
        html=True
    ),
    name="frontend"
)


# ==========================================
# Run Server
# ==========================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
