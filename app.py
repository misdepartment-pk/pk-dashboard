import streamlit as st
import pandas as pd
import requests

# ดึงค่าคอนฟิกจาก Secrets
SENIORSOFT_CFG = st.secrets.get("seniorsoft", {})
SERVER_URL = SENIORSOFT_CFG.get("SERVER_URL", "https://p1.seniorsoft.com/promaxxapi")
MERCHANT_ID = SENIORSOFT_CFG.get("MERCHANT_ID", "88821678")
BRANCH_ID = SENIORSOFT_CFG.get("BRANCH_ID", "PK000")
TOKEN = SENIORSOFT_CFG.get("TOKEN", "")
AUTH_TYPE = SENIORSOFT_CFG.get("AUTH_TYPE", "BlueId")

@st.cache_data(ttl=300)  # ดึงข้อมูลใหม่ทุกๆ 5 นาที
def load_data_from_seniorsoft():
    """ดึงข้อมูลยอดขายและรายการสินค้าจาก Seniorsoft Promaxx API"""
    headers = {
        "Authorization": f"{AUTH_TYPE} {TOKEN}",
        "MerchantID": MERCHANT_ID,
        "BranchID": BRANCH_ID,
        "Content-Type": "application/json"
    }
    
    try:
        # 1. ดึงข้อมูลรายการขาย (Sales Data)
        sales_response = requests.get(f"{SERVER_URL}/sales", headers=headers, timeout=15)
        sales_response.raise_for_status()
        sales_json = sales_response.json()
        
        df_sales = pd.DataFrame(sales_json.get('data', sales_json if isinstance(sales_json, list) else []))
        
        # 2. ดึงข้อมูลสินค้าขายดี (Product Data)
        prod_response = requests.get(f"{SERVER_URL}/products", headers=headers, timeout=15)
        prod_response.raise_for_status()
        prod_json = prod_response.json()
        
        df_products = pd.DataFrame(prod_json.get('data', prod_json if isinstance(prod_json, list) else []))
        
        # --- แปลงโครงสร้างข้อมูลให้ตรงกับ Dashboard ---
        if not df_sales.empty:
            date_col = next((c for c in ['doc_date', 'TRANDATE', 'Parsed_Date'] if c in df_sales.columns), None)
            if date_col:
                df_sales['Parsed_Date'] = pd.to_datetime(df_sales[date_col], errors='coerce')
                
            sales_col = next((c for c in ['grand_total', 'GRANDTOTAL', 'amount'] if c in df_sales.columns), None)
            if sales_col:
                df_sales['GRANDTOTAL'] = pd.to_numeric(df_sales[sales_col], errors='coerce').fillna(0)
                
            branch_col = next((c for c in ['branch_name', 'NAME', 'branch_id'] if c in df_sales.columns), None)
            if branch_col:
                df_sales['NAME'] = df_sales[branch_col].fillna(BRANCH_ID)
            else:
                df_sales['NAME'] = BRANCH_ID
                
            df_sales['ORDER_COUNT'] = 1

        if not df_products.empty:
            date_col_p = next((c for c in ['doc_date', 'TRANDATE', 'Parsed_Date'] if c in df_products.columns), None)
            if date_col_p:
                df_products['Parsed_Date'] = pd.to_datetime(df_products[date_col_p], errors='coerce')
                
            df_products['NAME'] = df_products.get('branch_name', BRANCH_ID)
            df_products['ITEMNAME_CLEAN'] = df_products.get('item_name', df_products.get('ITEMNAME', 'ไม่ระบุสินค้า'))
            df_products['QTY_CLEAN'] = pd.to_numeric(df_products.get('qty', df_products.get('QTY', 0)), errors='coerce').fillna(0)
            df_products['AMT_CLEAN'] = pd.to_numeric(df_products.get('amount', df_products.get('AMOUNT', 0)), errors='coerce').fillna(0)

        return df_sales, df_products

    except requests.exceptions.RequestException as e:
        st.error(f"❌ ไม่สามารถเชื่อมต่อ Seniorsoft API ได้: {e}")
        return pd.DataFrame(), pd.DataFrame()

# เรียกใช้งานแทน load_and_prep_data เดิม
df_master, df_product_master = load_data_from_seniorsoft()
