import streamlit as st
import pandas as pd
import datetime
import plotly.express as px

# 1. ตั้งค่าหน้าจอเว็บ
st.set_page_config(page_title="PK Noodle Shop Dashboard", page_icon="🍜", layout="wide")

st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
<style>
    div[data-testid="metric-container"] {
        background-color: #1e1e1e;
        border: 1px solid #333;
        padding: 5% 10%;
        border-radius: 10px;
        box-shadow: 2px 4px 12px rgba(0, 0, 0, 0.5);
    }
    div[data-testid="metric-container"] > label {
        color: #cccccc !important;
        font-size: 1.05rem !important;
        font-weight: bold;
    }
    div[data-testid="metric-container"] > div {
        color: #ffffff !important; 
    }
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

col_logo, col_title = st.columns([1, 4]) 
with col_logo:
    try: st.image("logo.png", width=150)
    except: st.write("🍜") 
        
with col_title:
    st.title("PK Noodle Shop - Executive Dashboard")
    st.info("📱 **ทริคสำหรับมือถือ:** กดปุ่ม **> หรือ ☰** ที่มุมซ้ายบน เพื่อเปิดเมนูตัวกรองข้อมูล")

@st.cache_data
def load_local_data(filename):
    try:
        try: return pd.read_csv(filename, encoding='utf-8-sig', low_memory=False)
        except: return pd.read_csv(filename, encoding='tis-620', low_memory=False)
    except: return None

# ฟังก์ชันแปลงวันที่ให้ฉลาดขึ้น รองรับทั้ง DD/MM/YYYY และ YYYY-MM-DD
def parse_thai_date(date_str):
    if pd.isna(date_str): return pd.NaT
    try:
        date_only = str(date_str).strip().split()[0]
        if '/' in date_only: parts = date_only.split('/')
        elif '-' in date_only: parts = date_only.split('-')
        else: return pd.NaT
            
        if len(parts) == 3:
            if int(parts[0]) <= 31: # format DD/MM/YYYY
                d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
            else: # format YYYY/MM/DD
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            
            if y > 2500: y -= 543 
            return pd.Timestamp(year=y, month=m, day=d)
    except: pass
    return pd.NaT

df = load_local_data("sales data.CSV")      
df_product = load_local_data("product data.CSV") 

