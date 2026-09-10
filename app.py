import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import base64
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

current_time_th = datetime.utcnow() + timedelta(hours=7)
if 'nav_date' not in st.session_state:
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
        font-weight: 800 !important; font-size: 20px !important;
        padding-top: 6px !important; padding-bottom: 6px !important;
        border-radius: 8px !important; border: 2px solid #38bdf8 !important;
        background-color: #f0f9ff !important;
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

def process_product_dataframe(df_p):
    df_p.columns = [str(c).upper().strip() for c in df_p.columns]
    df_p = df_p.loc[:, ~df_p.columns.duplicated()]
    
    date_col = next((c for c in ['CF_TRANDATE', 'DOC_DATE', 'DOCDATE', 'TRANDATE', 'PSH_DATE', 'PDATA_DATE', 'DATE', 'DATETIME', 'TRAN_DATE', 'วันที่', 'TIME'] if c in df_p.columns), None)
    if date_col: df_p['Parsed_Date'] = df_p[date_col].apply(parse_thai_date)
    else: df_p['Parsed_Date'] = pd.NaT
    df_p['Year_BE'] = np.where(df_p['Parsed_Date'].notna(), df_p['Parsed_Date'].dt.year + 543, np.nan)
    
    branch_col = next((c for c in ['BRANCH_NAME', 'BRANCHNAME', 'BRANCH', 'NAME', 'PSH_BR_NAME', 'สาขา', 'LOCATION'] if c in df_p.columns), None)
    if branch_col: df_p['BRANCH_NAME'] = df_p[branch_col].astype(str).str.replace('\u200b', '').str.replace('\xa0', ' ').str.replace('ตลาด', '').str.strip()
    else: df_p['BRANCH_NAME'] = 'สาขาหลัก'
    
    qty_col = next((c for c in ['QUANTITY', 'PDATA_QTY', 'QTY', 'AMOUNT_QTY', 'QTY_SOLD', 'TOTAL_QTY', 'SOLD_QTY', 'PD_QTY', 'จำนวน', 'จำนวนชิ้น', 'จำนวนขาย', 'ปริมาณ', 'COUNT'] if c in df_p.columns), None)
    if qty_col: df_p['QTY'] = pd.to_numeric(df_p[qty_col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(1)
    else: df_p['QTY'] = 1.0
    
    sales_col = next((c for c in ['AMOUNT', 'NET_AMT', 'PDATA_NET_AMT', 'TOTAL', 'PRICE', 'TOTAL_PRICE', 'GRAND_TOTAL', 'GRANDTOTAL', 'PSD_N_AMT', 'ยอดขาย(บาท)', 'ยอดขาย', 'ยอดรวม', 'จำนวนเงิน'] if c in df_p.columns), None)
    if sales_col: df_p['GRANDTOTAL'] = pd.to_numeric(df_p[sales_col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0.0)
    else: df_p['GRANDTOTAL'] = 0.0
    
    prod_col = next((c for c in ['ITEMNAME', 'PDATA_NAME', 'PRODUCT_NAME', 'NAME1', 'ITEM_NAME', 'GOODS_NAME', 'PD_NAME', 'DESCR', 'DESCRIPTION', 'ชื่อสินค้า', 'รายการ', 'สินค้า', 'NAME', 'TITLE', 'MENU'] if c in df_p.columns), None)
    if prod_col: df_p['PRODUCT_NAME'] = df_p[prod_col].astype(str).str.strip()
    else:
        str_cols = [c for c in df_p.columns if c not in ['Parsed_Date', 'Year_BE', 'BRANCH_NAME', 'QTY', 'GRANDTOTAL', date_col, branch_col, qty_col, sales_col]]
        if str_cols: df_p['PRODUCT_NAME'] = df_p[str_cols[0]].astype(str).str.strip()
        else: df_p['PRODUCT_NAME'] = 'ไม่ระบุชื่อสินค้า'
        
    unit_col = next((c for c in ['CF_UNITNAME', 'UNIT_NAME', 'UTQ_NAME', 'UNIT', 'UM', 'หน่วย', 'หน่วยนับ'] if c in df_p.columns), None)
    if unit_col: df_p['UNIT'] = df_p[unit_col].astype(str).str.strip()
    else: df_p['UNIT'] = '-'
    
    bill_col = next((c for c in ['TRANNO', 'DOC_NO', 'DOCNO', 'BILL_NO', 'BILLNO', 'PSH_DOC_NO', 'PDATA_DOC_NO', 'เลขที่เอกสาร', 'เลขที่บิล', 'REF_NO', 'DI_REF'] if c in df_p.columns), None)
    if bill_col: df_p['BILL_NO'] = df_p[bill_col].astype(str).str.strip()
    else: df_p['BILL_NO'] = df_p.index.astype(str)

    return df_p

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
                for enc in ['utf-8-sig', 'cp874', 'tis-620', 'utf-8']:
                    try:
                        df_temp = pd.read_csv(filename, encoding=enc, low_memory=False)
                        break
                    except: pass
            else: df_temp = pd.read_excel(filename)
            df_temp.columns = [str(c).upper().strip() for c in df_temp.columns]
            df_temp = df_temp.loc[:, ~df_temp.columns.duplicated()]
            dfs.append(df_temp)
        except: pass
    if not dfs: return pd.DataFrame(columns=['Parsed_Date', 'Year_BE', 'NAME', 'GRANDTOTAL', 'ORDER_COUNT'])
    df_combined = pd.concat(dfs, ignore_index=True).drop_duplicates()
    df_combined = df_combined.loc[:, ~df_combined.columns.duplicated()]
    
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
    files_in_dir = os.listdir('.') if os.path.exists('.') else []
    product_files = [
        f for f in files_in_dir 
        if (any(k in f.lower() for k in ['product', 'pdata', 'สินค้า', 'item', 'detail', 'menu']) or f.lower() == 'product data.csv')
        and f.lower().endswith(('.csv', '.xlsx', '.xls'))
    ]
    for filename in product_files:
        df_temp = None
        if filename.lower().endswith('.csv'):
            for enc in ['utf-8-sig', 'tis-620', 'cp874', 'utf-8']:
                try:
                    df_temp = pd.read_csv(filename, encoding=enc, low_memory=False)
                    break
                except: pass
        else:
            try: df_temp = pd.read_excel(filename)
            except: pass
            
        if df_temp is not None and not df_temp.empty:
            dfs.append(process_product_dataframe(df_temp))
        
    if not dfs: return pd.DataFrame()
    df_p = pd.concat(dfs, ignore_index=True)
    return df_p.loc[:, ~df_p.columns.duplicated()]

df_all = load_all_sales_data()

# ==========================================
# 4. SIDEBAR FILTERS
# ==========================================
st.sidebar.title("🔍 เมนูกรองข้อมูล")
st.sidebar.markdown("##### 🗓️ 1. เลือกเวลาที่ต้องการดู")

quick_time = st.sidebar.selectbox("เลือกช่วงเวลาแบบด่วน:", ["ใช้วันที่จาก Date Navigator (ด้านบน)", "ทั้งหมดในระบบ", "วันนี้", "เมื่อวาน", "7 วันล่าสุด", "30 วันล่าสุด", "เดือนนี้", "กำหนดเอง (เลือกปฏิทิน)"])
available_years = sorted([int(y) for y in df_all['Year_BE'].dropna().unique() if y > 2000], reverse=True)
if not available_years: available_years = [2569, 2568]
selected_years = st.sidebar.multiselect("เลือกปี พ.ศ.:", options=available_years, default=available_years)

start_date, end_date = None, None
if quick_time == "กำหนดเอง (เลือกปฏิทิน)":
    min_d = df_all['Parsed_Date'].min() if not df_all['Parsed_Date'].isna().all() else datetime.today()
    max_d = df_all['Parsed_Date'].max() if not df_all['Parsed_Date'].isna().all() else datetime.today()
    date_range = st.sidebar.date_input("เลือกช่วงวันที่:", [min_d, max_d])
    if len(date_range) == 2: start_date, end_date = date_range[0], date_range[1]

month_names = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
with st.sidebar.expander("➕ กรองตามเดือน", expanded=False):
    selected_months = st.sidebar.multiselect("เลือกเดือนที่ต้องการดู:", month_names, default=[])

st.sidebar.markdown("---")
all_branches = sorted(df_all['NAME'].dropna().unique().tolist())
if not all_branches: all_branches = ["ศรีเมือง", "ทุ่งปอ", "เจ้าพรหม", "บ้านไร่", "เทศบาล", "บ้านโป่ง"]
selected_branches = st.sidebar.multiselect("เลือกสาขา:", options=all_branches, default=all_branches)
st.sidebar.markdown("---")
st.sidebar.caption("Powered by peter pak: v.10.2.6")

# ==========================================
# 5. HEADER & DATE NAVIGATOR
# ==========================================
logo_img_tag = ""
if os.path.exists("logo.png"):
    with open("logo.png", "rb") as img_f:
        encoded_img = base64.b64encode(img_f.read()).decode()
    logo_img_tag = f'<img src="data:image/png;base64,{encoded_img}" style="height: 55px; margin-right: 15px; vertical-align: middle;">'
else:
    logo_img_tag = '<span style="font-size: 38px; margin-right: 12px; vertical-align: middle;">🍜</span>'

header_html = f"""
<div style="display: flex; align-items: center; flex-wrap: wrap; margin-bottom: 20px; margin-top: -10px;">
    {logo_img_tag}
    <div style="font-size: 22px; font-weight: 800; font-family: sans-serif;">
        <span style="color: #16a34a;">PK NOODLE SHOP COMPANY LIMITED </span>
        <span style="color: #dc2626;">(Senior Soft- &gt;&gt;เริ่ม 5 สิงหาคม 2569)</span>
    </div>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

st.markdown("<div style='background-color: #ffffff; padding: 12px 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 20px;'>", unsafe_allow_html=True)
nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
with nav_col1: st.button("❮ วันก่อนหน้า", on_click=go_prev, use_container_width=True, key="btn_prev_top")
with nav_col2: st.date_input("เลือกวันที่", label_visibility="collapsed", key="nav_date")
with nav_col3: st.button("วันถัดไป ❯", on_click=go_next, use_container_width=True, key="btn_next_top")
st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 6. DATA FILTERING
# ==========================================
df_filtered = df_all.copy()
if selected_years: df_filtered = df_filtered[df_filtered['Year_BE'].isin(selected_years)]
else: df_filtered = df_filtered.iloc[0:0]

if selected_branches: df_filtered = df_filtered[df_filtered['NAME'].isin(selected_branches)]
else: df_filtered = df_filtered.iloc[0:0]

if selected_months:
    month_map = {m: i+1 for i, m in enumerate(month_names)}
    target_month_nums = [month_map[m] for m in selected_months if m in month_map]
    df_filtered = df_filtered[df_filtered['Parsed_Date'].dt.month.isin(target_month_nums)]

today_date = current_time_th.date()
df_prev = pd.DataFrame()

if quick_time != "ทั้งหมดในระบบ" and not df_filtered.empty:
    if quick_time == "ใช้วันที่จาก Date Navigator (ด้านบน)":
        df_filtered = df_filtered[df_filtered['Parsed_Date'].dt.date == st.session_state.nav_date]
        df_prev = df_all[(df_all['Parsed_Date'].dt.date == (st.session_state.nav_date - timedelta(days=1))) & (df_all['NAME'].isin(selected_branches))]
    elif quick_time == "วันนี้":
        df_filtered = df_filtered[df_filtered['Parsed_Date'].dt.date == today_date]
        df_prev = df_all[(df_all['Parsed_Date'].dt.date == (today_date - timedelta(days=1))) & (df_all['NAME'].isin(selected_branches))]
    elif quick_time == "เมื่อวาน": df_filtered = df_filtered[df_filtered['Parsed_Date'].dt.date == (today_date - timedelta(days=1))]
    elif quick_time == "7 วันล่าสุด": df_filtered = df_filtered[df_filtered['Parsed_Date'].dt.date >= (today_date - timedelta(days=7))]
    elif quick_time == "30 วันล่าสุด": df_filtered = df_filtered[df_filtered['Parsed_Date'].dt.date >= (today_date - timedelta(days=30))]
    elif quick_time == "เดือนนี้": df_filtered = df_filtered[(df_filtered['Parsed_Date'].dt.month == today_date.month) & (df_filtered['Parsed_Date'].dt.year == today_date.year)]
    elif quick_time == "กำหนดเอง (เลือกปฏิทิน)" and start_date and end_date:
        df_filtered = df_filtered[(df_filtered['Parsed_Date'].dt.date >= start_date) & (df_filtered['Parsed_Date'].dt.date <= end_date)]

# ==========================================
# 7. SUMMARY METRICS
# ==========================================
total_sales = df_filtered['GRANDTOTAL'].sum() if not df_filtered.empty else 0
total_bills = df_filtered['ORDER_COUNT'].sum() if not df_filtered.empty else 0
avg_bill = total_sales / total_bills if total_bills > 0 else 0

delta_sales_html = ""
if quick_time in ["ใช้วันที่จาก Date Navigator (ด้านบน)", "วันนี้"] and not df_prev.empty:
    prev_sales = df_prev['GRANDTOTAL'].sum()
    if prev_sales > 0:
        diff_pct = ((total_sales - prev_sales) / prev_sales) * 100
        color = "#10b981" if diff_pct >= 0 else "#ef4444"
        arrow = "▲" if diff_pct >= 0 else "▼"
        delta_sales_html = f"<div style='color: {color}; font-size: 14px; font-weight: 600; margin-top: 4px;'>{arrow} {diff_pct:.1f}% เทียบกับวันก่อนหน้า</div>"

col1, col2, col3 = st.columns(3)
with col1: st.markdown(f"<div class='metric-card'><div class='metric-label'>ยอดขายรวมทั้งหมด (บาท)</div><div class='metric-value'>฿{total_sales:,.2f}</div>{delta_sales_html}</div>", unsafe_allow_html=True)
with col2: st.markdown(f"<div class='metric-card'><div class='metric-label'>จำนวนบิล (นับจากจำนวนบรรทัด)</div><div class='metric-value'>{total_bills:,.0f}</div></div>", unsafe_allow_html=True)
with col3: st.markdown(f"<div class='metric-card'><div class='metric-label'>ยอดเฉลี่ยต่อบิล (บาท)</div><div class='metric-value'>฿{avg_bill:,.2f}</div></div>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 8. TABS & VISUALIZATION
# ==========================================
tab_branch, tab_trend, tab_table, tab_bestseller = st.tabs(["🏢 ยอดรวมสาขา", "📈 เทรนด์รายวัน", "📋 ตารางตัวเลข", "🍜 สินค้าขายดี"])

with tab_branch:
    if not df_filtered.empty:
        branch_sales = df_filtered.groupby('NAME', as_index=False)[['GRANDTOTAL', 'ORDER_COUNT']].sum()
        branch_sales.rename(columns={'GRANDTOTAL': 'Total_Sales', 'ORDER_COUNT': 'Total_Bills'}, inplace=True)
        branch_sales = branch_sales.sort_values(by='Total_Sales', ascending=False)
        total_sum = branch_sales['Total_Sales'].sum()
        branch_sales['Pct_Sales'] = (branch_sales['Total_Sales'] / total_sum) * 100 if total_sum > 0 else 0.0
        branch_sales['Label_Text'] = branch_sales.apply(lambda r: f"฿{r['Total_Sales']:,.2f}<br>({r['Pct_Sales']:.1f}%)", axis=1)
        branch_colors = {'ศรีเมือง': '#FF3B30', 'ทุ่งปอ': '#3478F6', 'เจ้าพรหม': '#A259FF', 'บ้านไร่': '#00C853', 'เทศบาล': '#FFC107', 'บ้านโป่ง': '#FF2D55'}
        c1, c2 = st.columns([6, 4])
        with c1:
            fig_bar = px.bar(branch_sales, x='NAME', y='Total_Sales', color='NAME', color_discrete_map=branch_colors, text='Label_Text')
            fig_bar.update_traces(textposition='outside', textfont_size=11)
            fig_bar.update_layout(xaxis_title="", yaxis_title="ยอดขาย (บาท)", showlegend=False, height=480, plot_bgcolor='white', paper_bgcolor='white', margin=dict(l=20, r=20, t=40, b=20), yaxis=dict(showgrid=True, gridcolor='#f0f0f0'))
            st.plotly_chart(fig_bar, use_container_width=True)
        with c2:
            fig_pie = px.pie(branch_sales, values='Total_Sales', names='NAME', hole=0.55, color='NAME', color_discrete_map=branch_colors)
            fig_pie.update_traces(textinfo='label+percent', textposition='inside', insidetextorientation='horizontal')
            fig_pie.update_layout(height=480, showlegend=True, margin=dict(l=10, r=10, t=40, b=10), legend=dict(orientation="v", yanchor="top", y=0.9, xanchor="left", x=0.95))
            st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown("##### 📊 สรุปสัดส่วนยอดขายรายสาขา")
        table_df = branch_sales.copy()
        table_df['Avg_Bill'] = np.where(table_df['Total_Bills'] > 0, table_df['Total_Sales'] / table_df['Total_Bills'], 0)
        table_df.rename(columns={'NAME': 'สาขา', 'Total_Sales': 'ยอดขาย (บาท)', 'Pct_Sales': '% ยอดขาย', 'Total_Bills': 'จำนวนบิล', 'Avg_Bill': 'เฉลี่ย/บิล (บาท)'}, inplace=True)
        st.dataframe(table_df[['สาขา', 'ยอดขาย (บาท)', '% ยอดขาย', 'จำนวนบิล', 'เฉลี่ย/บิล (บาท)']].style.format({'ยอดขาย (บาท)': '฿{:,.2f}', '% ยอดขาย': '{:.2f}%', 'จำนวนบิล': '{:,.0f}', 'เฉลี่ย/บิล (บาท)': '฿{:,.2f}'}), use_container_width=True)
    else: st.info("ไม่พบข้อมูลสำหรับช่วงเวลาหรือสาขาที่เลือก")

with tab_trend:
    if not df_filtered.empty and not df_filtered['Parsed_Date'].isna().all():
        daily_sales = df_filtered.groupby(df_filtered['Parsed_Date'].dt.date, as_index=False)['GRANDTOTAL'].sum()
        daily_sales.columns = ['Date', 'Total_Sales']
        if len(daily_sales) > 1:
            fig_line = px.line(daily_sales.sort_values('Date'), x='Date', y='Total_Sales', markers=True)
            fig_line.update_traces(line_color='#0ea5e9', marker=dict(size=8, color='#0284c7'))
            fig_line.update_layout(xaxis_title="วันที่", yaxis_title="ยอดขาย (บาท)", height=400, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_line, use_container_width=True)
        else: st.info("มีข้อมูลเพียง 1 วัน ไม่สามารถสร้างกราฟแนวโน้มได้")
    else: st.info("ไม่มีข้อมูลวันที่ที่สามารถสร้างกราฟได้")

# --- การแก้ไข: ลำดับตารางตัวเลข ---
with tab_table:
    if not df_filtered.empty:
        st.markdown("##### 📋 สรุปข้อมูลยอดขาย (รวมยอดตามวันและสาขา)")
        df_tab3 = df_filtered.loc[:, ~df_filtered.columns.duplicated()].copy()
        summary_table = df_tab3.groupby(['Parsed_Date', 'NAME'], as_index=False)[['GRANDTOTAL', 'ORDER_COUNT']].sum()
        summary_table.rename(columns={'GRANDTOTAL': 'ยอดขายรวม', 'ORDER_COUNT': 'จำนวนบิล'}, inplace=True)
        summary_table['ยอดเฉลี่ย/บิล'] = np.where(summary_table['จำนวนบิล'] > 0, summary_table['ยอดขายรวม'] / summary_table['จำนวนบิล'], 0)
        summary_table = summary_table.sort_values(by=['Parsed_Date', 'ยอดขายรวม'], ascending=[False, False])
        
        # รีเซ็ตตัวเลขให้เรียง 1, 2, 3...
        summary_table = summary_table.reset_index(drop=True)
        summary_table.index = summary_table.index + 1
        summary_table = summary_table.reset_index().rename(columns={'index': 'ลำดับ'})
        
        if not summary_table['Parsed_Date'].isna().all(): 
            summary_table['Parsed_Date'] = summary_table['Parsed_Date'].dt.strftime('%d/%m/%Y')
        summary_table.rename(columns={'Parsed_Date': 'วันที่', 'NAME': 'สาขา', 'ยอดขายรวม': 'ยอดขายรวม (บาท)', 'จำนวนบิล': 'จำนวนบิล (ใบ)', 'ยอดเฉลี่ย/บิล': 'เฉลี่ย/บิล (บาท)'}, inplace=True)
        
        # ซ่อน index สีเทา
        st.dataframe(summary_table.style.format({
            'ยอดขายรวม (บาท)': '฿{:,.2f}', 
            'จำนวนบิล (ใบ)': '{:,.0f}', 
            'เฉลี่ย/บิล (บาท)': '฿{:,.2f}'
        }), use_container_width=True, hide_index=True)
    else: 
        st.info("ไม่พบข้อมูล")

with tab_bestseller:
    st.markdown("#### 🍜 รายงานสินค้าขายดี")
    df_product = load_product_data()
    if not df_product.empty:
        df_p_filtered = df_product.copy()
        has_dates = 'Parsed_Date' in df_p_filtered.columns and not df_p_filtered['Parsed_Date'].isna().all()
        if has_dates:
            if selected_years:
                df_p_filtered = df_p_filtered[df_p_filtered['Year_BE'].isin(selected_years)]
            if selected_months:
                month_map_p = {m: i+1 for i, m in enumerate(month_names)}
                target_month_nums_p = [month_map_p[m] for m in selected_months if m in month_map_p]
                df_p_filtered = df_p_filtered[df_p_filtered['Parsed_Date'].dt.month.isin(target_month_nums_p)]
            if quick_time != "ทั้งหมดในระบบ" and not df_p_filtered.empty:
                if quick_time == "ใช้วันที่จาก Date Navigator (ด้านบน)":
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

        has_branches = 'BRANCH_NAME' in df_p_filtered.columns and df_p_filtered['BRANCH_NAME'].nunique() > 1
        if selected_branches and has_branches:
            df_p_filtered = df_p_filtered[df_p_filtered['BRANCH_NAME'].isin(selected_branches)]

        if not df_p_filtered.empty:
            df_p_filtered = df_p_filtered[~df_p_filtered['PRODUCT_NAME'].astype(str).str.strip().str.lower().isin(['', 'nan', 'none', '0', 'nan.0', 'ไม่ระบุชื่อสินค้า'])]
            summary_df = df_p_filtered.groupby('PRODUCT_NAME', as_index=False).agg({
                'UNIT': lambda x: next((v for v in x if str(v).strip() not in ['', '-', 'nan', 'None']), '-'),
                'GRANDTOTAL': 'sum',
                'QTY': 'sum',
                'BILL_NO': 'nunique'
            })
            summary_df.rename(columns={'PRODUCT_NAME': 'ชื่อสินค้า', 'UNIT': 'หน่วย', 'GRANDTOTAL': 'ยอดขายรวม', 'QTY': 'จำนวนที่ขาย', 'BILL_NO': 'บิลที่มีสินค้านี้'}, inplace=True)
            summary_df = summary_df.sort_values(by='จำนวนที่ขาย', ascending=False).reset_index(drop=True)
            summary_df.index = summary_df.index + 1
            summary_df = summary_df.reset_index().rename(columns={'index': 'ลำดับ'})
            
            c1, c2 = st.columns([4.5, 5.5])
            with c1:
                st.markdown("##### Top 10 สินค้าขายดีที่สุด (ตามจำนวน)")
                top10_df = summary_df.head(10).copy()
                top10_df['Qty_Label'] = top10_df.apply(lambda r: f"{r['จำนวนที่ขาย']:,.0f}", axis=1)
                bar_colors = px.colors.qualitative.Bold[:10] if len(px.colors.qualitative.Bold[:10]) >= len(top10_df) else px.colors.qualitative.Plotly[:10]
                fig_prod = px.bar(top10_df, x='จำนวนที่ขาย', y='ชื่อสินค้า', orientation='h', text='Qty_Label', color='ชื่อสินค้า', color_discrete_sequence=bar_colors)
                fig_prod.update_traces(textposition='auto')
                fig_prod.update_layout(yaxis={'categoryorder':'total ascending', 'title':""}, xaxis_title="จำนวนที่ขาย", showlegend=False, height=450, margin=dict(l=10, r=30, t=20, b=10))
                st.plotly_chart(fig_prod, use_container_width=True)
            with c2:
                st.markdown("##### ตารางรายการสินค้าขายดีทั้งหมด")
                st.dataframe(summary_df.style.format({
                    'ยอดขายรวม': '฿{:,.2f}', 
                    'จำนวนที่ขาย': '{:,.2f}', 
                    'บิลที่มีสินค้านี้': '{:,.0f}'
                }), use_container_width=True, hide_index=True)
        else: st.warning("ไม่พบข้อมูลรายการสินค้าในช่วงเวลาที่เลือก (หรือข้อมูลไม่สมบูรณ์)")
    else: st.info("ไม่พบไฟล์ข้อมูลที่เกี่ยวกับสินค้า (Product Data) ในระบบ กรุณาตรวจสอบว่ามีไฟล์สำหรับสินค้านำเข้าแล้วหรือไม่")
