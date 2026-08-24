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
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
<style>
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #f0f2f6;
        padding: 5% 10%;
        border-radius: 10px;
        box-shadow: 2px 4px 12px rgba(0, 0, 0, 0.08);
    }
    div[data-testid="metric-container"] > label {
        color: #555555 !important;
        font-size: 1.05rem !important;
        font-weight: bold;
    }
    div[data-testid="metric-container"] > div {
        color: #003f5c !important; 
    }
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

# ==========================================
# 2. ระบบโหลดข้อมูลจากไฟล์ CSV
# ==========================================
@st.cache_data
def load_local_data(filename):
    try:
        try:
            return pd.read_csv(filename, encoding='utf-8-sig')
        except:
            return pd.read_csv(filename, encoding='tis-620')
    except Exception as e:
        return None

df = load_local_data("sales data.CSV")      
df_product = load_local_data("product data.CSV") 

# 3. เริ่มกระบวนการวิเคราะห์
if df is not None:
    if 'NAME' not in df.columns and len(df.columns) > 0:
        df.rename(columns={df.columns[0]: 'NAME'}, inplace=True)

    if 'FCANCEL' in df.columns:
        df = df[df['FCANCEL'] == 0]

    required_cols = ['GRANDTOTAL', 'NAME']
    if all(col in df.columns for col in required_cols):
        
        # --- [แก้ไขที่ 1] ระบบแปลงวันที่ให้ฉลาดขึ้น รองรับกรณีมีเวลาติดมาด้วย ---
        col_date = 'TRANDATE' if 'TRANDATE' in df.columns else 'CF_TRANDATE'
        
        if col_date in df.columns:
            def parse_thai_date(date_str):
                try:
                    # ตัดเอาเฉพาะวันที่ (ตัดเวลาทิ้ง)
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
                except:
                    return pd.NaT
                return pd.NaT
            
            df['Parsed_Date'] = df[col_date].apply(parse_thai_date)
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("🔍 ตัวกรองข้อมูล (Filters)")
        
        # กรองช่วงวันที่
        if 'Parsed_Date' in df.columns and not df['Parsed_Date'].dropna().empty:
            min_date = df['Parsed_Date'].min().date()
            max_date = df['Parsed_Date'].max().date()
            
            st.sidebar.markdown("**📅 กรองตามช่วงวันที่**")
            
            today = datetime.date.today()
            yesterday = today - datetime.timedelta(days=1)
            
            if yesterday > max_date: default_date = max_date  
            elif yesterday < min_date: default_date = min_date
            else: default_date = yesterday
                
            date_range = st.sidebar.date_input(
                "เลือกวันที่เริ่มต้น - สิ้นสุด:",
                value=(default_date, default_date),
                min_value=min_date,
                max_value=max_date
            )
            
            if len(date_range) == 2:
                start_date, end_date = date_range
                df = df[(df['Parsed_Date'].dt.date >= start_date) & (df['Parsed_Date'].dt.date <= end_date)]
            
            # กรองตามเดือน
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
            df_filtered = df[df['NAME'].isin(selected_branches)].copy()
            
            # ทำความสะอาดยอดเงิน GRANDTOTAL ให้เป็นตัวเลขชัวร์ๆ
            df_filtered['GRANDTOTAL'] = df_filtered['GRANDTOTAL'].astype(str).str.replace(',', '').str.strip()
            df_filtered['GRANDTOTAL'] = pd.to_numeric(df_filtered['GRANDTOTAL'], errors='coerce').fillna(0)

            # --- [แก้ไขที่ 2] ยุบบิลซ้ำก่อนคำนวณยอดขายรวม ---
            col_bill = 'TRANNO' if 'TRANNO' in df_filtered.columns else None
            if col_bill:
                df_unique_bills = df_filtered.drop_duplicates(subset=[col_bill]).copy()
            else:
                df_unique_bills = df_filtered.copy()

            total_sales = df_unique_bills['GRANDTOTAL'].sum()
            total_orders = len(df_unique_bills)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("ยอดขายรวมทั้งหมด (บาท)", f"฿{total_sales:,.2f}")
            col2.metric("จำนวนรายการ (บิล)", f"{total_orders:,}")
            if total_orders > 0:
                col3.metric("ยอดเฉลี่ยต่อบิล (บาท)", f"฿{(total_sales/total_orders):,.2f}")
            
            st.markdown("<br>", unsafe_allow_html=True) 

            executive_colors = ['#003f5c', '#2f4b7c', '#665191', '#a05195', '#d45087', '#f95d6a', '#ff7c43', '#ffa600']

            tab1, tab2, tab3, tab4 = st.tabs(["🏢 ยอดรวมสาขา", "📈 เทรนด์รายวัน", "📋 ตารางตัวเลข", "🍜 สินค้าขายดี"])

            with tab1:
                st.subheader("เปรียบเทียบยอดขายรายสาขา")
                # คำนวณยอดขายจาก DataFrame ที่ไม่ซ้ำบิลแล้ว
                branch_sales = df_unique_bills.groupby('NAME')['GRANDTOTAL'].sum().reset_index().sort_values('GRANDTOTAL', ascending=False)
                
                col_bar, col_pie = st.columns(2)
                chart_config = {'staticPlot': False} # เปลี่ยนเป็น False ให้คลิกดูข้อมูลบนกราฟได้
                
                with col_bar:
                    fig_bar = px.bar(branch_sales, x='NAME', y='GRANDTOTAL', color='NAME', 
                                     color_discrete_sequence=executive_colors,
                                     text_auto=',.2f', title="ยอดขาย (กราฟแท่ง)")
                    fig_bar.update_layout(showlegend=False, xaxis_title="", yaxis_title="ยอดขาย (บาท)",
                                          plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                          yaxis=dict(showgrid=True, gridcolor='#f0f2f6'))
                    st.plotly_chart(fig_bar, use_container_width=True, config=chart_config)
                    
                with col_pie:
                    fig_pie = px.pie(branch_sales, values='GRANDTOTAL', names='NAME', 
                                     color_discrete_sequence=executive_colors,
                                     title="สัดส่วนยอดขาย (กราฟโดนัท)", hole=0.45)
                    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                    fig_pie.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_pie, use_container_width=True, config=chart_config)

            with tab2:
                st.subheader("แนวโน้มการขายรายวัน")
                if 'Parsed_Date' in df_unique_bills.columns:
                    # ใช้ Parsed_Date เพราะเป็น Date ที่สมบูรณ์แล้ว
                    daily_trend = df_unique_bills.groupby('Parsed_Date')['GRANDTOTAL'].sum().reset_index()
                    daily_trend = daily_trend.sort_values('Parsed_Date')
                    
                    fig_line = px.line(daily_trend, x='Parsed_Date', y='GRANDTOTAL', markers=True, line_shape='spline') 
                    fig_line.update_traces(line_color='#2f4b7c', line_width=3, marker_size=8)
                    fig_line.update_layout(xaxis_title="วันที่", yaxis_title="ยอดขาย (บาท)",
                                           plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                           xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#f0f2f6'))
                    st.plotly_chart(fig_line, use_container_width=True)
                else:
                    st.info("ไม่มีข้อมูลวันที่สำหรับการสร้างเทรนด์")

            with tab3:
                st.subheader("รายละเอียดยอดขาย")
                display_df = branch_sales.rename(columns={'NAME': 'ชื่อสาขา', 'GRANDTOTAL': 'ยอดขายทั้งสิ้น'})
                
                display_df['ชื่อสาขา'] = display_df['ชื่อสาขา'].str.strip()
                branch_mapping = {
                    'ตลาดเทศบาล': '1. ตลาดเทศบาล',
                    'ตลาดศรีเมือง': '2. ตลาดศรีเมือง',
                    'ทุ่งปอ': '3. ทุ่งปอ',
                    'บ้านไร่': '4. บ้านไร่',
                    'ตลาดเจ้าพรหม': '5. ตลาดเจ้าพรหม',
                    'บ้านโป่ง': '6. บ้านโป่ง'
                }
                display_df['ชื่อสาขา'] = display_df['ชื่อสาขา'].replace(branch_mapping)
                display_df = display_df.sort_values('ชื่อสาขา')
                
                styled_df = (display_df.style
                             .format({'ยอดขายทั้งสิ้น': '{:,.2f}'})
                             .background_gradient(cmap='Blues', subset=['ยอดขายทั้งสิ้น']))
                st.dataframe(styled_df, use_container_width=True, hide_index=True)

            with tab4:
                st.subheader("🏆 20 อันดับสินค้าขายดี (Top 20 Products)")
                
                if df_product is not None and 'ITEMNAME' in df_product.columns and 'AMOUNT' in df_product.columns and 'BASEQUANTITY' in df_product.columns:
                    
                    col_amount, col_qty = st.columns(2)
                    chart_config_prod = {'staticPlot': True}
                    
                    # ทำความสะอาดข้อมูล AMOUNT เผื่อมีคอมม่า
                    df_product['AMOUNT'] = df_product['AMOUNT'].astype(str).str.replace(',', '').str.strip()
                    df_product['AMOUNT'] = pd.to_numeric(df_product['AMOUNT'], errors='coerce').fillna(0)
                    
                    with col_amount:
                        st.markdown("**💰 จัดอันดับตาม 'มูลค่าขาย (บาท)'**")
                        top_amount = df_product.groupby('ITEMNAME')['AMOUNT'].sum().reset_index()
                        top_amount = top_amount.sort_values('AMOUNT', ascending=False).head(20)
                        
                        fig_amount = px.bar(top_amount, x='AMOUNT', y='ITEMNAME', orientation='h',
                                          text_auto=',.2f', color='AMOUNT', color_continuous_scale='Blues')
                        
                        fig_amount.update_layout(
                            yaxis={'categoryorder':'total ascending'}, 
                            xaxis_title="มูลค่าขาย (บาท)", yaxis_title="",
                            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                            coloraxis_showscale=False, height=600 
                        )
                        st.plotly_chart(fig_amount, use_container_width=True, config=chart_config_prod)

                    with col_qty:
                        st.markdown("**📦 จัดอันดับตาม 'จำนวนที่ขาย (ชิ้น)'**")
                        df_product['BASEQUANTITY'] = pd.to_numeric(df_product['BASEQUANTITY'], errors='coerce').fillna(0)
                        top_qty = df_product.groupby('ITEMNAME')['BASEQUANTITY'].sum().reset_index()
                        top_qty = top_qty.sort_values('BASEQUANTITY', ascending=False).head(20)
                        
                        fig_qty = px.bar(top_qty, x='BASEQUANTITY', y='ITEMNAME', orientation='h',
                                          text_auto=',.0f', color='BASEQUANTITY', color_continuous_scale='Oranges')
                        
                        fig_qty.update_layout(
                            yaxis={'categoryorder':'total ascending'}, 
                            xaxis_title="จำนวนที่ขาย (ชิ้น)", yaxis_title="",
                            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                            coloraxis_showscale=False, height=600
                        )
                        st.plotly_chart(fig_qty, use_container_width=True, config=chart_config_prod)
                        
                else:
                    st.warning("⚠️ รอข้อมูลจากไฟล์ product data.CSV หรือข้อมูลคอลัมน์ไม่ครบถ้วน")
