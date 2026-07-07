import yfinance as yf
import pandas as pd
from datetime import datetime
from greeks_math import calculate_greeks

def get_options_chain(ticker_symbol, expiration_date):
    """
    Fetches the call and put options chain for a given ticker and date,
    and appends computed Greeks to every strike price.
    """
    ticker = yf.Ticker(ticker_symbol)
    
    # Get current underlying stock price
    # fast_info gives quick access to the last price
    underlying_price = ticker.fast_info['last_price']
    
    # Fetch options chain dataframes
    opt_chain = ticker.option_chain(expiration_date)
    calls = opt_chain.calls
    puts = opt_chain.puts
    
    # Calculate time to expiration (T) in years
    exp_date = datetime.strptime(expiration_date, "%Y-%m-%d")
    days_to_expiry = (exp_date - datetime.now()).days
    T = max(days_to_expiry, 0.5) / 365.0  # floor at 0.5 days to avoid div by zero
    
    # Risk-free rate (assumed 7% standard or fetched via macro data)
    r = 0.07 

    processed_calls = []
    processed_puts = []

    # Process Calls
    for _, row in calls.iterrows():
        # yfinance provides impliedVolatility directly
        iv = row['impliedVolatility']
        greeks = calculate_greeks(underlying_price, row['strike'], T, r, iv, "call")
        
        processed_calls.append({
            "strike": row['strike'],
            "bid": row['bid'],
            "ask": row['ask'],
            "lastPrice": row['lastPrice'],
            "volume": int(row['volume']) if not pd.isna(row['volume']) else 0,
            "openInterest": int(row['openInterest']) if not pd.isna(row['openInterest']) else 0,
            "impliedVolatility": round(iv, 2),
            **greeks
        })

    # Process Puts
    for _, row in puts.iterrows():
        iv = row['impliedVolatility']
        greeks = calculate_greeks(underlying_price, row['strike'], T, r, iv, "put")
        
        processed_puts.append({
            "strike": row['strike'],
            "bid": row['bid'],
            "ask": row['ask'],
            "lastPrice": row['lastPrice'],
            "volume": int(row['volume']) if not pd.isna(row['volume']) else 0,
            "openInterest": int(row['openInterest']) if not pd.isna(row['openInterest']) else 0,
            "impliedVolatility": round(iv, 2),
            **greeks
        })

    return {
        "underlyingPrice": round(underlying_price, 2),
        "calls": processed_calls,
        "puts": processed_puts
    }