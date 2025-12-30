import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(
    page_title="Copper Macro Confirmation – Step 1",
    page_icon="🌍",
    layout="centered"
)

st.title("🌍 Copper Macro Confirmation – Step 1")
st.caption("USD-INR + Volatility impact | Global → India translation")

# -----------------------------
# Data Download
# -----------------------------
@st.cache_data(ttl=3600)
def load_data():
    copper = yf.download("HG=F", period="6mo", interval="1d", progress=False)
    usdinr = yf.download("USDINR=X", period="6mo", interval="1d", progress=False)
    return copper, usdinr

copper, usdinr = load_data()

# -----------------------------
# Data Validation
# -----------------------------
if copper.empty or usdinr.empty:
    st.error("Market data not available.")
    st.stop()

if len(copper) < 30 or len(usdinr) < 30:
    st.error("Not enough market data yet.")
    st.stop()

# -----------------------------
# USD-INR Impact
# -----------------------------
inr_now = float(usdinr["Close"].iloc[-1])
inr_prev = float(usdinr["Close"].iloc[-6])
usd_inr_change = (inr_now - inr_prev) / inr_prev

# INR weakening → bullish MCX
usd_inr_score = float(np.clip(usd_inr_change / 0.01, -1, 1))

# -----------------------------
# Copper Volatility Regime
# -----------------------------
returns = copper["Close"].pct_change().dropna()
volatility = float(returns.rolling(10).std().dropna().iloc[-1])

if volatility > 0.025:
    vol_regime = "High"
    vol_score = -0.2
elif volatility > 0.015:
    vol_regime = "Normal"
    vol_score = 0.0
else:
    vol_regime = "Low"
    vol_score = 0.1

# -----------------------------
# Macro Confirmation Score
# -----------------------------
macro_score = (0.7 * usd_inr_score) + (0.3 * vol_score)

if macro_score > 0.25:
    verdict = "✅ Macro Supportive (Bullish)"
elif macro_score < -0.25:
    verdict = "⚠️ Macro Risky (Bearish)"
else:
    verdict = "➖ Macro Neutral"

# -----------------------------
# Display Results
# -----------------------------
st.subheader("📊 Macro Signals")

st.markdown(
    f"""
**USD-INR Change (5 days):** `{usd_inr_change*100:.2f}%`  
**Volatility Regime:** `{vol_regime}`  
**Volatility (10d σ):** `{volatility:.4f}`  

---

### 🔎 Macro Verdict
## {verdict}

**Macro Score:** `{macro_score:.2f}`
"""
)

st.divider()
st.caption("Step-1 model · Educational / planning tool · Not financial advice")
