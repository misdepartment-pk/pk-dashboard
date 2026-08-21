import streamlit as st
import pandas as pd

# 1. ตั้งค่าหน้าจอเว็บ
st.set_page_config(page_title="PK Noodle Shop", page_icon="🍜", layout="wide")

st.title("🍜 PK Noodle Shop - Executive Dashboard")
st.markdown("ระบบวิเคราะห์ยอดขายสำหรับผู้บริหาร (ดูได้ทุกที่ทุกเวลา)")

# 2. เมนูอัปโหลดไฟล์
st.sidebar.header("⚙️ เมนูจัดการข้อมูล")
uploaded_file = st.sidebar.file_uploader("อัปโหลดไฟล์ยอดขาย (CSV)", type=['csv'])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
    except:
        df = pd.read_csv(uploaded_file, encoding='tis-620', on_bad_lines='skip')
    
    if 'NAME' not in df.columns and len(df.columns) > 0:
        df.rename(columns={df.columns[0]: 'NAME'}, inplace=True)

    if 'FCANCEL' in df.columns:
        df = df[df['FCANCEL'] == 0]

    if 'GRANDTOTAL' in df.columns and 'NAME' in df.columns:
        total_sales = df['GRANDTOTAL'].sum()
        total_orders = len(df)
        
        # แสดง KPI
        col1, col2, col3 = st.columns(3)
        col1.metric("ยอดขายรวมทั้งหมด (บาท)", f"฿{total_sales:,.2f}")
        col2.metric("จำนวนรายการ (บิล)", f"{total_orders:,}")
        if total_orders > 0:
            col3.metric("ยอดเฉลี่ยต่อบิล (บาท)", f"฿{(total_sales/total_orders):,.2f}")
        
        st.markdown("---")
        
        # 3. จัดกลุ่มยอดขายตามสาขา
        st.subheader("🏢 ยอดขายแยกตามสาขา")
        branch_sales = df.groupby('NAME')['GRANDTOTAL'].sum().reset_index().sort_values('GRANDTOTAL', ascending=False)
        
        # ==========================================
        # แก้ปัญหาภาษาไทย: เปลี่ยนมาใช้ Native Chart
        # ==========================================
        st.bar_chart(data=branch_sales, x='NAME', y='GRANDTOTAL', color="#10B981")
        
        # แสดงตาราง
        st.subheader("📋 ตารางข้อมูลสรุป")
        st.dataframe(branch_sales, use_container_width=True)

else:
    st.info("👈 กรุณาอัปโหลดไฟล์ข้อมูลยอดขาย .CSV ผ่านเมนูด้านซ้ายเพื่อเริ่มต้น")
