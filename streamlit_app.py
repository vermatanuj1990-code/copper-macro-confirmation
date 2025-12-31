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
# ===============================
# ⚡ STEP 3: Momentum & Exhaustion
# ===============================

st.divider()
st.header("⚡ Step 3: Momentum & Exhaustion")

# --- Safety check ---
if len(copper) < 30:
    st.error("Not enough data for momentum analysis.")
    st.stop()

# --- RSI Calculation ---
delta = copper["Close"].diff()

gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)

avg_gain = gain.rolling(14).mean()
avg_loss = loss.rolling(14).mean()

rs = avg_gain / avg_loss
rsi = 100 - (100 / (1 + rs))

rsi_latest = rsi.iloc[-1]

if pd.isna(rsi_latest):
    st.error("RSI data not available yet.")
    st.stop()

rsi_latest = float(rsi_latest)

# --- Momentum (10d vs 20d) ---
ma10 = copper["Close"].rolling(10).mean().iloc[-1]
ma20 = copper["Close"].rolling(20).mean().iloc[-1]

if pd.isna(ma10) or pd.isna(ma20):
    st.error("Moving average data insufficient.")
    st.stop()

ma10 = float(ma10)
ma20 = float(ma20)

momentum_score = 0.0

if ma10 > ma20:
    momentum_score += 0.2
else:
    momentum_score -= 0.2

# --- Price Stretch (Exhaustion Check) ---
stretch = (copper["Close"].iloc[-1] - ma20) / ma20
stretch = float(stretch)

if stretch > 0.06:
    momentum_score -= 0.2   # overextended
elif stretch < 0.03:
    momentum_score += 0.1   # healthy trend

# --- RSI Exhaustion Logic ---
if rsi_latest > 70:
    rsi_state = "Overbought"
    momentum_score -= 0.3
elif rsi_latest < 30:
    rsi_state = "Oversold"
    momentum_score += 0.3
else:
    rsi_state = "Neutral"

# --- Final Step-3 Verdict ---
momentum_score = round(momentum_score, 2)

if momentum_score > 0.2:
    verdict = "Strong Momentum"
elif momentum_score > 0.05:
    verdict = "Mild Momentum"
elif momentum_score < -0.2:
    verdict = "Exhaustion Risk"
else:
    verdict = "Neutral Momentum"

# --- Display ---
st.subheader("📈 Momentum Signals")

st.markdown(f"""
- **RSI (14):** `{rsi_latest:.1f}` → **{rsi_state}**
- **MA10 vs MA20:** `{ma10:.2f}` vs `{ma20:.2f}`
- **Price Stretch from MA20:** `{stretch*100:.2f}%`
""")

st.subheader("🔍 Step-3 Verdict")
st.markdown(f"**{verdict}**")
st.caption(f"Momentum Score: `{momentum_score}`")
