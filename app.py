# ------------------------------------------
# แสดงตัวชี้วัด (Metrics) 3 รายการ
# ------------------------------------------
total_sales = df_filtered['GRANDTOTAL'].sum()
total_bills = len(df_filtered)
avg_per_bill = total_sales / total_bills if total_bills > 0 else 0

# คำนวณ % การเติบโต (Growth) เปรียบเทียบกับช่วงเวลาก่อนหน้า
current_time_th = datetime.utcnow() + timedelta(hours=7)
today_date = current_time_th.date()
prev_sales = 0
compare_text = ""

if quick_time == "ใช้วันที่จาก Date Navigator":
    prev_date = st.session_state.nav_date - timedelta(days=1)
    prev_sales = df_all[(df_all['Parsed_Date'].dt.date == prev_date) & (df_all['NAME'].isin(selected_branches))]['GRANDTOTAL'].sum()
    compare_text = "เทียบกับวันก่อนหน้า"
elif quick_time == "วันนี้":
    prev_date = today_date - timedelta(days=1)
    prev_sales = df_all[(df_all['Parsed_Date'].dt.date == prev_date) & (df_all['NAME'].isin(selected_branches))]['GRANDTOTAL'].sum()
    compare_text = "เทียบกับวันก่อนหน้า"
elif quick_time == "เมื่อวาน":
    prev_date = today_date - timedelta(days=2)
    prev_sales = df_all[(df_all['Parsed_Date'].dt.date == prev_date) & (df_all['NAME'].isin(selected_branches))]['GRANDTOTAL'].sum()
    compare_text = "เทียบกับวันก่อนหน้า"
elif quick_time == "7 วันล่าสุด":
    prev_start = today_date - timedelta(days=14)
    prev_end = today_date - timedelta(days=8)
    prev_sales = df_all[(df_all['Parsed_Date'].dt.date >= prev_start) & (df_all['Parsed_Date'].dt.date <= prev_end) & (df_all['NAME'].isin(selected_branches))]['GRANDTOTAL'].sum()
    compare_text = "เทียบกับ 7 วันก่อน"
elif quick_time == "30 วันล่าสุด":
    prev_start = today_date - timedelta(days=60)
    prev_end = today_date - timedelta(days=31)
    prev_sales = df_all[(df_all['Parsed_Date'].dt.date >= prev_start) & (df_all['Parsed_Date'].dt.date <= prev_end) & (df_all['NAME'].isin(selected_branches))]['GRANDTOTAL'].sum()
    compare_text = "เทียบกับ 30 วันก่อน"
elif quick_time == "เดือนนี้":
    prev_month = today_date.replace(day=1) - timedelta(days=1)
    prev_sales = df_all[(df_all['Parsed_Date'].dt.month == prev_month.month) & (df_all['Parsed_Date'].dt.year == prev_month.year) & (df_all['NAME'].isin(selected_branches))]['GRANDTOTAL'].sum()
    compare_text = "เทียบกับเดือนที่แล้ว"
else:
    # หากเลือกแบบอื่น ให้ดึงยอดขายของวันแรกสุดในระบบ (เช่น 05/08/2026) มาเป็นฐานเปรียบเทียบ
    first_date = df_all['Parsed_Date'].min()
    if pd.notnull(first_date):
        prev_sales = df_all[(df_all['Parsed_Date'].dt.date == first_date.date()) & (df_all['NAME'].isin(selected_branches))]['GRANDTOTAL'].sum()
        compare_text = f"เทียบกับวันแรก ({first_date.strftime('%d/%m/%Y')})"
    else:
        compare_text = "เทียบกับวันแรก"

# สร้าง HTML สำหรับแสดงผล % Growth
if prev_sales > 0:
    growth_pct = ((total_sales - prev_sales) / prev_sales) * 100
    if growth_pct > 0:
        growth_html = f'<div style="color: #10B981; font-size: 15px; font-weight: 600; margin-top: 5px;">▲ +{growth_pct:,.1f}% <span style="font-size: 12px; color: #94a3b8; font-weight: normal;">{compare_text}</span></div>'
    elif growth_pct < 0:
        growth_html = f'<div style="color: #EF4444; font-size: 15px; font-weight: 600; margin-top: 5px;">▼ {growth_pct:,.1f}% <span style="font-size: 12px; color: #94a3b8; font-weight: normal;">{compare_text}</span></div>'
    else:
        growth_html = f'<div style="color: #64748b; font-size: 15px; font-weight: 600; margin-top: 5px;">- 0.0% <span style="font-size: 12px; color: #94a3b8; font-weight: normal;">{compare_text}</span></div>'
else:
    if total_sales > 0:
        growth_html = f'<div style="color: #10B981; font-size: 15px; font-weight: 600; margin-top: 5px;">▲ +100% <span style="font-size: 12px; color: #94a3b8; font-weight: normal;">{compare_text}</span></div>'
    else:
        growth_html = f'<div style="color: #94a3b8; font-size: 12px; margin-top: 5px;">(ไม่มีข้อมูลยอดขายช่วงก่อนหน้าให้เปรียบเทียบ)</div>'

m1, m2, m3 = st.columns(3)

with m1:
    st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">ยอดขายรวมทั้งหมด (บาท)</div>
            <div class="metric-value">฿{total_sales:,.2f}</div>
            {growth_html}
        </div>
    ''', unsafe_allow_html=True)

with m2:
    st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">จำนวนบิล (นับจากจำนวนบรรทัด)</div>
            <div class="metric-value">{total_bills:,}</div>
        </div>
    ''', unsafe_allow_html=True)

with m3:
    st.markdown(f'''
        <div class="metric-card">
            <div class="metric-label">ยอดเฉลี่ยต่อบิล (บาท)</div>
            <div class="metric-value">฿{avg_per_bill:,.2f}</div>
        </div>
    ''', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
