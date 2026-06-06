import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ==================== 1. 網頁全域配置 ====================
st.set_page_config(page_title="💎 Cloud Finance Ultimate 2026", page_icon="💰", layout="wide")

# ==================== 2. 獨立狀態初始化引擎 ====================
if "my_assets" not in st.session_state:
    st.session_state.my_assets = {"現金帳戶 🟢": 15000.0, "銀行儲蓄 🏦": 65000.0}
if "my_liabilities" not in st.session_state:
    st.session_state.my_liabilities = {"信用卡欠款 🔴": 0.0}
    
# 所有初始預算金額強制設為 float 浮點數，防止 Streamlit MixedNumericTypesError 報錯
if "my_budget" not in st.session_state:
    st.session_state.my_budget = {
        "飲食": 3000.0, "租金": 7700.0, "交通": 1700.0, "化妝品": 1000.0,
        "家用品": 500.0, "娛樂": 700.0, "園藝": 300.0, "電費": 1000.0,
        "貓用品": 500.0, "其他": 500.0
    }

if "my_income_categories" not in st.session_state:
    st.session_state.my_income_categories = ["薪資", "投資所得", "被動收入", "其他收入"]

# 導入真實流水帳明細（已嚴格檢查字典語法與引號、冒號閉合）
if "my_logs" not in st.session_state:
    st.session_state.my_logs = [
        {"日期": "2026/05/01", "類型": "收入 📥", "分類": "薪資", "子分類": "月薪", "項目": "公司發薪", "金額": 25000.0, "帳戶/備註": "銀行儲蓄 🏦"},
        {"日期": "2026/05/10", "類型": "收入 📥", "分類": "投資所得", "子分類": "股票派息", "項目": "港股收息", "金額": 3500.0, "帳戶/備註": "銀行儲蓄 🏦"},
        {"日期": "2026/05/15", "類型": "收入 📥", "分類": "被動收入", "子分類": "網店/租金", "項目": "副業進帳", "金額": 1500.0, "帳戶/備註": "現金帳戶 🟢"},
        {"日期": "2026/05/01", "類型": "支出 💸", "分類": "租金", "子分類": "住屋", "項目": "每月固定租金支出", "金額": 7700.0, "帳戶/備註": "銀行儲蓄 🏦"},
        {"日期": "2026/05/05", "類型": "支出 💸", "分類": "交通", "子分類": "特別專款", "項目": "特別交通專款", "金額": 1000.0, "帳戶/備註": "現金帳戶 🟢"},
        {"日期": "2026/05/08", "類型": "支出 💸", "分類": "化妝品", "子分類": "子妝", "項目": "專櫃美妝粉餅", "金額": 880.0, "帳戶/備註": "信用卡欠款 🔴"},
        {"日期": "2026/05/12", "類型": "支出 💸", "分類": "電費", "子分類": "公用事業", "項目": "電費（2個月一次）", "金額": 864.0, "帳戶/備註": "銀行儲蓄 🏦"},
        {"日期": "2026/05/14", "類型": "支出 💸", "分類": "娛樂", "子分類": "玩具", "項目": "潮流公仔 Toy", "金額": 517.8, "帳戶/備註": "現金帳戶 🟢"},
        {"日期": "2026/05/16", "類型": "支出 💸", "分類": "其他", "子分類": "服飾", "項目": "舒適睡衣", "金額": 188.0, "帳戶/備註": "現金帳戶 🟢"},
        {"日期": "2026/05/16", "類型": "支出 💸", "分類": "飲食", "子分類": "外食", "項目": "元氣壽司 / Dinner", "金額": 182.6, "帳戶/備註": "現金帳戶 🟢"},
        {"日期": "2026/05/17", "類型": "支出 💸", "分類": "飲食", "子分類": "食材", "項目": "街市/超市面包食材", "金額": 1500.0, "帳戶/備註": "現金帳戶 🟢"},
        {"日期": "2026/05/17", "類型": "支出 💸", "分類": "園藝", "子分類": "花與花盆", "項目": "花同花盤資材", "金額": 105.0, "帳戶/備註": "現金帳戶 🟢"},
        {"日期": "2026/05/20", "類型": "支出 💸", "分類": "交通", "子分類": "日常交通", "項目": "地鐵/公共交通日常累計", "金額": 286.0, "帳戶/備註": "現金帳戶 🟢"},
        {"日期": "2026/05/21", "類型": "支出 💸", "分類": "其他", "子分類": "一般消費", "項目": "日常雜項 / Copy服務", "金額": 71.0, "帳戶/備註": "現金帳戶 🟢"},
        {"日期": "2026/05/21", "類型": "支出 💸", "分類": "家用品", "子分類": "日常用品", "項目": "差電線 小米熨斗 日本城累計", "金額": 458.0, "帳戶/備註": "現金帳戶 🟢"},
        {"日期": "2026/05/22", "類型": "支出 💸", "分類": "園藝", "子分類": "花盆", "項目": "花盆購買", "金額": 162.0, "帳戶/備註": "現金帳戶 🟢"},
        {"日期": "2026/05/22", "類型": "支出 💸", "分類": "園藝", "子分類": "工具", "項目": "園藝小鏟子", "金額": 20.0, "帳戶/備註": "現金帳戶 🟢"},
        {"日期": "2026/05/23", "類型": "支出 💸", "分類": "飲食", "子分類": "零食/生果", "項目": "Donki壽司雪糕西瓜荔枝", "金額": 140.4, "帳戶/備註": "現金帳戶 🟢"},
        {"日期": "2026/05/25", "類型": "支出 💸", "分類": "娛樂", "子分類": "社交", "項目": "週末聚會活動", "金額": 99.2, "帳戶/備註": "現金帳戶 🟢"},
        {"日期": "2026/05/28", "類型": "支出 💸", "分類": "貓用品", "子分類": "寵物罐頭", "項目": "主子主食罐頭", "金額": 60.0, "帳戶/備註": "現金帳戶 🟢"}
    ]

