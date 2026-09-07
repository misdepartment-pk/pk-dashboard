import glob
import os
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ==========================================
# 1. PAGE CONFIG & CUSTOM CSS
# ==========================================
st.set_page_config(
    page_title="PK NOODLE SHOP Dashboard",
    page_icon="🍜",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    /* Global styles */
    .main {
        background-color: #f8f9fa;
    }
    
    /* Top banner card */
    .metric-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        text-align: center;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: #1e293b;
    }
    .metric-label {
        font-size: 14px;
        color: #64748b;
        margin-bottom: 4px;
    }
    
    /* Trick Banner */
    .trick-banner {
        background-color: #e0f2fe;
        color: #0369a1;
        padding: 10px 16px;
        border-radius: 8px;
        font-size: 14px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Custom Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        white-space: pre-wrap;
        background-color: #ffffff;
        border-radius: 6px 6px 0px 0px;
        padding: 8px 16px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff;
        border-bottom: 3px solid #ef4444 !important;
        color: #ef4444 !important;
    }
</style>
""",
    unsafe_allow_html=True,
)


# ==========================================
# 2. HELPER FUNCTIONS & DATA LOADING
# ==========================================
def parse_thai_date(date_str):
  if pd.isna(date_str) or str(date_str).strip() == '':
    return pd.NaT
  date_s = str(date_str).strip()
  if 'T' in date_s:
    try:
      return pd.to_datetime(date_s.split('T')[0])
    except:
      pass

  try:
    date_only = date_s.split()[0]
    parts = date_only.replace('-', '/').split('/')
    if len(parts) == 3:
      p1, p2, p3 = int(parts[0]), int(parts[1]), int(parts[2])
      if p1 > 1000:
        y, m, d = p1, p2, p3
      elif p3 > 1000:
        y, m, d = p3, p2, p1 if p3 > 12 else (p3, p1, p2)
      else:
        y, m, d = p3, p2, p1
      if y > 2500:
        y -= 543
      return pd.Timestamp(year=y, month=m, day=d)
  except:
    pass
  try:
    return pd.to_datetime(date_s.split()[0], dayfirst=True, errors='coerce')
  except:
    return pd.NaT


@st.cache_data(ttl=300)
def load_all_sales_data():
  dfs = []

  # รายชื่อไฟล์ CSV ทั้งหมดที่ระบบรองรับ (ทั้งปี 2568 และ 2569)
  possible_csvs = [
      'Sale Data2568.csv',
      'Sale Data2868.csv',
      'Sale Data2569.csv',
      'sales data.CSV',
      'sales_data.csv',
  ]

  # ค้นหาไฟล์ยอดขายแยกสาขาเพิ่มเติม (ถ้ามี)
  branch_files = glob.glob('ยอดขายสาขา*.csv')
  all_files = list(set(possible_csvs + branch_files))

  for filename in all_files:
    if os.path.exists(filename):
      try:
        try:
          df_temp = pd.read_csv(
              filename, encoding='utf-8-sig', low_memory=False
          )
        except:
          df_temp = pd.read_csv(
              filename, encoding='tis-620', low_memory=False
          )

        # แปลงชื่อ Column ให้เป็นตัวพิมพ์ใหญ่เพื่อความสม่ำเสมอ
        df_temp.columns = [str(c).upper().strip() for c in df_temp.columns]
        dfs.append(df_temp)
      except Exception:
        pass

  if not dfs:
    return pd.DataFrame(
        columns=['Parsed_Date', 'Year_BE', 'NAME', 'GRANDTOTAL', 'ORDER_COUNT']
    )

  df_combined = pd.concat(dfs, ignore_index=True)
  df_combined = df_combined.drop_duplicates()

  # ค้นหา Column วันที่
  date_col = next(
      (
          c
          for c in [
              'DOC_DATE',
              'DOCDATE',
              'TRANDATE',
              'CF_TRANDATE',
              'PSH_DATE',
              'วันที่',
              'PDATA_CODE',
          ]
          if c in df_combined.columns
      ),
      None,
  )
  if date_col:
    df_combined['Parsed_Date'] = df_combined[date_col].apply(parse_thai_date)
  else:
    df_combined['Parsed_Date'] = pd.NaT

  # สร้างคอลัมน์ปี พ.ศ. (2568, 2569)
  df_combined['Year_BE'] = df_combined['Parsed_Date'].dt.year + 543

  # ค้นหา Column ยอดขาย
  sales_col = next(
      (
          c
          for c in [
              'GRAND_TOTAL',
              'GRANDTOTAL',
              'AMOUNT',
              'PSD_N_AMT',
              'ยอดขาย(บาท)',
              'PDATA_NET_AMT',
              'ยอดขายทั้งสิ้น',
          ]
          if c in df_combined.columns
      ),
      None,
  )
  if sales_col:
    df_combined['GRANDTOTAL'] = (
        pd.to_numeric(
            df_combined[sales_col]
            .astype(str)
            .str.replace(',', '')
            .str.strip(),
            errors='coerce',
        ).fillna(0)
    )
  else:
    df_combined['GRANDTOTAL'] = 0.0

  # ค้นหา Column ชื่อสาขา
  branch_col = next(
      (
          c
          for c in ['BRANCH_NAME', 'BRANCHNAME', 'NAME', 'PSH_BR_NAME', 'สาขา']
          if c in df_combined.columns
      ),
      None,
  )
  if branch_col:
    df_combined['NAME'] = (
        df_combined[branch_col]
        .astype(str)
        .str.replace('\u200b', '')
        .str.replace('\xa0', ' ')
        .str.replace('ตลาด', '')
        .str.strip()
    )
  else:
    df_combined['NAME'] = 'สาขาหลัก'

  # ค้นหา Column จำนวนบิล/รายการ
  bill_col = next(
      (
          c
          for c in [
              'ORDER_COUNT',
              'BILL_COUNT',
              'NO_OF_BILL',
              'BILL_QTY',
              'PDATA_QTY',
          ]
          if c in df_combined.columns
      ),
      None,
  )
  if bill_col:
    df_combined['ORDER_COUNT'] = pd.to_numeric(
        df_combined[bill_col], errors='coerce'
    ).fillna(1)
  else:
    df_combined['ORDER_COUNT'] = 1

  return df_combined


# โหลดข้อมูล
df_all = load_all_sales_data()

# ==========================================
# 3. SIDEBAR FILTERS
# ==========================================
st.sidebar.title('🔍 เมนูกรองข้อมูล')

st.sidebar.markdown('### 📅 1. เลือกเวลาที่ต้องการดู')

# ตัวเลือกกรองปี
available_years = sorted(
    [int(y) for y in df_all['Year_BE'].dropna().unique() if y > 2000],
    reverse=True,
)
year_options = ['ทั้งหมด'] + [str(y) for y in available_years]
if '2569' in year_options and '2568' in year_options:
  year_options = ['ทั้งหมด', '2569', '2568']

selected_year_str = st.sidebar.selectbox('กรองรายปี:', year_options, index=0)

# ตัวเลือกกรองช่วงเวลาแบบด่วน
quick_time = st.sidebar.selectbox(
    'เลือกช่วงเวลาแบบด่วน:',
    [
        'ดูข้อมูลทั้งหมด',
        'วันนี้',
        'เมื่อวาน',
        '7 วันล่าสุด',
        '30 วันล่าสุด',
        'เดือนนี้',
        'กำหนดเอง (เลือกปฏิทิน)',
    ],
)

start_date, end_date = None, None
if quick_time == 'กำหนดเอง (เลือกปฏิทิน)':
  min_d = (
      df_all['Parsed_Date'].min()
      if not df_all['Parsed_Date'].isna().all()
      else datetime.today()
  )
  max_d = (
      df_all['Parsed_Date'].max()
      if not df_all['Parsed_Date'].isna().all()
      else datetime.today()
  )
  date_range = st.sidebar.date_input('เลือกช่วงวันที่:', [min_d, max_d])
  if len(date_range) == 2:
    start_date, end_date = date_range[0], date_range[1]

# กรองตามเดือน (อยู่ใน Expander)
with st.sidebar.expander('➕ กรองตามเดือน (สำหรับดูข้ามปี)', expanded=False):
  month_names = [
      'มกราคม',
      'กุมภาพันธ์',
      'มีนาคม',
      'เมษายน',
      'พฤษภาคม',
      'มิถุนายน',
      'กรกฎาคม',
      'สิงหาคม',
      'กันยายน',
      'ตุลาคม',
      'พฤศจิกายน',
      'ธันวาคม',
  ]
  selected_months = st.multiselect('เลือกเดือน:', month_names, default=[])

st.sidebar.markdown('---')
st.sidebar.markdown('### 🏬 2. เลือกสาขา')

all_branches = sorted(df_all['NAME'].dropna().unique().tolist())
if not all_branches:
  all_branches = [
      'ศรีเมือง',
      'ทุ่งปอ',
      'เจ้าพรหม',
      'บ้านไร่',
      'เทศบาล',
      'บ้านโป่ง',
  ]

selected_branches = st.sidebar.multiselect(
    'กด X เพื่อลบ หรือพิมพ์เพื่อหาสาขา:',
    options=all_branches,
    default=all_branches,
)

st.sidebar.markdown('---')
st.sidebar.caption('Powered by peter pak: v.10.0.0 (API Edition)')

# ==========================================
# 4. FILTERING LOGIC
# ==========================================
df_filtered = df_all.copy()

# 1. กรองตามปี
if selected_year_str != 'ทั้งหมด':
  target_year = int(selected_year_str)
  df_filtered = df_filtered[df_filtered['Year_BE'] == target_year]

# 2. กรองตามสาขา
if selected_branches:
  df_filtered = df_filtered[df_filtered['NAME'].isin(selected_branches)]

# 3. กรองตามเดือน
if selected_months:
  month_map = {m: i + 1 for i, m in enumerate(month_names)}
  target_month_nums = [
      month_map[m] for m in selected_months if m in month_map
  ]
  df_filtered = df_filtered[
      df_filtered['Parsed_Date'].dt.month.isin(target_month_nums)
  ]

# 4. กรองตามช่วงเวลาด่วน
if quick_time != 'ดูข้อมูลทั้งหมด' and not df_filtered['Parsed_Date'].isna().all():
  latest_date = df_filtered['Parsed_Date'].max()
  if pd.isna(latest_date):
    latest_date = datetime.today()

  if quick_time == 'วันนี้':
    df_filtered = df_filtered[df_filtered['Parsed_Date'] == latest_date]
  elif quick_time == 'เมื่อวาน':
    df_filtered = df_filtered[
        df_filtered['Parsed_Date'] == (latest_date - timedelta(days=1))
    ]
  elif quick_time == '7 วันล่าสุด':
    df_filtered = df_filtered[
        df_filtered['Parsed_Date'] >= (latest_date - timedelta(days=7))
    ]
  elif quick_time == '30 วันล่าสุด':
    df_filtered = df_filtered[
        df_filtered['Parsed_Date'] >= (latest_date - timedelta(days=30))
    ]
  elif quick_time == 'เดือนนี้':
    df_filtered = df_filtered[
        (df_filtered['Parsed_Date'].dt.month == latest_date.month)
        & (df_filtered['Parsed_Date'].dt.year == latest_date.year)
    ]
  elif quick_time == 'กำหนดเอง (เลือกปฏิทิน)' and start_date and end_date:
    df_filtered = df_filtered[
        (df_filtered['Parsed_Date'].dt.date >= start_date)
        & (df_filtered['Parsed_Date'].dt.date <= end_date)
    ]

# ==========================================
# 5. HEADER & TOP METRICS
# ==========================================
col_logo, col_space = st.columns([1, 4])
with col_logo:
  st.markdown('### 🍜 PK NOODLE SHOP')

# Trick Banner
st.markdown(
    '<div class="trick-banner">🧮 <b>ทริค:</b>'
    ' เมนูกรองข้อมูลอยู่ด้านซ้ายมือ (หากซ่อนอยู่ให้กดปุ่ม > เพื่อเปิด)</div>',
    unsafe_allow_html=True,
)

# คำนวณค่าการ์ดสรุปยอด
total_sales = df_filtered['GRANDTOTAL'].sum()
total_bills = df_filtered['ORDER_COUNT'].sum()
avg_bill = total_sales / total_bills if total_bills > 0 else 0

m1, m2, m3 = st.columns(3)
with m1:
  st.markdown(
      '<div class="metric-card"><div'
      ' class="metric-label">ยอดขายรวมทั้งหมด (บาท)</div><div'
      f' class="metric-value">฿{total_sales:,.2f}</div></div>',
      unsafe_allow_html=True,
  )

with m2:
  st.markdown(
      '<div class="metric-card"><div'
      ' class="metric-label">จำนวนรายการ (บิล)</div><div'
      f' class="metric-value">{int(total_bills):,}</div></div>',
      unsafe_allow_html=True,
  )

with m3:
  st.markdown(
      '<div class="metric-card"><div'
      ' class="metric-label">ยอดเฉลี่ยต่อบิล (บาท)</div><div'
      f' class="metric-value">฿{avg_bill:,.2f}</div></div>',
      unsafe_allow_html=True,
  )

st.markdown('<br>', unsafe_allow_html=True)


# ==========================================
# 6. CHART RENDERING FUNCTION
# ==========================================
def render_branch_visualizations(df_source, year_label):
  # กรองเฉพาะสาขาที่เลือกใน Sidebar
  df_curr = (
      df_source[df_source['NAME'].isin(selected_branches)]
      if selected_branches
      else df_source
  )

  if df_curr.empty:
    st.info(f'ไม่พบข้อมูลยอดขายสำหรับปี {year_label}')
    return

  # จัดกลุ่มตามสาขา
  branch_summary = df_curr.groupby('NAME')['GRANDTOTAL'].sum().reset_index()
  branch_summary = branch_summary.sort_values(by='GRANDTOTAL', ascending=False)

  c_bar, c_donut = st.columns([1.2, 1])

  # 1. กราฟแท่ง (Bar Chart)
  with c_bar:
    st.markdown(f'##### ยอดขาย (กราฟแท่ง)')
    fig_bar = px.bar(
        branch_summary,
        x='NAME',
        y='GRANDTOTAL',
        color='NAME',
        text='GRANDTOTAL',
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig_bar.update_traces(
        texttemplate='%{text:,.2f}', textposition='outside', cliponaxis=False
    )
    fig_bar.update_layout(
        xaxis_title='',
        yaxis_title='ยอดขาย (บาท)',
        showlegend=False,
        height=420,
        margin=dict(l=20, r=20, t=30, b=20),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    st.plotly_chart(fig_bar, use_container_width=True)

  # 2. กราฟโดนัท (Donut Chart)
  with c_donut:
    st.markdown(f'##### สัดส่วนยอดขาย (กราฟโดนัท)')
    fig_donut = px.pie(
        branch_summary,
        values='GRANDTOTAL',
        names='NAME',
        hole=0.5,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig_donut.update_traces(
        textinfo='percent+label', insidetextorientation='radial'
    )
    fig_donut.update_layout(
        showlegend=True,
        height=420,
        margin=dict(l=20, r=20, t=30, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
    )
    st.plotly_chart(fig_donut, use_container_width=True)


# ==========================================
# 7. TABS NAVIGATION
# ==========================================
tab_2569, tab_2568, tab_trend, tab_table, tab_bestseller = st.tabs([
    '🏢 ยอดรวมสาขา2569',
    '🏢 ยอดรวมสาขา2568',
    '📈 เทรนด์รายวัน',
    '📋 ตารางตัวเลข',
    '🍜 สินค้าขายดี',
])

# --- Tab 1: ยอดรวมสาขา 2569 ---
with tab_2569:
  df_2569 = df_all[df_all['Year_BE'] == 2569]
  render_branch_visualizations(df_2569, '2569')

# --- Tab 2: ยอดรวมสาขา 2568 (แทรกใหม่โดยใช้ข้อมูล Sale Data2568) ---
with tab_2568:
  df_2568 = df_all[df_all['Year_BE'] == 2568]
  render_branch_visualizations(df_2568, '2568')

# --- Tab 3: เทรนด์รายวัน ---
with tab_trend:
  st.markdown('##### 📈 เทรนด์ยอดขายรายวัน')
  if not df_filtered.empty and not df_filtered['Parsed_Date'].isna().all():
    daily_trend = (
        df_filtered.groupby(['Parsed_Date', 'NAME'])['GRANDTOTAL']
        .sum()
        .reset_index()
    )
    fig_line = px.line(
        daily_trend,
        x='Parsed_Date',
        y='GRANDTOTAL',
        color='NAME',
        markers=True,
        title='แนวโน้มยอดขายรายวันตามสาขา',
    )
    fig_line.update_layout(
        xaxis_title='วันที่',
        yaxis_title='ยอดขาย (บาท)',
        height=450,
        hovermode='x unified',
    )
    st.plotly_chart(fig_line, use_container_width=True)
  else:
    st.info('ไม่มีข้อมูลเพียงพอสำหรับแสดงกราฟเทรนด์รายวัน')

# --- Tab 4: ตารางตัวเลข ---
with tab_table:
  st.markdown('##### 📋 ตารางสรุปยอดขายตามสาขา')
  if not df_filtered.empty:
    summary_table = (
        df_filtered.groupby('NAME')
        .agg(
            ยอดขายรวม=('GRANDTOTAL', 'sum'), จำนวนบิล=('ORDER_COUNT', 'sum')
        )
        .reset_index()
    )
    summary_table['เฉลี่ยต่อบิล'] = (
        summary_table['ยอดขายรวม'] / summary_table['จำนวนบิล']
    )
    summary_table = summary_table.sort_values(
        by='ยอดขายรวม', ascending=False
    )

    st.dataframe(
        summary_table.style.format({
            'ยอดขายรวม': '฿{:,.2f}',
            'จำนวนบิล': '{:,.0f}',
            'เฉลี่ยต่อบิล': '฿{:,.2f}',
        }),
        use_container_width=True,
    )
  else:
    st.info('ไม่พบข้อมูลที่จะแสดงในตาราง')

# --- Tab 5: สินค้าขายดี ---
with tab_bestseller:
  st.markdown('##### 🍜 รายงานสินค้าขายดี')
  p_col = next(
      (
          c
          for c in [
              'PDATA_NAME',
              'PRODUCT_NAME',
              'P_NAME',
              'NAME_1',
              'ชื่อสินค้า',
          ]
          if c in df_filtered.columns
      ),
      None,
  )
  if p_col:
    qty_col = next(
        (
            c
            for c in ['PDATA_QTY', 'QTY', 'AMOUNT_QTY', 'จำนวน']
            if c in df_filtered.columns
        ),
        'ORDER_COUNT',
    )
    top_products = (
        df_filtered.groupby(p_col)
        .agg(ยอดขายรวม=('GRANDTOTAL', 'sum'), จำนวนที่ขาย=(qty_col, 'sum'))
        .reset_index()
        .sort_values(by='ยอดขายรวม', ascending=False)
        .head(20)
    )

    st.dataframe(
        top_products.style.format(
            {'ยอดขายรวม': '฿{:,.2f}', 'จำนวนที่ขาย': '{:,.0f}'}
        ),
        use_container_width=True,
    )
  else:
    st.info('ข้อมูลปัจจุบันแสดงยอดสรุปในระดับสาขา')
