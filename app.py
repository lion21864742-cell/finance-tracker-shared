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

# ------ 頁面 2: 每日單筆記帳 ------
elif page_choice == "💸 每日單筆記帳 (收/支)":
    st.subheader("📥 填寫日常單筆收支")
    all_accs = list(st.session_state.my_assets.keys()) + list(st.session_state.my_liabilities.keys())
    in_type = st.selectbox("1. 選擇交易類型", ["支出 💸", "收入 📥"])
    
    dynamic_label = "選擇收入分類 (Category)" if in_type == "收入 📥" else "選擇支出分類 (Category)"
    
    with st.form("share_single_form_v2", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            in_date = st.date_input("日期", datetime.now())
            # 🔥 語法修復：三元運算子必須包含 else 分支，已完整補齊
            in_cat = st.selectbox(dynamic_label, st.session_state.my_income_categories) if in_type == "收入 📥" else st.selectbox(dynamic_label, list(st.session_state.my_budget.keys()))
            in_subcat = st.text_input("子分類（如：外食、服飾、日常交通）")
        with c2:
            in_title = st.text_input("項目名稱")
            in_amount = st.number_input("金額 ($)", min_value=0.0, step=1.0)
            in_acc = st.selectbox("動用帳戶/帳戶備註", all_accs)
            
        submit_btn = st.form_submit_button("確認記入我的歷史帳本 🚀")
        if submit_btn and in_amount > 0:
            if in_type == "收入 📥":
                if in_acc in st.session_state.my_assets: st.session_state.my_assets[in_acc] += in_amount
                elif in_acc in st.session_state.my_liabilities: st.session_state.my_liabilities[in_acc] -= in_amount
            else:
                if in_acc in st.session_state.my_assets: st.session_state.my_assets[in_acc] -= in_amount
                elif in_acc in st.session_state.my_liabilities: st.session_state.my_liabilities[in_acc] += in_amount
            
            st.session_state.my_logs.append({
                "日期": in_date.strftime("%Y/%m/%d"), "類型": in_type, "分類": in_cat, "子分類": in_subcat, "項目": in_title, "金額": in_amount, "帳戶/備註": in_acc
            })
            st.success(f"✅ 成功記入一筆 {in_type}：{in_title} ${in_amount}")
            st.rerun()

# ------ 頁面 3: 批量上載 ------
elif page_choice == "📤 批量上載 Excel/CSV 檔案":
    st.subheader("📤 批量匯入您現有的記帳表格")
    upload_file = st.file_uploader("上傳您的檔案", type=["csv", "xlsx"])
    if upload_file is not None:
        try:
            df_imported = pd.read_csv(upload_file, encoding='utf-8-sig') if upload_file.name.endswith('.csv') else pd.read_excel(upload_file)
            if "日期 (Date)" in df_imported.columns: df_imported = df_imported.rename(columns={"日期 (Date)": "日期"})
            if "備註" in df_imported.columns: df_imported = df_imported.rename(columns={"備註": "帳戶/備註"})
            
            required = ["日期", "分類", "項目", "金額"]
            if not all(x in df_imported.columns for x in required):
                st.error("❌ 格式不符！第一排必須包含欄位：『日期』, 『分類』, 『項目』, 『金額』。")
            else:
                df_imported["金額"] = df_imported["金額"].astype(str).str.replace('$', '').str.replace(',', '').str.strip()
                df_imported["金額"] = pd.to_numeric(df_imported["金額"], errors='coerce').fillna(0.0)
                df_imported = df_imported.dropna(subset=["分類", "金額"])[df_imported["金額"] > 0]
                
                st.success(f"✅ 檔案辨識成功！讀取到 {len(df_imported)} 筆收支明細。")
                st.dataframe(df_imported, use_container_width=True, hide_index=True)
                
                if st.button("🔥 確定將上載數據併入我的專屬系統"):
                    for _, row in df_imported.iterrows():
                        row_cat = str(row.get("分類")).strip()
                        row_type = "收入 📥" if (row_cat in st.session_state.my_income_categories or "收入" in row_cat) else "支出 💸"
                        
                        st.session_state.my_logs.append({
                            "日期": str(row.get("日期")), "類型": row_type, "分類": row_cat, "子分類": str(row.get("子分類", "未分類")),
                            "項目": str(row.get("項目", "批量匯入")), "金額": float(row.get("金額", 0.0)), "帳戶/備註": str(row.get("帳戶/備註", "Excel匯入"))
                        })
                    st.toast("🚀 數據合併完成！動態收支看板已全面對齊！")
                    st.rerun()
        except Exception as e:
            st.error(f"讀取失敗：{e}")

# ------ 頁面 4: 自訂您的資產/預算初始值 ------
elif page_choice == "⚙️ 自訂您的資產/預算初始值":
    st.subheader("⚙️ 個人化財務設定後台")
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🚨 清空我目前輸入的所有資料（重設網頁）", type="primary", use_container_width=True):
            st.session_state.my_logs = []
            st.rerun()
    with col_btn2:
        if st.button("✨ 點我快速一鍵套用系統預設預算值", type="secondary", use_container_width=True):
            st.session_state.my_budget = {
                "飲食": 3000.0, "租金": 7700.0, "交通": 1700.0, "化妝品": 1000.0,
                "家用品": 500.0, "娛樂": 700.0, "園藝": 300.0, "電費": 1000.0,
                "貓用品": 500.0, "其他": 500.0
            }
            st.session_state.my_income_categories = ["薪資", "投資所得", "被動收入", "其他收入"]
            st.toast("✅ 已成功重設支出與收入的經典預設組合！")
            st.rerun()
        
    st.markdown("---")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.write("### 🟢 設定您的資產初始餘額")
        for k, v in list(st.session_state.my_assets.items()):
            st.session_state.my_assets[k] = float(st.number_input(f"【{k}】可用餘額 ($)", value=float(v), key=f"asset_input_key_{k}"))
        st.write("### 🔴 設定您的負債初始欠款")
        for k, v in list(st.session_state.my_liabilities.items()):
            st.session_state.my_liabilities[k] = float(st.number_input(f"【{k}】應還欠款 ($)", value=float(v), key=f"lia_input_key_{k}"))
            
    with col_s2:
        st.write("### 🎯 調整每月預算上限 (Monthly Budget)")
        for cat, b_val in list(st.session_state.my_budget.items()):
            # 🔥 終極核心修復：強制將數值轉成 float(b_val) 以適應 step=100.0，完美解決 MixedNumericTypesError 報錯！
            st.session_state.my_budget[cat] = float(st.number_input(f"📊 修改【{cat}】月預算", value=float(b_val), min_value=0.0, step=100.0, key=f"budget_input_key_{cat}"))
            
        st.markdown("---")
        st.write("### 💰 自訂您的收入項目分類")
        st.caption("目前擁有的收入分類： " + " 、 ".join([f"`{c}`" for c in st.session_state.my_income_categories]))
        
        add_inc_cat = st.text_input("➕ 輸入想新增的收入分類名稱（例如：副業收入）", key="add_new_income_cat_text")
        if st.button("確認新增此收入分類 🚀"):
            if add_inc_cat.strip() and add_inc_cat.strip() not in st.session_state.my_income_categories:
                st.session_state.my_income_categories.append(add_inc_cat.strip())
                st.success(f"✅ 已成功新增分類：{add_inc_cat.strip()}")
                st.rerun()
