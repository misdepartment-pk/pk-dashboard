import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime, timedelta

# ==========================================
# 1. PAGE CONFIG & SESSION STATE
# ==========================================
st.set_page_config(
    page_title="PK NOODLE SHOP Dashboard",
    page_icon="logo.png" if os.path.exists("logo.png") else "🍜",
    layout="wide",
    initial_sidebar_state="expanded"
)

if 'nav_date' not in st.session_state:
    current_time_th = datetime.utcnow() + timedelta(hours=7)
    st.session_state.nav_date = current_time_th.date()

def go_prev():
    st.session_state.nav_date -= timedelta(days=1)

def go_next():
    st.session_state.nav_date += timedelta(days=1)

# ==========================================
# 2. CSS STYLING
# ==========================================
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .metric-card {
        background-color: #ffffff; border-radius: 12px; padding: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05); text-align: center;
    }
    .metric-value { font-size: 28px; font-weight: 700; color: #1e293b; }
    .metric-label { font-size: 14px; color: #64748b; margin-bottom: 4px; }
    .trick-banner {
        background-color: #e0f2fe; color: #0369a1; padding: 10px 16px;
        border-radius: 8px; font-size: 14px; margin-bottom: 20px;
        display: flex; align-items: center; gap: 8px;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 45px; white-space: pre-wrap; background-color: #ffffff;
        border-radius: 6px 6px 0px 0px; padding: 8px 16px; font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff; border-bottom: 3px solid #ef4444 !important;
        color: #ef4444 !important;
    }
    div[data-testid="stDateInput"] input {
        text-align: center !important; color: #0284c7 !important;
        font-weight: 800 !important; font-size: 26px !important;
        padding-top: 10px !important; padding-bottom: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. HELPER FUNCTIONS & DATA LOADING
# ==========================================
def parse_thai_date(date_str):
    if pd.isna(date_str) or str(date_str).strip() == '':
        return pd.NaT
    date_s = str(date_str).strip()
    if 'T' in date_s:
        try: return pd.to_datetime(date_s.split('T')[0])
        except: pass
    try:
        date_only = date_s.split()[0]
        parts = date_only.replace('-', '/').split('/')
        if len(parts) == 3:
            p1, p2, p3 = int(parts[0]), int(parts[1]), int(parts[2])
            if p1 > 1000: y, m, d = p1, p2, p3
            elif p3 > 1000: y, m, d = p3, p2, p1 if p3 > 12 else (p3, p1, p2)
            else: y, m, d = p3, p2, p1 
            if y > 2500: y -= 543 
            return pd.Timestamp(year=y, month=m, day=d)
    except: pass
    try: return pd.to_datetime(date_s.split()[0], dayfirst=True, errors='coerce')
    except: return pd.NaT

@st.cache_data(ttl=300)
def load_all_sales_data():
    dfs = []
    files_in_dir = os.listdir('.') if os.path.exists('.') else []
    
    sales_files = [
        f for f in files_in_dir 
        if any(k in f.lower() for k in ['sale', 'sales', 'ยอดขาย']) 
        and not any(p in f.lower() for p in ['product', 'สินค้า'])
        and f.lower().endswith(('.csv', '.xlsx', '.xls'))
    ]
    
    for filename in sales_files:
        try:
            if filename.lower().endswith('.csv'):
                try: df_temp = pd.read_csv(filename, encoding='utf-8-sig', low_memory=False)
                except: df_temp = pd.read_csv(filename, encoding='tis-620', low_memory=False)
            else:
                df_temp = pd.read_excel(filename)
                
            df_temp.columns = [str(c).upper().strip() for c in df_temp.columns]
            dfs.append(df_temp)
        except: pass
                
    if not dfs:
        return pd.DataFrame(columns=['Parsed_Date', 'Year_BE', 'NAME', 'GRANDTOTAL', 'ORDER_COUNT'])
        
    df_combined = pd.concat(dfs, ignore_index=True).drop_duplicates()
    
    date_col = next((c for c in ['DOC_DATE', 'DOCDATE', 'TRANDATE', 'CF_TRANDATE', 'PSH_DATE', 'วันที่', 'PDATA_CODE'] if c in df_combined.columns), None)
    if date_col: df_combined['Parsed_Date'] = df_combined[date_col].apply(parse_thai_date)
    else: df_combined['Parsed_Date'] = pd.NaT
    df_combined['Year_BE'] = df_combined['Parsed_Date'].dt.year + 543
    
    sales_col = next((c for c in ['GRAND_TOTAL', 'GRANDTOTAL', 'AMOUNT', 'PSD_N_AMT', 'ยอดขาย(บาท)', 'PDATA_NET_AMT', 'ยอดขายทั้งสิ้น'] if c in df_combined.columns), None)
    if sales_col: df_combined['GRANDTOTAL'] = pd.to_numeric(df_combined[sales_col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
    else: df_combined['GRANDTOTAL'] = 0.0

    branch_col = next((c for c in ['BRANCH_NAME', 'BRANCHNAME', 'NAME', 'PSH_BR_NAME', 'สาขา'] if c in df_combined.columns), None)
    if branch_col: df_combined['NAME'] = df_combined[branch_col].astype(str).str.replace('\u200b', '').str.replace('\xa0', ' ').str.replace('ตลาด', '').str.strip()
    else: df_combined['NAME'] = 'สาขาหลัก'

    bill_col = next((c for c in ['ORDER_COUNT', 'BILL_COUNT', 'NO_OF_BILL', 'BILL_QTY', 'PDATA_QTY'] if c in df_combined.columns), None)
    if bill_col: df_combined['ORDER_COUNT'] = pd.to_numeric(df_combined[bill_col], errors='coerce').fillna(1)
    else: df_combined['ORDER_COUNT'] = 1

    return df_combined

@st.cache_data(ttl=300)
def load_product_data():
    dfs = []
    files = [f for f in os.listdir('.') if any(k in f.lower() for k in ['product', 'pdata', 'สินค้า', 'item']) and f.lower().endswith(('.csv', '.xlsx', '.xls'))]
    for f in files:
        try:
            if f.endswith('.csv'):
                try: df = pd.read_csv(f, encoding='utf-8-sig', low_memory=False)
                except: df = pd.read_csv(f, encoding='tis-620', low_memory=False)
            else: df = pd.read_excel(f)
            df.columns = [str(c).upper().strip() for c in df.columns]
            dfs.append(df)
        except: pass
        
    if not dfs: return pd.DataFrame()
    df_p = pd.concat(dfs, ignore_index=True)
    
    # Date
    date_col = next((c for c in ['DOC_DATE', 'DOCDATE', 'TRANDATE', 'CF_TRANDATE', 'PSH_DATE', 'วันที่', 'PDATA_DATE'] if c in df_p.columns), None)
    if date_col: df_p['Parsed_Date'] = df_p[date_col].apply(parse_thai_date)
    else: df_p['Parsed_Date'] = pd.NaT
    df_p['Year_BE'] = df_p['Parsed_Date'].dt.year + 543
    
    # Branch
    branch_col = next((c for c in ['BRANCH_NAME', 'BRANCHNAME', 'NAME', 'PSH_BR_NAME', 'สาขา'] if c in df_p.columns), None)
    if branch_col: df_p['BRANCH_NAME'] = df_p[branch_col].astype(str).str.replace('\u200b', '').str.replace('\xa0', ' ').str.replace('ตลาด', '').str.strip()
    else: df_p['BRANCH_NAME'] = 'สาขาหลัก'
    
    # Qty & Amount
    qty_col = next((c for c in ['PDATA_QTY', 'QTY', 'AMOUNT_QTY', 'จำนวน', 'QUANTITY'] if c in df_p.columns), None)
    if qty_col: df_p['QTY'] = pd.to_numeric(df_p[qty_col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(1)
    else: df_p['QTY'] = 1
    
    sales_col = next((c for c in ['GRAND_TOTAL', 'GRANDTOTAL', 'AMOUNT', 'PSD_N_AMT', 'ยอดขาย(บาท)', 'PDATA_NET_AMT', 'NET_AMT', 'TOTAL'] if c in df_p.columns), None)
    if sales_col: df_p['GRANDTOTAL'] = pd.to_numeric(df_p[sales_col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
    else: df_p['GRANDTOTAL'] = 0.0
    
    # Product Name
    prod_col = next((c for c in ['PDATA_NAME', 'NAME1', 'PRODUCT_NAME', 'ITEM_NAME', 'ชื่อสินค้า', 'DESCR', 'GOODS_NAME'] if c in df_p.columns), None)
    if prod_col: df_p['PRODUCT_NAME'] = df_p[prod_col].astype(str).strip()
    else: df_p['PRODUCT_NAME'] = 'ไม่ระบุชื่อสินค้า'
    
    return df_p

df_all = load_all_sales_data()

# ==========================================
# 4. SIDEBAR FILTERS
# ==========================================
st.sidebar.title("🔍 เมนูกรองข้อมูล")
st.sidebar.markdown("### 📅 1. เลือกเวลาที่ต้องการดู")

available_years = sorted([int(y) for y in df_all['Year_BE'].dropna().unique() if y > 2000], reverse=True)
if not available_years: available_years = [2569, 2568]
selected_years = st.sidebar.multiselect("เลือกปี พ.ศ.:", options=available_years, default=available_years)

quick_time = st.sidebar.selectbox(
    "เลือกช่วงเวลาแบบด่วน:",
    ["ใช้วันที่จาก Date Navigator", "ดูข้อมูลทั้งหมด", "วันนี้", "เมื่อวาน", "7 วันล่าสุด", "30 วันล่าสุด", "เดือนนี้", "กำหนดเอง (เลือกปฏิทิน)"]
)

start_date, end_date = None, None
if quick_time == "กำหนดเอง (เลือกปฏิทิน)":
    min_d = df_all['Parsed_Date'].min() if not df_all['Parsed_Date'].isna().all() else datetime.today()
    max_d = df_all['Parsed_Date'].max() if not df_all['Parsed_Date'].isna().all() else datetime.today()
    date_range = st.sidebar.date_input("เลือกช่วงวันที่:", [min_d, max_d])
    if len(date_range) == 2: start_date, end_date = date_range[0], date_range[1]

with st.sidebar.expander("➕ กรองตามเดือน (สำหรับดูข้ามปี)", expanded=False):
    month_names = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", 
                   "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
    selected_months = st.sidebar.multiselect("เลือกเดือนที่ต้องการดู:", month_names, default=[])

st.sidebar.markdown("---")
st.sidebar.markdown("### 🏬 2. เลือกสาขา")

all_branches = sorted(df_all['NAME'].dropna().unique().tolist())
if not all_branches: all_branches = ["ศรีเมือง", "ทุ่งปอ", "เจ้าพรหม", "บ้านไร่", "เทศบาล", "บ้านโป่ง"]
selected_branches = st.sidebar.multiselect("กด X เพื่อลบ หรือพิมพ์เพื่อหาสาขา:", options=all_branches, default=all_branches)

st.sidebar.markdown("---")
st.sidebar.caption("Powered by peter pak: v.10.2.0")

# ==========================================
# 5. FILTERING LOGIC (SALES)
# ==========================================
df_filtered = df_all.copy()
current_time_th = datetime.utcnow() + timedelta(hours=7)
today_date = current_time_th.date()

if selected_years: df_filtered = df_filtered[df_filtered['Year_BE'].isin(selected_years)]
else: df_filtered = df_filtered.iloc[0:0]

if selected_branches: df_filtered = df_filtered[df_filtered['NAME'].isin(selected_branches)]
else: df_filtered = df_filtered.iloc[0:0]

if selected_months:
    month_map = {m: i+1 for i, m in enumerate(month_names)}
    target_month_nums = [month_map[m] for m in selected_months if m in month_map]
    df_filtered = df_filtered[df_filtered['Parsed_Date'].dt.month.isin(target_month_nums)]

if quick_time != "ดูข้อมูลทั้งหมด" and not df_filtered.empty:
    if quick_time == "ใช้วันที่จาก Date Navigator":
        df_filtered = df_filtered[df_filtered['Parsed_Date'].dt.date == st.session_state.nav_date]
    elif quick_time == "วันนี้":
        df_filtered = df_filtered[df_filtered['Parsed_Date'].dt.date == today_date]
    elif quick_time == "เมื่อวาน":
        df_filtered = df_filtered[df_filtered['Parsed_Date'].dt.date == (today_date - timedelta(days=1))]
    elif quick_time == "7 วันล่าสุด":
        df_filtered = df_filtered[df_filtered['Parsed_Date'].dt.date >= (today_date - timedelta(days=7))]
    elif quick_time == "30 วันล่าสุด":
        df_filtered = df_filtered[df_filtered['Parsed_Date'].dt.date >= (today_date - timedelta(days=30))]
    elif quick_time == "เดือนนี้":
        df_filtered = df_filtered[(df_filtered['Parsed_Date'].dt.month == today_date.month) & (df_filtered['Parsed_Date'].dt.year == today_date.year)]
    elif quick_time == "กำหนดเอง (เลือกปฏิทิน)" and start_date and end_date:
        df_filtered = df_filtered[(df_filtered['Parsed_Date'].dt.date >= start_date) & (df_filtered['Parsed_Date'].dt.date <= end_date)]

# ==========================================
# 6. HEADER & DATE NAVIGATOR
# ==========================================
col_header, col_space = st.columns([5, 1])
with col_header:
    col_img, col_txt = st.columns([1, 8])
    with col_img:
        if os.path.exists("logo.png"): st.image("logo.png", width=100)
    with col_txt:
        st.markdown(
            """
            <div style="display: flex; align-items: center; height: 100%; padding-top: 15px; white-space: nowrap;">
                <h2 style="margin: 0; line-height: 1.2; font-size: 26px;">
                    <span style="color: #2b9e3e; font-weight: 800;">PK NOODLE SHOP COMPANY LIMITED </span>
                    <span style="color: red; font-weight: bold;">(Senior Soft- >>เริ่ม 5 สิงหาคม 2569)</span>
                </h2>
            </div>
            """, unsafe_allow_html=True
        )

st.markdown('<div class="trick-banner">🧮 <b>ทริค:</b> เมนูกรองข้อมูลอยู่ด้านซ้ายมือ (หากซ่อนอยู่ให้กดปุ่ม > เพื่อเปิด)</div>', unsafe_allow_html=True)

nav_l, nav_m, nav_r = st.columns([1, 5, 1])
with nav_l: st.button("❮ วันก่อนหน้า", on_click=go_prev, use_container_width=True)
with nav_m: st.date_input("เลือกวันที่", key="nav_date", label_visibility="collapsed", format="DD/MM/YYYY")
with nav_r: st.button("วันถัดไป ❯", on_click=go_next, use_container_width=True)
st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 7. METRICS 
# ==========================================
total_sales = df_filtered['GRANDTOTAL'].sum()
total_bills = len(df_filtered)
avg_per_bill = total_sales / total_bills if total_bills > 0 else 0

m1, m2, m3 = st.columns(3)
with m1:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">ยอดขายรวมทั้งหมด (บาท)</div>
            <div class="metric-value">฿{total_sales:,.2f}</div>
        </div>
    """, unsafe_allow_html=True)

with m2:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">จำนวนบิล (นับจากจำนวนบรรทัด)</div>
            <div class="metric-value">{total_bills:,}</div>
        </div>
    """, unsafe_allow_html=True)

with m3:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">ยอดเฉลี่ยต่อบิล (บาท)</div>
            <div class="metric-value">฿{avg_per_bill:,.2f}</div>
        </div>
    """, unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 8. VISUALIZATIONS & TABS
# ==========================================
branch_color_map = {
    'ศรีเมือง': '#EF4444', 'ทุ่งปอ': '#3B82F6', 'เจ้าพรหม': '#A855F7',  
    'บ้านไร่': '#10B981', 'เทศบาล': '#EAB308', 'บ้านโป่ง': '#EC4899'   
}

tab_branch, tab_trend, tab_table, tab_bestseller = st.tabs([
    "🏢 ยอดรวมสาขา", "📈 เทรนด์รายวัน", "📋 ตารางตัวเลข", "🍜 สินค้าขายดี"
])

with tab_branch:
    if df_filtered.empty:
        st.info("ไม่พบข้อมูลยอดขาย (ภายใต้เงื่อนไขการกรองปัจจุบัน)")
    else:
        branch_summary = df_filtered.groupby('NAME')['GRANDTOTAL'].sum().reset_index().sort_values(by='GRANDTOTAL', ascending=False)
        c_bar, c_donut = st.columns([1.2, 1])
        with c_bar:
            st.markdown("##### ยอดขาย (กราฟแท่ง)")
            fig_bar = px.bar(branch_summary, x='NAME', y='GRANDTOTAL', color='NAME', text='GRANDTOTAL', color_discrete_map=branch_color_map)
            fig_bar.update_traces(texttemplate='%{text:,.2f}', textposition='outside', cliponaxis=False)
            fig_bar.update_layout(xaxis_title="", yaxis_title="ยอดขาย (บาท)", showlegend=False, height=400, margin=dict(l=20, r=20, t=30, b=20), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_bar, use_container_width=True)
        with c_donut:
            st.markdown("##### สัดส่วนยอดขาย (กราฟโดนัท)")
            fig_donut = px.pie(branch_summary, values='GRANDTOTAL', names='NAME', color='NAME', hole=0.5, color_discrete_map=branch_color_map)
            fig_donut.update_traces(textinfo='percent+label', insidetextorientation='radial')
            fig_donut.update_layout(showlegend=True, height=400, margin=dict(l=20, r=20, t=30, b=20), paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_donut, use_container_width=True)

with tab_trend:
    st.markdown("##### 📈 เทรนด์ยอดขายรายวัน")
    if not df_filtered.empty and not df_filtered['Parsed_Date'].isna().all():
        daily_trend = df_filtered.groupby(df_filtered['Parsed_Date'].dt.date)['GRANDTOTAL'].sum().reset_index()
        fig_trend = px.line(daily_trend, x='Parsed_Date', y='GRANDTOTAL', markers=True, title="แนวโน้มยอดขายรายวัน")
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("ไม่มีข้อมูลเพียงพอสำหรับสร้างกราฟเทรนด์")

with tab_table:
    st.markdown("##### 📋 ตารางข้อมูลดิบ (ตามตัวกรอง)")
    st.dataframe(df_filtered, use_container_width=True)

# ===== 9. BEST SELLER TAB LOGIC =====
with tab_bestseller:
    st.markdown("##### 🍜 ข้อมูลสินค้าขายดี")
    df_product = load_product_data()
    
    if not df_product.empty:
        df_p_filtered = df_product.copy()
        
        # Apply the exact same filters as sales data
        if selected_years: df_p_filtered = df_p_filtered[df_p_filtered['Year_BE'].isin(selected_years)]
        else: df_p_filtered = df_p_filtered.iloc[0:0]
        
        if selected_branches: df_p_filtered = df_p_filtered[df_p_filtered['BRANCH_NAME'].isin(selected_branches)]
        else: df_p_filtered = df_p_filtered.iloc[0:0]
            
        if selected_months:
            month_map_p = {m: i+1 for i, m in enumerate(month_names)}
            target_month_nums_p = [month_map_p[m] for m in selected_months if m in month_map_p]
            df_p_filtered = df_p_filtered[df_p_filtered['Parsed_Date'].dt.month.isin(target_month_nums_p)]

        if quick_time != "ดูข้อมูลทั้งหมด" and not df_p_filtered.empty:
            if quick_time == "ใช้วันที่จาก Date Navigator":
                df_p_filtered = df_p_filtered[df_p_filtered['Parsed_Date'].dt.date == st.session_state.nav_date]
            elif quick_time == "วันนี้":
                df_p_filtered = df_p_filtered[df_p_filtered['Parsed_Date'].dt.date == today_date]
            elif quick_time == "เมื่อวาน":
                df_p_filtered = df_p_filtered[df_p_filtered['Parsed_Date'].dt.date == (today_date - timedelta(days=1))]
            elif quick_time == "7 วันล่าสุด":
                df_p_filtered = df_p_filtered[df_p_filtered['Parsed_Date'].dt.date >= (today_date - timedelta(days=7))]
            elif quick_time == "30 วันล่าสุด":
                df_p_filtered = df_p_filtered[df_p_filtered['Parsed_Date'].dt.date >= (today_date - timedelta(days=30))]
            elif quick_time == "เดือนนี้":
                df_p_filtered = df_p_filtered[(df_p_filtered['Parsed_Date'].dt.month == today_date.month) & (df_p_filtered['Parsed_Date'].dt.year == today_date.year)]
            elif quick_time == "กำหนดเอง (เลือกปฏิทิน)" and start_date and end_date:
                df_p_filtered = df_p_filtered[(df_p_filtered['Parsed_Date'].dt.date >= start_date) & (df_p_filtered['Parsed_Date'].dt.date <= end_date)]

        if not df_p_filtered.empty:
            # Group by Product Name
จากภาพ **image_fc7d2b.png** สาเหตุที่ข้อมูลใน Tab "สินค้าขายดี" ไม่แสดง เนื่องจากระบบมีข้อความแจ้งเตือนสีฟ้าปรากฏอยู่ด้านล่างว่า:

**"กำลังพัฒนาฟังก์ชันสินค้าขายดี กรุณารออัปเดตในเวอร์ชันถัดไป"**

* ฟังก์ชันการดูข้อมูลสินค้าขายดียังอยู่ในระหว่างการพัฒนาและยังไม่เปิดให้ใช้งานในระบบเวอร์ชันปัจจุบัน
* ข้อมูลในส่วนนี้จะแสดงผลได้ก็ต่อเมื่อมีการอัปเดตระบบปฏิบัติการหรือโปรแกรมในเวอร์ชันถัดไป
