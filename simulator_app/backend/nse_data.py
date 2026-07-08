"""
nse_data.py

Data access layer for NSE (National Stock Exchange of India) instruments.

Design:
- Equity / index quotes and history: fetched via yfinance using NSE's
  ".NS" ticker suffix (e.g. "RELIANCE.NS", "^NSEI" for Nifty 50).
  This hits Yahoo Finance's servers, not NSE's — no scraping, no anti-bot
  evasion, same approach as the rest of this app.
- Options chain: NSE's live F&O options data is NOT available through
  Yahoo Finance or any free legitimate source. Real-time NSE options data
  requires a licensed provider. `get_nse_options_chain()` below is a
  pluggable seam — wire in whichever licensed API you get access to
  (Kite Connect, Upstox API, Angel One SmartAPI, or NSE's own paid feed)
  and it'll slot straight into the same shape `market_data.py` already
  expects from `get_options_chain()`.
"""

import time
import yfinance as yf
import pandas as pd


class NSEDataError(Exception):
    """Raised when NSE-related data can't be fetched or isn't available."""
    pass


# --- Simple in-memory TTL cache -------------------------------------------
# Avoids hammering Yahoo on every request (e.g. dashboard auto-refresh).
# Keyed by (function_name, args_tuple) -> (timestamp, value)

_CACHE = {}
_CACHE_TTL_SECONDS = 15  # quotes are cheap to refresh, but no need to spam


def _cache_get(key):
    entry = _CACHE.get(key)
    if not entry:
        return None
    ts, value = entry
    if time.time() - ts > _CACHE_TTL_SECONDS:
        _CACHE.pop(key, None)
        return None
    return value


def _cache_set(key, value):
    _CACHE[key] = (time.time(), value)


def _to_nse_symbol(symbol: str) -> str:
    """
    Normalizes a plain ticker into a Yahoo-recognized NSE symbol.
    'RELIANCE' -> 'RELIANCE.NS'. Index aliases are mapped explicitly
    since Yahoo uses caret-prefixed codes for indices.
    """
    symbol = symbol.strip().upper()

    index_aliases = {
        "NIFTY": "^NSEI",
        "NIFTY50": "^NSEI",
        "BANKNIFTY": "^NSEBANK",
        "SENSEX": "^BSESN",
    }
    if symbol in index_aliases:
        return index_aliases[symbol]

    if symbol.startswith("^") or symbol.endswith(".NS") or symbol.endswith(".BO"):
        return symbol

    return f"{symbol}.NS"


def _get_with_retry(fn, retries=3, delay=1.5):
    last_err = None
    for attempt in range(retries):
        try:
            return fn()
        except Exception as e:
            last_err = e
            time.sleep(delay * (attempt + 1))
    raise NSEDataError(f"Request failed after {retries} attempts: {last_err}")


# --- Public: Quotes ---------------------------------------------------------

def get_nse_quote(symbol: str) -> dict:
    """
    Returns a live-ish quote for an NSE equity or index.
    Example: get_nse_quote("RELIANCE") or get_nse_quote("NIFTY")
    """
    yf_symbol = _to_nse_symbol(symbol)
    cache_key = ("quote", yf_symbol)
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    def _fetch():
        ticker = yf.Ticker(yf_symbol)
        info = ticker.fast_info
        return {
            "symbol": symbol.upper(),
            "yfSymbol": yf_symbol,
            "lastPrice": round(info["last_price"], 2),
            "previousClose": round(info.get("previous_close", 0.0), 2) if info.get("previous_close") else None,
            "dayHigh": round(info.get("day_high", 0.0), 2) if info.get("day_high") else None,
            "dayLow": round(info.get("day_low", 0.0), 2) if info.get("day_low") else None,
            "currency": info.get("currency", "INR"),
        }

    try:
        result = _get_with_retry(_fetch)
    except Exception as e:
        raise NSEDataError(f"Could not fetch quote for '{symbol}' ({yf_symbol}): {e}")

    _cache_set(cache_key, result)
    return result


def get_nse_history(symbol: str, period: str = "3mo", interval: str = "1d") -> list:
    """
    Returns OHLC candles for an NSE equity or index, formatted for
    Lightweight Charts (same shape as your existing /history endpoint).
    """
    yf_symbol = _to_nse_symbol(symbol)
    cache_key = ("history", yf_symbol, period, interval)
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    def _fetch():
        ticker = yf.Ticker(yf_symbol)
        hist = ticker.history(period=period, interval=interval)
        if hist.empty:
            raise NSEDataError(f"No historical data returned for '{symbol}' ({yf_symbol}).")

        candles = []
        for date, row in hist.iterrows():
            candle_time = int(date.timestamp()) if interval.endswith(("m", "h")) else date.strftime("%Y-%m-%d")
            candles.append({
                "time": candle_time,
                "open": round(row["Open"], 2),
                "high": round(row["High"], 2),
                "low": round(row["Low"], 2),
                "close": round(row["Close"], 2),
                "volume": int(row["Volume"]) if not pd.isna(row["Volume"]) else 0,
            })
        return candles

    result = _get_with_retry(_fetch)
    _cache_set(cache_key, result)
    return result


# --- Public: Options (pluggable seam) ---------------------------------------

def get_nse_options_chain(symbol: str, expiration_date: str) -> dict:
    """
    Placeholder for NSE F&O options data.

    Free, legitimate sources (Yahoo/yfinance) do not carry NSE options data,
    so this deliberately raises until a licensed provider is wired in.

    To connect a real provider, replace the body below with a call to
    that provider's SDK/REST API, then reshape its response into the same
    dict shape `market_data.get_options_chain()` already returns:

        {
            "underlyingPrice": float,
            "expiration": "YYYY-MM-DD",
            "calls": [ {strike, bid, ask, lastPrice, volume,
                        openInterest, impliedVolatility, ...greeks}, ... ],
            "puts":  [ ... same shape ... ]
        }

    Candidates with official APIs for NSE F&O data:
      - Zerodha Kite Connect  (kiteconnect Python SDK)
      - Upstox API v2
      - Angel One SmartAPI
      - NSE's own licensed real-time data feed

    Once you have credentials for one of these, tell me which one and
    I'll write the actual integration (auth, request shape, response
    parsing) for it.
    """
    raise NSEDataError(
        "Live NSE options data requires a licensed provider (Kite Connect, "
        "Upstox, Angel One SmartAPI, or NSE's paid feed). No free legitimate "
        "source exposes it. Wire in a provider here — see docstring."
    )