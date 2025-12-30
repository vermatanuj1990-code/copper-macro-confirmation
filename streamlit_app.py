import streamlit as st
import yfinance as yf
import numpy as np
import time

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
# Safe Downloader with Retry
# -----------------------------
@st.cache_data(ttl=3600)
def safe_download(ticker, retries=3):
    for i in range(retries):
        try:
            df = yf.download(
                ticker,
                period="6mo",
                interval="1d",
                progress=False,
                threads=False
            )
            if not df.empty:
                return df
        except:
            pass
        time.sleep(2)
    return None

# -----------------------------
# Load Data
# -----------------------------
copper = safe_download("HG=F")
usdinr = safe_download("USDINR=X")

# -----------------------------
# Validation
# -----------------------------
if copper is None or usdinr is None:
    st.warning("⚠️ Data source temporarily unavailable. Please reload in a minute.")
    st.stop()

if len(copper) < 30 or len(usdinr) < 30:
    st.warning("⚠️ Not enough historical data yet.")
    st.stop()

# -----------------------------
# USD-INR Impact
# -----------------------------
inr_now = float(usdinr["Close"].iloc[-1])
inr_prev = float(usdinr["Close"].iloc[-6])
usd_inr_change = (inr_now - inr_prev) / inr_prev
usd_inr_score = float(np.clip(usd_inr_change / 0.01, -1, 1))

# -----------------------------
# Volatility Regime
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
# Macro Score
# -----------------------------
macro_score = 0.7 * usd_inr_score + 0.3 * vol_score

if macro_score > 0.25:
    verdict = "✅ Macro Supportive (Bullish)"
elif macro_score < -0.25:
    verdict = "⚠️ Macro Risky (Bearish)"
else:
    verdict = "➖ Macro Neutral"

# -----------------------------
# Output
# -----------------------------
st.subheader("📊 Macro Signals")

st.markdown(f"""
**USD-INR Change (5 days):** `{usd_inr_change*100:.2f}%`  
**Volatility Regime:** `{vol_regime}`  
**10-Day Volatility:** `{volatility:.4f}`  

---

## 🔎 Macro Verdict
### {verdict}

**Macro Score:** `{macro_score:.2f}`
""")

st.divider()
st.caption("Step-1 macro confirmation | Planning tool | Not financial advice")
