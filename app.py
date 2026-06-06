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
        "飲食": 3000.0, "租金": 7700.0, "交通": 1700.0, "化妝品": 1000.0,
        "家用品": 500.0, "娛樂": 700.0, "園藝": 300.0, "電費": 1000.0,
        "貓用品": 500.0, "其他": 500.0
    }

# 收入分類初始架構
if "my_income_categories" not in st.session_state:
    st.session_state.my_income_categories = ["薪資", "投資所得", "被動收入", "其他收入"]

# 初始化流水帳
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
st.caption("🚀 雲端收支全功能分享版 — 內建「雙欄黃金比例看板
