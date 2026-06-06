import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ==================== 1. 網頁全域配置 ====================
st.set_page_config(page_title="💎 Cloud Finance Ultimate 2026", page_icon="💰", layout="wide")

# ==================== 2. 多用戶獨立狀態初始化引擎 ====================
if "my_assets" not in st.session_state:
    st.session_state.my_assets = {"現金帳戶 🟢": 10000.0, "銀行儲蓄 🏦": 50000.0}
if "my_liabilities" not in st.session_state:
    st.session_state.my_liabilities = {"信用卡欠款 🔴": 2000.0}
    
# 這裡就是你可以隨時在網頁上修改的 Budget 初始值
if "my_budget" not in st.session_state:
    st.session_state.my_budget = {
        "飲食": 3000.0, "租金": 7700.0, "交通": 1700.0, "化妝品": 1000.0,
        "家用品": 500.0, "娛樂": 700.0, "園藝": 300.0, "電費": 1000.0,
        "貓用品": 500.0, "其他": 500.0
    }
if "my_logs" not in st.session_state:
    st.session_state.my_logs = [
        {"日期": "2026/05/20", "分類": "飲食", "子分類": "外食", "項目": "歡迎使用雲端記帳系統", "金額": 0.0, "帳戶/備註": "系統初始"}
    ]

# ==================== 3. 核心財務數據即時計算 ====================
total_assets = sum(st.session_state.my_assets.values())
total_liabilities = sum(st.session_state.my_liabilities.values())
net_worth = total_assets - total_liabilities

# 統計已使用的預算
df_current_logs = pd.DataFrame(st.session_state.my_logs)
actual_spent_map = {cat: 0.0 for cat in st.session_state.my_budget.keys()}

if not df_current_logs.empty:
    df_current_logs["金額"] = pd.to_numeric(df_current_logs["金額"], errors='coerce').fillna(0.0)
    for cat in actual_spent_map.keys():
        actual_spent_map[cat] = float(df_current_logs[df_current_logs["分類"] == cat]["金額"].sum())

total_actual_expense = sum(actual_spent_map.values())

# ==================== 4. 網頁 UI 視覺介面 ====================
st.title("💎 CLOUD FINANCE MASTER PLAN 2026")
st.caption("🚀 雲端多用戶分享版 — 本網頁不會儲存您的私密隱私，每次打開皆為獨立全新專屬記帳空間")
st.markdown("---")

# 頂部三大看板
col1, col2, col3 = st.columns(3)
col1.metric("👑 當前淨身家 (Net Worth)", f"${net_worth:,.2f}")
col2.metric("📊 本月實際總支出", f"${total_actual_expense:,.2f}")
col3.metric("🔴 總負債庫存", f"${total_liabilities:,.2f}")
st.markdown("---")

# 側邊欄：導覽選單
st.sidebar.title(" Menu 功能選單")
page_choice = st.sidebar.radio("切換功能頁面", [
    "📊 財務總覽 & 預算監控", 
    "💸 每日單筆記帳", 
    "📤 批量上載 Excel/CSV 檔案",
    "⚙️ 自訂您的資產/預算初始值"
])

st.sidebar.markdown("---")
st.sidebar.info("""
💡 **給使用者的提示：**
本系統採用瀏覽器內存技術，您可以放心分享此網址給其他人。每個打開此連結的人看到的都是自己輸入的數據，互不干涉！
""")

# ==================== 頁面邏輯切換 ====================

# ------ 頁面 1: 財務總覽 & 預算監控 ------
if page_choice == "📊 財務總覽 & 預算監控":
    chart_col, budget_col = st.columns([1, 1.2])
    
    with chart_col:
        st.subheader("📊 支出分類比例")
        if total_actual_expense > 0:
            fig_data = pd.DataFrame(list(actual_spent_map.items()), columns=["分類", "實際支出"])
            fig_data = fig_data[fig_data["實際支出"] > 0]
            fig = px.pie(fig_data, values="實際支出", names="分類", hole=0.4, color_discrete_sequence=px.colors.sequential.Mint)
            fig.update_layout(template="plotly_dark", margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("💡 尚無支出數據，請前往「每日單筆記帳」或「批量上載」匯入您的資料。")
            
    with budget_col:
        st.subheader("🎯 Budget Tracker 預算進度條")
        budget_rows = []
        for cat, b_amount in st.session_state.my_budget.items():
            a_amount = actual_spent_map.get(cat, 0.0)
            remaining = b_amount - a_amount
            use_rate = (a_amount / b_amount) * 100 if b_amount > 0 else 0.0
            
            if use_rate >= 100: status_icon = "🔴 已超支"
            elif use_rate >= 80: status_icon = "🟡 預警"
            else: status_icon = "🟢 正常"
            
            budget_rows.append({
                "分類 (Category)": cat, "預算 (Budget)": f"${b_amount:,.1f}", "已使用 (Actual)": f"${a_amount:,.1f}",
                "剩餘 (Remaining)": f"${remaining:,.1f}", "使用率": f"{use_rate:.1f}%", "狀態": status_icon
            })
        st.dataframe(pd.DataFrame(budget_rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("📋 您的歷史收支明細報表")
    if st.session_state.my_logs:
        st.dataframe(pd.DataFrame(st.session_state.my_logs).iloc[::-1], use_container_width=True, hide_index=True)
        csv_data = pd.DataFrame(st.session_state.my_logs).to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 匯出這份明細成 Excel/CSV 下載", data=csv_data, file_name="My_Finance_Log.csv", mime="text/csv")

# ------ 頁面 2: 每日單筆記帳 ------
elif page_choice == "💸 每日單筆記帳":
    st.subheader("📥 填寫日常單筆開銷")
    all_accs = list(st.session_state.my_assets.keys()) + list(st.session_state.my_liabilities.keys())
    
    with st.form("share_single_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            in_date = st.date_input("日期", datetime.now())
            in_cat = st.selectbox("分類", list(st.session_state.my_budget.keys()))
        with c2:
            in_subcat = st.text_input("子分類（如：外食、零食）")
            in_title = st.text_input("項目名稱（如：譚仔、元氣）")
        with c3:
            in_amount = st.number_input("金額 ($)", min_value=0.0, step=1.0)
            in_acc = st.selectbox("扣款帳戶/備註", all_accs)
            
        submit_btn = st.form_submit_button("確認記入我的歷史帳本 🚀")
        if submit_btn and in_amount > 0:
            if in_acc in st.session_state.my_assets: st.session_state.my_assets[in_acc] -= in_amount
            elif in_acc in st.session_state.my_liabilities: st.session_state.my_liabilities[in_acc] += in_amount
            
            st.session_state.my_logs.append({
                "日期": in_date.strftime("%Y/%m/%d"), "分類": in_cat, "子分類": in_subcat, "項目": in_title, "金額": in_amount, "帳戶/備註": in_acc
            })
            st.success(f"✅ 成功記帳：{in_title} ${in_amount}")
            st.rerun()

# ------ 頁面 3: 批量上載 Excel/CSV 檔案 ------
elif page_choice == "📤 批量上載 Excel/CSV 檔案":
    st.subheader("📤 批量匯入您現有的記帳表格")
    st.markdown("您可以直接將您常用的記帳 Excel/CSV 檔案拖曳至下方。系統支援自動對齊『日期 (Date)』, 『分類』, 『項目』, 『金額』欄位。")
    
    upload_file = st.file_uploader("上傳您的檔案", type=["csv", "xlsx"])
    if upload_file is not None:
        try:
            df_imported
