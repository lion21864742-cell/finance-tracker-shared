import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import firebase_admin
from firebase_admin import credentials, firestore
import requests

# ==================== Firebase 初始化 ====================
FIREBASE_API_KEY = "AIzaSyCWAcZjTZ02lc2-ILd3rY-hZa0qmM-F-ik"

if not firebase_admin._apps:
    try:
        sa = dict(st.secrets["firebase_service_account"])
        cred = credentials.Certificate(sa)
    except Exception:
        cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ==================== Auth Helper ====================
def sign_in(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    r = requests.post(url, json={"email": email, "password": password, "returnSecureToken": True})
    return r.json()

def sign_up(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
    r = requests.post(url, json={"email": email, "password": password, "returnSecureToken": True})
    return r.json()

# ==================== Firestore Helper ====================
def load_user_data(uid):
    doc = db.collection("users").document(uid).get()
    if doc.exists:
        return doc.to_dict()
    return None

def save_user_data(uid, data):
    db.collection("users").document(uid).set(data)

def get_default_data():
    return {
        "assets": {"現金帳戶 🟢": 0.0, "銀行儲蓄 🏦": 0.0},
        "liabilities": {"信用卡欠款 🔴": 0.0},
        "budget": {
            "飲食": 0.0, "租金": 0.0, "交通": 0.0, "化妝品": 0.0,
            "家用品": 0.0, "娛樂": 0.0, "電費": 0.0,
            "寵物用品": 0.0, "其他支出": 0.0, "其他收入": 0.0,
            "薪資": 0.0, "股票收入": 0.0
        },
        "income_categories": ["薪資", "投資所得", "被動收入", "其他收入"],
        "logs": [
            {"日期": "2026/05/01", "類型": "收入 📥", "分類": "收入", "子分類": "薪資",
             "項目": "公司發薪", "金額": 25000.0, "帳戶/備註": "銀行儲蓄 🏦"},
            {"日期": "2026/05/20", "類型": "支出 💸", "分類": "飲食", "子分類": "外食",
             "項目": "歡迎使用收支理財系統", "金額": 0.0, "帳戶/備註": "系統初始"}
        ]
    }

# ==================== 網頁配置 ====================
st.set_page_config(page_title="💎 Cloud Finance Ultimate 2026", page_icon="💰", layout="wide")

# ==================== 登入狀態 ====================
if "uid" not in st.session_state:
    st.session_state.uid = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None

# ==================== 登入/註冊頁面 ====================
if st.session_state.uid is None:
    st.title("💎 Cloud Finance Master Plan 2026")
    st.markdown("---")
    tab_login, tab_signup = st.tabs(["🔑 登入", "📝 註冊新帳號"])

    with tab_login:
        st.subheader("登入你的帳號")
        login_email = st.text_input("電郵", key="login_email")
        login_pw = st.text_input("密碼", type="password", key="login_pw")
        if st.button("登入 🚀", use_container_width=True):
            if login_email and login_pw:
                result = sign_in(login_email, login_pw)
                if "idToken" in result:
                    st.session_state.uid = result["localId"]
                    st.session_state.user_email = login_email
                    data = load_user_data(st.session_state.uid)
                    if data is None:
                        data = get_default_data()
                        save_user_data(st.session_state.uid, data)
                    st.session_state.my_assets = data.get("assets", {})
                    st.session_state.my_liabilities = data.get("liabilities", {})
                    st.session_state.my_budget = data.get("budget", {})
                    st.session_state.my_income_categories = data.get("income_categories", [])
                    st.session_state.my_logs = data.get("logs", [])
                    st.success("✅ 登入成功！")
                    st.rerun()
                else:
                    err = result.get("error", {}).get("message", "登入失敗")
                    st.error(f"❌ {err}")
            else:
                st.warning("請輸入電郵和密碼")

    with tab_signup:
        st.subheader("建立新帳號")
        signup_email = st.text_input("電郵", key="signup_email")
        signup_pw = st.text_input("密碼（最少6位）", type="password", key="signup_pw")
        signup_pw2 = st.text_input("確認密碼", type="password", key="signup_pw2")
        if st.button("註冊 ✨", use_container_width=True):
            if not signup_email or not signup_pw:
                st.warning("請填寫所有欄位")
            elif signup_pw != signup_pw2:
                st.error("❌ 兩次密碼不一致")
            elif len(signup_pw) < 6:
                st.error("❌ 密碼最少6位")
            else:
                result = sign_up(signup_email, signup_pw)
                if "idToken" in result:
                    st.session_state.uid = result["localId"]
                    st.session_state.user_email = signup_email
                    data = get_default_data()
                    save_user_data(st.session_state.uid, data)
                    st.session_state.my_assets = data["assets"]
                    st.session_state.my_liabilities = data["liabilities"]
                    st.session_state.my_budget = data["budget"]
                    st.session_state.my_income_categories = data["income_categories"]
                    st.session_state.my_logs = data["logs"]
                    st.success("✅ 註冊成功！歡迎使用！")
                    st.rerun()
                else:
                    err = result.get("error", {}).get("message", "註冊失敗")
                    st.error(f"❌ {err}")
    st.stop()

# ==================== 存檔 Helper ====================
def save_now():
    save_user_data(st.session_state.uid, {
        "assets": st.session_state.my_assets,
        "liabilities": st.session_state.my_liabilities,
        "budget": st.session_state.my_budget,
        "income_categories": st.session_state.my_income_categories,
        "logs": st.session_state.my_logs
    })

# ==================== 核心財務計算 ====================
total_assets = sum(st.session_state.my_assets.values())
total_liabilities = sum(st.session_state.my_liabilities.values())
net_worth = total_assets - total_liabilities

df_current_logs = pd.DataFrame(st.session_state.my_logs)
total_actual_income = 0.0
total_actual_expense = 0.0
actual_spent_map = {cat: 0.0 for cat in st.session_state.my_budget.keys()}

if not df_current_logs.empty:
    df_current_logs["金額"] = pd.to_numeric(df_current_logs["金額"], errors='coerce').fillna(0.0)
    is_income_mask = (df_current_logs["類型"] == "收入 📥") | (df_current_logs["分類"] == "收入")
    total_actual_income = float(df_current_logs[is_income_mask]["金額"].sum())
    df_expenses_only = df_current_logs[~is_income_mask]
    total_actual_expense = float(df_expenses_only["金額"].sum())
    for cat in actual_spent_map.keys():
        actual_spent_map[cat] = float(df_expenses_only[df_expenses_only["分類"] == cat]["金額"].sum())

expected_savings = total_actual_income - total_actual_expense
savings_rate = (expected_savings / total_actual_income * 100) if total_actual_income > 0 else 0.0

# ==================== 頁面標題 ====================
st.title("💎 CLOUD FINANCE MASTER PLAN 2026")
st.caption("🚀 雲端收支全功能分享版 — 支援「收入/支出雙引擎」與「儲蓄率動態追蹤看板」")

col_title, col_logout = st.columns([4, 1])
with col_logout:
    st.caption(f"👤 {st.session_state.user_email}")
    if st.button("登出", use_container_width=True):
        for key in ["uid", "user_email", "my_assets", "my_liabilities",
                    "my_budget", "my_income_categories", "my_logs"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

st.markdown("---")

m_col1, m_col2, m_col3, m_col4 = st.columns(4)
m_col1.metric("💰 本月總收入", f"${total_actual_income:,.2f}")
m_col2.metric("💸 本月總支出", f"${total_actual_expense:,.2f}")
m_col3.metric("📈 預計儲蓄", f"${expected_savings:,.2f}", delta=f"儲蓄率 {savings_rate:.1f}%")
m_col4.metric("👑 當前淨身家", f"${net_worth:,.2f}")
st.markdown("---")

# ==================== 側邊欄 ====================
st.sidebar.title("Menu 功能選單")
page_choice = st.sidebar.radio("切換功能頁面", [
    "📊 財務總覽 & 預算監控",
    "📋 歷史收支明細",
    "💸 每日單筆記帳 (收/支)",
    "📤 批量上載 Excel/CSV 檔案",
    "⚙️ 自訂您的資產/預算初始值"
])
st.sidebar.markdown("---")
st.sidebar.info("💡 數據已雲端儲存，刷新頁面不會消失！")

all_accs = list(st.session_state.my_assets.keys()) + list(st.session_state.my_liabilities.keys())
if not all_accs:
    all_accs = ["現金", "銀行帳戶"]

# ==================== 頁面 1: 財務總覽 ====================
if page_choice == "📊 財務總覽 & 預算監控":
    chart_col, budget_col = st.columns([1, 1.2])

    with chart_col:
        st.subheader("📊 本月開支分類比例")
        if total_actual_expense > 0:
            fig_data = pd.DataFrame(list(actual_spent_map.items()), columns=["分類", "實際支出"])
            fig_data = fig_data[fig_data["實際支出"] > 0]
            fig = px.pie(fig_data, values="實際支出", names="分類", hole=0.4,
                         color_discrete_sequence=px.colors.sequential.Mint)
            fig.update_layout(template="plotly_dark", margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("💡 尚無支出數據，記帳後自動呈現。")

    with budget_col:
        st.subheader("🎯 Budget Tracker 預算進度條")
        budget_rows = []
        for cat, b_amount in st.session_state.my_budget.items():
            a_amount = actual_spent_map.get(cat, 0.0)
            remaining = b_amount - a_amount
            use_rate = (a_amount / b_amount) * 100 if b_amount > 0 else 0.0
            if use_rate >= 100:
                status_icon = "🔴 已超支"
            elif use_rate >= 80:
                status_icon = "🟡 預警"
            else:
                status_icon = "🟢 正常"
            budget_rows.append({
                "分類": cat, "預算": f"${b_amount:,.1f}", "已使用": f"${a_amount:,.1f}",
                "剩餘": f"${remaining:,.1f}", "使用率": f"{use_rate:.1f}%", "狀態": status_icon
            })
        st.dataframe(pd.DataFrame(budget_rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    total_logs = len(st.session_state.my_logs)
    st.info(f"📋 共有 **{total_logs}** 筆記錄，詳細記錄請前往左側「📋 歷史收支明細」頁面查看及編輯。")

# ==================== 頁面 2: 歷史收支明細 ====================
elif page_choice == "📋 歷史收支明細":
    st.subheader("📋 歷史收支明細")

    if "editing_index" not in st.session_state:
        st.session_state.editing_index = None

    # ---- 日期篩選 ----
    import calendar
    now = datetime.now()
    this_month_start = date(now.year, now.month, 1)
    last_month = now.month - 1 if now.month > 1 else 12
    last_month_year = now.year if now.month > 1 else now.year - 1
    last_month_start = date(last_month_year, last_month, 1)
    last_month_end = date(last_month_year, last_month,
                          calendar.monthrange(last_month_year, last_month)[1])

    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    with f_col1:
        if st.button("本月", use_container_width=True):
            st.session_state.filter_mode = "本月"
    with f_col2:
        if st.button("上月", use_container_width=True):
            st.session_state.filter_mode = "上月"
    with f_col3:
        if st.button("全部", use_container_width=True):
            st.session_state.filter_mode = "全部"
    with f_col4:
        if st.button("自訂日期", use_container_width=True):
            st.session_state.filter_mode = "自訂"

    if "filter_mode" not in st.session_state:
        st.session_state.filter_mode = "全部"

    if st.session_state.filter_mode == "自訂":
        d_col1, d_col2 = st.columns(2)
        with d_col1:
            custom_start = st.date_input("開始日期", value=this_month_start, key="custom_start")
        with d_col2:
            custom_end = st.date_input("結束日期", value=date.today(), key="custom_end")
    else:
        custom_start = this_month_start
        custom_end = date.today()

    # ---- 排序控制 + 匯出 ----
    sort_col1, sort_col2, export_col = st.columns([2, 2, 1])
    with sort_col1:
        sort_by = st.selectbox("排序方式", ["日期", "類型", "分類", "金額"], key="sort_by")
    with sort_col2:
        sort_order = st.radio("順序", ["新→舊 / 高→低", "舊→新 / 低→高"], key="sort_order", horizontal=True)
    sort_ascending = sort_order == "舊→新 / 低→高"

    st.caption(f"目前篩選：**{st.session_state.filter_mode}**")
    st.markdown("---")

    # ---- 套用篩選 ----
    logs = st.session_state.my_logs
    filtered_logs = []
    for i, log in enumerate(logs):
        try:
            log_date = datetime.strptime(str(log.get("日期", "")), "%Y/%m/%d").date()
        except:
            log_date = None

        include = False
        if st.session_state.filter_mode == "全部" or log_date is None:
            include = True
        elif st.session_state.filter_mode == "本月":
            if log_date >= this_month_start:
                include = True
        elif st.session_state.filter_mode == "上月":
            if last_month_start <= log_date <= last_month_end:
                include = True
        elif st.session_state.filter_mode == "自訂":
            if custom_start <= log_date <= custom_end:
                include = True

        if include:
            filtered_logs.append((i, log, log_date))

    # ---- 套用排序 ----
    if sort_by == "日期":
        filtered_logs.sort(key=lambda x: x[2] or date.min, reverse=not sort_ascending)
    elif sort_by == "類型":
        filtered_logs.sort(key=lambda x: x[1].get("類型", ""), reverse=not sort_ascending)
    elif sort_by == "分類":
        filtered_logs.sort(key=lambda x: x[1].get("分類", ""), reverse=not sort_ascending)
    elif sort_by == "金額":
        filtered_logs.sort(key=lambda x: float(x[1].get("金額", 0)), reverse=not sort_ascending)

    # ---- 匯出 Excel ----
    with export_col:
        if filtered_logs:
            import io
            export_df = pd.DataFrame([log for _, log, _ in filtered_logs])
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                export_df.to_excel(writer, index=False, sheet_name="收支明細")
            buf.seek(0)
            filename = f"收支明細_{datetime.now().strftime('%Y%m%d')}.xlsx"
            st.download_button("📥 匯出", data=buf, file_name=filename,
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               use_container_width=True)

    if not filtered_logs:
        st.info("此時間範圍內沒有記錄。")
    else:
        st.caption(f"共 {len(filtered_logs)} 筆記錄")

        h1, h2, h3, h4, h5, h6, h7 = st.columns([1.2, 1.2, 1, 1.5, 1, 0.5, 0.5])
        h1.markdown("**日期**")
        h2.markdown("**類型**")
        h3.markdown("**分類**")
        h4.markdown("**項目**")
        h5.markdown("**金額**")
        h6.markdown("✏️")
        h7.markdown("🗑️")
        st.markdown("---")

        for idx, (i, log, _) in enumerate(filtered_logs):
            col_date, col_type, col_cat, col_item, col_amt, col_edit, col_del = st.columns([1.2, 1.2, 1, 1.5, 1, 0.5, 0.5])
            col_date.write(log.get("日期", ""))
            col_type.write(log.get("類型", ""))
            col_cat.write(log.get("分類", ""))
            col_item.write(log.get("項目", ""))
            col_amt.write(f'${log.get("金額", 0):,.1f}')

            if col_edit.button("✏️", key=f"edit_{i}_{idx}"):
                st.session_state.editing_index = i

            if col_del.button("🗑️", key=f"del_{i}_{idx}"):
                st.session_state.my_logs.pop(i)
                save_now()
                st.success("✅ 已刪除")
                st.rerun()

            if st.session_state.editing_index == i:
                with st.form(key=f"edit_form_{i}_{idx}"):
                    st.markdown(f"**編輯記錄**")
                    e1, e2, e3 = st.columns(3)
                    with e1:
                        new_date = st.text_input("日期", value=log.get("日期", ""), key=f"edate_{i}_{idx}")
                        new_type = st.selectbox("類型", ["支出 💸", "收入 📥"],
                            index=0 if log.get("類型") == "支出 💸" else 1, key=f"etype_{i}_{idx}")
                    with e2:
                        new_cat = st.text_input("分類", value=log.get("分類", ""), key=f"ecat_{i}_{idx}")
                        new_subcat = st.text_input("子分類", value=log.get("子分類", ""), key=f"esubcat_{i}_{idx}")
                    with e3:
                        new_item = st.text_input("項目", value=log.get("項目", ""), key=f"eitem_{i}_{idx}")
                        new_amt = st.number_input("金額", value=float(log.get("金額", 0)), min_value=0.0, key=f"eamt_{i}_{idx}")
                        new_acc = st.text_input("帳戶/備註", value=log.get("帳戶/備註", ""), key=f"eacc_{i}_{idx}")

                    sb, cb = st.columns(2)
                    with sb:
                        if st.form_submit_button("💾 儲存修改", use_container_width=True):
                            st.session_state.my_logs[i] = {
                                "日期": new_date, "類型": new_type, "分類": new_cat,
                                "子分類": new_subcat, "項目": new_item,
                                "金額": float(new_amt), "帳戶/備註": new_acc
                            }
                            save_now()
                            st.session_state.editing_index = None
                            st.success("✅ 已儲存")
                            st.rerun()
                    with cb:
                        if st.form_submit_button("取消", use_container_width=True):
                            st.session_state.editing_index = None
                            st.rerun()

            st.divider()

# ==================== 頁面 3: 單筆記帳 ====================
elif page_choice == "💸 每日單筆記帳 (收/支)":
    st.subheader("📥 填寫日常單筆收支")

    with st.form("single_entry_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            in_date = st.date_input("日期", datetime.now())
            in_type = st.selectbox("交易類型", ["支出 💸", "收入 📥"])
        with c2:
            if in_type == "收入 📥":
                in_cat = st.selectbox("分類", st.session_state.my_income_categories)
            else:
                in_cat = st.selectbox("分類", list(st.session_state.my_budget.keys()))
            in_subcat = st.text_input("子分類 (如：外食、零食)")
        with c3:
            in_title = st.text_input("項目名稱")
            in_amount = st.number_input("金額 ($)", min_value=0.0, step=1.0)
            in_acc = st.selectbox("帳戶", all_accs)

        submit_btn = st.form_submit_button("確認記入 🚀")

        if submit_btn and in_amount > 0:
            if in_type == "收入 📥":
                if in_acc in st.session_state.my_assets:
                    st.session_state.my_assets[in_acc] += in_amount
                if in_acc in st.session_state.my_liabilities:
                    st.session_state.my_liabilities[in_acc] -= in_amount
            else:
                if in_acc in st.session_state.my_assets:
                    st.session_state.my_assets[in_acc] -= in_amount
                if in_acc in st.session_state.my_liabilities:
                    st.session_state.my_liabilities[in_acc] += in_amount

            st.session_state.my_logs.append({
                "日期": in_date.strftime("%Y/%m/%d"),
                "類型": in_type,
                "分類": in_cat,
                "子分類": in_subcat,
                "項目": in_title,
                "金額": float(in_amount),
                "帳戶/備註": in_acc
            })
            save_now()
            st.success(f"✅ 已記入並儲存：{in_title} ${in_amount}")
            st.rerun()

# ==================== 頁面 4: 批量上載 ====================
elif page_choice == "📤 批量上載 Excel/CSV 檔案":
    st.subheader("📤 批量匯入現有的記帳明細表格")
    st.info("💡 請確保 Excel/CSV 標題包含：【日期】、【分類】、【項目】、【金額】")

    upload_file = st.file_uploader("上傳您的檔案", type=["csv", "xlsx"])

    if upload_file is not None:
        try:
            if upload_file.name.endswith('.csv'):
                try:
                    df_imported = pd.read_csv(upload_file, encoding='utf-8-sig')
                except:
                    df_imported = pd.read_csv(upload_file, encoding='big5')
            else:
                df_imported = pd.read_excel(upload_file, engine="openpyxl", dtype=str)

            df_imported.columns = df_imported.columns.astype(str).str.strip()
            df_imported = df_imported.dropna(how='all')
            if df_imported.columns.str.contains('Unnamed').any():
                df_imported = df_imported.dropna(axis=1, how='all')

            if df_imported.empty:
                st.warning("⚠️ 沒有偵測到任何數據，請檢查檔案。")
            else:
                if (df_imported.columns.str.contains('Unnamed').all()
                        or df_imported.iloc[0].astype(str).str.contains('日期').any()
                        or not any(x in df_imported.columns for x in ["日期", "分類", "項目", "金額"])):
                    for idx in range(len(df_imported)):
                        if df_imported.iloc[idx].astype(str).str.contains('日期').any():
                            df_imported.columns = df_imported.iloc[idx].astype(str).str.strip()
                            df_imported = df_imported.iloc[idx + 1:].reset_index(drop=True)
                            break

                col_mapping = {}
                for col in df_imported.columns:
                    col_str = str(col).strip()
                    if "日期" in col_str:
                        col_mapping[col] = "日期"
                    elif "子分類" in col_str:
                        col_mapping[col] = "子分類"
                    elif "分類" in col_str:
                        col_mapping[col] = "分類"
                    elif "項目" in col_str:
                        col_mapping[col] = "項目"
                    elif "金額" in col_str:
                        col_mapping[col] = "金額"
                    elif "備註" in col_str or "帳戶" in col_str:
                        col_mapping[col] = "帳戶/備註"

                df_imported = df_imported.rename(columns=col_mapping)
                required = ["日期", "分類", "項目", "金額"]
                if not all(x in df_imported.columns for x in required):
                    st.error("❌ 格式不符！必須包含：『日期』,『分類』,『項目』,『金額』")
                    st.write("目前偵測到的欄位：", list(df_imported.columns))
                else:
                    df_imported["金額"] = df_imported["金額"].astype(str).str.replace('$', '').str.replace(',', '').str.strip()
                    df_imported["金額"] = pd.to_numeric(df_imported["金額"], errors='coerce').fillna(0.0)
                    df_imported = df_imported[df_imported["金額"] > 0]

                    st.success(f"✅ 辨識成功！讀取到 {len(df_imported)} 筆明細。")
                    st.dataframe(df_imported[["日期", "分類", "項目", "金額"]], use_container_width=True, hide_index=True)

                    if st.button("🔥 確定併入帳本並儲存到雲端"):
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
                        save_now()
                        st.success("🚀 已成功合併並儲存到雲端！")
                        st.rerun()

        except Exception as e:
            st.error(f"❌ 讀取失敗，原因：{e}")

# ==================== 頁面 5: 設定 ====================
elif page_choice == "⚙️ 自訂您的資產/預算初始值":
    st.subheader("⚙️ 個人化財務設定後台")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🚨 清空所有記帳記錄", type="primary", use_container_width=True):
            st.session_state.my_logs = []
            save_now()
            st.rerun()
    with col_btn2:
        if st.button("✨ 套用系統預設預算值", type="secondary", use_container_width=True):
            st.session_state.my_budget = {"飲食": 3000.0, "租金": 7000.0, "交通": 1000.0, "其他支出": 500.0}
            save_now()
            st.rerun()

    st.markdown("---")
    st.write("### ➕ 自訂收入分類")

    # 顯示現有分類 + 刪除按鈕
    st.caption("目前分類：")
    cat_cols = st.columns(min(len(st.session_state.my_income_categories), 4))
    for idx, cat in enumerate(st.session_state.my_income_categories):
        with cat_cols[idx % 4]:
            st.markdown(f"`{cat}`")
            if st.button(f"✕ 刪除", key=f"del_cat_{idx}"):
                if len(st.session_state.my_income_categories) > 1:
                    st.session_state.my_income_categories.pop(idx)
                    save_now()
                    st.rerun()
                else:
                    st.warning("至少保留一個分類！")

    st.markdown("")
    new_cat = st.text_input("新增收入分類名稱", key="add_new_income_cat_input")
    if st.button("新增分類 🚀"):
        if new_cat.strip() and new_cat.strip() not in st.session_state.my_income_categories:
            st.session_state.my_income_categories.append(new_cat.strip())
            save_now()
            st.success(f"✅ 已新增：{new_cat.strip()}")
            st.rerun()
        else:
            st.warning("⚠️ 輸入無效或分類已存在！")

    st.markdown("---")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.write("### 🟢 資產初始餘額")
        for k, v in list(st.session_state.my_assets.items()):
            new_val = st.number_input(f"【{k}】", value=float(v), key=f"asset_input_{k}")
            if new_val != v:
                st.session_state.my_assets[k] = new_val
                save_now()

        st.write("### 🔴 負債初始欠款")
        for k, v in list(st.session_state.my_liabilities.items()):
            new_val = st.number_input(f"【{k}】", value=float(v), key=f"lia_input_{k}")
            if new_val != v:
                st.session_state.my_liabilities[k] = new_val
                save_now()

    with col_s2:
        st.write("### 🎯 每月預算上限")
        for cat, b_val in list(st.session_state.my_budget.items()):
            new_budget = st.number_input(f"【{cat}】", value=float(b_val), min_value=0.0,
                                          step=100.0, key=f"budget_input_{cat}")
            if new_budget != b_val:
                st.session_state.my_budget[cat] = new_budget
                save_now()
