# python -m pip install --upgrade pip
# pip install TA-Lib
# pip install streamlit ccxt numpy pandas
# ===   or ==
#  pip install streamlit ccxt talib numpy pandas
# streamlit run main.py

import streamlit as st
import pandas as pd

# Set page layout to wide for comfortable chart reading
st.set_page_config(layout="wide", page_title="Volatility Band Viewer")

st.title("📈 Volatility Band Historical Viewer")
st.subheader("Upload your exported CSV file to render the interactive price channel")

# --- FILE UPLOADER ENGINE ---
uploaded_file = st.file_uploader("Choose the generated volatility CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        # Load the CSV file and parse dates cleanly
        df = pd.read_csv(uploaded_file)

        # Ensure standard datetime indexing works properly for the charts
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])
            df.set_index('datetime', inplace=True)
        elif 'timestamp' in df.columns:
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('datetime', inplace=True)

        # Confirm required tracking columns exist in the file structure
        required_columns = ['close', 'Price + ATR', 'Price - ATR', 'Price + TR', 'Price - TR']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            st.error(f"❌ The uploaded file is missing critical tracking columns: {missing_columns}")
        else:
            st.success("✅ Data successfully loaded from file footprint!")

            # --- TARGET GRAPH VISUALIZATION ---
            st.markdown("### Market Price with Overlaid Volatility Bands")
            st.caption(
                "TR and ATR values projected directly relative to the closed price from your historic session footprint.")

            st.line_chart(
                df[required_columns],
                y_label="Price in USD",
                color=["#FF0000", "#1E88E5", "#1E88E5", "#00ACC1", "#00ACC1"]  # Red price, blue ATR, teal TR
            )

            # --- GRANULAR STEPPING SLIDER ---
            st.markdown("---")
            st.markdown("### 🔍 Timeline Inspector")

            selected_time = st.select_slider(
                "Navigate back and forth through the uploaded timeline:",
                options=df.index.tolist(),
                format_func=lambda x: x.strftime('%Y-%m-%d %H:%M')
            )

            row = df.loc[selected_time]

            # Display a clean data readout summary layout
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Candle Close Price", f"${row['close']:.2f}")
            with col2:
                st.metric("ATR Upper Boundary", f"${row['Price + ATR']:.2f}")
                st.metric("ATR Lower Boundary", f"${row['Price - ATR']:.2f}")
            with col3:
                st.metric("TR Upper Envelope", f"${row['Price + TR']:.2f}")
                st.metric("TR Lower Envelope", f"${row['Price - TR']:.2f}")

    except Exception as e:
        st.error(f"Failed to process the uploaded file format: {e}")

else:
    st.info(
        "💡 Please upload a valid CSV data export from your main volatility simulator to generate the chart channel views.")