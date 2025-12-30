# =========================================================
# COPPER MACRO CONFIRMATION MODEL – STEP 1
# USD–INR + VOLATILITY
# =========================================================

import streamlit as st
import yfinance as yf
import numpy as np

st.set_page_config(page_title="Copper Macro – Step 1", layout="centered")

st.title("🌍 Copper Macro Confirmation – Step 1")
st.caption("USD–INR + Volatility impact | Global to India translation")

@st.cache_data(ttl=3600)
def fetch_data():
    usdinr = yf.download("USDINR=X", period="60d")
    copper = yf.download("HG=F", period="60d")
    return usdinr, copper

usdinr, copper = fetch_data()

if len(usdinr) < 15 or len(copper) < 15:
    st.error("Not enough market data yet.")
    st.stop()

# -------------------------------
# USD–INR Trend
# -------------------------------
inr_now = usdinr["Close"].iloc[-1]
inr_prev = usdinr["Close"].iloc[-6]
usd_inr_change = (inr_now - inr_prev) / inr_prev

# INR weakening = bullish MCX
usd_inr_score = np.clip(usd_inr_change / 0.005, -1, 1)

# -------------------------------
# Volatility Regime (Copper)
# -------------------------------
returns = copper["Close"].pct_change().dropna()

volatility_series = returns.rolling(10).std()
volatility = float(volatility_series.iloc[-1])

if volatility > 0.025:
    vol_regime = "High"
    vol_score = -0.2
elif volatility > 0.015:
    vol_regime = "Normal"
    vol_score = 0.0
else:
    vol_regime = "Low"
    vol_score = 0.1

# -------------------------------
# Final Macro Confirmation Score
# -------------------------------
macro_score = (
    0.7 * usd_inr_score +
    0.3 * vol_score
)

macro_score = float(np.clip(macro_score, -1, 1))

# -------------------------------
# Interpretation
# -------------------------------
def interpret(score):
    if score > 0.4:
        return "Strong Tailwind for MCX", "🟢"
    elif score > 0.15:
        return "Mild Tailwind for MCX", "🟢"
    elif score > -0.15:
        return "Neutral", "🟡"
    elif score > -0.4:
        return "Headwind for MCX", "🔴"
    else:
        return "Strong Headwind for MCX", "🔴"

bias, icon = interpret(macro_score)
confidence = int(abs(macro_score) * 100)

# -------------------------------
# Display
# -------------------------------
st.markdown("## Macro Confirmation")

st.markdown(f"""
**USD–INR 5-Day Change:** {usd_inr_change*100:.2f}%  
**Volatility Regime:** {vol_regime}  

### {icon} {bias}  
**Confidence:** {confidence}%
""")

st.divider()

st.caption("""
⚠️ This model does NOT predict price.
It confirms whether global copper moves are likely to TRANSLATE into MCX.
""")
