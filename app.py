with tab_table:
    if not df_filtered.empty:
        st.markdown("##### 📋 สรุปข้อมูลยอดขาย (รวมยอดตามวันและสาขา)")
        df_tab3 = df_filtered.loc[:, ~df_filtered.columns.duplicated()].copy()
        
        # จัดกลุ่มและรวมยอด
        summary_table = df_tab3.groupby(['Parsed_Date', 'NAME'], as_index=False)[['GRANDTOTAL', 'ORDER_COUNT']].sum()
        summary_table.rename(columns={'GRANDTOTAL': 'ยอดขายรวม', 'ORDER_COUNT': 'จำนวนบิล'}, inplace=True)
        summary_table['ยอดเฉลี่ย/บิล'] = np.where(summary_table['จำนวนบิล'] > 0, summary_table['ยอดขายรวม'] / summary_table['จำนวนบิล'], 0)
        
        # จัดเรียงข้อมูลจากมากไปน้อย
        summary_table = summary_table.sort_values(by=['Parsed_Date', 'ยอดขายรวม'], ascending=[False, False])
        
        # --- ส่วนที่แก้ไข: รีเซ็ตลำดับตัวเลขใหม่ให้เรียง 1, 2, 3... ---
        summary_table = summary_table.reset_index(drop=True)
        summary_table.index = summary_table.index + 1
        summary_table = summary_table.reset_index().rename(columns={'index': 'ลำดับ'})
        # ---------------------------------------------------
        
        # จัดฟอร์แมตวันที่
        if not summary_table['Parsed_Date'].isna().all(): 
            summary_table['Parsed_Date'] = summary_table['Parsed_Date'].dt.strftime('%d/%m/%Y')
            
        # เปลี่ยนชื่อคอลัมน์สำหรับแสดงผล
        summary_table.rename(columns={'Parsed_Date': 'วันที่', 'NAME': 'สาขา', 'ยอดขายรวม': 'ยอดขายรวม (บาท)', 'จำนวนบิล': 'จำนวนบิล (ใบ)', 'ยอดเฉลี่ย/บิล': 'เฉลี่ย/บิล (บาท)'}, inplace=True)
        
        # แสดงตาราง (เพิ่ม hide_index=True เพื่อซ่อน index สีเทาด้านหน้าสุด)
        st.dataframe(
            summary_table.style.format({
                'ยอดขายรวม (บาท)': '฿{:,.2f}', 
                'จำนวนบิล (ใบ)': '{:,.0f}', 
                'เฉลี่ย/บิล (บาท)': '฿{:,.2f}'
            }), 
            use_container_width=True,
            hide_index=True 
        )
    else: 
        st.info("ไม่พบข้อมูล")
