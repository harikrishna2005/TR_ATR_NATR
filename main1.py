import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import talib
from datetime import datetime, timedelta

# Set page to wide mode to comfortably see the 6-month timeline
st.set_page_config(layout="wide", page_title="Grid Bot ATR Analytics")

st.title("📊 Grid Bot Volatility Simulator")
st.subheader("Visualizing TR, ATR, NATR, & Base NATR Over 6 Months")

# --- SIMPLIFIED SIDEBAR CONTROLS ---
st.sidebar.header("Bot Parameters")
symbol = st.sidebar.selectbox("Currency Pair", ["BTC/USDT", "ETH/USDT", "SOL/USDT"], index=0)
base_spacing = st.sidebar.number_input("Baseline Grid Spacing (%)", value=3.13, step=0.1)
vol_trigger = st.sidebar.number_input("Volatility Ratio Trigger (x)", value=1.5, step=0.1)


# --- LIGHTWEIGHT HIGH-SPEED DATA LOADER ---
@st.cache_data(ttl=3600)  # Cache data for 1 hour to keep UI snap-fast on adjustments
def load_six_months_data(target_symbol):
    exchange = ccxt.binance({'enableRateLimit': True, 'options': {'defaultType': 'spot'}})

    # Calculate timestamp for 180 days ago
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    since_timestamp = int(six_months_ago.timestamp() * 1000)

    all_candles = []
    while since_timestamp < int(datetime.utcnow().timestamp() * 1000):
        # Fetch in max allowed batches of 1000
        candles = exchange.fetch_ohlcv(target_symbol, timeframe='1h', since=since_timestamp, limit=1000)
        if not candles:
            break
        all_candles.extend(candles)
        # Advance timestamp to the end of current batch
        since_timestamp = candles[-1][0] + 60000
        if len(candles) < 1000:
            break  # Reached current time

    # Build memory-efficient DataFrame
    df = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('datetime', inplace=True)
    return df


with st.spinner("Fetching 6 months of hourly candles from exchange..."):
    df = load_six_months_data(symbol)

# --- TA-LIB ENGINE OPERATIONS ---
high_arr = df['high'].to_numpy()
low_arr = df['low'].to_numpy()
close_arr = df['close'].to_numpy()

# 1. Raw TR and ATR (14 Period)
df['TR'] = talib.TRANGE(high_arr, low_arr, close_arr)
df['ATR'] = talib.ATR(high_arr, low_arr, close_arr, timeperiod=14)

# 2. Projecting TR and ATR directly onto the Close Price
df['Price + ATR'] = df['close'] + df['ATR']
df['Price - ATR'] = df['close'] - df['ATR']
df['Price + TR'] = df['close'] + df['TR']
df['Price - TR'] = df['close'] - df['TR']

# 3. NATR (Current Volatility Percentage)
df['NATR'] = talib.NATR(high_arr, low_arr, close_arr, timeperiod=14)

# 4. Base NATR (100-Hour Rolling Average of NATR, shifted to ignore current candle)
df['Base_NATR'] = df['NATR'].shift(2).rolling(window=100).mean()

# 5. Grid Spacing Simulation Logic
df['Vol_Ratio'] = df['NATR'] / df['Base_NATR']
df['Dynamic_Spacing'] = np.where(
    df['Vol_Ratio'] > vol_trigger,
    base_spacing * df['Vol_Ratio'],
    base_spacing
)

# Clean up empty setup values for clean charting
df.dropna(subset=['Base_NATR'], inplace=True)

# --- UI CHARTS LAYOUT ---

st.markdown("### 1. Market Price with Overlaid Volatility Bands")
st.caption(
    "TR and ATR values projected directly relative to the closed price. This creates a real-time volatility envelope around the asset.")
# We pass the close price alongside the projected upper and lower bounds to maintain a uniform scale
st.line_chart(
    df[['close', 'Price + ATR', 'Price - ATR', 'Price + TR', 'Price - TR']],
    y_label="Price in USD",
    color=["#FF0000", "#1E88E5", "#1E88E5", "#00ACC1", "#00ACC1"]  # Red price, blue ATR bands, teal TR bands
)

st.markdown("---")

st.markdown("### 2. The Bot Brain: NATR vs Base NATR")
st.caption(
    "When the Blue Line (NATR %) spikes significantly above the Orange Line (Base NATR % Floor), the bot actively stretches your grid spacing.")
st.line_chart(df[['NATR', 'Base_NATR']], y_label="Percentage Value (%)", color=["#3F51B5", "#FF9800"])

st.markdown("---")

st.markdown("### 3. Historical Spacing Grid Adjustments")
st.caption(
    f"Visualizing what your exact grid spacing percentage would look like over the last 6 months based on your {base_spacing}% baseline setting.")
st.line_chart(df['Dynamic_Spacing'], y_label="Calculated Grid Spacing (%)", color="#4CAF50")

# --- INTERACTIVE SINGLE CANDLE INSPECTOR ---
st.markdown("---")
st.markdown("### 🔍 Granular Hourly Candle Inspector")
st.write("Pick an exact historical date and hour below to read out exactly where all metrics landed:")

selected_time = st.select_slider(
    "Slide to navigate back and forth through the 6-month timeline:",
    options=df.index.tolist(),
    format_func=lambda x: x.strftime('%Y-%m-%d %H:%M')
)

row = df.loc[selected_time]

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Candle Close Price", f"${row['close']:.2f}")
    st.metric("True Range (TR)", f"${row['TR']:.2f}")
with col2:
    st.metric("ATR (14)", f"${row['ATR']:.2f}")
    st.metric("Current NATR", f"{row['NATR']:.2f}%")
with col3:
    st.metric("Base NATR Floor (100h)", f"{row['Base_NATR']:.2f}%")
    st.metric("Volatility Ratio", f"{row['Vol_Ratio']:.2f}x")
with col4:
    is_triggered = "⚠️ WIDENED" if row['Vol_Ratio'] > vol_trigger else "✅ STANDARD"
    st.metric("Bot Status Regime", is_triggered)
    st.metric("Assigned Grid Spacing", f"{row['Dynamic_Spacing']:.2f}%")

st.markdown("---")
st.markdown("### 💾 Export Simulation Data")

# Convert dataframe to CSV format in memory
csv_data = df.to_csv(index=True)

st.download_button(
    label="Download Full Volatility Data as CSV",
    data=csv_data,
    file_name=f"{symbol.replace('/', '_')}_6m_volatility_data.csv",
    mime="text/csv",
    help="Click here to download all candles and calculated volatility bands to your computer."
)