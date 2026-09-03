import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="PK Noodle Shop Dashboard", layout="wide")

# ==================== 1. Login ====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.subheader("🔒 เข้าสู่ระบบ")
    user = st.text_input("ชื่อผู้ใช้")
    pwd = st.text_input("รหัสผ่าน", type="password")
    if st.button("เข้าสู่ระบบ"):
        if user == "peter" and pwd == "100100":
            st.session_state.logged_in = True
            st.session_state.user = user
            st.rerun()
        else:
            st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    st.stop()

st.sidebar.write(f"👤 {st.session_state.user}")
if st.sidebar.button("ออกจากระบบ"):
    st.session_state.logged_in = False
    st.rerun()

# ==================== 2. CSS ====================
st.markdown("""
<style>
    footer {visibility: hidden;}
    .stMetric {background-color: #f8f9fa; padding: 10px; border-radius: 8px;}
</style>
""", unsafe_allow_html=True)

st.title("🍜 PK Noodle Shop - Executive Dashboard")

# ==================== 3. โหลดข้อมูล ====================
@st.cache_data(ttl=300)
def load_sales_data():
    if os.path.exists("sales data.CSV"):
        try:
            return pd.read_csv("sales data.CSV", encoding="utf-8-sig")
        except:
            return pd.read_csv("sales data.CSV", encoding="tis-620")
    return pd.DataFrame()

@st.cache_data(ttl=300)
def load_product_data():
    if os.path.exists("product data.CSV"):
        try:
            return pd.read_csv("product data.CSV", encoding="utf-8-sig")
        except:
            return pd.read_csv("product data.CSV", encoding="tis-620")
    return pd.DataFrame()

df_sales = load_sales_data()
df_product = load_product_data()

# ==================== 4. ทำความสะอาดข้อมูล ====================
def clean_data(df):
    if df.empty:
        return df
    df.columns = [str(c).strip() for c in df.columns]
    
    # ตัวอย่างการจัดการวันที่ (ปรับให้ตรงกับไฟล์จริงของคุณ)
    date_cols = [c for c in df.columns if "DATE" in c.upper() or "วันที่" in c]
    if date_cols:
        df["Parsed_Date"] = pd.to_datetime(df[date_cols[0]], errors="coerce")
    
    if "GRANDTOTAL" in df.columns:
        df["GRANDTOTAL"] = pd.to_numeric(df["GRANDTOTAL"], errors="coerce").fillna(0)
    if "BRANCH" in df.columns or "สาขา" in df.columns:
        branch_col = "BRANCH" if "BRANCH" in df.columns else "สาขา"
        df["BRANCH"] = df[branch_col].astype(str).str.strip()
    return df

df_sales = clean_data(df_sales)

# ==================== 5. เมนูกรองข้อมูล ====================
st.sidebar.header("📅 ตัวกรองข้อมูล")

# ตัวกรองวันที่ (คงฟังก์ชันเดิมไว้)
date_options = ["วันนี้", "7 วันล่าสุด", "30 วันล่าสุด", "เลือกเอง"]
selected_option = st.sidebar.selectbox("เลือกช่วงเวลา", date_options)

if selected_option == "เลือกเอง":
    if not df_sales.empty and "Parsed_Date" in df_sales.columns:
        min_d = df_sales["Parsed_Date"].min().date()
        max_d = df_sales["Parsed_Date"].max().date()
        date_range = st.sidebar.date_input("ช่วงวันที่", [min_d, max_d])
    else:
        date_range = [datetime.now().date(), datetime.now().date()]
else:
    today = datetime.now().date()
    if selected_option == "วันนี้":
        date_range = [today, today]
    elif selected_option == "7 วันล่าสุด":
        date_range = [today - timedelta(days=7), today]
    else:
        date_range = [today - timedelta(days=30), today]

# กรองสาขา
if not df_sales.empty and "BRANCH" in df_sales.columns:
    branches = st.sidebar.multiselect("เลือกสาขา", df_sales["BRANCH"].unique(), default=df_sales["BRANCH"].unique())
    df_filtered = df_sales[df_sales["BRANCH"].isin(branches)]
else:
    df_filtered = df_sales.copy()

# กรองวันที่
if "Parsed_Date" in df_filtered.columns and len(date_range) == 2:
    df_filtered = df_filtered[
        (df_filtered["Parsed_Date"].dt.date >= date_range[0]) & 
        (df_filtered["Parsed_Date"].dt.date <= date_range[1])
    ]

# ==================== 6. แสดงผล ====================
if df_filtered.empty:
    st.warning("ไม่พบข้อมูลในช่วงที่เลือก")
else:
    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("ยอดขายรวม", f"฿{df_filtered['GRANDTOTAL'].sum():,.0f}")
    col2.metric("จำนวนบิล", f"{len(df_filtered):,}")
    col3.metric("เฉลี่ยต่อบิล", f"฿{df_filtered['GRANDTOTAL'].mean():,.0f}")

    # Tabs (คงฟังก์ชันเดิม)
    tab1, tab2, tab3, tab4 = st.tabs(["📊 สรุปตามสาขา", "📈 แนวโน้มรายวัน", "📋 ตารางข้อมูล", "🏆 สินค้าขายดี"])

    with tab1:
        if "BRANCH" in df_filtered.columns:
            branch_sum = df_filtered.groupby("BRANCH")["GRANDTOTAL"].sum().reset_index()
            fig1 = px.bar(branch_sum, x="BRANCH", y="GRANDTOTAL", color="BRANCH")
            st.plotly_chart(fig1, use_container_width=True)

            fig2 = px.pie(branch_sum, values="GRANDTOTAL", names="BRANCH")
            st.plotly_chart(fig2, use_container_width=True)

    with tab2:
        if "Parsed_Date" in df_filtered.columns:
            daily = df_filtered.groupby(df_filtered["Parsed_Date"].dt.date)["GRANDTOTAL"].sum().reset_index()
            daily.columns = ["Date", "Sales"]
            fig3 = px.line(daily, x="Date", y="Sales")
            st.plotly_chart(fig3, use_container_width=True)

    with tab3:
        st.dataframe(df_filtered, use_container_width=True)

    with tab4:
        if not df_product.empty:
            st.bar_chart(df_product.head(10))   # ตัวอย่างแสดงสินค้าขายดี

    # ปุ่ม Export
    if st.button("📥 Export ข้อมูลที่กรองแล้ว"):
        csv = df_filtered.to_csv(index=False).encode("utf-8-sig")
        st.download_button("ดาวน์โหลด CSV", csv, "filtered_sales.csv", "text/csv")
