import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import glob
from datetime import datetime, timedelta

# ==========================================
# 1. PAGE CONFIG & CUSTOM CSS
# ==========================================
# ==========================================
# 1. PAGE CONFIG & CUSTOM CSS
# ==========================================
st.set_page_config(
    page_title="PK NOODLE SHOP Dashboard",
    page_icon="logo.png" if os.path.exists("logo.png") else "🍜",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. HELPER FUNCTIONS & DATA LOADING
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
            df_temp['FILE_SOURCE'] = filename
            dfs.append(df_temp)
        except: pass
                
    if not dfs:
        return pd.DataFrame(columns=['Parsed_Date', 'Year_BE', 'NAME', 'GRANDTOTAL', 'ORDER_COUNT', 'FILE_SOURCE'])
        
    df_combined = pd.concat(dfs, ignore_index=True).drop_duplicates()
    
    date_col = next((c for c in ['DOC_DATE', 'DOCDATE', 'TRANDATE', 'CF_TRANDATE', 'PSH_DATE', 'วันที่', 'PDATA_CODE'] if c in df_combined.columns), None)
    if date_col: df_combined['Parsed_Date'] = df_combined[date_col].apply(parse_thai_date)
    else: df_combined['Parsed_Date'] = pd.NaT

    df_combined['Year_BE'] = df_combined['Parsed_Date'].dt.year + 543
    
    sales_col = next((c for c in ['GRAND_TOTAL', 'GRANDTOTAL', 'AMOUNT', 'PSD_N_AMT', 'ยอดขาย(บาท)', 'PDATA_NET_AMT', 'ยอดขายทั้งสิ้น'] if c in df_combined.columns), None)
    if sales_col:
        df_combined['GRANDTOTAL'] = pd.to_numeric(
            df_combined[sales_col].astype(str).str.replace(',', '').str.strip(), errors='coerce'
        ).fillna(0)
    else: df_combined['GRANDTOTAL'] = 0.0

    branch_col = next((c for c in ['BRANCH_NAME', 'BRANCHNAME', 'NAME', 'PSH_BR_NAME', 'สาขา'] if c in df_combined.columns), None)
    if branch_col:
        df_combined['NAME'] = df_combined[branch_col].astype(str).str.replace('\u200b', '').str.replace('\xa0', ' ').str.replace('ตลาด', '').str.strip()
    else: df_combined['NAME'] = 'สาขาหลัก'

    bill_col = next((c for c in ['ORDER_COUNT', 'BILL_COUNT', 'NO_OF_BILL', 'BILL_QTY', 'PDATA_QTY'] if c in df_combined.columns), None)
    if bill_col: df_combined['ORDER_COUNT'] = pd.to_numeric(df_combined[bill_col], errors='coerce').fillna(1)
    else: df_combined['ORDER_COUNT'] = 1

    return df_combined

def process_product_dataframe(df_raw):
    if df_raw.empty:
        return pd.DataFrame()
    
    df_p = df_raw.copy()
    df_p.columns = [str(c).upper().strip() for c in df_p.columns]
    
    date_col = next((c for c in ['DOC_DATE', 'DOCDATE', 'TRANDATE', 'CF_TRANDATE', 'PSH_DATE', 'วันที่', 'PDATA_CODE', 'PDATA_DATE', 'DATE'] if c in df_p.columns), None)
    if date_col: df_p['Parsed_Date'] = df_p[date_col].apply(parse_thai_date)
    else: df_p['Parsed_Date'] = pd.NaT

    df_p['Year_BE'] = df_p['Parsed_Date'].dt.year + 543
    
    branch_col = next((c for c in ['BRANCH_NAME', 'BRANCHNAME', 'NAME', 'PSH_BR_NAME', 'สาขา'] if c in df_p.columns), None)
    if branch_col:
        df_p['NAME'] = df_p[branch_col].astype(str).str.replace('\u200b', '').str.replace('\xa0', ' ').str.replace('ตลาด', '').str.strip()
        df_p['HAS_BRANCH_COL'] = True
    else:
        df_p['NAME'] = 'สาขาหลัก'
        df_p['HAS_BRANCH_COL'] = False

    sales_col = next((c for c in ['GRAND_TOTAL', 'GRANDTOTAL', 'AMOUNT', 'PSD_N_AMT', 'ยอดขาย(บาท)', 'PDATA_NET_AMT', 'NET_AMT', 'TOTAL', 'PRICE', 'SUM'] if c in df_p.columns), None)
    if sales_col:
        df_p['GRANDTOTAL'] = pd.to_numeric(
            df_p[sales_col].astype(str).str.replace(',', '').str.strip(), errors='coerce'
        ).fillna(0)
    else: df_p['GRANDTOTAL'] = 0.0

    qty_col = next((c for c in ['PDATA_QTY', 'QTY', 'AMOUNT_QTY', 'จำนวน', 'QUANTITY'] if c in df_p.columns), None)
    if qty_col:
        df_p['QTY'] = pd.to_numeric(
            df_p[qty_col].astype(str).str.replace(',', '').str.strip(), errors='coerce'
        ).fillna(1)
    else: df_p['QTY'] = 1

    return df_p

@st.cache_data(ttl=300)
def load_product_data_from_folder():
    dfs = []
    files_in_dir = os.listdir('.') if os.path.exists('.') else []
    
    product_files = [
        f for f in files_in_dir 
        if any(k in f.lower() for k in ['product', 'pdata', 'สินค้า', 'item']) 
        and f.lower().endswith(('.csv', '.xlsx', '.xls'))
    ]
    
    for filename in product_files:
        try:
            if filename.lower().endswith('.csv'):
                try: df_temp = pd.read_csv(filename, encoding='utf-8-sig', low_memory=False)
                except: df_temp = pd.read_csv(filename, encoding='tis-620', low_memory=False)
            else:
                df_temp = pd.read_excel(filename)
            dfs.append(df_temp)
        except: pass
                
    if dfs:
        combined = pd.concat(dfs, ignore_index=True).drop_duplicates()
        return process_product_dataframe(combined)
    return pd.DataFrame()

df_all = load_all_sales_data()

# ==========================================
# 3. SIDEBAR FILTERS
# ==========================================
st.sidebar.title("🔍 เมนูกรองข้อมูล")
st.sidebar.markdown("### 📅 1. เลือกเวลาที่ต้องการดู")

available_years = sorted([int(y) for y in df_all['Year_BE'].dropna().unique() if y > 2000], reverse=True)
if not available_years: available_years = [2569, 2568]
selected_years = st.sidebar.multiselect("เลือกปี พ.ศ.:", options=available_years, default=available_years)

quick_time = st.sidebar.selectbox(
    "เลือกช่วงเวลาแบบด่วน:",
    ["ดูข้อมูลทั้งหมด", "วันนี้", "เมื่อวาน", "7 วันล่าสุด", "30 วันล่าสุด", "เดือนนี้", "กำหนดเอง (เลือกปฏิทิน)"]
)

start_date, end_date = None, None
if quick_time == "กำหนดเอง (เลือกปฏิทิน)":
    min_d = df_all['Parsed_Date'].min() if not df_all['Parsed_Date'].isna().all() else datetime.today()
    max_d = df_all['Parsed_Date'].max() if not df_all['Parsed_Date'].isna().all() else datetime.today()
    date_range = st.sidebar.date_input("เลือกช่วงวันที่:", [min_d, max_d])
    if len(date_range) == 2:
        start_date, end_date = date_range[0], date_range[1]

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
# 4. FILTERING LOGIC FOR MAIN DASHBOARD
# ==========================================
df_filtered = df_all.copy()

if selected_years:
    df_filtered = df_filtered[df_filtered['Year_BE'].isin(selected_years)]
else:
    df_filtered = df_filtered.iloc[0:0]

if selected_branches:
    df_filtered = df_filtered[df_filtered['NAME'].isin(selected_branches)]
else:
    df_filtered = df_filtered.iloc[0:0]

if selected_months:
    month_map = {m: i+1 for i, m in enumerate(month_names)}
    target_month_nums = [month_map[m] for m in selected_months if m in month_map]
    df_filtered = df_filtered[df_filtered['Parsed_Date'].dt.month.isin(target_month_nums)]

if quick_time != "ดูข้อมูลทั้งหมด" and not df_filtered.empty:
    current_time_th = datetime.utcnow() + timedelta(hours=7)
    today_date = current_time_th.date()
    
    if quick_time == "วันนี้":
        df_filtered = df_filtered[df_filtered['Parsed_Date'].dt.date == today_date]
    elif quick_time == "เมื่อวาน":
        target_date = today_date - timedelta(days=1)
        df_filtered = df_filtered[df_filtered['Parsed_Date'].dt.date == target_date]
    elif quick_time == "7 วันล่าสุด":
        target_date = today_date - timedelta(days=7)
        df_filtered = df_filtered[df_filtered['Parsed_Date'].dt.date >= target_date]
    elif quick_time == "30 วันล่าสุด":
        target_date = today_date - timedelta(days=30)
        df_filtered = df_filtered[df_filtered['Parsed_Date'].dt.date >= target_date]
    elif quick_time == "เดือนนี้":
        df_filtered = df_filtered[
            (df_filtered['Parsed_Date'].dt.month == today_date.month) & 
            (df_filtered['Parsed_Date'].dt.year == today_date.year)
        ]
    elif quick_time == "กำหนดเอง (เลือกปฏิทิน)" and start_date and end_date:
        df_filtered = df_filtered[
            (df_filtered['Parsed_Date'].dt.date >= start_date) & 
            (df_filtered['Parsed_Date'].dt.date <= end_date)
        ]

# ==========================================
# 5. HEADER & TOP METRICS
# ==========================================
col_header, col_space = st.columns([2.5, 1.5])

with col_header:
    col_img, col_txt = st.columns([1, 4])
    with col_img:
        if os.path.exists("logo.png"):
            st.image("logo.png", width=100)
    with col_txt:
        st.markdown(
            """
            <div style="display: flex; align-items: center; height: 100%; padding-top: 12px;">
                <h2 style="color: #2b9e3e; font-weight: 800; font-size: 26px; margin: 0; line-height: 1.2;">
                    PK NOODLE SHOP COMPANY LIMITED
                </h2>
            </div>
            """, 
            unsafe_allow_html=True
        )

st.markdown('<div class="trick-banner">🧮 <b>ทริค:</b> เมนูกรองข้อมูลอยู่ด้านซ้ายมือ (หากซ่อนอยู่ให้กดปุ่ม > เพื่อเปิด)</div>', unsafe_allow_html=True)

# ------------------------------------------
# ส่วนเพิ่มใหม่: แสดงตัวชี้วัด (Metrics) 3 รายการ
# ------------------------------------------
# คำนวณยอดจากข้อมูลที่ผ่านการกรอง (df_filtered)
total_sales = df_filtered['GRANDTOTAL'].sum()
total_bills = len(df_filtered) # นับจากจำนวนแถว (บรรทัด)
avg_per_bill = total_sales / total_bills if total_bills > 0 else 0

# วาดการ์ด 3 คอลัมน์ โดยเรียกใช้ Class CSS ของคุณ
m1, m2, m3 = st.columns(3)

with m1:
    st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">ยอดขายรวมทั้งหมด (บาท)</div>
            <div class="metric-value">฿{total_sales:,.2f}</div>
        </div>
    ''', unsafe_allow_html=True)

with m2:
    st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">จำนวนบิล (นับจากจำนวนบรรทัด)</div>
            <div class="metric-value">{total_bills:,}</div>
        </div>
    ''', unsafe_allow_html=True)

