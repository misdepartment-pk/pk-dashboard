import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# ดึงค่า Secrets
SENIORSOFT_CFG = st.secrets.get("seniorsoft", {})
SERVER_URL = SENIORSOFT_CFG.get("SERVER_URL", "https://p1.seniorsoft.com/promaxxapi")
MERCHANT_ID = SENIORSOFT_CFG.get("MERCHANT_ID", "88821678")
BRANCH_ID = SENIORSOFT_CFG.get("BRANCH_ID", "PK000")
TOKEN = SENIORSOFT_CFG.get("TOKEN", "")
AUTH_TYPE = SENIORSOFT_CFG.get("AUTH_TYPE", "BlueId")

@st.cache_data(ttl=180)  # รีเฟรชข้อมูลทุก 3 นาที
def load_data_from_seniorsoft():
    headers = {
        "Authorization": f"{AUTH_TYPE} {TOKEN}",
        "MerchantID": MERCHANT_ID,
        "BranchID": BRANCH_ID,
        "Content-Type": "application/json"
    }
    
    # กำหนดช่วงวันที่ดึงข้อมูล (ย้อนหลัง 30 วัน จนถึงปัจจุบัน)
    today_str = datetime.now().strftime("%Y-%m-%d")
    start_str = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    params = {
        "startDate": start_str,
        "endDate": today_str
    }
    
    try:
        # 1. ดึงข้อมูลยอดขาย
        sales_res = requests.get(f"{SERVER_URL}/sales", headers=headers, params=params, timeout=15)
        
        if sales_res.status_code != 200:
            st.warning(f"⚠️ Seniorsoft API ตอบกลับด้วย Status Code: {sales_res.status_code}")
            return pd.DataFrame(), pd.DataFrame()
            
        sales_json = sales_res.json()
        data_list = sales_json.get('data', sales_json if isinstance(sales_json, list) else [])
        df_sales = pd.DataFrame(data_list)
        
        # 2. ดึงข้อมูลสินค้า
        prod_res = requests.get(f"{SERVER_URL}/products", headers=headers, params=params, timeout=15)
        prod_json = prod_res.json() if prod_res.status_code == 200 else {}
        prod_list = prod_json.get('data', prod_json if isinstance(prod_json, list) else [])
        df_products = pd.DataFrame(prod_list)

        # --- แปลงข้อมูลตารางยอดขาย ---
        if not df_sales.empty:
            # แปลงคอลัมน์ให้อยู่ในรูปแบบเดียวกัน (รองรับทั้งพิมพ์ใหญ่และพิมพ์เล็ก)
            cols = {col.lower(): col for col in df_sales.columns}
            
            date_col = cols.get('docdate') or cols.get('doc_date') or cols.get('trandate') or cols.get('parsed_date')
            if date_col:
                df_sales['Parsed_Date'] = pd.to_datetime(df_sales[date_col], errors='coerce')
                
            grand_col = cols.get('grandtotal') or cols.get('grand_total') or cols.get('amount')
            if grand_col:
                df_sales['GRANDTOTAL'] = pd.to_numeric(df_sales[grand_col], errors='coerce').fillna(0)
            else:
                df_sales['GRANDTOTAL'] = 0.0
                
            branch_col = cols.get('branchname') or cols.get('branch_name') or cols.get('branchid') or cols.get('branch_id')
            if branch_col:
                df_sales['NAME'] = df_sales[branch_col].fillna('ทุ่งปอ') # หรือสาขาเริ่มต้นของคุณ
            else:
                df_sales['NAME'] = 'ทุ่งปอ'  # ตั้งค่าเริ่มต้นให้ตรงกับตัวเลือกใน Sidebar
                
            df_sales['ORDER_COUNT'] = 1

        # --- แปลงข้อมูลตารางสินค้า ---
        if not df_products.empty:
            p_cols = {col.lower(): col for col in df_products.columns}
            
            p_date = p_cols.get('docdate') or p_cols.get('doc_date') or p_cols.get('trandate')
            if p_date:
                df_products['Parsed_Date'] = pd.to_datetime(df_products[p_date], errors='coerce')
                
            p_item = p_cols.get('itemname') or p_cols.get('item_name') or p_cols.get('productname')
            df_products['ITEMNAME_CLEAN'] = df_products[p_item] if p_item else 'ไม่ระบุชื่อสินค้า'
            
            p_qty = p_cols.get('qty') or p_cols.get('quantity')
            df_products['QTY_CLEAN'] = pd.to_numeric(df_products[p_qty], errors='coerce').fillna(0) if p_qty else 0
            
            p_amt = p_cols.get('amount') or p_cols.get('totalamount')
            df_products['AMT_CLEAN'] = pd.to_numeric(df_products[p_amt], errors='coerce').fillna(0) if p_amt else 0
            
            df_products['NAME'] = df_products.get('branch_name', 'ทุ่งปอ')

        return df_sales, df_products

    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาดในการดึงข้อมูลจาก Seniorsoft: {e}")
        return pd.DataFrame(), pd.DataFrame()

# เรียกใช้งานฟังก์ชัน
df_master, df_product_master = load_data_from_seniorsoft()
