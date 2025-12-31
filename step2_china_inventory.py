import numpy as np
import yfinance as yf

def run_step2():
    """
    Step 2: China Demand + Inventory Pressure
    Returns: (step2_score, label, diagnostics_dict)
    """

    # --- Download data ---
    china_eq = yf.download("FXI", period="3mo", progress=False)
    copper_px = yf.download("HG=F", period="3mo", progress=False)

    if china_eq.empty or copper_px.empty or len(china_eq) < 20 or len(copper_px) < 20:
        return 0.0, "Data unavailable", {}

    # ----------------------------
    # China demand proxy
    # ----------------------------
    china_now = float(china_eq["Close"].iloc[-1])
    china_prev = float(china_eq["Close"].iloc[-10])
    china_return = (china_now - china_prev) / china_prev

    china_score = float(np.clip(china_return / 0.05, -1, 1))

    # ----------------------------
    # Inventory pressure proxy
    # ----------------------------
    returns = copper_px["Close"].pct_change().dropna()
    vol = float(returns.rolling(10).std().dropna().iloc[-1])

    price_trend = float(
        (copper_px["Close"].iloc[-1] - copper_px["Close"].iloc[-10])
        / copper_px["Close"].iloc[-10]
    )

    if price_trend > 0 and vol < 0.02:
        inventory_score = 0.5
    elif price_trend < 0 and vol > 0.025:
        inventory_score = -0.5
    else:
        inventory_score = 0.0

    # ----------------------------
    # Final Step-2 score
    # ----------------------------
    step2_score = 0.6 * china_score + 0.4 * inventory_score

    if step2_score > 0.4:
        label = "Strong Supportive"
    elif step2_score > 0.15:
        label = "Mild Supportive"
    elif step2_score > -0.15:
        label = "Neutral"
    elif step2_score > -0.4:
        label = "Mild Pressure"
    else:
        label = "Heavy Pressure"

    diagnostics = {
        "china_return": china_return,
        "price_trend": price_trend,
        "volatility": vol,
    }

    return float(step2_score), label, diagnostics