# ==================== 3. 數據動態計算引擎 ====================
total_assets = sum(st.session_state.my_assets.values())
total_liabilities = sum(st.session_state.my_liabilities.values())
net_worth = total_assets - total_liabilities

df_current_logs = pd.DataFrame(st.session_state.my_logs)
total_actual_income = 0.0
total_actual_expense = 0.0

actual_spent_map = {cat: 0.0 for cat in st.session_state.my_budget.keys()}
actual_income_map = {cat: 0.0 for cat in st.session_state.my_income_categories}

if not df_current_logs.empty:
    df_current_logs["金額"] = pd.to_numeric(df_current_logs["金額"], errors='coerce').fillna(0.0)
    
    # 統計實際收入
    df_income_only = df_current_logs[df_current_logs["類型"] == "收入 📥"]
    total_actual_income = float(df_income_only["金額"].sum())
    for cat in actual_income_map.keys():
        actual_income_map[cat] = float(df_income_only[df_income_only["分類"] == cat]["金額"].sum())
        
    # 統計實際支出
    df_expenses_only = df_current_logs[df_current_logs["類型"] == "支出 💸"]
    total_actual_expense = float(df_expenses_only["金額"].sum())
    for cat in actual_spent_map.keys():
        actual_spent_map[cat] = float(df_expenses_only[df_expenses_only["分類"] == cat]["金額"].sum())

expected_savings = total_actual_income - total_actual_expense
savings_rate = (expected_savings / total_actual_income * 100) if total_actual_income > 0 else 0.0

# ==================== 4. 網頁 UI 視覺介面 ====================
st.title("💎 CLOUD FINANCE MASTER PLAN 2026")
st.caption("🚀 雲端收支全功能分享版 — 內建「華爾街標準會計對齊引擎」與「全動態閉環畫布」")
st.markdown("---")

# 頂部核心財務看板
m_col1, m_col2, m_col3, m_col4 = st.columns(4)
m_col1.metric("💰 本月總收入 (Income)", f"${total_actual_income:,.2f}")
m_col2.metric("💸 本月總支出 (Actual)", f"${total_actual_expense:,.2f}")
m_col3.metric("📈 預計儲蓄 (Savings)", f"${expected_savings:,.2f}", delta=f"儲蓄率 {savings_rate:.1f}%")
m_col4.metric("👑 當前淨身家 (Net Worth)", f"${net_worth:,.2f}")
st.markdown("---")

# 側邊欄選單
page_choice = st.sidebar.radio("切換功能頁面", [
    "📊 財務總覽 & 預算監控", 
    "💸 每日單筆記帳 (收/支)", 
    "📤 批量上載 Excel/CSV 檔案",
    "⚙️ 自訂您的資產/預算初始值"
])
st.sidebar.markdown("---")
st.sidebar.info("💡 **提示：** 個人流水帳即時渲染更新，保障獨立安全空間！")

