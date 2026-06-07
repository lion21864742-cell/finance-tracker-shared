import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ==================== 1. 網頁全域配置 ====================
st.set_page_config(page_title="💎 Cloud Finance Ultimate 2026", page_icon="💰", layout="wide")

# ==================== 2. 多用戶獨立狀態初始化引擎 ====================
if "my_assets" not in st.session_state:
    st.session_state.my_assets = {"現金帳戶 🟢": 0.0, "銀行儲蓄 🏦": 0.0}
if "my_liabilities" not in st.session_state:
    st.session_state.my_liabilities = {"信用卡欠款 🔴": 0.0}
    
# 預算初始架構
if "my_budget" not in st.session_state:
    st.session_state.my_budget = {
                "飲食": 0.0, "租金": 0.0, "交通": 0.0, "化妝品": 0.0,
                "家用品": 0.0, "娛樂": 0.0, "電費": 0.0,
                "寵物用品": 0.0, "其他支出": 0.0,"其他收入": 0.0,"薪資": 0.0,
                "股票收入": 0.0

    }

# 初始化流水帳（預設加入一筆收入與一筆支出範例）
if "my_logs" not in st.session_state:
    st.session_state.my_logs = [
        {"日期": "2026/05/01", "類型": "收入 📥", "分類": "收入", "子分類": "薪資", "項目": "公司發薪", "金額": 25000.0, "帳戶/備註": "銀行儲蓄 🏦"},
        {"日期": "2026/05/20", "類型": "支出 💸", "分類": "飲食", "子分類": "外食", "項目": "歡迎使用收支理財系統", "金額": 0.0, "帳戶/備註": "系統初始"}
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

if not df_current_logs.empty:
    # 確保金額格式正確
    df_current_logs["金額"] = pd.to_numeric(df_current_logs["金額"], errors='coerce').fillna(0.0)
    
    # 1. 計算總收入（類型為收入，或者分類叫收入）
    is_income_mask = (df_current_logs["類型"] == "收入 📥") | (df_current_logs["分類"] == "收入")
    total_actual_income = float(df_current_logs[is_income_mask]["金額"].sum())
    
    # 2. 計算各分類的支出總和（排除收入項目）
    df_expenses_only = df_current_logs[~is_income_mask]
    total_actual_expense = float(df_expenses_only["金額"].sum())
    
    for cat in actual_spent_map.keys():
        actual_spent_map[cat] = float(df_expenses_only[df_expenses_only["分類"] == cat]["金額"].sum())

# 計算儲蓄指標
expected_savings = total_actual_income - total_actual_expense
savings_rate = (expected_savings / total_actual_income * 100) if total_actual_income > 0 else 0.0

# ==================== 4. 網頁 UI 視覺介面 ====================
st.title("💎 CLOUD FINANCE MASTER PLAN 2026")
st.caption("🚀 雲端收支全功能分享版 — 支援「收入/支出雙引擎」與「儲蓄率動態追蹤看板」")
st.markdown("---")

# 頂部核心財務看板（串聯你原有的 Excel 核心指標）
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
        st.subheader("📊 本月開支分類比例")
        if total_actual_expense > 0:
            fig_data = pd.DataFrame(list(actual_spent_map.items()), columns=["分類", "實際支出"])
            fig_data = fig_data[fig_data["實際支出"] > 0]
            fig = px.pie(fig_data, values="實際支出", names="分類", hole=0.4, color_discrete_sequence=px.colors.sequential.Mint)
            fig.update_layout(template="plotly_dark", margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("💡 尚無支出數據，圓餅圖將於您記帳或上載後自動呈現。")
            
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
    # ==========================================
# 側邊欄與全域基礎資料初始化
# ==========================================
if "my_income_categories" not in st.session_state:
    st.session_state.my_income_categories = ["薪資", "投資所得", "被動收入", "其他收入"]

if "my_budget" not in st.session_state:
    st.session_state.my_budget = {"飲食": 3000.0, "租金": 7000.0, "交通": 1000.0, "其他支出": 500.0}

if "my_logs" not in st.session_state:
    st.session_state.my_logs = []

# 提取所有資產與負債的帳戶名稱（供下拉選單使用）
all_accs = []
if "my_assets" in st.session_state:
    all_accs += list(st.session_state.my_assets.keys())
if "my_liabilities" in st.session_state:
    all_accs += list(st.session_state.my_liabilities.keys())
if not all_accs:
    all_accs = ["現金", "銀行帳戶"]

# ==========================================
# 頁面路由分流 (確保縮排完全一致)
# ==========================================

# ------ 頁面 1: 總覽 Dashboard ------
if page_choice == "📊 您的雲端財務 dashboard 總覽":
    st.subheader("📊 您的雲端財務 Dashboard 總覽")
    st.write("歡迎回來！這裡顯示您的財務摘要。")
    # (此處保留您原本的圖表與數據顯示代碼...)

# ------ 頁面 2: 每日單筆記帳 ------
elif page_choice == "💸 每日單筆記帳 (收/支)":
    st.subheader("📥 填寫日常單筆收支")
    
    with st.form("share_single_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            in_date = st.date_input("日期", datetime.now())
            in_type = st.selectbox("交易類型", ["支出 💸", "收入 📥"])
        with c2:
            # ✨ 動態選單：如果是收入，讀取自訂收入清單！
            if in_type == "收入 📥":
                in_cat = st.selectbox("分類", st.session_state.my_income_categories)
            else:
                in_cat = st.selectbox("分類", list(st.session_state.my_budget.keys()))
            in_subcat = st.text_input("子分類 (如：外食、零食)")
        with c3:
            in_title = st.text_input("項目名稱 (如：公司發薪、譚仔)")
            in_amount = st.number_input("金額 ($)", min_value=0.0, step=1.0)
            in_acc = st.selectbox("動用帳戶/帳戶備註", all_accs)

        submit_btn = st.form_submit_button("確認記入我的歷史帳本 🚀")
        
        if submit_btn and in_amount > 0:
            # 智慧連動變更餘額
            if in_type == "收入 📥":
                if "my_assets" in st.session_state and in_acc in st.session_state.my_assets: 
                    st.session_state.my_assets[in_acc] += in_amount
                if "my_liabilities" in st.session_state and in_acc in st.session_state.my_liabilities: 
                    st.session_state.my_liabilities[in_acc] -= in_amount
            else:
                if "my_assets" in st.session_state and in_acc in st.session_state.my_assets: 
                    st.session_state.my_assets[in_acc] -= in_amount
                if "my_liabilities" in st.session_state and in_acc in st.session_state.my_liabilities: 
                    st.session_state.my_liabilities[in_acc] += in_amount

            # 寫入帳本
            st.session_state.my_logs.append({
                "日期": in_date.strftime("%Y/%m/%d"),
                "類型": in_type,
                "分類": in_cat,
                "子分類": in_subcat,
                "項目": in_title,
                "金額": float(in_amount),
                "帳戶/備註": in_acc
            })
            st.success(f"✅ 成功記入：{in_title} ${in_amount}")
            st.rerun()

# ------ 面 3: 批量上載 Excel/CSV 檔案 ------
elif page_choice == "📤 批量上載 Excel/CSV 檔案":
    st.subheader("📤 批量匯入現有的記帳明細表格")
    st.info("💡 請確保您的 Excel/CSV 標題包含以下四個欄位：【日期】、【分類】、【項目】、【金額】")
    
    upload_file = st.file_uploader("上傳您的檔案", type=["csv", "xlsx"])
    
    if upload_file is not None:
        try:
            # 1. 讀取檔案
            if upload_file.name.endswith('.csv'):
                try:
                    df_imported = pd.read_csv(upload_file, encoding='utf-8-sig')
                except:
                    df_imported = pd.read_csv(upload_file, encoding='big5')
            else:
                df_imported = pd.read_excel(
    upload_file,
    engine="openpyxl"
)
            
            # 🔥 智慧修正 1：先踢走完全空白嘅行同列
            df_imported = df_imported.dropna(how='all')
            if "Unnamed" in df_imported.columns or df_imported.columns.str.contains('Unnamed').any():
                df_imported = df_imported.dropna(axis=1, how='all')
            
            # 🔥 智慧修正 2：【安全關鍵】如果表格是空的，直接中止，防止 iloc 報錯
            if df_imported.empty:
                st.warning("⚠️ 上傳的檔案中沒有偵測到任何數據，請檢查檔案內容。")
            else:
                # 智慧修正 3：尋找真正的標題列（兼容第一行是空行的情況）
                if df_imported.columns.str.contains('Unnamed').all() or df_imported.iloc[0].astype(str).str.contains('日期').any() or not any(x in df_imported.columns for x in ["日期", "分類", "項目", "金額"]):
                    for idx in range(len(df_imported)):
                        if df_imported.iloc[idx].astype(str).str.contains('日期').any():
                            df_imported.columns = df_imported.iloc[idx].astype(str).str.strip()
                            df_imported = df_imported.iloc[idx+1:].reset_index(drop=True)
                            break

                # 智慧修正 4：模糊欄位匹配
                col_mapping = {}
                for col in df_imported.columns:
                    col_str = str(col).strip()
                    if "日期" in col_str: col_mapping[col] = "日期"
                    elif "分類" in col_str: col_mapping[col] = "分類"
                    elif "項目" in col_str: col_mapping[col] = "項目"
                    elif "金額" in col_str: col_mapping[col] = "金額"
                    elif "子分類" in col_str: col_mapping[col] = "子分類"
                    elif "備註" in col_str or "帳戶" in col_str: col_mapping[col] = "帳戶/備註"

                df_imported = df_imported.rename(columns=col_mapping)
                
                # 2. 檢查四大關鍵欄位
                required = ["日期", "分類", "項目", "金額"]
                if not all(x in df_imported.columns for x in required):
                    st.error("❌ 格式不符！表格必須包含欄位：『日期』, 『分類』, 『項目』, 『金額』")
                    st.write("目前偵測到的欄位有：", list(df_imported.columns))
                else:
                    # 3. 數據清洗：移除金額的 $ 和 , 符號
                    df_imported["金額"] = df_imported["金額"].astype(str).str.replace('$', '').str.replace(',', '').str.strip()
                    df_imported["金額"] = pd.to_numeric(df_imported["金額"], errors='coerce').fillna(0.0)
                    df_imported = df_imported[df_imported["金額"] > 0]
                    
                    st.success(f"✅ 辨識成功！讀取到 {len(df_imported)} 筆收支明細。")
                    st.dataframe(df_imported[["日期", "分類", "項目", "金額"]], use_container_width=True, hide_index=True)
                    
                    if st.button("🔥 確定將上載數據併入系統帳本"):
                        for _, row in df_imported.iterrows():
                            row_cat = str(row.get("分類")).strip()
                            
                            if row_cat in st.session_state.my_income_categories or "收入" in row_cat or "薪資" in row_cat:
                                row_type = "收入 📥"
                            else:
                                row_type = "支出 💸"
                                
                            st.session_state.my_logs.append({
                                "日期": str(row.get("日期")).strip(),
                                "類型": row_type,
                                "分類": row_cat,
                                "子分類": str(row.get("子分類", "批量匯入")),
                                "項目": str(row.get("項目", "未命名項目")),
                                "金額": float(row.get("金額", 0.0)),
                                "帳戶/備註": str(row.get("帳戶/備註", "Excel匯入"))
                            })
                        st.success("🚀 數據已成功批量合併！財務圖表已同步更新！")
                        st.rerun()
        except Exception as e:
            st.error(f"❌ 讀取失敗，原因：{e}")
            
# ------ 頁面 4: 自訂初始值與收入分類 ------
elif page_choice == "⚙️ 自訂您的資產/預算初始值":
    st.subheader("⚙️ 個人化財務設定後台")
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🚨 清空我目前輸入的所有資料 (重設網頁)", type="primary", use_container_width=True):
            st.session_state.my_logs = []
            st.rerun()
    with col_btn2:
        if st.button("✨ 點我快速一鍵套用系統預設預算值", type="secondary", use_container_width=True):
            st.session_state.my_budget = {"飲食": 3000.0, "租金": 7000.0, "交通": 1000.0, "其他支出": 500.0}
            st.rerun()

    st.markdown("---")
    st.write("### ➕ 自訂您的收入項目分類")
    st.caption("目前分類： " + ", ".join([f"`{c}`" for c in st.session_state.my_income_categories]))
    
    new_cat = st.text_input("輸入新收入分類名稱（例如：股息收入）", key="add_new_income_cat_input")
    if st.button("確認新增分類 🚀"):
        if new_cat.strip() and new_cat.strip() not in st.session_state.my_income_categories:
            st.session_state.my_income_categories.append(new_cat.strip())
            st.success(f"✅ 已新增：{new_cat.strip()}")
            st.rerun()
        else:
            st.warning("⚠️ 輸入無效或分類已存在！")

    st.markdown("---")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if "my_assets" in st.session_state:
            st.write("### 🟢 設定您的資產初始餘額")
            for k, v in list(st.session_state.my_assets.items()):
                st.session_state.my_assets[k] = st.number_input(f"【{k}】可用餘額 ($)", value=float(v), key=f"asset_input_{k}")
        
        if "my_liabilities" in st.session_state:
            st.write("### 🔴 設定您的負債初始欠款")
            for k, v in list(st.session_state.my_liabilities.items()):
                st.session_state.my_liabilities[k] = st.number_input(f"【{k}】應還欠款 ($)", value=float(v), key=f"lia_input_{k}")
    with col_s2:
        st.write("### 🎯 調整每月預算上限 (Monthly Budget)")
        for cat, b_val in list(st.session_state.my_budget.items()):
            new_budget = st.number_input(f"修改【{cat}】月預算", value=float(b_val), min_value=0.0, step=100.0, key=f"budget_input_{cat}")
            st.session_state.my_budget[cat] = new_budget
