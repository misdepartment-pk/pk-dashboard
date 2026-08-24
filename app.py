import streamlit as st
import pandas as pd
import datetime
import plotly.express as px

st.set_page_config(page_title="PK Noodle Shop Dashboard", page_icon="🍜", layout="wide")

st.markdown("""
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
with col_title:
    st.title("PK Noodle Shop - Executive Dashboard")

@st.cache_data
def load_local_data(filename):
    try:
        try: return pd.read_csv(filename, encoding='utf-8-sig')
        except: return pd.read_csv(filename, encoding='tis-620')
    except: return None

def parse_thai_date(date_str):
    try:
        date_only = str(date_str).split()[0]
        parts = date_only.split('/')
        if len(parts) == 3:
            d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
            if y > 2500: y -= 543 
            return pd.Timestamp(year=y, month=m, day=d)
        elif '-' in date_only:
            parts = date_only.split('-')
            if len(parts) == 3:
                y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                if y > 2500: y -= 543
                return pd.Timestamp(year=y, month=m, day=d)
    except: return pd.NaT
    return pd.NaT

df = load_local_data("sales data.CSV")      
df_product = load_local_data("product data.CSV") 

if df is not None:
    df.columns = df.columns.str.strip()
    if df_product is not None:
        df_product.columns = df_product.columns.str.strip()

    if 'NAME' not in df.columns and len(df.columns) > 0:
        df.rename(columns={df.columns[0]: 'NAME'}, inplace=True)
    if 'FCANCEL' in df.columns:
        df = df[df['FCANCEL'] == 0]

    col_date = 'TRANDATE' if 'TRANDATE' in df.columns else ('CF_TRANDATE' if 'CF_TRANDATE' in df.columns else None)
    
    if col_date:
        df['Parsed_Date'] = df[col_date].apply(parse_thai_date)
        
        st.sidebar.subheader("🔍 ตัวกรองข้อมูล")
        
        min_date, max_date = df['Parsed_Date'].min().date(), df['Parsed_Date'].max().date()
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        default_date = max_date if yesterday > max_date else (min_date if yesterday < min_date else yesterday)
            
        date_range = st.sidebar.date_input("เลือกช่วงวันที่:", value=(default_date, default_date), min_value=min_date, max_value=max_date)
        if len(date_range) == 2:
            start_date, end_date = date_range
            df = df[(df['Parsed_Date'].dt.date >= start_date) & (df['Parsed_Date'].dt.date <= end_date)]
        else:
            start_date, end_date = min_date, max_date
        
        all_branches = df['NAME'].dropna().unique()
        selected_branches = st.sidebar.multiselect("เลือกสาขา:", all_branches, default=all_branches)
        
        if selected_branches:
            df_filtered = df[df['NAME'].isin(selected_branches)].copy()
            df_filtered['GRANDTOTAL'] = pd.to_numeric(df_filtered['GRANDTOTAL'].astype(str).str.replace(',', '').str.strip(), errors='coerce').fillna(0)

            col_bill = 'TRANNO' if 'TRANNO' in df_filtered.columns else None
            df_unique_bills = df_filtered.drop_duplicates(subset=[col_bill]).copy() if col_bill else df_filtered.copy()

            total_sales = df_unique_bills['GRANDTOTAL'].sum()
            total_orders = len(df_unique_bills)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("ยอดขายรวม", f"฿{total_sales:,.2f}")
            c2.metric("จำนวนบิล", f"{total_orders:,}")
            if total_orders > 0: c3.metric("ยอดเฉลี่ย/บิล", f"฿{(total_sales/total_orders):,.2f}")
            
            tab1, tab2, tab3, tab4 = st.tabs(["🏢 ยอดรวมสาขา", "📈 เทรนด์รายวัน", "📋 ตาราง", "🍜 สินค้าขายดี (Debug)"])
            
            # (ข้ามส่วน Tab 1, 2, 3 ไป เพื่อโฟกัสที่ Tab 4)
            with tab1: st.write("✅ โหลดแท็บ 1 สำเร็จ")
            with tab2: st.write("✅ โหลดแท็บ 2 สำเร็จ")
            with tab3: st.write("✅ โหลดแท็บ 3 สำเร็จ")

            with tab4:
                st.subheader("🏆 20 อันดับสินค้าขายดี (Top 20 Products)")
                
                if df_product is not None:
                    # ==========================================
                    # โหมดนักพัฒนา: ปริ้นท์ชื่อคอลัมน์ให้ดู!
                    # ==========================================
                    st.error("🚨 **(สำหรับแก้ปัญหา) รายชื่อคอลัมน์ทั้งหมดในไฟล์ `product data.CSV`:**")
                    st.code(list(df_product.columns))
                    st.error("🚨 **รายชื่อคอลัมน์ทั้งหมดในไฟล์ `sales data.CSV`:**")
                    st.code(list(df_filtered.columns))

                    # พยายามเชื่อมข้อมูลแบบบังคับ (Force Join)
                    df_prod_filtered = df_product.copy()
                    
                    # ลองหาคอลัมน์วันที่ในไฟล์สินค้า
                    prod_date_col = None
                    for c in ['TRANDATE', 'CF_TRANDATE', 'DATE', 'วันที่']:
                        if c in df_prod_filtered.columns:
                            prod_date_col = c
                            break
                            
                    # ลองหาคอลัมน์สาขาในไฟล์สินค้า
                    prod_branch_col = None
                    for c in ['NAME', 'CF_WAHOUSENAME', 'สาขา', 'FNAME']:
                        if c in df_prod_filtered.columns:
                            prod_branch_col = c
                            break
                            
                    # ลองหาเลขที่บิลในไฟล์สินค้า
                    prod_bill_col = None
                    for c in ['TRANNO', 'BILLNO', 'RECEIPTNO', 'เลขที่บิล']:
                        if c in df_prod_filtered.columns:
                            prod_bill_col = c
                            break

                    st.info(f"🔍 ระบบหาคอลัมน์เจอแบบนี้: วันที่=`{prod_date_col}`, สาขา=`{prod_branch_col}`, เลขที่บิล=`{prod_bill_col}`")
                    
                    # เริ่มกรองข้อมูลจริงๆ
                    if prod_bill_col and col_bill:
                        valid_bills = df_filtered[col_bill].astype(str).str.strip().str.upper().unique()
                        df_prod_filtered = df_prod_filtered[df_prod_filtered[prod_bill_col].astype(str).str.strip().str.upper().isin(valid_bills)]
                        st.success("✅ กรองข้อมูลด้วย **เลขที่บิล** สำเร็จ!")
                    
                    elif prod_date_col and prod_branch_col:
                        df_prod_filtered['Parsed_Date'] = df_prod_filtered[prod_date_col].apply(parse_thai_date)
                        df_prod_filtered = df_prod_filtered[(df_prod_filtered['Parsed_Date'].dt.date >= start_date) & (df_prod_filtered['Parsed_Date'].dt.date <= end_date)]
                        df_prod_filtered = df_prod_filtered[df_prod_filtered[prod_branch_col].isin(selected_branches)]
                        st.success("✅ กรองข้อมูลด้วย **วันที่ + สาขา** สำเร็จ!")
                    else:
                        st.warning("❌ ไม่สามารถกรองข้อมูลได้ เพราะหาชื่อคอลัมน์ไม่เจอ กราฟด้านล่างคือข้อมูลทั้งหมด!")

                    if not df_prod_filtered.empty and 'ITEMNAME' in df_prod_filtered.columns:
                        col_amount, col_qty = st.columns(2)
                        
                        if 'AMOUNT' in df_prod_filtered.columns:
                            df_prod_filtered['AMOUNT'] = pd.to_numeric(df_prod_filtered['AMOUNT'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                            with col_amount:
                                top_amt = df_prod_filtered.groupby('ITEMNAME')['AMOUNT'].sum().reset_index().sort_values('AMOUNT', ascending=False).head(20)
                                fig_amt = px.bar(top_amt, x='AMOUNT', y='ITEMNAME', orientation='h', text_auto=',.2f', color='AMOUNT', color_continuous_scale='Blues')
                                fig_amt.update_layout(yaxis={'categoryorder':'total ascending'}, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                                st.plotly_chart(fig_amt, use_container_width=True)

                        if 'BASEQUANTITY' in df_prod_filtered.columns:
                            df_prod_filtered['BASEQUANTITY'] = pd.to_numeric(df_prod_filtered['BASEQUANTITY'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
                            with col_qty:
                                top_qty = df_prod_filtered.groupby('ITEMNAME')['BASEQUANTITY'].sum().reset_index().sort_values('BASEQUANTITY', ascending=False).head(20)
                                fig_qty = px.bar(top_qty, x='BASEQUANTITY', y='ITEMNAME', orientation='h', text_auto=',.0f', color='BASEQUANTITY', color_continuous_scale='Oranges')
                                fig_qty.update_layout(yaxis={'categoryorder':'total ascending'}, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                                st.plotly_chart(fig_qty, use_container_width=True)
                else:
                    st.error("ไฟล์ product data.CSV หายไปครับ")