if df is not None:
    df.columns = df.columns.str.strip()
    # ลบช่องว่างในชื่อสาขา ป้องกันการกรองไม่ติด
    if 'NAME' in df.columns: df['NAME'] = df['NAME'].astype(str).str.strip()
    
    if df_product is not None:
        df_product.columns = df_product.columns.str.strip()
        if 'NAME' in df_product.columns: df_product['NAME'] = df_product['NAME'].astype(str).str.strip()

    required_cols = ['GRANDTOTAL', 'NAME']
    if all(col in df.columns for col in required_cols):
        
        # ค้นหาคอลัมน์วันที่ของไฟล์ Sales
        col_date = 'TRANDATE' if 'TRANDATE' in df.columns else ('CF_TRANDATE' if 'CF_TRANDATE' in df.columns else None)
        if col_date:
            df['Parsed_Date'] = df[col_date].apply(parse_thai_date)
            
        # ค้นหาคอลัมน์วันที่ของไฟล์ Product (ถ้ามี)
        if df_product is not None:
            col_date_prod = 'TRANDATE' if 'TRANDATE' in df_product.columns else ('CF_TRANDATE' if 'CF_TRANDATE' in df_product.columns else None)
            if col_date_prod:
                df_product['Parsed_Date'] = df_product[col_date_prod].apply(parse_thai_date)
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("🔍 ตัวกรองข้อมูล (Filters)")
        
        # 1. ตั้งค่าช่วงวันที่
        if 'Parsed_Date' in df.columns and not df['Parsed_Date'].dropna().empty:
            min_date = df['Parsed_Date'].min().date()
            max_date = df['Parsed_Date'].max().date()
            
            st.sidebar.markdown("**📅 กรองตามช่วงวันที่**")
            today = datetime.date.today()
            yesterday = today - datetime.timedelta(days=1)
            default_date = max_date if yesterday > max_date else (min_date if yesterday < min_date else yesterday)
                
            date_range = st.sidebar.date_input(
                "เลือกวันที่เริ่มต้น - สิ้นสุด:",
                value=(default_date, default_date), min_value=min_date, max_value=max_date
            )
            
            if len(date_range) == 2:
                start_date, end_date = date_range
            else:
                start_date, end_date = min_date, max_date
                
            # นำวันที่ไปกรอง DataFrame
            df = df[(df['Parsed_Date'].dt.date >= start_date) & (df['Parsed_Date'].dt.date <= end_date)]
            if df_product is not None and 'Parsed_Date' in df_product.columns:
                df_product = df_product[(df_product['Parsed_Date'].dt.date >= start_date) & (df_product['Parsed_Date'].dt.date <= end_date)]
            
            # 2. กรองตามเดือน
            st.sidebar.markdown("**🗓️ กรองตามเดือน**")
            all_months = sorted(df['Parsed_Date'].dropna().dt.month.unique())
            month_names = {1:'มกราคม', 2:'กุมภาพันธ์', 3:'มีนาคม', 4:'เมษายน', 5:'พฤษภาคม', 6:'มิถุนายน', 7:'กรกฎาคม', 8:'สิงหาคม', 9:'กันยายน', 10:'ตุลาคม', 11:'พฤศจิกายน', 12:'ธันวาคม'}
            
            selected_months = st.sidebar.multiselect(
                "เลือกเดือนที่ต้องการดู:",
                options=all_months, default=all_months, format_func=lambda x: month_names.get(x, str(x))
            )
            
            if selected_months:
                df = df[df['Parsed_Date'].dt.month.isin(selected_months)]
                if df_product is not None and 'Parsed_Date' in df_product.columns:
                    df_product = df_product[df_product['Parsed_Date'].dt.month.isin(selected_months)]
        
        # 3. กรองสาขา
        st.sidebar.markdown("**🏢 กรองตามสาขา**")
        all_branches = df['NAME'].dropna().unique()
        selected_branches = st.sidebar.multiselect("เลือกสาขาที่ต้องการดู:", all_branches, default=all_branches)
        
        if not selected_branches:
            st.warning("⚠️ กรุณาเลือกสาขาอย่างน้อย 1 สาขา จากเมนูด้านซ้าย")
        else:
            # กรองสาขาใน df_sales
            df_filtered = df[df['NAME'].isin(selected_branches)].copy()
            if 'FCANCEL' in df_filtered.columns:
                df_filtered = df_filtered[df_filtered['FCANCEL'] == 0]
                
            # กรองสาขาใน df_product โดยตรงเช่นกัน
            if df_product is not None and 'NAME' in df_product.columns:
                df_prod_filtered = df_product[df_product['NAME'].isin(selected_branches)].copy()
            else:
                df_prod_filtered = df_product.copy() if df_product is not None else None
                
            if df_prod_filtered is not None and 'FCANCEL' in df_prod_filtered.columns:
                df_prod_filtered = df_prod_filtered[df_prod_filtered['FCANCEL'] == 0]

            # คำนวณสรุปยอดขายบน Dashboard (ทำความสะอาดยอดเงิน GRANDTOTAL)
            df_filtered['GRANDTOTAL'] = df_filtered['GRANDTOTAL'].astype(str).str.replace(',', '').str.strip()
            df_filtered['GRANDTOTAL'] = pd.to_numeric(df_filtered['GRANDTOTAL'], errors='coerce').fillna(0)

            col_bill = 'TRANNO' if 'TRANNO' in df_filtered.columns else None
            df_unique_bills = df_filtered.drop_duplicates(subset=[col_bill]).copy() if col_bill else df_filtered.copy()

            total_sales = df_unique_bills['GRANDTOTAL'].sum()
            total_orders = len(df_unique_bills)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("ยอดขายรวมทั้งหมด (บาท)", f"฿{total_sales:,.2f}")
            col2.metric("จำนวนรายการ (บิล)", f"{total_orders:,}")
            if total_orders > 0:
                col3.metric("ยอดเฉลี่ยต่อบิล (บาท)", f"฿{(total_sales/total_orders):,.2f}")
            
            st.markdown("<br>", unsafe_allow_html=True) 

            executive_colors = ['#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600']
            chart_bg = 'rgba(0,0,0,0)'

            tab1, tab2, tab3, tab4 = st.tabs(["🏢 ยอดรวมสาขา", "📈 เทรนด์รายวัน", "📋 ตารางตัวเลข", "🍜 สินค้าขายดี"])

            with tab1:
                branch_sales = df_unique_bills.groupby('NAME')['GRANDTOTAL'].sum().reset_index().sort_values('GRANDTOTAL', ascending=False)
                col_bar, col_pie = st.columns(2)
                with col_bar:
                    fig_bar = px.bar(branch_sales, x='NAME', y='GRANDTOTAL', color='NAME', color_discrete_sequence=executive_colors, text_auto=',.2f', title="ยอดขาย (กราฟแท่ง)")
                    fig_bar.update_layout(showlegend=False, xaxis_title="", yaxis_title="ยอดขาย (บาท)", plot_bgcolor=chart_bg, paper_bgcolor=chart_bg, yaxis=dict(showgrid=True, gridcolor='#444'))
                    st.plotly_chart(fig_bar, use_container_width=True)
                with col_pie:
                    fig_pie = px.pie(branch_sales, values='GRANDTOTAL', names='NAME', color_discrete_sequence=executive_colors, title="สัดส่วนยอดขาย (กราฟโดนัท)", hole=0.45)
                    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                    fig_pie.update_layout(plot_bgcolor=chart_bg, paper_bgcolor=chart_bg)
                    st.plotly_chart(fig_pie, use_container_width=True)

            with tab2:
                if 'Parsed_Date' in df_unique_bills.columns:
                    daily_trend = df_unique_bills.groupby('Parsed_Date')['GRANDTOTAL'].sum().reset_index().sort_values('Parsed_Date')
                    fig_line = px.line(daily_trend, x='Parsed_Date', y='GRANDTOTAL', markers=True, line_shape='spline') 
                    fig_line.update_traces(line_color='#ff7c43', line_width=3, marker_size=8)
                    fig_line.update_layout(xaxis_title="วันที่", yaxis_title="ยอดขาย (บาท)", plot_bgcolor=chart_bg, paper_bgcolor=chart_bg, xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#444'))
                    st.plotly_chart(fig_line, use_container_width=True)

            with tab3:
                display_df = branch_sales.rename(columns={'NAME': 'ชื่อสาขา', 'GRANDTOTAL': 'ยอดขายทั้งสิ้น'})
                display_df = display_df.sort_values('ชื่อสาขา')
                st.dataframe(display_df.style.format({'ยอดขายทั้งสิ้น': '{:,.2f}'}).background_gradient(cmap='Blues', subset=['ยอดขายทั้งสิ้น']), use_container_width=True, hide_index=True)

            # ==========================================
            # แท็บ 4: วิเคราะห์สินค้า (รับผลจากตัวกรองโดยตรง 100%)
            # ==========================================
            with tab4:
                st.subheader("🏆 20 อันดับสินค้าขายดี (Top 20 Products)")
                
                if df_prod_filtered is not None and 'ITEMNAME' in df_prod_filtered.columns:
                    
                    if df_prod_filtered.empty:
                        st.info("⚠️ ไม่มีข้อมูลสินค้าขายดีในช่วงเวลา หรือสาขาที่คุณเลือก")
                    else:
                        col_amount, col_qty = st.columns(2)
                        
                        # ลบช่องว่างชื่อสินค้า เพื่อให้รวมกลุ่มถูกต้อง
                        df_prod_filtered['ITEMNAME'] = df_prod_filtered['ITEMNAME'].astype(str).str.strip()
                        
                        if 'AMOUNT' in df_prod_filtered.columns:
                            df_prod_filtered['AMOUNT'] = df_prod_filtered['AMOUNT'].astype(str).str.replace(',', '').str.strip()
                            df_prod_filtered['AMOUNT'] = pd.to_numeric(df_prod_filtered['AMOUNT'], errors='coerce').fillna(0)
                        
                        if 'BASEQUANTITY' in df_prod_filtered.columns:
                            df_prod_filtered['BASEQUANTITY'] = df_prod_filtered['BASEQUANTITY'].astype(str).str.replace(',', '').str.strip()
                            df_prod_filtered['BASEQUANTITY'] = pd.to_numeric(df_prod_filtered['BASEQUANTITY'], errors='coerce').fillna(0)
                        
                        with col_amount:
                            st.markdown("**💰 จัดอันดับตาม 'มูลค่าขาย (บาท)'**")
                            if 'AMOUNT' in df_prod_filtered.columns:
                                top_amount = df_prod_filtered.groupby('ITEMNAME')['AMOUNT'].sum().reset_index()
                                top_amount = top_amount.sort_values('AMOUNT', ascending=False).head(20)
                                
                                fig_amount = px.bar(top_amount, x='AMOUNT', y='ITEMNAME', orientation='h',
                                                  text_auto=',.2f', color='AMOUNT', color_continuous_scale='Blues')
                                fig_amount.update_layout(
                                    yaxis={'categoryorder':'total ascending'}, 
                                    xaxis_title="มูลค่าขาย (บาท)", yaxis_title="",
                                    plot_bgcolor=chart_bg, paper_bgcolor=chart_bg,
                                    coloraxis_showscale=False, height=600 
                                )
                                st.plotly_chart(fig_amount, use_container_width=True)

                        with col_qty:
                            st.markdown("**📦 จัดอันดับตาม 'จำนวนที่ขาย (ชิ้น)'**")
                            if 'BASEQUANTITY' in df_prod_filtered.columns:
                                top_qty = df_prod_filtered.groupby('ITEMNAME')['BASEQUANTITY'].sum().reset_index()
                                top_qty = top_qty.sort_values('BASEQUANTITY', ascending=False).head(20)
                                
                                fig_qty = px.bar(top_qty, x='BASEQUANTITY', y='ITEMNAME', orientation='h',
                                                  text_auto=',.0f', color='BASEQUANTITY', color_continuous_scale='Oranges')
                                fig_qty.update_layout(
                                    yaxis={'categoryorder':'total ascending'}, 
                                    xaxis_title="จำนวนที่ขาย (ชิ้น)", yaxis_title="",
                                    plot_bgcolor=chart_bg, paper_bgcolor=chart_bg,
                                    coloraxis_showscale=False, height=600
                                )
                                st.plotly_chart(fig_qty, use_container_width=True)
                else:
                    st.warning("⚠️ รอข้อมูลจากไฟล์ product data.CSV")
