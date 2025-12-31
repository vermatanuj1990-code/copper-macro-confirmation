# ==============================
# STEP 2: China Demand + Inventory Pressure (Price Proxies)
# ==============================

import yfinance as yf
import numpy as np
import streamlit as st

st.subheader("🇨🇳 Step 2: China Demand & Inventory Pressure")

# --- Download data ---
china_eq = yf.download("FXI", period="3mo", progress=False)
copper_px = yf.download("HG=F", period="3mo", progress=False)

if len(china_eq) < 20 or len(copper_px) < 20:
    st.error("Not enough China / Copper data for Step 2.")
    st.stop()

# ==============================
# China Demand Signal
# ==============================
china_now = china_eq["Close"].iloc[-1]
china_prev = china_eq["Close"].iloc[-10]
china_return = (china_now - china_prev) / china_prev

china_score = np.clip(china_return / 0.05, -1, 1)

# ==============================
# Inventory Pressure Proxy (Copper behavior)
# ==============================
returns = copper_px["Close"].pct_change().dropna()
vol = returns.rolling(10).std().iloc[-1]
price_trend = (copper_px["Close"].iloc[-1] -
               copper_px["Close"].iloc[-10]) / copper_px["Close"].iloc[-10]

if price_trend > 0 and vol < 0.02:
    inventory_score = 0.5      # Tight supply
elif price_trend < 0 and vol > 0.025:
    inventory_score = -0.5     # Inventory pressure
else:
    inventory_score = 0.0      # Neutral

# ==============================
# Final Step 2 Score
# ==============================
step2_score = 0.6 * china_score + 0.4 * inventory_score

# ==============================
# Labels
# ==============================
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

# ==============================
# Display
# ==============================
st.markdown("### 📊 Step 2 Signals")
st.write(f"China Equity Change (10d): **{china_return*100:.2f}%**")
st.write(f"Copper Price Trend (10d): **{price_trend*100:.2f}%**")
st.write(f"Copper Volatility (10d): **{vol:.4f}**")

st.markdown("### 🧭 Step 2 Verdict")
st.success(f"**{label}**")
st.write(f"Step 2 Score: **{step2_score:.2f}**")
