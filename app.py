import streamlit as st
import pandas as pd
import datetime
import plotly.express as px

# 1. ตั้งค่าหน้าจอเว็บ
st.set_page_config(page_title="PK Noodle Shop Dashboard", page_icon="🍜", layout="wide")

# ==========================================
# 🎨 ส่วนตกแต่ง CSS สำหรับผู้บริหาร (Executive Theme)
# ==========================================
st.markdown("""
<style>
    /* ตกแต่งกล่องตัวเลข KPI ให้มีกรอบและเงา (Card Style) */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #f0f2f6;
        padding: 5% 10%;
        border-radius: 10px;
        box-shadow: 2px 4px 12px rgba(0, 0, 0, 0.08);
    }
    /* ปรับสีตัวอักษรหัวข้อ KPI */
    div[data-testid="metric-container"] > label {
        color: #555555 !important;
        font-size: 1.05rem !important;
        font-weight: bold;
    }
    /* ปรับสีตัวเลข KPI ให้เป็นโทนสีกรมท่าที่ดูน่าเชื่อถือ */
    div[data-testid="metric-container"] > div {
        color: #003f5c !important; 
    }
    /* ซ่อนลายน้ำของ Streamlit ด้านล่าง */
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# ส่วนหัวของเว็บ
# ==========================================
col_logo, col_title = st.columns([1, 4]) 
with col_logo:
    try:
        st.image("logo.png", width=150)
    except:
        st.write("🍜") 
        
with col_title:
    st.title("PK Noodle Shop - Executive Dashboard")
    st.info("📱 **ทริคสำหรับมือถือ:** กดปุ่ม **> หรือ ☰** ที่มุมซ้ายบน เพื่อเปิดเมนูตัวกรองข้อมูล")

# 2. นำ URL ที่คัดลอกมาจาก Google Sheets มาวางที่นี่
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRY7ex-fj9WSoY0H6PdP-POfww4cmK-FZRyLFVg1gB1vj-Y-Nme9Ag3wBg844Ml99vlSGI0DnCglAkZ/pub?gid=1767953677&single=true&output=csv" 

# 3. เมนูด้านข้าง (Sidebar)
st.sidebar.header("⚙️ การตั้งค่าข้อมูล")
data_source = st.sidebar.radio("เลือกแหล่งข้อมูล:", ["อัพโหลดไฟล์ อัตโนมัติ", "อัปโหลดไฟล์ (CSV)"])

@st.cache_data(ttl=600)
def load_data_from_url(url):
    try:
        if url == "วาง_URL_ของคุณที่นี่" or url.strip() == "":
            return None
        return pd.read_csv(url)
    except Exception as e:
        st.sidebar.error(f"เกิดข้อผิดพลาดในการโหลดจาก URL: {e}")
        return None

@st.cache_data
def load_data_from_upload(file):
    try:
        try:
            return pd.read_csv(file, encoding='utf-8-sig')
        except:
            return pd.read_csv(file, encoding='tis-620', on_bad_lines='skip')
    except Exception as e:
        st.sidebar.error(f"เกิดข้อผิดพลาดในการอ่านไฟล์: {e}")
        return None

df = None

# โหลดข้อมูล
if data_source == "อัปโหลดไฟล์ (CSV)":
    uploaded_file = st.sidebar.file_uploader("อัปโหลดไฟล์ยอดขาย", type=['csv'])
    if uploaded_file is not None:
        df = load_data_from_upload(uploaded_file)
    else:
        st.sidebar.info("👈 กรุณาอัปโหลดไฟล์ CSV")
else:
    df = load_data_from_url(GOOGLE_SHEET_URL)
    if df is None:
        st.warning("⚠️ ไม่พบข้อมูลจาก Google Sheets กรุณาตรวจสอบ URL ในโค้ด")
        if st.button("🔄 ลองดึงข้อมูลอีกครั้ง"):
            st.cache_data.clear()

# 4. เริ่มกระบวนการวิเคราะห์
if df is not None:
    if 'NAME' not in df.columns and len(df.columns) > 0:
        df.rename(columns={df.columns[0]: 'NAME'}, inplace=True)

    if 'FCANCEL' in df.columns:
        df = df[df['FCANCEL'] == 0]

    required_cols = ['GRANDTOTAL', 'NAME']
    if all(col in df.columns for col in required_cols):
        
        # --- แปลงวันที่ ---
        if 'CF_TRANDATE' in df.columns:
            def parse_thai_date(date_str):
                try:
                    parts = str(date_str).split('/')
                    d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
                    if y > 2500: y -= 543 
                    return pd.Timestamp(year=y, month=m, day=d)
                except:
                    return pd.NaT
            
            df['Parsed_Date'] = df['CF_TRANDATE'].apply(parse_thai_date)
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("🔍 ตัวกรองข้อมูล (Filters)")
        
        # กรองวันที่
        if 'Parsed_Date' in df.columns and not df['Parsed_Date'].dropna().empty:
            min_date = df['Parsed_Date'].min().date()
            max_date = df['Parsed_Date'].max().date()
            
            st.sidebar.markdown("**📅 กรองตามช่วงวันที่**")
            date_range = st.sidebar.date_input(
                "เลือกวันที่เริ่มต้น - สิ้นสุด:",
                value=(min_date, max_date), 
                min_value=min_date,
                max_value=max_date
            )
            
            if len(date_range) == 2:
                start_date, end_date = date_range
                df = df[(df['Parsed_Date'].dt.date >= start_date) & (df['Parsed_Date'].dt.date <= end_date)]
            
            # กรองเดือน
            st.sidebar.markdown("**🗓️ กรองตามเดือน**")
            all_months = sorted(df['Parsed_Date'].dropna().dt.month.unique())
            month_names = {1:'มกราคม', 2:'กุมภาพันธ์', 3:'มีนาคม', 4:'เมษายน', 5:'พฤษภาคม', 6:'มิถุนายน', 7:'กรกฎาคม', 8:'สิงหาคม', 9:'กันยายน', 10:'ตุลาคม', 11:'พฤศจิกายน', 12:'ธันวาคม'}
            
            selected_months = st.sidebar.multiselect(
                "เลือกเดือนที่ต้องการดู:",
                options=all_months,
                default=all_months, 
                format_func=lambda x: month_names.get(x, str(x))
            )
            
            if selected_months:
                df = df[df['Parsed_Date'].dt.month.isin(selected_months)]
        
        # กรองสาขา
        st.sidebar.markdown("**🏢 กรองตามสาขา**")
        all_branches = df['NAME'].dropna().unique()
        selected_branches = st.sidebar.multiselect("เลือกสาขาที่ต้องการดู:", all_branches, default=all_branches)
        
        if not selected_branches:
            st.warning("⚠️ กรุณาเลือกสาขาอย่างน้อย 1 สาขา จากเมนูด้านซ้าย")
        else:
            df_filtered = df[df['NAME'].isin(selected_branches)]

            # 📊 ส่วนแสดง KPI
            total_sales = df_filtered['GRANDTOTAL'].sum()
            total_orders = len(df_filtered)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("ยอดขายรวมทั้งหมด (บาท)", f"฿{total_sales:,.2f}")
            col2.metric("จำนวนรายการ (บิล)", f"{total_orders:,}")
            if total_orders > 0:
                col3.metric("ยอดเฉลี่ยต่อบิล (บาท)", f"฿{(total_sales/total_orders):,.2f}")
            
            st.markdown("<br>", unsafe_allow_html=True) # เว้นบรรทัดนิดนึงให้ดูโปร่งขึ้น

            # โทนสีสำหรับผู้บริหาร (Executive Modern Palette)
            executive_colors = ['#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600']

            tab1, tab2, tab3 = st.tabs(["🏢 ยอดรวมสาขา", "📈 เทรนด์รายวัน", "📋 ตารางตัวเลข"])

            with tab1:
                st.subheader("เปรียบเทียบยอดขายรายสาขา")
                branch_sales = df_filtered.groupby('NAME')['GRANDTOTAL'].sum().reset_index().sort_values('GRANDTOTAL', ascending=False)
                
                col_bar, col_pie = st.columns(2)
                
                with col_bar:
                    fig_bar = px.bar(branch_sales, x='NAME', y='GRANDTOTAL', color='NAME', 
                                     color_discrete_sequence=executive_colors,
                                     text_auto=',.2f', title="ยอดขาย (กราฟแท่ง)")
                    # ทำให้กราฟดูสะอาดขึ้น ซ่อนเส้น Grid ที่ไม่จำเป็น
                    fig_bar.update_layout(showlegend=False, xaxis_title="", yaxis_title="ยอดขาย (บาท)",
                                          plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                          yaxis=dict(showgrid=True, gridcolor='#f0f2f6'))
                    st.plotly_chart(fig_bar, use_container_width=True)
                    
                with col_pie:
                    fig_pie = px.pie(branch_sales, values='GRANDTOTAL', names='NAME', 
                                     color_discrete_sequence=executive_colors,
                                     title="สัดส่วนยอดขาย (กราฟโดนัท)", hole=0.45)
                    # ให้ข้อความชี้เปอร์เซ็นต์อยู่ด้านในวงกลม
                    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                    fig_pie.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_pie, use_container_width=True)

            with tab2:
                st.subheader("แนวโน้มการขายรายวัน")
                if 'CF_TRANDATE' in df_filtered.columns:
                    daily_trend = df_filtered.groupby('CF_TRANDATE')['GRANDTOTAL'].sum().reset_index()
                    try:
                        daily_trend['Day'] = daily_trend['CF_TRANDATE'].apply(lambda x: int(str(x).split('/')[0]))
                        daily_trend = daily_trend.sort_values('Day').drop('Day', axis=1)
                    except:
                        pass
                    
                    # เปลี่ยนกราฟเส้นเป็น Plotly เพื่อให้โค้งสวยงามและหรูหราขึ้น
                    fig_line = px.line(daily_trend, x='CF_TRANDATE', y='GRANDTOTAL', 
                                       markers=True, line_shape='spline') # spline ทำให้เส้นโค้งมน
                    fig_line.update_traces(line_color='#2f4b7c', line_width=3, marker_size=8)
                    fig_line.update_layout(xaxis_title="วันที่", yaxis_title="ยอดขาย (บาท)",
                                           plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                           xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#f0f2f6'))
                    
                    st.plotly_chart(fig_line, use_container_width=True)
                else:
                    st.info("ไม่มีคอลัมน์ 'CF_TRANDATE'")

          with tab3:
                st.subheader("รายละเอียดยอดขาย")
                display_df = branch_sales.rename(columns={
                    'NAME': 'ชื่อสาขา', 
                    'GRANDTOTAL': 'ยอดขายทั้งสิ้น'
                })
                
                # เพิ่มลูกเล่นสีแรเงา (Background Gradient) ให้กับคอลัมน์ตัวเลข
                styled_df = (display_df.style
                             .format({'ยอดขายทั้งสิ้น': '{:,.2f}'})
                             .background_gradient(cmap='Blues', subset=['ยอดขายทั้งสิ้น']))
                
                st.dataframe(styled_df, use_container_width=True) 
    else:
        st.error("ข้อมูลไม่มีคอลัมน์ที่จำเป็น ('NAME', 'GRANDTOTAL')")
