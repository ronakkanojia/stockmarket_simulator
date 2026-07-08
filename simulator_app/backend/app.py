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
            "^NSEBANK": "^NSEBANK"
        }

        ticker = symbol_map.get(ticker.upper(), ticker.upper())

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
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"])
            })

        return chart_data

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )