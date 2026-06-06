# python -m pip install --upgrade pip
# pip install streamlit numpy pandas plotly
# streamlit run main.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# NATR	Market State
# < 1%	Quiet
# 1–3%	Normal
# 3–6%	High volatility
# > 6%	Extreme volatility


# Set page layout to wide for comfortable chart reading
st.set_page_config(layout="wide", page_title="Advanced Volatility Candlestick Viewer")

st.title("📈 Volatility Band Historical Candlestick Viewer")
st.subheader("Upload your exported CSV file to render the interactive price channels and indicators")

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
        required_columns = [
            'open', 'high', 'low', 'close',
            'Price + ATR', 'Price - ATR',
            'Price + TR', 'Price - TR',
            'ATR', 'NATR', 'Base_NATR'
        ]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            st.error(f"❌ The uploaded file is missing critical tracking columns: {missing_columns}")
        else:
            st.success("✅ Complete market footprint and indicators loaded successfully!")

            # --- TARGET GRAPH VISUALIZATION (PLOTLY PANEL) ---
            st.markdown("### Interactive Candlestick Chart & Volatility Panels")
            st.caption(
                "💡 **Zoom Tip:** Click and drag left/right on the chart body to zoom the timeline. "
                "To zoom vertically, click and drag up/down directly on the right-side price axis numbers."
            )

            # Create a shared X-axis subplot configuration layout
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.04,
                row_width=[0.3, 0.7]  # 70% height for price channel, 30% for percentage indicators
            )

            # 1. Base Candlestick Overlay (Row 1)
            fig.add_trace(
                go.Candlestick(
                    x=df.index,
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    name="OHLC Candle"
                ),
                row=1, col=1
            )

            # 2. Add Average True Range (ATR) Envelope lines (Row 1)
            fig.add_trace(
                go.Scatter(x=df.index, y=df['Price + ATR'], name="Price + ATR", line=dict(color='#1E88E5', width=1.5)),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=df.index, y=df['Price - ATR'], name="Price - ATR", line=dict(color='#1E88E5', width=1.5), showlegend=False),
                row=1, col=1
            )

            # 3. Add True Range (TR) Envelope lines (Row 1)
            fig.add_trace(
                go.Scatter(x=df.index, y=df['Price + TR'], name="Price + TR", line=dict(color='#00ACC1', width=1.2, dash='dash')),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(x=df.index, y=df['Price - TR'], name="Price - TR", line=dict(color='#00ACC1', width=1.2, dash='dash'), showlegend=False),
                row=1, col=1
            )

            # 4. Add Percentage Volatility Indicators (Row 2 Subplot)
            fig.add_trace(
                go.Scatter(x=df.index, y=df['NATR'], name="NATR (%)", line=dict(color='#FF9800', width=1.5)),
                row=2, col=1
            )
            fig.add_trace(
                go.Scatter(x=df.index, y=df['Base_NATR'], name="Base NATR (%)", line=dict(color='#E91E63', width=1.5, dash='dot')),
                row=2, col=1
            )

            # Layout Settings for Independent Axis Adjustment
            fig.update_layout(
                height=750,
                hovermode="x unified",
                xaxis_rangeslider_visible=False,  # Turned off messy slider to give you precise control
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )

            # Enforce clean label distributions across layouts
            fig.update_yaxes(title_text="Price in USD", row=1, col=1)
            fig.update_yaxes(title_text="Volatility Value (%)", row=2, col=1)
            fig.update_xaxes(title_text="Timeline Execution Steps", row=2, col=1)

            # Render the final interactive canvas frame inside the container
            st.plotly_chart(fig, use_container_width=True)

            # --- GRANULAR STEPPING SLIDER ---
            st.markdown("---")
            st.markdown("### 🔍 Timeline Inspector")

            selected_time = st.select_slider(
                "Navigate back and forth through the uploaded timeline:",
                options=df.index.tolist(),
                format_func=lambda x: x.strftime('%Y-%m-%d %H:%M')
            )

            row = df.loc[selected_time]

            # Display a clean data readout summary layout matching your custom metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.subheader("📊 Session Core")
                st.metric("Candle Open", f"${row['open']:.2f}")
                st.metric("Candle High", f"${row['high']:.2f}")
                st.metric("Candle Low", f"${row['low']:.2f}")
                st.metric("Candle Close", f"${row['close']:.2f}")
            with col2:
                st.subheader("🛡️ ATR Envelopes")
                st.metric("ATR Upper Bound", f"${row['Price + ATR']:.2f}")
                st.metric("ATR Lower Bound", f"${row['Price - ATR']:.2f}")
                st.caption(f"Raw Rolling ATR: ${row['ATR']:.2f}")
            with col3:
                st.subheader("⚡ TR Boundaries")
                st.metric("TR Upper Envelope", f"${row['Price + TR']:.2f}")
                st.metric("TR Lower Envelope", f"${row['Price - TR']:.2f}")
                st.caption(f"Raw Candle TR: ${row['TR']:.2f}")
            with col4:
                st.subheader("📉 Percent Scales")
                st.metric("Current NATR", f"{row['NATR']:.3f}%")
                st.metric("Base NATR", f"{row['Base_NATR']:.3f}%")

    except Exception as e:
        st.error(f"Failed to process the uploaded file format: {e}")

else:
    st.info(
        "💡 Please upload a valid CSV data export from your main volatility simulator to generate the chart channel views.")
