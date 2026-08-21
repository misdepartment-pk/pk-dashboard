import streamlit as st
import pandas as pd

# 1. ตั้งค่าหน้าจอเว็บ
st.set_page_config(page_title="PK Noodle Shop", page_icon="🍜", layout="wide")

st.title("🍜 PK Noodle Shop - Executive Dashboard")
st.markdown("ระบบวิเคราะห์ยอดขายดึงข้อมูลอัตโนมัติจาก Google Sheets")

# 2. นำ URL ที่คัดลอกมาจาก Google Sheets (Publish to web) มาวางที่นี่
# ⚠️ สำคัญ: ต้องเป็นลิงก์ที่ลงท้ายด้วย output=csv เท่านั้น
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRY7ex-fj9WSoY0H6PdP-POfww4cmK-FZRyLFVg1gB1vj-Y-Nme9Ag3wBg844Ml99vlSGI0DnCglAkZ/pub?gid=1767953677&single=true&output=csv" 

# สร้างปุ่มสำหรับบังคับโหลดข้อมูลใหม่ (Refresh) 
if st.button("🔄 อัปเดตข้อมูลล่าสุด"):
    st.cache_data.clear()

# 3. ฟังก์ชันสำหรับโหลดข้อมูลจาก URL อัตโนมัติ (ใส่ Cache เพื่อให้โหลดเร็วขึ้น)
@st.cache_data(ttl=600) # ttl=600 หมายถึงให้จดจำข้อมูลไว้ 10 นาที (ลดภาระการโหลด)
def load_data_from_gsheets(url):
    try:
        if url == "วาง_URL_ของคุณที่นี่":
            return None # กรณีลืมเปลี่ยน URL
        # อ่านข้อมูลจากลิงก์ Google Sheets ตรงๆ
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการโหลดข้อมูล: {e}")
        return None

# เรียกใช้งานฟังก์ชันโหลดข้อมูล
df = load_data_from_gsheets(GOOGLE_SHEET_URL)

# 4. ประมวลผลและสร้าง Dashboard (ถ้ามีข้อมูล)
if df is not None:
    # เคลียร์ชื่อคอลัมน์ภาษาไทยที่มีปัญหา
    if 'NAME' not in df.columns and len(df.columns) > 0:
        df.rename(columns={df.columns[0]: 'NAME'}, inplace=True)

    # กรองเฉพาะบิลที่ไม่ถูกยกเลิก (ถ้ามีคอลัมน์นี้)
    if 'FCANCEL' in df.columns:
        df = df[df['FCANCEL'] == 0]

    # ตรวจสอบคอลัมน์สำคัญ
    if 'GRANDTOTAL' in df.columns and 'NAME' in df.columns:
        
        # --- แสดงตัวเลขสรุป (KPIs) ---
        total_sales = df['GRANDTOTAL'].sum()
        total_orders = len(df)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("ยอดขายรวมทั้งหมด (บาท)", f"฿{total_sales:,.2f}")
        col2.metric("จำนวนรายการ (บิล)", f"{total_orders:,}")
        if total_orders > 0:
            col3.metric("ยอดเฉลี่ยต่อบิล (บาท)", f"฿{(total_sales/total_orders):,.2f}")
        
        st.markdown("---")
        
        # --- สร้างกราฟยอดขายแยกตามสาขา ---
        st.subheader("🏢 ยอดขายแยกตามสาขา")
        branch_sales = df.groupby('NAME')['GRANDTOTAL'].sum().reset_index().sort_values('GRANDTOTAL', ascending=False)
        
        # ใช้ Native Chart ของ Streamlit เพื่อรองรับภาษาไทย
        st.bar_chart(data=branch_sales, x='NAME', y='GRANDTOTAL', color="#10B981")
        
       # แสดงตารางข้อมูลดิบ
        st.subheader("📋 ตารางข้อมูลสรุป")
        st.dataframe(
            branch_sales.style.format({'GRANDTOTAL': '{:,.2f}'}), 
            use_container_width=True
        )

    else:
        st.error("ข้อมูลใน Google Sheets ไม่มีคอลัมน์ที่จำเป็น (ต้องการ 'NAME' และ 'GRANDTOTAL')")
else:
    st.info("กำลังรอการเชื่อมต่อข้อมูล... (กรุณาตรวจสอบ URL ในโค้ดว่าถูกต้องหรือไม่)")
