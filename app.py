import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. 網頁配置
st.set_page_config(page_title="💎 Cloud Finance Master Plan 2026", layout="wide")

# 2. 狀態初始化 (強制 float 確保不報錯)
if "my_assets" not in st.session_state:
    st.session_state.my_assets = {"現金": 15000.0, "銀行": 65000.0}
if "my_budget" not in st.session_state:
    st.session_state.my_budget = {"飲食": 3000.0, "租金": 7700.0, "交通": 1700.0}

# 3. 繪圖前的安全防禦機制 (這是解決你 AttributeError 的關鍵)
def plot_safe_pie(data, values, names, title):
    st.subheader(title)
    # 必須檢查 Dataframe 是否為空，且數值總和大於 0，否則 Plotly 會當機
    if not data.empty and data[values].sum() > 0:
        fig = px.pie(data, values=values, names=names, hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("💡 目前尚無資料可繪製圖表。")

# 4. 你的核心輸入介面 (已修正三元運算子語法)
st.title("💎 Cloud Finance Master Plan 2026")
st.caption("🚀 雲端收支全功能分享版")

# 修正行 147 的三元運算子錯誤：必須要有 else
in_type = st.selectbox("選擇交易類型", ["收入", "支出"])
in_cat = st.selectbox("分類", ["薪資", "投資"]) if in_type == "收入" else st.selectbox("分類", ["飲食", "交通"])

# 5. 數值輸入 (修正類型錯誤)
val = float(st.number_input("金額", value=100.0, step=100.0))

# 6. 範例字典 (修正 line 38 的語法錯誤)
# 確保每一行都正確閉合
my_entry = {
    "日期": "2026/05/08", 
    "類型": "支出", 
    "分類": "化妝品", 
    "項目": "專櫃美妝粉餅", 
    "金額": 880.0
}
# 錯誤修正範例
if fig_inc_data is not None and not fig_inc_data.empty:
    fig_inc = px.pie(fig_inc_data, values="金額", names="收入分類", hole=0.4)
    st.plotly_chart(fig_inc)
else:
    st.write("目前無資料顯示")
