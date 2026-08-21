import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# 1. ตั้งค่าหน้าจอเว็บให้รองรับมือถือและคอมฯ
st.set_page_config(page_title="PK Noodle Shop", page_icon="🍜", layout="wide")

st.title("🍜 PK Noodle Shop - Executive Dashboard")
st.markdown("ระบบวิเคราะห์ยอดขายสำหรับผู้บริหาร (ดูได้ทุกที่ทุกเวลา)")

# 2. สร้างเมนูแถบด้านข้าง (Sidebar) สำหรับอัปโหลดไฟล์
st.sidebar.header("⚙️ เมนูจัดการข้อมูล")
uploaded_file = st.sidebar.file_uploader("อัปโหลดไฟล์ยอดขาย (CSV)", type=['csv'])

if uploaded_file is not None:
    # 3. โหลดข้อมูล (รองรับภาษาไทย)
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
    except:
        df = pd.read_csv(uploaded_file, encoding='tis-620', on_bad_lines='skip')
    
    if 'NAME' not in df.columns and len(df.columns) > 0:
        df.rename(columns={df.columns[0]: 'NAME'}, inplace=True)

    # กรองเฉพาะบิลที่ไม่ถูกยกเลิก
    if 'FCANCEL' in df.columns:
        df = df[df['FCANCEL'] == 0]

    if 'GRANDTOTAL' in df.columns and 'NAME' in df.columns:
        # 4. คำนวณสรุปตัวเลข (KPIs)
        total_sales = df['GRANDTOTAL'].sum()
        total_orders = len(df)
        
        # แสดงตัวเลขแบบการ์ด 3 ช่อง
        col1, col2, col3 = st.columns(3)
        col1.metric("ยอดขายรวมทั้งหมด (บาท)", f"฿{total_sales:,.2f}")
        col2.metric("จำนวนรายการ (บิล)", f"{total_orders:,}")
        if total_orders > 0:
            col3.metric("ยอดเฉลี่ยต่อบิล (บาท)", f"฿{(total_sales/total_orders):,.2f}")
        
        st.markdown("---")
        
        # 5. วาดกราฟเปรียบเทียบสาขา
        st.subheader("🏢 ยอดขายแยกตามสาขา")
        branch_sales = df.groupby('NAME')['GRANDTOTAL'].sum().reset_index().sort_values('GRANDTOTAL', ascending=False)
        
        # ตั้งค่าฟอนต์ภาษาไทยสำหรับกราฟ
        plt.rcParams['font.family'] = 'Tahoma'
        
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.bar(branch_sales['NAME'], branch_sales['GRANDTOTAL'], color='#10B981')
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
        ax.tick_params(axis='x', rotation=45)
        
        # โชว์กราฟบนหน้าเว็บ
        st.pyplot(fig)
        
        # โชว์ตารางข้อมูลดิบ
        st.subheader("📋 ตารางข้อมูลสรุป")
        st.dataframe(branch_sales, use_container_width=True)

else:
    st.info("👈 กรุณาอัปโหลดไฟล์ข้อมูลยอดขาย .CSV ผ่านเมนูด้านซ้ายเพื่อเริ่มต้น")