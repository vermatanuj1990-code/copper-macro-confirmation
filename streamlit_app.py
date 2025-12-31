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
# 🇨🇳 STEP 2: China Demand & Inventory
# ==============================

st.divider()
st.subheader("🇨🇳 Step 2: China Demand & Inventory Pressure")
st.write("Assessing China-linked demand signals and copper stress…")

# ---- Defaults (critical) ----
step2_score = 0.0
step2_label = "Neutral"
step2_diag = "China data unavailable – neutral stance"

try:
    china = yf.download("000001.SS", period="6mo", progress=False)
    copper_cn = yf.download("HG=F", period="6mo", progress=False)

    if not china.empty and not copper_cn.empty:

        china_ret_10d = float(china["Close"].pct_change(10).iloc[-1])
        copper_ret_10d = float(copper_cn["Close"].pct_change(10).iloc[-1])
        copper_vol = float(
            copper_cn["Close"].pct_change().rolling(10).std().iloc[-1]
        )

        if not (
            pd.isna(china_ret_10d)
            or pd.isna(copper_ret_10d)
            or pd.isna(copper_vol)
        ):

            step2_score = 0.0

            if china_ret_10d > 0.015:
                step2_score += 0.15
            elif china_ret_10d < -0.015:
                step2_score -= 0.15

            if copper_ret_10d > 0.05:
                step2_score += 0.15
            elif copper_ret_10d < -0.05:
                step2_score -= 0.15

            if copper_vol > 0.03:
                step2_score -= 0.05

            if step2_score > 0.15:
                step2_label = "Supportive"
            elif step2_score < -0.15:
                step2_label = "Negative"
            else:
                step2_label = "Mild Supportive"

            step2_diag = (
                f"China equity (10d): {china_ret_10d:.2%} | "
                f"Copper trend (10d): {copper_ret_10d:.2%} | "
                f"Volatility: {copper_vol:.4f}"
            )

except Exception as e:
    step2_diag = "China data error – neutral stance"

# ---- Display ----
st.markdown("### 📊 Step-2 Signals")
st.write(step2_diag)

st.markdown("### 🔍 Step-2 Verdict")
if step2_score > 0:
    st.success(step2_label)
elif step2_score < 0:
    st.error(step2_label)
else:
    st.info(step2_label)

st.write(f"**Step-2 Score:** `{step2_score:.2f}`")
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
# ================================
# FINAL VERDICT & TRAFFIC LIGHT
# ================================

st.divider()
st.subheader("🚦 Final Market Verdict")

# --- Combine scores ---
final_score = macro_score + step2_score + step3_score

# --- Decide traffic light ---
if final_score >= 0.40:
    light = "🟢"
    final_label = "Bullish Bias"
    action = "Accumulate / Buy on dips"
    color = "success"
elif final_score >= 0.10:
    light = "🟡"
    final_label = "Cautious / Range-bound"
    action = "Wait or partial action"
    color = "warning"
else:
    light = "🔴"
    final_label = "Risk / Exhaustion Zone"
    action = "Reduce exposure / Avoid fresh buys"
    color = "error"

# --- Display result ---
st.markdown(f"## {light} {final_label}")

if color == "success":
    st.success(action)
elif color == "warning":
    st.warning(action)
else:
    st.error(action)

# --- Diagnostics ---
st.markdown(
    f"""
**Score Breakdown**
- Step 1 (Macro): `{macro_score:.2f}`
- Step 2 (China & Inventory): `{step2_score:.2f}`
- Step 3 (Momentum): `{step3_score:.2f}`

**Final Composite Score:** `{final_score:.2f}`
"""
)

st.caption("Decision-support tool | Use with price levels & risk management")
# ==================================================
# 📅 NEXT-DAY MCX RISK & BIAS METER (FLOW-BASED)
# ==================================================

st.divider()
st.subheader("📅 Next-Day MCX Copper Risk Meter")
st.caption("Uses yesterday’s MCX price & Open Interest (flow-based check)")

with st.expander("🔎 Enter Yesterday’s MCX Data (Manual)", expanded=False):

    price_1d = st.number_input(
        "Yesterday – MCX Copper Price Change (%)",
        value=0.0,
        step=0.1,
        key="nd_price_1d"
    )

    price_5d = st.number_input(
        "Last 5 Days – MCX Copper Price Change (%)",
        value=0.0,
        step=0.1,
        key="nd_price_5d"
    )

    oi_1d = st.number_input(
        "Yesterday – Open Interest Change (%)",
        value=0.0,
        step=0.1,
        key="nd_oi_1d"
    )

if st.button("▶️ Generate Next-Day Risk Outlook", key="nd_button"):

    score = 0
    notes = []
    penalty = 0

    # ---- Direction ----
    score += 1 if price_1d > 0 else -1
    score += 1 if price_5d > 0 else -1

    # ---- OI regime ----
    if price_1d > 0 and oi_1d > 0:
        score += 1
        notes.append("Long buildup – new longs added")
    elif price_1d > 0 and oi_1d < 0:
        notes.append("Short covering – bounce may lack follow-through")
    elif price_1d < 0 and oi_1d > 0:
        score -= 1
        notes.append("Short buildup – fresh shorts entering")
    elif price_1d < 0 and oi_1d < 0:
        score += 0.5
        notes.append("Long unwinding – selling pressure easing")

    # ---- Exhaustion penalties ----
    if abs(price_1d) > 3:
        penalty -= 1
        notes.append("Large 1-day move – exhaustion risk")

    if abs(oi_1d) > 5:
        penalty -= 0.5
        notes.append("Sharp OI change – crowded positioning")

    final_score = round(score + penalty, 2)

    # ---- Bias classification ----
    if final_score >= 1.5:
        bias = "Bullish"
        light = "🟢"
    elif final_score >= 0.5:
        bias = "Mild Bullish"
        light = "🟡"
    elif final_score <= -1.5:
        bias = "Bearish"
        light = "🔴"
    elif final_score <= -0.5:
        bias = "Mild Bearish"
        light = "🟡"
    else:
        bias = "Neutral"
        light = "⚪"

    risk = "High (Crowded / Reversal Risk)" if penalty < 0 else "Normal"

    # ---- Display card ----
    st.markdown("### 📌 Next-Day Outlook")
    st.markdown(f"## {light} {bias}")
    st.write(f"**Final Flow Score:** `{final_score}`")

    if risk.startswith("High"):
        st.error(f"⚠️ Risk Level: {risk}")
    else:
        st.success(f"✅ Risk Level: {risk}")

    st.markdown("### 🧠 Interpretation")
    for n in notes:
        st.write(f"- {n}")

    st.caption("Flow-based check for next session only. Use with main model.")
