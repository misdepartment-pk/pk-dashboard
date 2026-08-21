import streamlit as st
import pandas as pd

# 1. ตั้งค่าหน้าจอเว็บ (layout="wide" จะแสดงผลเต็มจอคอม และจะเรียงซ้อนกันอัตโนมัติบนมือถือ)
st.set_page_config(page_title="PK Noodle Shop Dashboard", page_icon="🍜", layout="wide")

st.title("🍜 PK Noodle Shop - Executive Dashboard")

# ข้อความแนะนำสำหรับคนเปิดผ่านมือถือ (ช่วยแก้ปัญหาคนหาเมนูตัวกรองไม่เจอ)
st.info("📱 **ทริคสำหรับมือถือ:** กดปุ่ม **> หรือ ☰** ที่มุมซ้ายบน เพื่อเปิดเมนูตัวกรองสาขาและอัปเดตข้อมูล")

# 2. นำ URL ที่คัดลอกมาจาก Google Sheets มาวางที่นี่
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRY7ex-fj9WSoY0H6PdP-POfww4cmK-FZRyLFVg1gB1vj-Y-Nme9Ag3wBg844Ml99vlSGI0DnCglAkZ/pub?gid=1767953677&single=true&output=csv" 

# เมนูด้านข้าง (Sidebar)
st.sidebar.header("⚙️ การตั้งค่าข้อมูล")

# สลับเอา "อัพโหลดไฟล์ อัตโนมัติ" ขึ้นก่อน และเปลี่ยนชื่อให้ตรงกับที่คุณต้องการ
data_source = st.sidebar.radio(
    "เลือกแหล่งข้อมูล:", 
    ["อัพโหลดไฟล์ อัตโนมัติ", "อัปโหลดไฟล์ (CSV)"]
)

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

# 3. เริ่มกระบวนการวิเคราะห์
if df is not None:
    if 'NAME' not in df.columns and len(df.columns) > 0:
        df.rename(columns={df.columns[0]: 'NAME'}, inplace=True)

    if 'FCANCEL' in df.columns:
        df = df[df['FCANCEL'] == 0]

    required_cols = ['GRANDTOTAL', 'NAME']
    if all(col in df.columns for col in required_cols):
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("🔍 ตัวกรองข้อมูล (Filters)")
        
        all_branches = df['NAME'].dropna().unique()
        selected_branches = st.sidebar.multiselect("เลือกสาขาที่ต้องการดู:", all_branches, default=all_branches)
        
        if not selected_branches:
            st.warning("⚠️ กรุณาเลือกสาขาอย่างน้อย 1 สาขา จากเมนูด้านซ้าย")
        else:
            df_filtered = df[df['NAME'].isin(selected_branches)]

            # KPIs (ในมือถือ ระบบจะจับเรียงซ้อนกันเป็นแนวตั้งให้อัตโนมัติ ทำให้ตัวเลขใหญ่และอ่านง่าย)
            total_sales = df_filtered['GRANDTOTAL'].sum()
            total_orders = len(df_filtered)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("ยอดขายรวม (ที่เลือก)", f"฿{total_sales:,.2f}")
            col2.metric("จำนวนบิล", f"{total_orders:,}")
            if total_orders > 0:
                col3.metric("เฉลี่ยต่อบิล", f"฿{(total_sales/total_orders):,.2f}")
            
            st.markdown("---")

            # ปรับชื่อแท็บให้สั้นลง เพื่อให้พอดีกับหน้าจอมือถือ
            tab1, tab2, tab3 = st.tabs(["🏢 ยอดรวมสาขา", "📈 เทรนด์รายวัน", "📋 ตารางตัวเลข"])

            with tab1:
                st.subheader("เปรียบเทียบยอดขาย")
                branch_sales = df_filtered.groupby('NAME')['GRANDTOTAL'].sum().reset_index().sort_values('GRANDTOTAL', ascending=False)
                # เอา height=400 ออก เพื่อให้กราฟปรับสัดส่วนอัตโนมัติตามมือถือ
                st.bar_chart(data=branch_sales.set_index('NAME'), y='GRANDTOTAL', color="#10B981")

            with tab2:
                st.subheader("แนวโน้มการขายรายวัน")
                if 'CF_TRANDATE' in df_filtered.columns:
                    daily_trend = df_filtered.groupby('CF_TRANDATE')['GRANDTOTAL'].sum().reset_index()
                    try:
                        daily_trend['Day'] = daily_trend['CF_TRANDATE'].apply(lambda x: int(str(x).split('/')[0]))
                        daily_trend = daily_trend.sort_values('Day').drop('Day', axis=1)
                    except:
                        pass
                    # เอา height=400 ออกเช่นกัน
                    st.line_chart(data=daily_trend.set_index('CF_TRANDATE'), y='GRANDTOTAL', color="#2196F3")
                else:
                    st.info("ไม่มีคอลัมน์ 'CF_TRANDATE'")

            with tab3:
                st.subheader("รายละเอียด")
                st.dataframe(
                    branch_sales.style.format({'GRANDTOTAL': '{:,.2f}'}), 
                    use_container_width=True
                )
    else:
        st.error("ข้อมูลไม่มีคอลัมน์ที่จำเป็น ('NAME', 'GRANDTOTAL')")