# ------ 頁面 1: 財務總覽 & 預算監控 ------
if page_choice == "📊 財務總覽 & 預算監控":
    main_left_col, main_right_col = st.columns([1.3, 1.1])
    
    with main_left_col:
        st.subheader("📊 本月收支結構圖表分析")
        pie_col1, pie_col2 = st.columns(2)
        
        with pie_col1:
            st.markdown("<p style='text-align: center; font-weight: bold; margin-bottom: -10px;'>💰 收入來源比例</p>", unsafe_allow_html=True)
            fig_inc_data = pd.DataFrame(list(actual_income_map.items()), columns=["收入分類", "金額"])
            # 🔥 安全閥門：確保大於 0 才畫圖，杜絕 Plotly 找不到欄位而噴紅字
            fig_inc_data = fig_inc_data[fig_inc_data["金額"] > 0]
            if not fig_inc_data.empty:
                fig_inc = px.pie(fig_inc_data, values="金額", names="收入分類", hole=0.4, color_discrete_sequence=px.colors.sequential.Solar)
                fig_inc.update_traces(
                    textposition='inside', textinfo='label+percent', texttemplate='%{label}<br>%{percent:.1%}',
                    insidetextorientation='horizontal', hovertemplate='<b>%{label}</b><br>實際金額: $%{value:,.2f}<br>佔比: %{percent:.1%}<extra></extra>'
                )
                fig_inc.update_layout(
                    template="plotly_dark", margin=dict(l=10, r=10, t=40, b=10), height=280, showlegend=False,
                    uniformtext=dict(mode='hide', minsize=11)
                )
                st.plotly_chart(fig_inc, use_container_width=True)
            else:
                st.info("💡 尚無實際收入數據，暫不渲染圖表。")
                
        with pie_col2:
            st.markdown("<p style='text-align: center; font-weight: bold; margin-bottom: -10px;'>💸 開支分類比例</p>", unsafe_allow_html=True)
            fig_exp_data = pd.DataFrame(list(actual_spent_map.items()), columns=["分類", "實際支出"])
            # 🔥 安全閥門：確保開支總大於 0 才畫圖
            fig_exp_data = fig_exp_data[fig_exp_data["實際支出"] > 0]
            if not fig_exp_data.empty:
                fig = px.pie(fig_exp_data, values="實際支出", names="分類", hole=0.4, color_discrete_sequence=px.colors.sequential.Mint)
                fig.update_traces(
                    textposition='inside', textinfo='label+percent', texttemplate='%{label}<br>%{percent:.1%}',
                    insidetextorientation='horizontal', hovertemplate='<b>%{label}</b><br>實際金額: $%{value:,.2f}<br>佔比: %{percent:.1%}<extra></extra>'
                )
                fig.update_layout(
                    template="plotly_dark", margin=dict(l=10, r=10, t=40, b=10), height=280, showlegend=False,
                    uniformtext=dict(mode='hide', minsize=11)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("💡 尚無實際支出數據，暫不渲染圖表。")
            
    with main_right_col:
        st.subheader("🎯 Budget Tracker 預算進度條")
        budget_rows = []
        total_b_sum = 0.0
        total_a_sum = 0.0
        
        for cat, b_amount in st.session_state.my_budget.items():
            a_amount = actual_spent_map.get(cat, 0.0)
            remaining = b_amount - a_amount
            use_rate = (a_amount / b_amount) * 100 if b_amount > 0 else 0.0
            status_icon = "🔴 已超支" if use_rate >= 100 else ("🟡 預警" if use_rate >= 80 else "🟢 正常")
            
            total_b_sum += b_amount
            total_a_sum += a_amount
            
            budget_rows.append({
                "分類 (Category)": cat, "預算 (Budget)": f"${b_amount:,.1f}", "已使用 (Actual)": f"${a_amount:,.1f}",
                "剩餘 (Remaining)": f"${remaining:,.1f}", "使用率": f"{use_rate:.1f}%", "狀態": status_icon
            })
            
        total_remain = total_b_sum - total_a_sum
        total_rate = (total_a_sum / total_b_sum) * 100 if total_b_sum > 0 else 0.0
        budget_rows.append({
            "分類 (Category)": "📊 總計 (Total)", "預算 (Budget)": f"${total_b_sum:,.1f}", "已使用 (Actual)": f"${total_a_sum:,.1f}",
            "剩餘 (Remaining)": f"${total_remain:,.1f}", "使用率": f"{total_rate:.1f}%", "狀態": "🔥 全面掌控"
        })
        st.dataframe(pd.DataFrame(budget_rows), use_container_width=True, hide_index=True, height=335)

    st.markdown("---")
    st.subheader("📋 您的歷史收支明細報表")
    if st.session_state.my_logs:
        st.dataframe(pd.DataFrame(st.session_state.my_logs).iloc[::-1], use_container_width=True, hide_index=True)
        csv_data = pd.DataFrame(st.session_state.my_logs).to_csv(index=False).encode('utf-8-sig')
        st.download_button(label="📥 匯出這份明細成 Excel/CSV 下載", data=csv_data, file_name="My_Finance_Log.csv", mime="text/csv")
