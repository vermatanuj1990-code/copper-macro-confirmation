# ============================================
# COPPER MACRO CONFIRMATION – STEP 1
# USD-INR + Volatility Impact
# ============================================

import streamlit as st
import yfinance as yf
import numpy as np

st.set_page_config(page_title="Copper Macro – Step 1", layout="centered")

st.title("🌍 Copper Macro Confirmation – Step 1")
st.caption("USD-INR + Volatility impact | Global → India translation")

# --------------------------------------------
# Data Fetch
# --------------------------------------------
import streamlit as st
import yfinance as yf
import numpy as np

st.set_page_config(page_title="Copper Macro Confirmation – Step 1", layout="centered")

st.title("🌍 Copper Macro Confirmation – Step 1")
st.caption("USD-INR + Volatility impact | Global → India translation")

# -----------------------------
# Fetch market data (NO INDENT)
# -----------------------------
copper = yf.download("HG=F", period="6mo", progress=False)
usdinr = yf.download("INR=X", period="6mo", progress=False)

# -----------------------------
# Data safety check
# -----------------------------
if copper.empty or usdinr.empty or len(copper) < 20 or len(usdinr) < 20:
    st.error("Not enough market data yet.")
    st.stop()

# -----------------------------
# USD-INR trend
# -----------------------------
inr_now = usdinr["Close"].iloc[-1]
inr_prev = usdinr["Close"].iloc[-6]
usd_inr_change = (inr_now - inr_prev) / inr_prev

usd_inr_score = np.clip(usd_inr_change / 0.01, -1, 1)

# -----------------------------
# Copper volatility regime
# -----------------------------
returns = copper["Close"].pct_change().dropna()
volatility = returns.rolling(10).std().iloc[-1]

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
# Final macro score
# -----------------------------
macro_score = 0.7 * usd_inr_score + 0.3 * vol_score

if macro_score > 0.3:
    verdict = "🟢 Supportive for MCX Copper"
elif macro_score < -0.3:
    verdict = "🔴 Risky for MCX Copper"
else:
    verdict = "🟡 Neutral"

# -----------------------------
# Display
# -----------------------------
st.subheader("Macro Assessment")
st.write(f"**USD-INR change (5 days):** {usd_inr_change*100:.2f}%")
st.write(f"**Volatility regime:** {vol_regime}")
st.write(f"**Macro score:** {macro_score:.2f}")
st.success(verdict)

# --------------------------------------------
# Data Validation
# --------------------------------------------
if copper.empty or usdinr.empty or len(copper) < 20 or len(usdinr) < 20:
    st.error("Not enough market data yet.")
    st.stop()

# --------------------------------------------
# USD-INR Impact
# --------------------------------------------
inr_now = float(usdinr["Close"].iloc[-1])
inr_prev = float(usdinr["Close"].iloc[-6])

usd_inr_change = (inr_now - inr_prev) / inr_prev

# INR weakening = bullish MCX copper
usd_inr_score = np.clip(usd_inr_change / 0.01, -1, 1)
usd_inr_score = float(usd_inr_score)

# --------------------------------------------
# Copper Volatility Regime
# --------------------------------------------
returns = copper["Close"].pct_change().dropna()

if len(returns) < 10:
    st.error("Not enough data for volatility calculation.")
    st.stop()

volatility = float(returns.rolling(10).std().iloc[-1])

if volatility > 0.025:
    vol_regime = "High"
    vol_score = -0.2
elif volatility > 0.015:
    vol_regime = "Normal"
    vol_score = 0.0
else:
    vol_regime = "Low"
    vol_score = 0.1

# --------------------------------------------
# Final Macro Score
# --------------------------------------------
macro_score = 0.7 * usd_inr_score + 0.3 * vol_score
macro_score = float(np.clip(macro_score, -1, 1))

# --------------------------------------------
# Interpretation
# --------------------------------------------
if macro_score > 0.25:
    macro_verdict = "Supportive (Bullish for MCX)"
elif macro_score > -0.25:
    macro_verdict = "Neutral"
else:
    macro_verdict = "Risky (Bearish for MCX)"

# --------------------------------------------
# Display
# --------------------------------------------
st.markdown("### 📊 Macro Confirmation Summary")

st.markdown(f"""
**USD-INR Change (5 days):** `{usd_inr_change:.2%}`  
**USD-INR Impact Score:** `{usd_inr_score:.2f}`  

**Copper Volatility (10-day):** `{volatility:.2%}`  
**Volatility Regime:** **{vol_regime}**

---

### 🧠 Final Macro Verdict

**Macro Score:** `{macro_score:.2f}`  
**Environment:** **{macro_verdict}**
""")
