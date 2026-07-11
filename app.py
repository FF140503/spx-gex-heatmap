import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import yfinance as yf

st.set_page_config(page_title="Multi-Asset GEX Dashboard", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #ffffff; }
    h1, h2, h3 { color: #00ff88 !important; text-align: center; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 منصة سيولة صناع السوق والجاما الحية (GEX)")
st.write("---")

asset_options = {
    "S&P 500 Index (SPX)": "^SPX",
    "SPY ETF": "SPY",
    "QQQ ETF": "QQQ",
    "NVIDIA (NVDA)": "NVDA",
    "TESLA (TSLA)": "TSLA",
    "META (META)": "META"
}

col1, col2 = st.columns(2)
with col1:
    selected_asset_label = st.selectbox("🎯 اختر المؤشر أو السهم:", list(asset_options.keys()))
    ticker_symbol = asset_options[selected_asset_label]

ticker = yf.Ticker(ticker_symbol)

with col2:
    try:
        options_list = ticker.options
        if options_list:
            selected_expiry = st.selectbox("📅 اختر تاريخ انتهاء العقود (Expiry):", options_list)
        else:
            selected_expiry = None
            st.error("لا توجد عقود متاحة حالياً.")
    except:
        selected_expiry = None
        st.error("خطأ في جلب تواريخ الخيارات.")

st.write("---")

@st.cache_data(ttl=120)
def load_asset_gex(symbol, expiry_date):
    try:
        tk = yf.Ticker(symbol)
        opt_chain = tk.option_chain(expiry_date)
        
        calls = opt_chain.calls[['strike', 'openInterest']].set_index('strike')
        puts = opt_chain.puts[['strike', 'openInterest']].set_index('strike')
        
        net_gex = (calls['openInterest'].fillna(0) - puts['openInterest'].fillna(0)) / 1000.0
        df_final = pd.DataFrame(net_gex, columns=[expiry_date])
        
        # حماية الموقع لو كان السوق مغلقاً (الأحد)
        hist = tk.history(period="5d")
        if not hist.empty and 'Close' in hist.columns:
            spot_price = hist['Close'].iloc[-1]
        else:
            spot_price = df_final.index.median() if not df_final.empty else 100.0
            
        # فلترة النطاق بذكاء تفادياً للكراش
        if not df_final.empty:
            min_strike = int(spot_price) - (35 if symbol in ["NVDA", "TSLA", "META"] else 75)
            max_strike = int(spot_price) + (35 if symbol in ["NVDA", "TSLA", "META"] else 75)
            df_final = df_final.loc[min_strike:max_strike]
            
        return df_final, spot_price
    except:
        return pd.DataFrame(), 0

if selected_expiry:
    with st.spinner("جاري معالجة البيانات الحية للسوق..."):
        df_data, current_spot = load_asset_gex(ticker_symbol, selected_expiry)
        
    if not df_data.empty and current_spot > 0:
        st.metric(label=f"السعر الحالي لـ {selected_asset_label}", value=f"${current_spot:,.2f}")
        
        fig = px.imshow(
            df_data,
            labels=dict(x="تاريخ الانتهاء", y="Strike", color="صافي السيولة"),
            aspect="auto",
            color_continuous_scale=[[0, "#ff0055"], [0.5, "#161b22"], [1, "#00ff88"]],
            text_auto=".1f"
        )
        fig.update_layout(plot_bgcolor="#0d1117", paper_bgcolor="#0d1117", font_color="#ffffff", height=800)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ لا توجد سيولة كافية مسجلة لهذه العقود اليوم أو أن الداتا التاريخية غير متاحة حالياً، جرب اختيار أصل آخر مثل NVDA أو TSLA.")
