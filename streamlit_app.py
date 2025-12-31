import streamlit as st
import yfinance as yf
import numpy as np
import time
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
# =========================================================
# STEP 3: MOMENTUM & EXHAUSTION ANALYSIS (SAFE)
# =========================================================

st.divider()
st.header("⚡ Step 3: Momentum & Exhaustion")

# --- Safety check ---
if len(copper) < 30:
    st.warning("Not enough data for momentum analysis.")
    st.stop()

# --- RSI Calculation ---
delta = copper["Close"].diff()
gain = delta.where(delta > 0, 0.0)
loss = -delta.where(delta < 0, 0.0)

avg_gain = gain.rolling(14).mean()
avg_loss = loss.rolling(14).mean()

rs = avg_gain / avg_loss
rsi = 100 - (100 / (1 + rs))

rsi_latest = float(rsi.dropna().iloc[-1])

# --- Momentum ---
roc_10 = (
    copper["Close"].iloc[-1] - copper["Close"].iloc[-11]
) / copper["Close"].iloc[-11]

# --- Price Stretch ---
ma20 = copper["Close"].rolling(20).mean().iloc[-1]
stretch = (copper["Close"].iloc[-1] - ma20) / ma20

# --- Scoring ---
momentum_score = 0.0

if rsi_latest >= 70:
    phase = "Exhaustion Risk"
    momentum_score -= 0.3
elif rsi_latest >= 65:
    phase = "Late Trend"
    momentum_score -= 0.1
elif rsi_latest >= 55:
    phase = "Healthy Expansion"
    momentum_score += 0.15
else:
    phase = "Weak / Early"
    momentum_score -= 0.1

if stretch > 0.06:
    momentum_score -= 0.2
elif stretch < 0.03:
    momentum_score += 0.1

momentum_score = round(momentum_score, 2)

# --- Verdict ---
if momentum_score >= 0.2:
    verdict = "Expansion Phase – Buy on strength"
elif momentum_score >= 0:
    verdict = "Healthy – Buy selectively"
elif momentum_score >= -0.2:
    verdict = "Late Trend – Buy on dips only"
else:
    verdict = "Exhaustion – Avoid fresh buys"

# --- Display ---
st.markdown(f"""
**Momentum Phase:** {phase}  
**RSI (14):** {rsi_latest:.1f}  
**10-Day Momentum:** {roc_10*100:.2f}%  
**Price Stretch from 20-DMA:** {stretch*100:.2f}%  

### 🔎 Step-3 Verdict
**{verdict}**

**Step-3 Score:** `{momentum_score}`
""")
