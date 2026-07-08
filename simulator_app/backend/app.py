from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from market_data import (
    get_options_chain,
    get_available_expiries,
    OptionsDataError,
)

from nse_data import (
    get_nse_quote,
    get_nse_history,
    normalize_symbol,
    NSEDataError,
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

        ticker = normalize_symbol(ticker)

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

        ticker = normalize_symbol(ticker)

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
# Live Quote
# ==========================================

@app.get("/quote/{ticker}")
def quote(ticker: str):

    try:

        return get_nse_quote(ticker)

    except NSEDataError as e:

        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ==========================================
# Historical Chart Data
# ==========================================

@app.get("/history/{ticker}")
def historical_data(
    ticker: str,
    period: str = "1mo",
    interval: str = "1d"
):

    try:

        return get_nse_history(
            ticker,
            period=period,
            interval=interval
        )

    except NSEDataError as e:

        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

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