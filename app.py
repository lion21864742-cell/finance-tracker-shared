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
    
# 支出預算初始架構
if "my_budget" not in st.session_state:
    st.session_state.my_budget = {
       "飲食": 1000.0, "租金": 1000.0, "交通": 1000.0, 
        "家用品": 1000.0, "娛樂": 1000.0, "園藝": 1000.0, "電費": 1000.0,
        "寵物用品": 1000.0, "其他": 500.0

    }

# 收入分類初始架構
if "my_income_categories" not in st.session_state:
    st.session_state.my_income_categories = ["薪資", "投資所得", "被動收入", "其他收入"]

# 🔥 核心修正：讓系統初始數據完美對齊新的收入分類，確保圓餅圖一打開就100%顯示！
if "my_logs" not in st.session_state:
    st.session_state.my_logs = [
        {"日期": "2026/05/01", "類型": "收入 📥", "分類": "薪資", "子分類": "月薪", "項目": "公司發薪", "金額": 25000.0, "帳戶/備註": "銀行儲蓄 🏦"},
        {"日期": "2026/05/10", "類型": "收入 📥", "分類": "投資所得", "子分類": "股票派息", "項目": "港股收息", "金額": 3500.0, "帳戶/備註": "銀行儲蓄 🏦"},
        {"日期": "2026/05/15", "類型": "收入 📥", "分類": "被動收入", "子分類": "網店/租金", "項目": "副業進帳", "金額": 1500.0, "帳戶/備註": "現金帳戶 🟢"},
        {"日期": "2026/05/20", "類型": "支出 💸", "分類": "飲食", "子分類": "外食", "項目": "歡迎使用全功能系統", "金額": 120.0, "帳戶/備註": "現金帳戶 🟢"}
    ]

# ==================== 3. 核心財務數據即時計算 ====================
total_assets = sum(st.session_state.my_assets.values())
total_liabilities = sum(st.session_state.my_liabilities.values())
net_worth = total_assets - total_liabilities

# 轉成 DataFrame 開始精確統計收入與支出
df_current_logs = pd.DataFrame(st.session_state.my_logs)
total_actual_income = 0.0
total_actual_expense = 0.0

actual_spent_map = {cat: 0.0 for cat in st.session_state.my_budget.keys()}
actual_income_map = {cat: 0.0 for cat in st.session_state.my_income_categories}

if not df_current_logs.empty:
    df_current_logs["金額"] = pd.to_numeric(df_current_logs["金額"], errors='coerce').fillna(0.0)
    
    # 1. 統計收入
    df_income_only = df_current_logs[df_current_logs["類型"] == "收入 📥"]
    total_actual_income = float(df_income_only["金額"].sum())
    for cat in actual_income_map.keys():
        actual_income_map[cat] = float(df_income_only[df_income_only["分類"] == cat]["金額"].sum())
        
    # 2. 統計支出
    df_expenses_only = df_current_logs[df_current_logs["類型"] == "支出 💸"]
    total_actual_expense = float(df_expenses_only["金額"].sum())
    for cat in actual_spent_map.keys():
        actual_spent_map[cat] = float(df_expenses_only[df_expenses_only["分類"] == cat]["金額"].sum())

# 計算儲蓄指標
expected_savings = total_actual_income - total_actual_expense
savings_rate = (expected_savings / total_actual_income * 100) if total_actual_income > 0 else 0.0

# ==================== 4. 網頁 UI 視覺介面 ====================
st.title("💎 CLOUD FINANCE MASTER PLAN 2026")
st.caption("🚀 雲端收支全功能分享版 — 已完美加入「投資所得、被動收入」分類架構與雙圓餅圖分析")
st.markdown("---")

# 頂部核心財務看板
m_col1, m_col2, m_col3, m_col4 = st.columns(4)
m_col1.metric("💰 本月總收入 (Income)", f"${total_actual_income:,.2f}")
m_col2.metric("💸 本月總支出 (Actual)", f"${total_actual_expense:,.2f}")
m_col3.metric("📈 預計儲蓄 (Savings)", f"${expected_savings:,.2f}", delta=f"儲蓄率 {savings_rate:.1f}%")
m_col4.metric("👑 當前淨身家 (Net Worth)", f"${net_worth:,.2f}")
st.markdown("---")

# 側邊欄：導覽選單
st.sidebar.title(" Menu 功能選單")
page_choice = st.sidebar.radio("切換功能頁面", [
    "📊 財務總覽 & 預算監控", 
    "💸 每日單筆記帳 (收/支)", 
    "📤 批量上載 Excel/CSV 檔案",
    "⚙️ 自訂您的資產/預算初始值"
])

st.sidebar.markdown("---")
st.sidebar.info("💡 **提示：** 本系統為獨立安全空間，每個人打開網址看到的都是自己專屬輸入的數據，互不干涉！")

# ==================== 頁面邏輯切換 ====================

# ------ 頁面 1: 財務總覽 & 預算監控 ------
if page_choice == "📊 財務總覽 & 預算監控":
    chart_col, budget_col = st.columns([1, 1.2])
    
    with chart_col:
        # 🟢 收入來源分析圖
        st.subheader("💰 本月收入來源分析")
        fig_inc_data = pd.DataFrame(list(actual_income_map.items()), columns=["收入分類", "金額"])
        fig_inc_data = fig_inc_data[fig_inc_data["金額"] > 0]
        
        if not fig_inc_data.empty:
            fig_inc = px.pie(fig_inc_data, values="金額", names="收入分類", hole=0.4, color_discrete_sequence=px.colors.sequential.Solar)
            fig_inc.update_layout(template="plotly_dark", margin=dict(l=10, r=10, t=15, b=15), height=260)
            st.plotly_chart(fig_inc, use_container_width=True)
        else:
            st.info("💡 尚無實際收入數據。")

        st.markdown("<br>", unsafe_allow_html=True)

        # 🔴 支出分類比例圖
        st.subheader("📊 本月開支分類比例")
        if total_actual_expense > 0:
            fig_data = pd.DataFrame(list(actual_spent_map.items()), columns=["分類", "實際支出"])
            fig_data = fig_data[fig_data["實際支出"] > 0]
            fig = px.pie(fig_data, values="實際支出", names="分類", hole=0.4, color_discrete_sequence=px.colors.sequential.Mint)
            fig.update_layout(template="plotly_dark", margin=dict(l=10, r=10, t=15, b=15), height=260)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("💡 尚無支出數據，圓餅圖將於您記帳後自動呈現。")
            
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
        st.dataframe(pd.DataFrame(budget_rows), use_container_width=True, hide_index=True, height=580)

    st.markdown("---")
    st.subheader("📋 您的歷史收支明細報表")
    if st.session_state.my_logs:
        st.dataframe(pd.DataFrame(st.session_state.my_logs).iloc[::-1], use_container_width=True, hide_index=True)
        csv_data = pd.DataFrame(st.session_state.my_logs).to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 匯出這份明細成 Excel/CSV 下載", data=csv
