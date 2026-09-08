# ==========================================
# 3. SIDEBAR FILTERS (อัปเดตใหม่)
# ==========================================
st.sidebar.title("🔍 เมนูกรองข้อมูล")

st.sidebar.markdown("### 📅 1. เลือกเวลาที่ต้องการดู")

# 1. กรองปี (รองรับการเลือกหลายปีพร้อมกัน 2568, 2569)
available_years = sorted([int(y) for y in df_all['Year_BE'].dropna().unique() if y > 2000], reverse=True)
if not available_years:
    available_years = [2569, 2568]
    
selected_years = st.sidebar.multiselect(
    "เลือกปี พ.ศ.:",
    options=available_years,
    default=available_years
)

# 2. กรองวัน / ช่วงเวลาด่วน
quick_time = st.sidebar.selectbox(
    "เลือกช่วงเวลาแบบด่วน:",
    ["ดูข้อมูลทั้งหมด", "วันนี้", "เมื่อวาน", "7 วันล่าสุด", "30 วันล่าสุด", "เดือนนี้", "กำหนดเอง (เลือกปฏิทิน)"]
)

start_date, end_date = None, None
if quick_time == "กำหนดเอง (เลือกปฏิทิน)":
    min_d = df_all['Parsed_Date'].min() if not df_all['Parsed_Date'].isna().all() else datetime.today()
    max_d = df_all['Parsed_Date'].max() if not df_all['Parsed_Date'].isna().all() else datetime.today()
    date_range = st.sidebar.date_input("เลือกช่วงวันที่:", [min_d, max_d])
    if len(date_range) == 2:
        start_date, end_date = date_range[0], date_range[1]

# 3. กรองเดือน
with st.sidebar.expander("➕ กรองตามเดือน (สำหรับดูข้ามปี)", expanded=False):
    month_names = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", 
                   "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
    selected_months = st.sidebar.multiselect("เลือกเดือนที่ต้องการดู:", month_names, default=[])

st.sidebar.markdown("---")
st.sidebar.markdown("### 🏬 2. เลือกสาขา")

# 4. กรองสาขา
all_branches = sorted(df_all['NAME'].dropna().unique().tolist())
if not all_branches:
    all_branches = ["ศรีเมือง", "ทุ่งปอ", "เจ้าพรหม", "บ้านไร่", "เทศบาล", "บ้านโป่ง"]

selected_branches = st.sidebar.multiselect(
    "กด X เพื่อลบ หรือพิมพ์เพื่อหาสาขา:",
    options=all_branches,
    default=all_branches
)

st.sidebar.markdown("---")
st.sidebar.caption("Powered by peter pak: v.10.0.0 (API Edition)")

# ==========================================
# 4. FILTERING LOGIC (ประมวลผลตัวกรอง)
# ==========================================
df_filtered = df_all.copy()

# กรอง 1: ปี พ.ศ.
if selected_years:
    df_filtered = df_filtered[df_filtered['Year_BE'].isin(selected_years)]
else:
    df_filtered = df_filtered.iloc[0:0] # คืนค่าว่างถ้าไม่เลือกปีเลย

# กรอง 2: สาขา
if selected_branches:
    df_filtered = df_filtered[df_filtered['NAME'].isin(selected_branches)]
else:
    df_filtered = df_filtered.iloc[0:0]

# กรอง 3: เดือน
if selected_months:
    month_map = {m: i+1 for i, m in enumerate(month_names)}
    target_month_nums = [month_map[m] for m in selected_months if m in month_map]
    df_filtered = df_filtered[df_filtered['Parsed_Date'].dt.month.isin(target_month_nums)]

# กรอง 4: วัน / ช่วงเวลาแบบด่วน
if quick_time != "ดูข้อมูลทั้งหมด" and not df_filtered.empty:
    # ใช้วันที่อัปเดตล่าสุดจากฐานข้อมูลรวม เพื่อไม่ให้เกิด Error เวลาเลือกข้ามปี/เดือน
    global_max_date = df_all['Parsed_Date'].max()
    if pd.isna(global_max_date):
        global_max_date = datetime.today()
        
    if quick_time == "วันนี้":
        df_filtered = df_filtered[df_filtered['Parsed_Date'].dt.date == global_max_date.date()]
    elif quick_time == "เมื่อวาน":
        target_date = (global_max_date - timedelta(days=1)).date()
        df_filtered = df_filtered[df_filtered['Parsed_Date'].dt.date == target_date]
    elif quick_time == "7 วันล่าสุด":
        target_date = (global_max_date - timedelta(days=7)).date()
        df_filtered = df_filtered[df_filtered['Parsed_Date'].dt.date >= target_date]
    elif quick_time == "30 วันล่าสุด":
        target_date = (global_max_date - timedelta(days=30)).date()
        df_filtered = df_filtered[df_filtered['Parsed_Date'].dt.date >= target_date]
    elif quick_time == "เดือนนี้":
        df_filtered = df_filtered[
            (df_filtered['Parsed_Date'].dt.month == global_max_date.month) & 
            (df_filtered['Parsed_Date'].dt.year == global_max_date.year)
        ]
    elif quick_time == "กำหนดเอง (เลือกปฏิทิน)" and start_date and end_date:
        df_filtered = df_filtered[
            (df_filtered['Parsed_Date'].dt.date >= start_date) & 
            (df_filtered['Parsed_Date'].dt.date <= end_date)
        ]
