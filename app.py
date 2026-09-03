import streamlit as st
import pandas as pd
import datetime
import pytz
import plotly.express as px
import os

st.set_page_config(page_title="PK Noodle Shop Dashboard", page_icon="🍜", layout="wide")

# ==================== 1. ระบบ Login (ปรับปรุง) ====================
def login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.markdown("<h2 style='text-align: center;'>🔒 เข้าสู่ระบบ PK Noodle Shop</h2>", unsafe_allow_html=True)
        
        with st.form("login"):
            username = st.text_input("ชื่อผู้ใช้")
            password = st.text_input("รหัสผ่าน", type="password")
            if st.form_submit_button("เข้าสู่ระบบ"):
                # แนะนำ: ใช้ st.secrets แทนการ hardcode
                if username == "peter" and password == "100100":
                    st.session_state.logged_in = True
                    st.session_state.user = username
                    st.rerun()
                else:
                    st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
        st.stop()

login()

# ==================== 2. CSS และ UI ====================
st.markdown("""
<style>
    div[data-testid="metric-container"] {background-color: #f8f9fa; border-radius: 10px; padding: 15px;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.title("🍜 PK Noodle Shop - Executive Dashboard")
st.caption(f"ผู้ใช้งาน: **{st.session_state.user}** | v.11.0 (ปรับปรุง)")

# ==================== 3. โหลดข้อมูล ====================
@st.cache_data(ttl=300)
def load_data():
    df = pd.DataFrame()
    if os.path.exists("sales data.CSV"):
        try:
            df = pd.read_csv("sales data.CSV", encoding='utf-8-sig')
        except:
            df = pd.read_csv("sales data.CSV", encoding='tis-620')
    
    # ทำความสะอาดคอลัมน์เบื้องต้น
    if not df.empty:
        df.columns = df.columns.str.strip()
        # ตัวอย่างการจัดการวันที่ (แนะนำปรับให้ตรงกับไฟล์จริง)
        if 'TRANDATE' in df.columns:
            df['Parsed_Date'] = pd.to_datetime(df['TRANDATE'], errors='coerce')
        if 'GRANDTOTAL' in df.columns:
            df['GRANDTOTAL'] = pd.to_numeric(df['GRANDTOTAL'], errors='coerce').fillna(0)
        if 'NAME' in df.columns:
            df['NAME'] = df['NAME'].astype(str).str.strip()
    return df

df = load_data()

# ==================== 4. เมนูกรองข้อมูล ====================
st.sidebar.header("🔍 ตัวกรองข้อมูล")
if not df.empty:
    # ตัวอย่างกรองวันที่แบบง่าย
    min_date = df['Parsed_Date'].min().date() if 'Parsed_Date' in df.columns else datetime.date.today()
    max_date = df['Parsed_Date'].max().date() if 'Parsed_Date' in df.columns else datetime.date.today()
    
    date_range = st.sidebar.date_input("เลือกช่วงวันที่", [min_date, max_date])
    
    branches = st.sidebar.multiselect("เลือกสาขา", df['NAME'].unique(), default=df['NAME'].unique())
    df_filtered = df[df['NAME'].isin(branches)]
    
    if len(date_range) == 2:
        df_filtered = df_filtered[(df_filtered['Parsed_Date'].dt.date >= date_range[0]) & 
                                  (df_filtered['Parsed_Date'].dt.date <= date_range[1])]

# ==================== 5. แสดงผล ====================
if not df_filtered.empty:
    col1, col2, col3 = st.columns(3)
    col1.metric("ยอดขายรวม", f"฿{df_filtered['GRANDTOTAL'].sum():,.0f}")
    col2.metric("จำนวนบิล", f"{len(df_filtered):,}")
    col3.metric("เฉลี่ยต่อบิล", f"฿{df_filtered['GRANDTOTAL'].mean():,.0f}")

    # กราฟตัวอย่าง
    st.subheader("ยอดขายตามสาขา")
    branch_sum = df_filtered.groupby('NAME')['GRANDTOTAL'].sum().reset_index()
    fig = px.bar(branch_sum, x='NAME', y='GRANDTOTAL', color='NAME')
    st.plotly_chart(fig, use_container_width=True)

    # ปุ่ม Export
    if st.button("📥 Export เป็น CSV"):
        csv = df_filtered.to_csv(index=False).encode('utf-8-sig')
        st.download_button("ดาวน์โหลดไฟล์", csv, "sales_filtered.csv", "text/csv")
else:
    st.warning("ไม่พบข้อมูลในช่วงที่เลือก")

st.caption("ปรับปรุงแล้ว • ง่ายต่อการบำรุงรักษา")
