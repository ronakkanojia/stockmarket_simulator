import numpy as np
from scipy.stats import norm

def calculate_greeks(S, K, T, r, sigma, option_type="call"):
    """
    S: Underlying Stock Price
    K: Strike Price
    T: Time to Expiration in years (e.g., 30 days = 30/365)
    r: Risk-free interest rate (e.g., 0.07 for 7%)
    sigma: Implied Volatility (e.g., 0.25 for 25%)
    """
    # Avoid division by zero or negative time/volatility
    if T <= 0 or sigma <= 0:
        return {"price": 0.0, "delta": 0.0, "gamma": 0.0, "theta": 0.0, "vega": 0.0}

    # Calculate d1 and d2
    d1 = (np.log(S / K) + (r + (sigma ** 2) / 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    # Standard normal probability density function (pdf) and cumulative distribution function (cdf)
    pdf_d1 = norm.pdf(d1)
    cdf_d1 = norm.cdf(d1)
    cdf_d2 = norm.cdf(d2)
    
    # Gamma and Vega are identical for Calls and Puts
    gamma = pdf_d1 / (S * sigma * np.sqrt(T))
    vega = S * np.sqrt(T) * pdf_d1 / 100  # Divided by 100 to represent a 1% change in IV

    if option_type.lower() == "call":
        price = S * cdf_d1 - K * np.exp(-r * T) * cdf_d2
        delta = cdf_d1
        # Theta for Call (divided by 365 to show daily decay)
        theta = (- (S * pdf_d1 * sigma) / (2 * np.sqrt(T)) - r * K * np.exp(-r * T) * cdf_d2) / 365
    else:
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        delta = cdf_d1 - 1
        # Theta for Put (divided by 365 for daily decay)
        theta = (- (S * pdf_d1 * sigma) / (2 * np.sqrt(T)) + r * K * np.exp(-r * T) * norm.cdf(-d2)) / 365

    return {
        "price": round(float(price), 2),
        "delta": round(float(delta), 3),
        "gamma": round(float(gamma), 4),
        "theta": round(float(theta), 3),
        "vega": round(float(vega), 3)
    }