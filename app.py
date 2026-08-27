import streamlit as st
import pandas as pd
import datetime
import pytz
import plotly.express as px
import os

# 1. ตั้งค่าหน้าจอเว็บ (ต้องอยู่บรรทัดแรกสุดเสมอ)
st.set_page_config(page_title="PK Noodle Shop Dashboard", page_icon="🍜", layout="wide")

# ==========================================
# 🔐 ระบบ Login กำหนดสิทธิ์ผู้เข้าใช้งาน
# ==========================================
USER_CREDENTIALS = {
    "admin": "1234",
    "peter": "pk2026",
    "manager": "5678"
}

def check_password():
    """ตรวจสอบการ Login"""
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.markdown("<br><br><h2 style='text-align: center; color: #003f5c;'>🔒 เข้าสู่ระบบ PK Noodle Shop</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1.5, 1, 1.5])
        with col2:
            with st.form("login_form"):
                username = st.text_input("👤 Username")
                password = st.text_input("🔑 Password", type="password")
                submit_button = st.form_submit_button("เข้าสู่ระบบ", use_container_width=True)
                
                if submit_button:
                    if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
                        st.session_state["password_correct"] = True
                        st.session_state["current_user"] = username
                        st.rerun()
                    else:
                        st.error("❌ Username หรือ Password ไม่ถูกต้อง!")
        return False
    return True

if not check_password():
    st.stop()

# ==========================================
# 🎨 ปรับแต่ง CSS
# ==========================================
st.markdown("""
<style>
    div[data-testid="metric-container"] {
        background-color: #ffffff; border: 1px solid #e6e6e6; padding: 5% 10%; border-radius: 10px; box-shadow: 2px 4px 12px rgba(0, 0, 0, 0.05);
    }
    div[data-testid="metric-container"] > label { color: #555555 !important; font-size: 1.05rem !important; font-weight: bold; }
    div[data-testid="metric-container"] > div { color: #003f5c !important; }
    footer {visibility: hidden;}
    .viewerBadge_container, .viewerBadge_link, [data-testid="stToolbar"], #MainMenu { display: none !important; }
    .sidebar-footer { position: relative; bottom: 0; width: 100%; padding-top: 50px; text-align: left; font-size: 0.85rem; color: #888888; }
</style>
""", unsafe_allow_html=True)

col_logo, col_title = st.columns([1, 4]) 
with col_logo:
    try: st.image("logo.png", width=150)
    except: st.write("🍜") 
        
with col_title:
    st.title("PK Noodle Shop - Executive Dashboard")
    st.info("📱 **ทริค:** เมนูกรองข้อมูลอยู่ด้านซ้ายมือ (หากซ่อนอยู่ให้กดปุ่ม > เพื่อเปิด)")

@st.cache_data
def load_and_prep_data():
    df, df_prod = pd.DataFrame(), pd.DataFrame()
    
    # 🌟 อ่านไฟล์ sales data.CSV
    if os.path.exists("sales data.CSV"):
        try: df = pd.read_csv("sales data.CSV", encoding='utf-8-sig', low_memory=False)
        except: df = pd.read_csv("sales data.CSV", encoding='tis-620', low_memory=False)
            
    # 🌟 อ่านไฟล์ product data.CSV
    if os.path.exists("product data.CSV"):
        try: df_prod = pd.read_csv("product data.CSV", encoding='utf-8-sig', low_memory=False)
        except: df_prod = pd.read_csv("product data.CSV", encoding='tis-620', low_memory=False)

    def parse_thai_date(date_str):
        if pd.isna(date_str) or str(date_str).strip() == '': return pd.NaT
        try:
            date_only = str(date_str).strip().split()[0]
            parts = date_only.replace('-', '/').split('/')
            if len(parts) == 3:
                p1, p2, p3 = int(parts[0]), int(parts[1]), int(parts[2])
                if p1 > 1000: y, m, d = p1, p2, p3
                elif p3 > 1000: y, m, d = p3, p2, p1 if p3 > 12 else (p3, p1, p2)
                else: y, m, d = p3, p2, p1 
                if y > 2500: y -= 543 
                return pd.Timestamp(year=y, month=m, day=d)
        except: pass
        try: return pd.to_datetime(str(date_str).strip().split()[0], dayfirst=True, errors='coerce')
        except: return pd.NaT

    # --- ทำความสะอาดไฟล์ยอดขาย ---
    if not df.empty:
        df.columns = df.columns.str.strip()
        
        # ค้นหาคอลัมน์วันที่ (รองรับทั้งไฟล์ดิบและไฟล์จัดตารางแล้ว)
        date_col = next((c for c in ['TRANDATE', 'CF_TRANDATE', 'PSH_DATE', 'วันที่', 'PDATA_CODE'] if c in df.columns), None)
        if date_col: df['Parsed_Date'] = df[date_col].apply(parse_thai_date)
            
        # ค้นหาคอลัมน์ยอดขายรวม
        sales_col = next((c for c in ['GRANDTOTAL', 'PSD_N_AMT', 'ยอดขาย(บาท)', 'PDATA_NET_AMT', 'ยอดขายทั้งสิ้น'] if c in df.columns), None)
        if sales_col: df['GRANDTOTAL'] = pd.to_numeric(df[sales_col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
        else: df['GRANDTOTAL'] = 0
            
        # ค้นหาคอลัมน์สาขา
        branch_col = next((c for c in ['NAME', 'PSH_BR_NAME', 'สาขา'] if c in df.columns), None)
        if branch_col: df['NAME'] = df[branch_col].astype(str).str.replace('\u200b', '').str.replace('\xa0', ' ').str.replace('ตลาด', '').str.strip()
        else: df['NAME'] = 'ไม่ระบุสาขา'

        # คำนวณจำนวนบิล/จำนวนรายการ
        if 'ยอดขาย(ชิ้น)' in df.columns: df['ORDER_COUNT'] = 1 # หากยุบรวมมาแล้ว ให้นับเป็นรายการ
        elif 'PDATA_CNT' in df.columns: df['ORDER_COUNT'] = pd.to_numeric(df['PDATA_CNT'], errors='coerce').fillna(1)
        else: df['ORDER_COUNT'] = 1

    # --- ทำความสะอาดไฟล์สินค้า ---
    if not df_prod.empty:
        df_prod.columns = df_prod.columns.str.strip()
        
        date_col_p = next((c for c in ['TRANDATE', 'CF_TRANDATE', 'PSH_DATE', 'วันที่', 'PDATA_CODE'] if c in df_prod.columns), None)
        if date_col_p: df_prod['Parsed_Date'] = df_prod[date_col_p].apply(parse_thai_date)
            
        branch_col_p = next((c for c in ['NAME', 'PSH_BR_NAME', 'สาขา'] if c in df_prod.columns), None)
        if branch_col_p: df_prod['NAME'] = df_prod[branch_col_p].astype(str).str.replace('\u200b', '').str.replace('\xa0', ' ').str.replace('ตลาด', '').str.strip()
            
        item_col = next((c for c in ['ITEMNAME', 'PSD_SHOW_SKUNAME', 'รายการสินค้า', 'PDATA_NAME'] if c in df_prod.columns), None)
        if item_col: df_prod['ITEMNAME_CLEAN'] = df_prod[item_col].astype(str).str.strip()
        
        qty_col = next((c for c in ['BASEQUANTITY', 'PSD_QTY', 'ยอดขาย(ชิ้น)', 'PDATA_QTY'] if c in df_prod.columns), None)
        if qty_col: df_prod['QTY_CLEAN'] = pd.to_numeric(df_prod[qty_col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)
        
        amt_col = next((c for c in ['AMOUNT', 'PSD_N_AMT', 'ยอดขาย(บาท)', 'PDATA_NET_AMT'] if c in df_prod.columns), None)
        if amt_col: df_prod['AMT_CLEAN'] = pd.to_numeric(df_prod[amt_col].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)

    return df, df_prod

df_master, df_product_master = load_and_prep_data()

if df_master is not None and not df_master.empty:
    df = df_master.copy()
    
    st.sidebar.markdown(f"👤 **ผู้ใช้งาน:** `{st.session_state.get('current_user', 'Unknown')}`")
    if st.sidebar.button("🚪 ออกจากระบบ"):
        st.session_state["password_correct"] = False
        st.rerun()
        
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 เมนูกรองข้อมูล")
    
    if 'Parsed_Date' in df.columns and not df['Parsed_Date'].dropna().empty:
        min_date = df['Parsed_Date'].dropna().min().date()
        max_date = df['Parsed_Date'].dropna().max().date()
        tz = pytz.timezone('Asia/Bangkok')
        today = datetime.datetime.now(tz).date()
        
        st.sidebar.markdown("**📅 1. เลือกเวลาที่ต้องการดู**")
        date_mode = st.sidebar.selectbox("เลือกช่วงเวลาแบบด่วน:", ["ดูข้อมูลทั้งหมด", "วันนี้", "เมื่อวาน", "7 วันล่าสุด", "เดือนนี้", "กำหนดเอง (เลือกปฏิทิน)"])
        
        if date_mode == "ดูข้อมูลทั้งหมด": start_date, end_date = min_date, max_date
        elif date_mode == "วันนี้": start_date, end_date = today, today
        elif date_mode == "เมื่อวาน": 
            yesterday = today - datetime.timedelta(days=1)
            start_date, end_date = yesterday, yesterday
        elif date_mode == "7 วันล่าสุด": start_date, end_date = today - datetime.timedelta(days=7), today
        elif date_mode == "เดือนนี้": start_date, end_date = today.replace(day=1), today
        else:
            st.sidebar.markdown("👇 **เลือกวันที่เอง (ตั้งแต่ - จนถึง):**")
            col_sd, col_ed = st.sidebar.columns(2)
            with col_sd: start_date = st.date_input("ตั้งแต่", value=min_date)
            with col_ed: end_date = st.date_input("จนถึง", value=max_date)
            
        df = df[(df['Parsed_Date'].dt.date >= start_date) & (df['Parsed_Date'].dt.date <= end_date)]
        
        with st.sidebar.expander("➕ กรองตามเดือน (สำหรับดูข้ามปี)"):
            all_months = sorted(df['Parsed_Date'].dropna().dt.month.unique())
            month_names = {1:'มกราคม', 2:'กุมภาพันธ์', 3:'มีนาคม', 4:'เมษายน', 5:'พฤษภาคม', 6:'มิถุนายน', 7:'กรกฎาคม', 8:'สิงหาคม', 9:'กันยายน', 10:'ตุลาคม', 11:'พฤศจิกายน', 12:'ธันวาคม'}
            selected_months = st.multiselect("เลือกเดือนที่ต้องการดู:", options=all_months, default=all_months, format_func=lambda x: month_names.get(x, str(x)))
            if selected_months: df = df[df['Parsed_Date'].dt.month.isin(selected_months)]
    
    st.sidebar.markdown("**🏢 2. เลือกสาขา**")
    all_branches = sorted(list(df['NAME'].dropna().unique()))
    selected_branches = st.sidebar.multiselect("กด X เพื่อลบ หรือพิมพ์เพื่อหาสาขา:", all_branches, default=all_branches)
    
    st.sidebar.markdown("<div class='sidebar-footer'>Power by peter pak: v.10.0.0</div>", unsafe_allow_html=True)
    
    if not selected_branches:
        st.warning("⚠️ กรุณาเลือกสาขาอย่างน้อย 1 สาขา จากเมนูด้านซ้าย")
    else:
        df_filtered = df[df['NAME'].isin(selected_branches)].copy()
        total_sales = df_filtered['GRANDTOTAL'].sum()
        total_orders = int(df_filtered['ORDER_COUNT'].sum()) if 'ORDER_COUNT' in df_filtered.columns else len(df_filtered)
            
        col1, col2, col3 = st.columns(3)
        col1.metric("ยอดขายรวมทั้งหมด (บาท)", f"฿{total_sales:,.2f}")
        col2.metric("จำนวนรายการ (บิล)", f"{total_orders:,}")
        if total_orders > 0: col3.metric("ยอดเฉลี่ยต่อบิล (บาท)", f"฿{(total_sales/total_orders):,.2f}")
        
        st.markdown("<br>", unsafe_allow_html=True) 

        executive_colors = ['#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600']
        chart_bg = 'rgba(0,0,0,0)'

        tab1, tab2, tab3, tab4 = st.tabs(["🏢 ยอดรวมสาขา", "📈 เทรนด์รายวัน", "📋 ตารางตัวเลข", "🍜 สินค้าขายดี"])

        branch_sales = df_filtered.groupby('NAME')['GRANDTOTAL'].sum().reset_index()
        all_selected_df = pd.DataFrame({'NAME': selected_branches})
        branch_sales = pd.merge(all_selected_df, branch_sales, on='NAME', how='left')
        branch_sales['GRANDTOTAL'] = branch_sales['GRANDTOTAL'].fillna(0)
        branch_sales = branch_sales.sort_values('GRANDTOTAL', ascending=False)

        with tab1:
            col_bar, col_pie = st.columns(2)
            with col_bar:
                fig_bar = px.bar(branch_sales, x='NAME', y='GRANDTOTAL', color='NAME', color_discrete_sequence=executive_colors, text_auto=',.2f', title="ยอดขาย (กราฟแท่ง)")
                fig_bar.update_layout(showlegend=False, xaxis_title="", yaxis_title="ยอดขาย (บาท)", plot_bgcolor=chart_bg, paper_bgcolor=chart_bg, yaxis=dict(showgrid=True, gridcolor='#e6e6e6'))
                st.plotly_chart(fig_bar, use_container_width=True)
            with col_pie:
                pie_data = branch_sales[branch_sales['GRANDTOTAL'] > 0]
                if not pie_data.empty:
                    fig_pie = px.pie(pie_data, values='GRANDTOTAL', names='NAME', color_discrete_sequence=executive_colors, title="สัดส่วนยอดขาย (กราฟโดนัท)", hole=0.45)
                    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                    fig_pie.update_layout(plot_bgcolor=chart_bg, paper_bgcolor=chart_bg)
                    st.plotly_chart(fig_pie, use_container_width=True)

        with tab2:
            if 'Parsed_Date' in df_filtered.columns:
                daily_trend = df_filtered.groupby('Parsed_Date')['GRANDTOTAL'].sum().reset_index().sort_values('Parsed_Date')
                if not daily_trend.empty:
                    fig_line = px.line(daily_trend, x='Parsed_Date', y='GRANDTOTAL', markers=True, line_shape='spline') 
                    fig_line.update_traces(line_color='#2f4b7c', line_width=3, marker_size=8)
                    fig_line.update_layout(xaxis_title="วันที่", yaxis_title="ยอดขาย (บาท)", plot_bgcolor=chart_bg, paper_bgcolor=chart_bg, xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#e6e6e6'))
                    st.plotly_chart(fig_line, use_container_width=True)

        with tab3:
            display_df = branch_sales.rename(columns={'NAME': 'ชื่อสาขา', 'GRANDTOTAL': 'ยอดขายทั้งสิ้น'}).sort_values('ชื่อสาขา')
            st.dataframe(display_df.style.format({'ยอดขายทั้งสิ้น': '{:,.2f}'}).background_gradient(cmap='Blues', subset=['ยอดขายทั้งสิ้น']), use_container_width=True, hide_index=True)

        with tab4:
            st.subheader("🏆 20 อันดับสินค้าขายดี (Top 20 Products)")
            if df_product_master is not None and not df_product_master.empty:
                df_prod_filtered = df_product_master.copy()
                
                if 'Parsed_Date' in df_prod_filtered.columns:
                    df_prod_filtered = df_prod_filtered[(df_prod_filtered['Parsed_Date'].dt.date >= start_date) & (df_prod_filtered['Parsed_Date'].dt.date <= end_date)]
                    if selected_months: df_prod_filtered = df_prod_filtered[df_prod_filtered['Parsed_Date'].dt.month.isin(selected_months)]
                
                if 'NAME' in df_prod_filtered.columns:
                    df_prod_filtered = df_prod_filtered[df_prod_filtered['NAME'].isin(selected_branches)]

                if df_prod_filtered.empty or 'ITEMNAME_CLEAN' not in df_prod_filtered.columns:
                    st.info("⚠️ ไม่มีข้อมูลสินค้าขายดีในช่วงเวลา หรือสาขาที่คุณเลือก")
                else:
                    col_amount, col_qty = st.columns(2)
                    
                    with col_amount:
                        st.markdown("**💰 จัดอันดับตาม 'มูลค่าขาย (บาท)'**")
                        if 'AMT_CLEAN' in df_prod_filtered.columns:
                            top_amount = df_prod_filtered.groupby('ITEMNAME_CLEAN')['AMT_CLEAN'].sum().reset_index().sort_values('AMT_CLEAN', ascending=False).head(20)
                            if not top_amount.empty:
                                fig_amount = px.bar(top_amount, x='AMT_CLEAN', y='ITEMNAME_CLEAN', orientation='h', text_auto=',.2f', color='AMT_CLEAN', color_continuous_scale='Blues')
                                fig_amount.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="มูลค่าขาย (บาท)", yaxis_title="", plot_bgcolor=chart_bg, paper_bgcolor=chart_bg, coloraxis_showscale=False, height=600)
                                st.plotly_chart(fig_amount, use_container_width=True)

                    with col_qty:
                        st.markdown("**📦 จัดอันดับตาม 'จำนวนที่ขาย (ชิ้น)'**")
                        if 'QTY_CLEAN' in df_prod_filtered.columns:
                            top_qty = df_prod_filtered.groupby('ITEMNAME_CLEAN')['QTY_CLEAN'].sum().reset_index().sort_values('QTY_CLEAN', ascending=False).head(20)
                            if not top_qty.empty:
                                fig_qty = px.bar(top_qty, x='QTY_CLEAN', y='ITEMNAME_CLEAN', orientation='h', text_auto=',.0f', color='QTY_CLEAN', color_continuous_scale='Oranges')
                                fig_qty.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis_title="จำนวนที่ขาย (ชิ้น)", yaxis_title="", plot_bgcolor=chart_bg, paper_bgcolor=chart_bg, coloraxis_showscale=False, height=600)
                                st.plotly_chart(fig_qty, use_container_width=True)
else:
    st.error("⚠️ ไม่สามารถโหลดไฟล์ข้อมูลยอดขายได้ กรุณาตรวจสอบว่ามีไฟล์ `sales data.CSV` อยู่ในระบบ")
