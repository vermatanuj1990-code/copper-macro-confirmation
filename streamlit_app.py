import streamlit as st
import yfinance as yf
import numpy as np
import time
import pandas as pd
from step2_china_inventory import run_step2

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
# ==============================
# STEP 2: China + Inventory
# ==============================
st.divider()
st.subheader("🇨🇳 Step 2: China Demand & Inventory Pressure")

step2_score, step2_label, step2_diag = run_step2()
# ===============================
# ⚡ STEP 3: MOMENTUM & EXHAUSTION
# ===============================
st.markdown("## ⚡ Step 3: Momentum & Exhaustion")

copper = yf.download("HG=F", period="6mo", interval="1d")

if copper.empty or len(copper) < 30:
    st.warning("Not enough copper data for momentum analysis.")
    st.stop()

# --- RSI (force scalar values) ---
close = copper["Close"]

delta = close.diff()
gain = delta.where(delta > 0, 0.0)
loss = -delta.where(delta < 0, 0.0)

avg_gain = gain.rolling(14).mean()
avg_loss = loss.rolling(14).mean()

rs = avg_gain / avg_loss
rsi_series = 100 - (100 / (1 + rs))

rsi_latest = float(rsi_series.iloc[-1])

# --- Price stretch ---
price_now = float(close.iloc[-1])
price_20 = float(close.iloc[-20])
stretch = float((price_now - price_20) / price_20)

# --- Hard safety gate ---
if np.isnan(rsi_latest) or np.isnan(stretch):
    st.warning("Momentum indicators not ready yet.")
    st.stop()

# --- Scoring logic ---
step3_score = 0.0
regime = "Neutral"

if rsi_latest > 70:
    step3_score -= 0.25
    regime = "Overbought (Exhaustion Risk)"
elif rsi_latest < 30:
    step3_score += 0.25
    regime = "Oversold (Rebound Potential)"

if stretch > 0.06:
    step3_score -= 0.15
elif stretch < -0.05:
    step3_score += 0.15

# --- Display ---
st.markdown("### 📊 Momentum Signals")
st.write(f"RSI (14): {rsi_latest:.1f}")
st.write(f"20-Day Price Stretch: {stretch*100:.2f}%")
st.write(f"Momentum Regime: {regime}")

st.markdown("### 🔍 Step-3 Verdict")
if step3_score > 0.1:
    st.success("Momentum Supportive")
elif step3_score < -0.1:
    st.error("Momentum Exhausted")
else:
    st.info("Momentum Neutral")

st.write(f"Step-3 Score: `{step3_score:.2f}`")
st.markdown("---")
