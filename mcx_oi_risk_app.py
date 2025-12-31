import streamlit as st
import pandas as pd
import requests
import io
from datetime import datetime, timedelta

st.set_page_config(page_title="MCX Copper OI Risk Meter", layout="centered")

st.title("📊 Next-Day MCX Copper Risk Meter")
st.caption("Auto-derived from MCX Bhavcopy (Price + Open Interest)")

# =========================
# BHAVCOPY FETCH
# =========================

@st.cache_data(ttl=86400)
def fetch_mcx_bhavcopy(date):
    url = "https://www.mcxindia.com/backpage.aspx/GetBhavCopy"

    payload = {
        "Commodity": "ALL",
        "Date": date.strftime("%d-%b-%Y")
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json"
    }

    r = requests.post(url, json=payload, headers=headers, timeout=20)
    r.raise_for_status()

    data = r.json()
    if "d" not in data:
        raise ValueError("Bhavcopy not available")

    return pd.read_csv(io.StringIO(data["d"]))


# =========================
# COPPER SNAPSHOT
# =========================

def get_copper_snapshot(df):
    copper = df[
        (df["COMMODITY"] == "COPPER") &
        (df["INSTRUMENT"] == "FUTCOM")
    ].copy()

    if copper.empty:
        raise ValueError("Copper FUT not found")

    copper["EXPIRY_DT"] = pd.to_datetime(copper["EXPIRY_DT"])
    copper = copper.sort_values("EXPIRY_DT").iloc[0]

    return {
        "close": float(copper["CLOSE"]),
        "oi": float(copper["OPEN_INT"]),
        "expiry": copper["EXPIRY_DT"].date()
    }


# =========================
# OI REGIME LOGIC
# =========================

def oi_regime(price_chg, oi_chg):
    if price_chg > 0 and oi_chg > 0:
        return "Long Buildup", "Bullish continuation likely", +0.30, "🟢"
    elif price_chg < 0 and oi_chg > 0:
        return "Short Buildup", "Downside pressure dominant", -0.30, "🔴"
    elif price_chg > 0 and oi_chg < 0:
        return "Short Covering", "Bounce / squeeze risk", +0.15, "🟡"
    elif price_chg < 0 and oi_chg < 0:
        return "Long Unwinding", "Trend exhaustion risk", -0.15, "🟡"
    else:
        return "Neutral", "No clear positioning", 0.0, "⚪"


# =========================
# UI ACTION
# =========================

if st.button("▶ Generate from MCX Bhavcopy"):

    try:
        today = datetime.today().date()
        d1 = today - timedelta(days=1)
        d2 = today - timedelta(days=2)

        df1 = fetch_mcx_bhavcopy(d1)
        df2 = fetch_mcx_bhavcopy(d2)

        snap1 = get_copper_snapshot(df1)
        snap2 = get_copper_snapshot(df2)

        price_chg = (snap1["close"] - snap2["close"]) / snap2["close"]
        oi_chg = (snap1["oi"] - snap2["oi"]) / snap2["oi"]

        regime, meaning, score, light = oi_regime(price_chg, oi_chg)

        st.divider()
        st.subheader("📌 OI Interpretation")

        st.markdown(f"### {light} {regime}")
        st.caption(meaning)

        col1, col2 = st.columns(2)
        col1.metric("Price Change", f"{price_chg*100:.2f}%")
        col2.metric("OI Change", f"{oi_chg*100:.2f}%")

        st.divider()
        st.subheader("🚦 Risk Outlook")

        if score >= 0.25:
            st.success("Bullish bias — longs safer than shorts")
        elif score <= -0.25:
            st.error("Bearish bias — downside risk elevated")
        else:
            st.warning("Caution — range / reversal risk")

        st.caption(f"Active Contract Expiry: {snap1['expiry']}")

    except Exception as e:
        st.error(f"Error fetching bhavcopy: {e}")
