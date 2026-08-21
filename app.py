import streamlit as st
import pandas as pd
import datetime
import plotly.express as px  # <-- เพิ่มเครื่องมือวาดกราฟตัวใหม่

# 1. ตั้งค่าหน้าจอเว็บ
st.set_page_config(page_title="PK Noodle Shop Dashboard", page_icon="🍜", layout="wide")

# ==========================================
# ส่วนหัวของเว็บ (แทรกโลโก้)
# ==========================================
col_logo, col_title = st.columns([1, 4]) # แบ่งสัดส่วนพื้นที่ โลโก้ 1 ส่วน : ชื่อเรื่อง 4 ส่วน
with col_logo:
    try:
        # ดึงรูป logo.png มาแสดง
        st.image("logo.png", width=150)
    except:
        st.write("🍜") # ถ้าหารูปไม่เจอจะขึ้นอิโมจิแทน
        
with col_title:
    st.title("PK Noodle Shop - Executive Dashboard")
    st.info("📱 **ทริคสำหรับมือถือ:** กดปุ่ม **> หรือ ☰** ที่มุมซ้ายบน เพื่อเปิดเมนูตัวกรองข้อมูล")

# 2. นำ URL ที่คัดลอกมาจาก Google Sheets มาวางที่นี่
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRY7ex-fj9WSoY0H6PdP-POfww4cmK-FZRyLFVg1gB1vj-Y-Nme9Ag3wBg844Ml99vlSGI0DnCglAkZ/pub?gid=1767953677&single=true&output=csv" 

# 3. เมนูด้านข้าง (Sidebar) - ตั้งค่าแหล่งข้อมูล
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

# โหลดข้อมูลตามเมนูที่เลือก
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
        
        # --- แปลงวันที่ (รองรับ พ.ศ.) ---
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
        
        # ตัวกรองที่ 1: ช่วงวันที่
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
            
            # ตัวกรองที่ 2: เดือน
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
        
        # ตัวกรองที่ 3: สาขา
        st.sidebar.markdown("**🏢 กรองตามสาขา**")
        all_branches = df['NAME'].dropna().unique()
        selected_branches = st.sidebar.multiselect("เลือกสาขาที่ต้องการดู:", all_branches, default=all_branches)
        
        if not selected_branches:
            st.warning("⚠️ กรุณาเลือกสาขาอย่างน้อย 1 สาขา จากเมนูด้านซ้าย")
        else:
            df_filtered = df[df['NAME'].isin(selected_branches)]

            total_sales = df_filtered['GRANDTOTAL'].sum()
            total_orders = len(df_filtered)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("ยอดขายรวม (ที่เลือก)", f"฿{total_sales:,.2f}")
            col2.metric("จำนวนบิล", f"{total_orders:,}")
            if total_orders > 0:
                col3.metric("เฉลี่ยต่อบิล", f"฿{(total_sales/total_orders):,.2f}")
            
            st.markdown("---")

            tab1, tab2, tab3 = st.tabs(["🏢 ยอดรวมสาขา", "📈 เทรนด์รายวัน", "📋 ตารางตัวเลข"])

            # ==========================================
            # มิติที่ 1: เปรียบเทียบสาขา (แท่งหลากสี + วงกลม)
            # ==========================================
            with tab1:
                st.subheader("เปรียบเทียบยอดขายรายสาขา")
                branch_sales = df_filtered.groupby('NAME')['GRANDTOTAL'].sum().reset_index().sort_values('GRANDTOTAL', ascending=False)
                
                # แบ่งครึ่งหน้าจอ (ซ้าย กราฟแท่ง / ขวา กราฟวงกลม)
                # เมื่อเปิดบนมือถือ มันจะเรียงซ้อนกันบนล่างอัตโนมัติ ทำให้ขนาดเล็กลงพอดีจอ
                col_bar, col_pie = st.columns(2)
                
                with col_bar:
                    # สร้างกราฟแท่งแยกสีตามสาขา
                    fig_bar = px.bar(branch_sales, x='NAME', y='GRANDTOTAL', color='NAME', 
                                     text_auto='.2s', title="ยอดขาย (กราฟแท่ง)")
                    fig_bar.update_layout(showlegend=False, xaxis_title="", yaxis_title="ยอดขาย (บาท)")
                    st.plotly_chart(fig_bar, use_container_width=True)
                    
                with col_pie:
                    # สร้างกราฟโดนัท
                    fig_pie = px.pie(branch_sales, values='GRANDTOTAL', names='NAME', 
                                     title="สัดส่วนยอดขาย (กราฟโดนัท)", hole=0.4)
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
                    st.line_chart(data=daily_trend.set_index('CF_TRANDATE'), y='GRANDTOTAL', color="#2196F3")
                else:
                    st.info("ไม่มีคอลัมน์ 'CF_TRANDATE'")

            with tab3:
                st.subheader("รายละเอียดยอดขาย")
                st.dataframe(
                    branch_sales.style.format({'GRANDTOTAL': '{:,.2f}'}), 
                    use_container_width=True
                )
    else:
        st.error("ข้อมูลไม่มีคอลัมน์ที่จำเป็น ('NAME', 'GRANDTOTAL')")
