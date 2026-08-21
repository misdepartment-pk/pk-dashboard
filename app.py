import streamlit as st
import pandas as pd

# 1. ตั้งค่าหน้าจอเว็บ
st.set_page_config(page_title="PK Noodle Shop Dashboard", page_icon="🍜", layout="wide")

st.title("🍜 PK Noodle Shop - Executive Dashboard")
st.markdown("ระบบวิเคราะห์ยอดขายหลายมิติ (Multi-Dimensional Analysis)")

# 2. นำ URL ที่คัดลอกมาจาก Google Sheets (Publish to web) มาวางที่นี่
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRY7ex-fj9WSoY0H6PdP-POfww4cmK-FZRyLFVg1gB1vj-Y-Nme9Ag3wBg844Ml99vlSGI0DnCglAkZ/pub?gid=1767953677&single=true&output=csv" 

# สร้างตัวเลือกให้ผู้ใช้เลือกว่าจะใช้ไฟล์อัปโหลดหรือดึงจาก Google Sheets
st.sidebar.header("⚙️ การตั้งค่าข้อมูล")
data_source = st.sidebar.radio("เลือกแหล่งข้อมูล:", ["อัปโหลดไฟล์ (CSV)", "ดึงอัตโนมัติจาก Google Sheets"])

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

# โหลดข้อมูลตามที่เลือก
if data_source == "อัปโหลดไฟล์ (CSV)":
    uploaded_file = st.sidebar.file_uploader("อัปโหลดไฟล์ยอดขาย", type=['csv'])
    if uploaded_file is not None:
        df = load_data_from_upload(uploaded_file)
    else:
        st.info("👈 กรุณาอัปโหลดไฟล์ CSV เพื่อเริ่มต้น")
else:
    df = load_data_from_url(GOOGLE_SHEET_URL)
    if df is None:
        st.info("⚠️ ไม่พบข้อมูลจาก Google Sheets กรุณาตรวจสอบ URL ในโค้ด")
        if st.button("🔄 ลองดึงข้อมูลอีกครั้ง"):
            st.cache_data.clear()

# 3. เริ่มกระบวนการวิเคราะห์เมื่อมีข้อมูล
if df is not None:
    # เคลียร์ชื่อคอลัมน์ (รองรับไฟล์ที่มีปัญหาคอลัมน์แรก)
    if 'NAME' not in df.columns and len(df.columns) > 0:
        df.rename(columns={df.columns[0]: 'NAME'}, inplace=True)

    # กรองเฉพาะบิลที่ไม่ถูกยกเลิก
    if 'FCANCEL' in df.columns:
        df = df[df['FCANCEL'] == 0]

    # ตรวจสอบว่ามีคอลัมน์สำคัญครบไหม
    required_cols = ['GRANDTOTAL', 'NAME']
    if all(col in df.columns for col in required_cols):
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("🔍 ตัวกรองข้อมูล (Filters)")
        
        # ตัวกรองสาขา
        all_branches = df['NAME'].dropna().unique()
        selected_branches = st.sidebar.multiselect("เลือกสาขาที่ต้องการดู:", all_branches, default=all_branches)
        
        # ถ้าไม่ได้เลือกสาขาเลย ให้แสดงข้อความเตือน
        if not selected_branches:
            st.warning("⚠️ กรุณาเลือกสาขาอย่างน้อย 1 สาขา จากเมนูด้านซ้าย")
        else:
            # กรอง DataFrame ตามสาขาที่เลือก
            df_filtered = df[df['NAME'].isin(selected_branches)]

            # ---------------------------------------------------------
            # ส่วนแสดงผลหลัก (KPIs)
            # ---------------------------------------------------------
            total_sales = df_filtered['GRANDTOTAL'].sum()
            total_orders = len(df_filtered)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("ยอดขายรวม (เฉพาะที่เลือก)", f"฿{total_sales:,.2f}")
            col2.metric("จำนวนรายการ (บิล)", f"{total_orders:,}")
            if total_orders > 0:
                col3.metric("ยอดเฉลี่ยต่อบิล", f"฿{(total_sales/total_orders):,.2f}")
            
            st.markdown("---")

            # ---------------------------------------------------------
            # ระบบแท็บ (Tabs) สำหรับมุมมองหลากหลายมิติ
            # ---------------------------------------------------------
            tab1, tab2, tab3 = st.tabs(["🏢 ภาพรวมรายสาขา", "📈 แนวโน้มรายวัน", "📋 ตารางข้อมูลเชิงลึก"])

            # มิติที่ 1: เปรียบเทียบสาขา
            with tab1:
                st.subheader("ยอดขายเปรียบเทียบแต่ละสาขา")
                branch_sales = df_filtered.groupby('NAME')['GRANDTOTAL'].sum().reset_index().sort_values('GRANDTOTAL', ascending=False)
                # ใช้ Native Chart สำหรับกราฟแท่ง
                st.bar_chart(data=branch_sales.set_index('NAME'), y='GRANDTOTAL', color="#10B981", height=400)

            # มิติที่ 2: แนวโน้มตามวัน
            with tab2:
                st.subheader("กราฟเส้นแสดงแนวโน้มยอดขายตามวัน")
                if 'CF_TRANDATE' in df_filtered.columns:
                    # จัดกลุ่มรายวัน
                    daily_trend = df_filtered.groupby('CF_TRANDATE')['GRANDTOTAL'].sum().reset_index()
                    
                    # เรียงวันที่ให้ถูกต้อง 
                    try:
                        daily_trend['Day'] = daily_trend['CF_TRANDATE'].apply(lambda x: int(str(x).split('/')[0]))
                        daily_trend = daily_trend.sort_values('Day').drop('Day', axis=1)
                    except:
                        pass
                        
                    # ใช้ Native Chart สำหรับกราฟเส้น
                    st.line_chart(data=daily_trend.set_index('CF_TRANDATE'), y='GRANDTOTAL', color="#2196F3", height=400)
                else:
                    st.info("ไฟล์ของคุณไม่มีคอลัมน์ 'CF_TRANDATE' จึงไม่สามารถสร้างกราฟรายวันได้")

            # มิติที่ 3: ตารางข้อมูล
            with tab3:
                st.subheader("ตารางยอดขายรายสาขา (พร้อมจัดรูปแบบตัวเลข)")
                st.dataframe(
                    branch_sales.style.format({'GRANDTOTAL': '{:,.2f}'}), 
                    use_container_width=True
                )
                
    else:
        st.error("ข้อมูลไม่มีคอลัมน์ที่จำเป็น (ต้องการ 'NAME' และ 'GRANDTOTAL')")
