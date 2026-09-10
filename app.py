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
    
    date_col = next((c for c in ['DOC_DATE', 'DOCDATE', 'TRANDATE', 'CF_TRANDATE', 'PSH_DATE', 'PDATA_DATE', 'DATE', 'DATETIME', 'TRAN_DATE', 'วันที่', 'TIME'] if c in df_p.columns), None)
    if date_col: df_p['Parsed_Date'] = df_p[date_col].apply(parse_thai_date)
    else: df_p['Parsed_Date'] = pd.NaT
    df_p['Year_BE'] = np.where(df_p['Parsed_Date'].notna(), df_p['Parsed_Date'].dt.year + 543, np.nan)
    
    branch_col = next((c for c in ['BRANCH_NAME', 'BRANCHNAME', 'BRANCH', 'NAME', 'PSH_BR_NAME', 'สาขา', 'LOCATION'] if c in df_p.columns), None)
    if branch_col: df_p['BRANCH_NAME'] = df_p[branch_col].astype(str).str.replace('\u200b', '').str.replace('\xa0', ' ').str.replace('ตลาด', '').str.strip()
    else: df_p['BRANCH_NAME'] = 'สาขาหลัก'
    
    qty_col = next((c for c in ['PDATA_QTY', 'QTY', 'QUANTITY', 'AMOUNT_QTY', 'จำนวน', 'จำนวนชิ้น', 'UNIT', 'COUNT', 'QTY_SOLD'] if c in df_p.columns), None)
    if qty_col: df_p['QTY'] = pd.to_numeric(df_p[qty_col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(1)
    else: df_p['QTY'] = 1
    
    sales_col = next((c for c in ['GRAND_TOTAL', 'GRANDTOTAL', 'AMOUNT', 'PSD_N_AMT', 'ยอดขาย(บาท)', 'ยอดขาย', 'PDATA_NET_AMT', 'NET_AMT', 'TOTAL', 'PRICE', 'TOTAL_PRICE', 'ยอดรวม'] if c in df_p.columns), None)
    if sales_col: df_p['GRANDTOTAL'] = pd.to_numeric(df_p[sales_col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
    else: df_p['GRANDTOTAL'] = 0.0
    
    prod_col = next((c for c in ['PDATA_NAME', 'PRODUCT_NAME', 'NAME1', 'ITEM_NAME', 'GOODS_NAME', 'DESCR', 'DESCRIPTION', 'ชื่อสินค้า', 'รายการ', 'สินค้า', 'NAME', 'TITLE', 'MENU'] if c in df_p.columns), None)
    if prod_col: df_p['PRODUCT_NAME'] = df_p[prod_col].astype(str).str.strip()
    else:
        str_cols = [c for c in df_p.columns if c not in ['Parsed_Date', 'Year_BE', 'BRANCH_NAME', 'QTY', 'GRANDTOTAL', date_col, branch_col, qty_col, sales_col]]
        if str_cols: df_p['PRODUCT_NAME'] = df_p[str_cols[0]].astype(str).str.strip()
        else: df_p['PRODUCT_NAME'] = 'ไม่ระบุชื่อสินค้า'
        
    unit_col = next((c for c in ['UNIT_NAME', 'หน่วย', 'UNIT', 'UM', 'UTQ_NAME'] if c in df_p.columns), None)
    if unit_col: df_p['UNIT'] = df_p[unit_col].astype(str).str.strip()
    else: df_p['UNIT'] = '-'
    
    bill_col = next((c for c in ['DOC_NO', 'DOCNO', 'BILL_NO', 'เลขที่เอกสาร', 'เลขที่บิล', 'REF_NO', 'DI_REF'] if c in df_p.columns), None)
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
                    df_temp = pd.read_csv(filename, encoding=encรบกวนส่งโค้ดที่คุณต้องการให้แก้ไขมาให้อีกครั้งครับ เนื่องจากผมยังไม่มีข้อมูลหรือบริบทของโค้ดก่อนหน้านี้ในตอนนี้

หากคุณแนบโค้ดชุดเดิมและแจ้งปัญหาหรือสิ่งที่ต้องการปรับปรุงมาให้ ผมจะตรวจสอบและเขียนโค้ดที่แก้ไขแล้วทั้งหมดกลับไปให้ทันทีครับ (หากระบุภาษาโปรแกรมมาด้วยจะดีมากครับ)
