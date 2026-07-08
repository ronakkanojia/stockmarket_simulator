import time
import yfinance as yf
import pandas as pd
from datetime import datetime
from greeks_math import calculate_greeks


class OptionsDataError(Exception):
    """Raised when real options data can't be fetched or is unavailable."""
    pass


def _get_ticker_with_retry(ticker_symbol, retries=3, delay=1.5):
    """
    yfinance occasionally gets rate-limited or returns an empty body.
    Retry a few times with backoff before giving up.
    """
    last_err = None
    for attempt in range(retries):
        try:
            ticker = yf.Ticker(ticker_symbol)
            # Force a real network call now so we fail fast if something's wrong,
            # instead of failing later deep inside option_chain().
            _ = ticker.fast_info["last_price"]
            return ticker
        except Exception as e:
            last_err = e
            time.sleep(delay * (attempt + 1))
    raise OptionsDataError(
        f"Could not reach Yahoo Finance for '{ticker_symbol}' after {retries} attempts: {last_err}"
    )


def get_available_expiries(ticker_symbol):
    """
    Returns the list of valid expiration dates yfinance actually has for this ticker.
    Use this to populate a dropdown instead of letting the user type an arbitrary date.
    """
    ticker = _get_ticker_with_retry(ticker_symbol)
    expiries = ticker.options
    if not expiries:
        raise OptionsDataError(f"'{ticker_symbol}' has no listed options chain.")
    return list(expiries)


def get_options_chain(ticker_symbol, expiration_date):
    """
    Fetches the call and put options chain for a given ticker and date,
    and appends computed Greeks to every strike price.
    """
    ticker = _get_ticker_with_retry(ticker_symbol)

    # Validate the expiry against what's actually listed, so a bad/expired
    # date fails with a clear message instead of a raw yfinance traceback.
    valid_expiries = ticker.options
    if not valid_expiries:
        raise OptionsDataError(f"'{ticker_symbol}' has no listed options chain.")
    if expiration_date not in valid_expiries:
        raise OptionsDataError(
            f"'{expiration_date}' is not a valid expiry for {ticker_symbol}. "
            f"Valid expiries: {', '.join(valid_expiries)}"
        )

    underlying_price = ticker.fast_info["last_price"]

    # Fetch options chain dataframes (retry once — this call is separate
    # from the fast_info call above and can independently rate-limit)
    try:
        opt_chain = ticker.option_chain(expiration_date)
    except Exception:
        time.sleep(1.5)
        opt_chain = ticker.option_chain(expiration_date)

    calls = opt_chain.calls
    puts = opt_chain.puts

    if calls.empty and puts.empty:
        raise OptionsDataError(
            f"No strikes returned for {ticker_symbol} on {expiration_date}."
        )

    # Calculate time to expiration (T) in years
    exp_date = datetime.strptime(expiration_date, "%Y-%m-%d")
    days_to_expiry = (exp_date - datetime.now()).days
    T = max(days_to_expiry, 0.5) / 365.0  # floor at 0.5 days to avoid div by zero

    # Risk-free rate (assumed 7% standard or fetched via macro data)
    r = 0.07

    def _process(rows, option_type):
        processed = []
        for _, row in rows.iterrows():
            # yfinance sometimes returns 0 or NaN IV for illiquid strikes;
            # skip Greeks (rather than crash) when that happens.
            iv = row["impliedVolatility"]
            if pd.isna(iv) or iv <= 0:
                greeks = {"price": None, "delta": None, "gamma": None, "theta": None, "vega": None}
            else:
                greeks = calculate_greeks(underlying_price, row["strike"], T, r, iv, option_type)

            processed.append({
                "strike": row["strike"],
                "bid": row["bid"] if not pd.isna(row["bid"]) else 0.0,
                "ask": row["ask"] if not pd.isna(row["ask"]) else 0.0,
                "lastPrice": row["lastPrice"] if not pd.isna(row["lastPrice"]) else 0.0,
                "volume": int(row["volume"]) if not pd.isna(row["volume"]) else 0,
                "openInterest": int(row["openInterest"]) if not pd.isna(row["openInterest"]) else 0,
                "impliedVolatility": round(iv, 4) if not pd.isna(iv) else None,
                **greeks
            })
        return processed

    return {
        "underlyingPrice": round(underlying_price, 2),
        "expiration": expiration_date,
        "calls": _process(calls, "call"),
        "puts": _process(puts, "put")
    }