with m3:
    st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">ยอดเฉลี่ยต่อบิล (บาท)</div>
            <div class="metric-value">฿{avg_per_bill:,.2f}</div>
        </div>
    ''', unsafe_allow_html=True)

# เว้นช่องว่างเล็กน้อยก่อนแสดงเนื้อหา Tabs (Section 7)
st.markdown("<br>", unsafe_allow_html=True)
# ==========================================
# 6. CHART DRAWING HELPER FUNCTIONS
# ==========================================
# กำหนดสีประจำสาขา
branch_color_map = {
    'ศรีเมือง': '#EF4444',  # สีแดง
    'ทุ่งปอ': '#3B82F6',   # สีฟ้า
    'เจ้าพรหม': '#A855F7',  # สีม่วง
    'บ้านไร่': '#10B981',   # สีเขียว
    'เทศบาล': '#EAB308',  # สีเหลือง
    'บ้านโป่ง': '#EC4899'   # สีชมพู
}

def render_branch_visualizations(df_source):
    if df_source.empty:
        st.info("ไม่พบข้อมูลยอดขาย (ภายใต้เงื่อนไขการกรองปัจจุบัน)")
        return

    branch_summary = df_source.groupby('NAME')['GRANDTOTAL'].sum().reset_index()
    branch_summary = branch_summary.sort_values(by='GRANDTOTAL', ascending=False)
    
    c_bar, c_donut = st.columns([1.2, 1])
    
    with c_bar:
        st.markdown("##### ยอดขาย (กราฟแท่ง)")
        fig_bar = px.bar(
            branch_summary, 
            x='NAME', 
            y='GRANDTOTAL', 
            color='NAME', 
            text='GRANDTOTAL', 
            color_discrete_map=branch_color_map
        )
        fig_bar.update_traces(texttemplate='%{text:,.2f}', textposition='outside', cliponaxis=False)
        fig_bar.update_layout(
            xaxis_title="", 
            yaxis_title="ยอดขาย (บาท)", 
            showlegend=False, 
            height=400, 
            margin=dict(l=20, r=20, t=30, b=20), 
            plot_bgcolor='rgba(0,0,0,0)', 
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with c_donut:
        st.markdown("##### สัดส่วนยอดขาย (กราฟโดนัท)")
        fig_donut = px.pie(
            branch_summary, 
            values='GRANDTOTAL', 
            names='NAME', 
            color='NAME',
            hole=0.5, 
            color_discrete_map=branch_color_map
        )
        fig_donut.update_traces(textinfo='percent+label', insidetextorientation='radial')
        fig_donut.update_layout(
            showlegend=True, 
            height=400, 
            margin=dict(l=20, r=20, t=30, b=20), 
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_donut, use_container_width=True)
# ==========================================
# 7. TABS NAVIGATION
# ==========================================
tab_branch, tab_trend, tab_table, tab_bestseller = st.tabs([
    "🏢 ยอดรวมสาขา", "📈 เทรนด์รายวัน", "📋 ตารางตัวเลข", "🍜 สินค้าขายดี"
])

with tab_branch:
    if 'FILE_SOURCE' in df_filtered.columns:
        df_sales_data = df_filtered[
            df_filtered['FILE_SOURCE'].astype(str).str.lower().str.contains('sales data|sales_data', na=False)
        ]
    else:
        df_sales_data = df_filtered
        
    render_branch_visualizations(df_sales_data)

with tab_trend:
    st.markdown("##### 📈 เทรนด์ยอดขายรายวัน")
    if not df_filtered.empty and not df_filtered['Parsed_Date'].isna().all():
        daily_trend = df_filtered.groupby(['Parsed_Date', 'NAME'])['GRANDTOTAL'].sum().reset_index()
        fig_line = px.line(daily_trend, x='Parsed_Date', y='GRANDTOTAL', color='NAME', markers=True, title="แนวโน้มยอดขายรายวันตามสาขา")
        fig_line.update_layout(xaxis_title="วันที่", yaxis_title="ยอดขาย (บาท)", height=450, hovermode="x unified")
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("ไม่มีข้อมูลเพียงพอสำหรับแสดงกราฟเทรนด์รายวัน (โปรดตรวจสอบช่วงเวลาที่เลือก)")

with tab_table:
    st.markdown("##### 📋 ตารางสรุปยอดขายตามสาขา")
    if not df_filtered.empty:
        summary_table = df_filtered.groupby('NAME').agg(
            total_sales=('GRANDTOTAL', 'sum'),
            bill_count=('ORDER_COUNT', 'sum')
        ).reset_index()
        summary_table.columns = ['NAME', 'ยอดขายรวม', 'จำนวนบิล']
        summary_table['เฉลี่ยต่อบิล'] = summary_table['ยอดขายรวม'] / summary_table['จำนวนบิล']
        summary_table = summary_table.sort_values(by='ยอดขายรวม', ascending=False)
        st.dataframe(summary_table.style.format({'ยอดขายรวม': '฿{:,.2f}', 'จำนวนบิล': '{:,.0f}', 'เฉลี่ยต่อบิล': '฿{:,.2f}'}), use_container_width=True)
    else:
        st.info("ไม่พบข้อมูลที่จะแสดงในตาราง")

with tab_bestseller:
    st.markdown("##### 🍜 รายงานสินค้าขายดี")
    
    # 1. โหลดข้อมูลจากไฟล์ Product Data
    df_product = load_product_data_from_folder()
    
    # 2. ตัวเลือกการอัปโหลดไฟล์ตรงจากหน้าเว็บ
    if df_product.empty:
        st.info("💡 หากไม่พบไฟล์ในโฟลเดอร์ สามารถเลือกอัปโหลดไฟล์ Product Data เพื่อประมวลผลทันทีได้ครับ")
        uploaded_pfile = st.file_uploader(
            "📂 เลือกอัปโหลดไฟล์ Product Data (.csv หรือ .xlsx):", 
            type=['csv', 'xlsx', 'xls'],
            key="p_file_uploader"
        )
        if uploaded_pfile is not None:
            try:
                if uploaded_pfile.name.lower().endswith('.csv'):
                    try: df_raw = pd.read_csv(uploaded_pfile, encoding='utf-8-sig', low_memory=False)
                    except: df_raw = pd.read_csv(uploaded_pfile, encoding='tis-620', low_memory=False)
                else:
                    df_raw = pd.read_excel(uploaded_pfile)
                df_product = process_product_dataframe(df_raw)
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดในการอ่านไฟล์: {e}")

    # 3. ประมวลผลเมื่อมีข้อมูล
    if not df_product.empty:
        df_p_filtered = df_product.copy()
        
        # Smart Branch Filtering
        if selected_branches and df_p_filtered.get('HAS_BRANCH_COL', [False])[0]:
            matched_p = df_p_filtered[df_p_filtered['NAME'].isin(selected_branches)]
            if not matched_p.empty:
                df_p_filtered = matched_p
        
        # Smart Year Filtering
        if selected_years and 'Year_BE' in df_p_filtered.columns and not df_p_filtered['Year_BE'].isna().all():
            matched_y = df_p_filtered[df_p_filtered['Year_BE'].isin(selected_years)]
            if not matched_y.empty:
                df_p_filtered = matched_y

        # Smart Quick Time Filtering
        if quick_time != "ดูข้อมูลทั้งหมด" and 'Parsed_Date' in df_p_filtered.columns and not df_p_filtered['Parsed_Date'].isna().all():
            current_time_th = datetime.utcnow() + timedelta(hours=7)
            today_date = current_time_th.date()
            matched_q = pd.DataFrame()
            if quick_time == "วันนี้":
                matched_q = df_p_filtered[df_p_filtered['Parsed_Date'].dt.date == today_date]
            elif quick_time == "เมื่อวาน":
                matched_q = df_p_filtered[df_p_filtered['Parsed_Date'].dt.date == (today_date - timedelta(days=1))]
            elif quick_time == "7 วันล่าสุด":
                matched_q = df_p_filtered[df_p_filtered['Parsed_Date'].dt.date >= (today_date - timedelta(days=7))]
            elif quick_time == "30 วันล่าสุด":
                matched_q = df_p_filtered[df_p_filtered['Parsed_Date'].dt.date >= (today_date - timedelta(days=30))]
            elif quick_time == "เดือนนี้":
                matched_q = df_p_filtered[(df_p_filtered['Parsed_Date'].dt.month == today_date.month) & (df_p_filtered['Parsed_Date'].dt.year == today_date.year)]
            elif quick_time == "กำหนดเอง (เลือกปฏิทิน)" and start_date and end_date:
                matched_q = df_p_filtered[(df_p_filtered['Parsed_Date'].dt.date >= start_date) & (df_p_filtered['Parsed_Date'].dt.date <= end_date)]
            
            if not matched_q.empty:
                df_p_filtered = matched_q

        # Auto-detect Product Column Name
        possible_p_cols = ['PDATA_NAME', 'PRODUCT_NAME', 'P_NAME', 'NAME_1', 'ชื่อสินค้า', 'PRODUCT', 'ITEM_NAME', 'DESCR', 'ITEMNAME', 'PROD_NAME', 'DESCRIPTION', 'TITLE', 'GOODS_NAME', 'สินค้า', 'รายการ', 'ชื่อรายการ', 'NAME_TH', 'NAME']
        p_col = next((c for c in possible_p_cols if c in df_p_filtered.columns and c != 'NAME' or (c == 'NAME' and not df_p_filtered.get('HAS_BRANCH_COL', [False])[0])), None)

        if not p_col:
            st.warning("⚠️ ไม่พบชื่อคอลัมน์สินค้าอัตโนมัติ โปรดเลือกคอลัมน์ที่เป็น **ชื่อสินค้า** จากรายการด้านล่าง:")
            p_col = st.selectbox("เลือกคอลัมน์ชื่อสินค้า:", options=[c for c in df_p_filtered.columns if c not in ['GRANDTOTAL', 'QTY', 'Year_BE', 'Parsed_Date', 'HAS_BRANCH_COL']])

        if p_col and not df_p_filtered.empty:
            top_products = df_p_filtered.groupby(p_col).agg(
                total_sales=('GRANDTOTAL', 'sum'),
                total_qty=('QTY', 'sum')
            ).reset_index()
            top_products.columns = ['ชื่อสินค้า', 'ยอดขายรวม', 'จำนวนที่ขาย']
            top_products = top_products[top_products['ยอดขายรวม'] > 0]
            
            # เรียงลำดับตามจำนวนที่ขายจากมากไปน้อย
            top_products = top_products.sort_values(by='จำนวนที่ขาย', ascending=False).head(20).reset_index(drop=True)
            
            # เพิ่มคอลัมน์ลำดับ 1-20 ด้านหน้าสุด
            top_products.insert(0, 'ลำดับ', range(1, len(top_products) + 1))
            
            if not top_products.empty:
                col_b1, col_b2 = st.columns([1.3, 1])
                with col_b1:
                    st.markdown("###### Top 10 สินค้าขายดีที่สุด (ยอดขาย)")
                    
                    df_top10_chart = top_products.sort_values(by='ยอดขายรวม', ascending=True).tail(10)
                    max_sales = df_top10_chart['ยอดขายรวม'].max()
                    
                    fig_pbar = px.bar(
                        df_top10_chart,
                        y='ชื่อสินค้า',
                        x='ยอดขายรวม',
                        orientation='h',
                        text='ยอดขายรวม',
                        color='ชื่อสินค้า',
                        color_discrete_sequence=px.colors.qualitative.Bold
                    )
                    
                    fig_pbar.update_traces(
                        texttemplate='฿%{text:,.2f}', 
                        textposition='outside', 
                        cliponaxis=False
                    )
                    
                    fig_pbar.update_layout(
                        xaxis_title="ยอดขาย (บาท)", 
                        yaxis_title="", 
                        height=430, 
                        margin=dict(l=10, r=90, t=20, b=20), 
                        showlegend=False,
                        plot_bgcolor='rgba(0,0,0,0)', 
                        paper_bgcolor='rgba(0,0,0,0)'
                    )
                    
                    fig_pbar.update_xaxes(range=[0, max_sales * 1.22])
                    st.plotly_chart(fig_pbar, use_container_width=True)

                with col_b2:
                    st.markdown("###### ตารางรายละเอียดสินค้าขายดี 20 อันดับแรก")
                    
                    st.dataframe(
                        top_products.style.format({'ยอดขายรวม': '฿{:,.2f}', 'จำนวนที่ขาย': '{:,.0f}'}),
                        use_container_width=True, 
                        height=430,
                        hide_index=True
                    )
            else:
                st.info("ไม่พบรายการสินค้าที่มียอดขายมากกว่า 0 บาท")
        else:
            st.info("ไม่พบข้อมูลสินค้าในการประมวลผล")
