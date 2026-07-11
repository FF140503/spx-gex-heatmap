import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import yfinance as yf

# إعدادات مظهر الواجهة الداكنة والعريضة
st.set_page_config(page_title="SPX GEX Heatmap", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #ffffff; }
    h1, h2, h3 { color: #00ff88 !important; text-align: center; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 لوحة تحكم مستويات الجاما والسيولة لـ SPX")
st.write("---")

# جلب بيانات SPX الحية
@st.cache_data(ttl=300)
def load_gex_data():
    # سحب بيانات سلسلة عقود الخيارات لمؤشر SPX
    ticker = yf.Ticker("^SPX")
    
    # اختيار أول تاريخ انتهاء متوفر كمثال
    if not ticker.options:
        return pd.DataFrame()
    
    target_expiry = ticker.options[0]
    opt_chain = ticker.option_chain(target_expiry)
    
    calls = opt_chain.calls[['strike', 'openInterest', 'volume']]
    puts = opt_chain.puts[['strike', 'openInterest', 'volume']]
    
    # دمج البيانات لحساب صافي السيولة المفتوحة (GEX التقريبي)
    df_calls = calls.set_index('strike')
    df_puts = puts.set_index('strike')
    
    # معادلة تقريبية لحساب توازن السيولة (Calls - Puts)
    df_net = (df_calls['openInterest'].fillna(0) - df_puts['openInterest'].fillna(0)) / 1000.0
    df_final = pd.DataFrame(df_net, columns=[target_expiry])
    
    # حصر النطاق حول السعر الحالي لتفادي الزحمة
    spot_price = ticker.history(period="1d")['Close'].iloc[-1]
    df_final = df_final.loc[int(spot_price)-50:int(spot_price)+50]
    
    return df_final

try:
    with st.spinner("جاري سحب بيانات الخيارات الحية من السوق..."):
        df_data = load_gex_data()
        
    if not df_data.empty:
        # رسم الهيت ماب التفاعلي بألوان Quant Data (أحمر للـ Call، أخضر للـ Put)
        fig = px.imshow(
            df_data,
            labels=dict(x="تاريخ الانتهاء", y="Strike (سعر التنفيذ)", color="صافي السيولة (بالآلاف)"),
            aspect="auto",
            color_continuous_scale=[[0, "#ff0055"], [0.5, "#161b22"], [1, "#00ff88"]],
            text_auto=".1f"
        )
        
        fig.update_layout(plot_bgcolor="#0d1117", paper_bgcolor="#0d1117", font_color="#ffffff", height=800)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("لم يتم العثور على بيانات خيارات نشطة حالياً.")
except Exception as e:
    st.error(f"حدث خطأ أثناء جلب البيانات: {e}")
