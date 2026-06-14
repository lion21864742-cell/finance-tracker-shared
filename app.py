import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import firebase_admin
from firebase_admin import credentials, firestore
import requests
import calendar
import re as _re

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

# ==================== Firebase ====================
FIREBASE_API_KEY = "AIzaSyCWAcZjTZ02lc2-ILd3rY-hZa0qmM-F-ik"

if not firebase_admin._apps:
    try:
        sa = dict(st.secrets["firebase_service_account"])
        cred = credentials.Certificate(sa)
    except Exception:
        cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

def sign_in(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    r = requests.post(url, json={"email": email, "password": password, "returnSecureToken": True})
    return r.json()

def sign_up(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
    r = requests.post(url, json={"email": email, "password": password, "returnSecureToken": True})
    return r.json()

def load_user_data(uid):
    doc = db.collection("users").document(uid).get()
    if doc.exists:
        return doc.to_dict()
    return None

def save_user_data(uid, data):
    db.collection("users").document(uid).set(data)

def get_default_data():
    return {
        "assets": {"現金帳戶 🟢": 0.0, "銀行儲蓄 🏦": 0.0, "投資帳戶 📈": 0.0},
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
        ],
        "trades": []
    }

# ==================== Page Config ====================
st.set_page_config(page_title="💎 Cloud Finance Ultimate 2026", page_icon="💰", layout="wide")

# ==================== CSS ====================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0d1117 0%, #0f1923 50%, #0d1f2d 100%) !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stAppViewContainer"] > .main { background: transparent !important; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f1923 0%, #111d2b 100%) !important;
    border-right: 1px solid rgba(0, 212, 170, 0.15) !important;
}
[data-testid="stSidebar"] .stRadio label { color: #a0aec0 !important; font-size: 0.9rem !important; padding: 4px 0 !important; transition: color 0.2s; }
[data-testid="stSidebar"] .stRadio label:hover { color: #00d4aa !important; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #718096 !important; font-size: 0.8rem !important; }

h1 { background: linear-gradient(90deg, #00d4aa, #3b82f6) !important; -webkit-background-clip: text !important; -webkit-text-fill-color: transparent !important; font-weight: 700 !important; letter-spacing: -0.5px !important; }
h2, h3 { color: #e2e8f0 !important; font-weight: 600 !important; letter-spacing: -0.3px !important; }
p, span, div, label { color: #cbd5e0 !important; }

[data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.02) 100%) !important;
    border: 1px solid rgba(0, 212, 170, 0.2) !important;
    border-radius: 16px !important;
    padding: 1.2rem 1.4rem !important;
    backdrop-filter: blur(10px) !important;
    transition: border-color 0.3s, transform 0.2s !important;
}
[data-testid="stMetric"]:hover { border-color: rgba(0, 212, 170, 0.5) !important; transform: translateY(-2px) !important; }
[data-testid="stMetricValue"] { color: #f7fafc !important; font-weight: 700 !important; font-size: 1.5rem !important; }
[data-testid="stMetricLabel"] { color: #718096 !important; font-size: 0.78rem !important; text-transform: uppercase !important; letter-spacing: 0.05em !important; }
[data-testid="stMetricDelta"] { font-size: 0.85rem !important; }

.stButton > button {
    background: linear-gradient(135deg, #00d4aa, #0ea5e9) !important;
    color: #0d1117 !important; font-weight: 600 !important; font-size: 0.88rem !important;
    border: none !important; border-radius: 10px !important; padding: 0.55rem 1.2rem !important;
    transition: opacity 0.2s, transform 0.15s, box-shadow 0.2s !important;
    box-shadow: 0 4px 15px rgba(0, 212, 170, 0.25) !important;
}
.stButton > button:hover { opacity: 0.88 !important; transform: translateY(-1px) !important; box-shadow: 0 6px 20px rgba(0, 212, 170, 0.4) !important; }
.stButton > button[kind="secondary"] { background: rgba(255,255,255,0.06) !important; color: #a0aec0 !important; box-shadow: none !important; border: 1px solid rgba(255,255,255,0.1) !important; }
.stButton > button[kind="primary"] { background: linear-gradient(135deg, #e53e3e, #c05621) !important; box-shadow: 0 4px 15px rgba(229, 62, 62, 0.3) !important; }

.stTextInput input, .stNumberInput input, textarea {
    background: rgba(15, 25, 40, 0.8) !important; border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 10px !important; color: #f7fafc !important; font-family: 'Inter', sans-serif !important;
}
.stTextInput input:focus, .stNumberInput input:focus { border-color: #00d4aa !important; box-shadow: 0 0 0 3px rgba(0, 212, 170, 0.15) !important; }
.stSelectbox > div > div { background: rgba(15, 25, 40, 0.8) !important; border: 1px solid rgba(255,255,255,0.15) !important; border-radius: 10px !important; color: #f7fafc !important; }
[data-testid="stNumberInput"] input { color: #f7fafc !important; background: rgba(15, 25, 40, 0.8) !important; }
[data-testid="stWidgetLabel"] p, .stTextInput label, .stNumberInput label, .stSelectbox label, .stRadio label { color: #a0aec0 !important; font-size: 0.85rem !important; }

.stTabs [data-baseweb="tab-list"] { background: rgba(255,255,255,0.03) !important; border-radius: 12px !important; padding: 4px !important; gap: 4px !important; border-bottom: none !important; }
.stTabs [data-baseweb="tab"] { border-radius: 8px !important; color: #718096 !important; font-weight: 500 !important; padding: 0.5rem 1.2rem !important; }
.stTabs [aria-selected="true"] { background: linear-gradient(135deg, rgba(0,212,170,0.2), rgba(59,130,246,0.2)) !important; color: #00d4aa !important; }

[data-testid="stDataFrame"] { border: 1px solid rgba(0, 212, 170, 0.15) !important; border-radius: 12px !important; overflow: hidden !important; }
[data-testid="stAlert"] { border-radius: 12px !important; border-left-width: 4px !important; backdrop-filter: blur(8px) !important; }
hr { border: none !important; border-top: 1px solid rgba(255,255,255,0.07) !important; margin: 1rem 0 !important; }
[data-testid="stForm"] { background: rgba(255,255,255,0.02) !important; border: 1px solid rgba(255,255,255,0.07) !important; border-radius: 16px !important; padding: 1rem !important; }
[data-testid="stCaptionContainer"] p { color: #4a5568 !important; font-size: 0.8rem !important; }

/* ══ AI 建議卡片 ══ */
.ai-card {
    background: linear-gradient(135deg, rgba(0,212,170,0.08), rgba(59,130,246,0.08));
    border: 1px solid rgba(0,212,170,0.25);
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
    line-height: 1.7;
}

/* ══ Metric 數值自動縮放（全局）══ */
[data-testid="stMetricValue"] {
    font-size: clamp(0.85rem, 2vw, 1.5rem) !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    max-width: 100% !important;
}
[data-testid="stMetricLabel"] {
    font-size: clamp(0.6rem, 1.2vw, 0.78rem) !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
[data-testid="stMetricDelta"] {
    font-size: clamp(0.6rem, 1.1vw, 0.85rem) !important;
    white-space: normal !important;
    word-break: break-all !important;
}
[data-testid="stMetric"] {
    min-width: 0 !important;
    overflow: hidden !important;
}

/* ══ iPad 橫向 (1024px 以下) ══ */
@media (max-width: 1024px) {
    [data-testid="stSidebar"] { min-width: 200px !important; max-width: 240px !important; }
    .main .block-container { padding-left: 0.8rem !important; padding-right: 0.8rem !important; }
    [data-testid="stMetric"] { padding: 0.8rem 0.7rem !important; border-radius: 12px !important; }
    h1 { font-size: 1.2rem !important; }
    h2, h3 { font-size: 1rem !important; }
}

/* ══ iPad 直向 / 大手機 (768px 以下) ══ */
@media (max-width: 768px) {
    h1 { font-size: 1.1rem !important; }
    h2, h3 { font-size: 0.95rem !important; }
    .stButton > button { min-height: 2.8rem !important; font-size: 0.92rem !important; border-radius: 12px !important; }
    .stTextInput input, .stNumberInput input { font-size: 1rem !important; min-height: 2.6rem !important; }
    .main .block-container { padding-left: 0.4rem !important; padding-right: 0.4rem !important; padding-top: 0.5rem !important; }
    [data-testid="stMetric"] { padding: 0.7rem 0.6rem !important; border-radius: 10px !important; }
    .stTabs [data-baseweb="tab"] { padding: 0.4rem 0.6rem !important; font-size: 0.78rem !important; }
    [data-testid="stForm"] { padding: 0.6rem !important; }
    section[data-testid="stSidebar"] > div { padding-top: 0.8rem !important; }
}

/* ══ 手機小屏 (480px 以下) ══ */
@media (max-width: 480px) {
    h1 { font-size: 0.95rem !important; }
    [data-testid="stMetric"] { padding: 0.6rem 0.5rem !important; }
    .ai-card { padding: 0.8rem 0.9rem !important; font-size: 0.86rem !important; }
}
</style>
""", unsafe_allow_html=True)

# ==================== yfinance helpers ====================
def fetch_price(ticker: str):
    if not YFINANCE_AVAILABLE:
        return None, "yfinance 未安裝"
    try:
        import math
        t = yf.Ticker(ticker.strip())
        hist = t.history(period="5d")
        if not hist.empty:
            closes = hist["Close"].dropna()
            if not closes.empty:
                price = float(closes.iloc[-1])
                if not math.isnan(price) and price > 0:
                    return round(price, 4), None
        info = t.fast_info
        price = getattr(info, "last_price", None)
        if price is not None:
            price = float(price)
            if not math.isnan(price) and price > 0:
                return round(price, 4), None
        return None, "無法取得價格（ticker 可能錯誤或非交易時段）"
    except Exception as e:
        return None, str(e)

def extract_ticker(name: str, currency: str):
    name = name.strip()
    if currency == "HKD":
        num_match = _re.match(r'^(\d{4,5})', name)
        if num_match:
            code = int(num_match.group(1))
            return f"{code:04d}.HK"
        hk_match = _re.search(r'(\d{1,5}\.HK)', name, _re.IGNORECASE)
        if hk_match:
            return hk_match.group(1).upper()
    us_match = _re.match(r'^([A-Z]{1,5})[\s\u4e00-\u9fff]', name)
    if us_match:
        return us_match.group(1)
    us_any = _re.search(r'\b([A-Z]{1,5})\b', name)
    if us_any:
        return us_any.group(1)
    return None

# ==================== FIFO 持倉計算（修正版）====================
def compute_holdings_from_trades(trades: list) -> list:
    """
    FIFO 持倉計算。
    Key = (名稱, 幣別) 避免同名不同幣混淆。
    買入：加入 lot queue（成本含手續費）
    賣出：從最舊 lot 扣除，並追蹤已實現盈虧
    """
    from collections import defaultdict

    sorted_trades = sorted(trades, key=lambda t: t.get("日期", ""))

    # lots[key] = list of {"qty": float, "cost": float}  (cost = per share cost incl. fee)
    lots = defaultdict(list)
    realized_pnl = defaultdict(float)  # (name, ccy) -> realized pnl

    for tr in sorted_trades:
        name     = tr.get("名稱", "").strip()
        currency = tr.get("幣別", "USD")
        qty      = float(tr.get("數量") or 0)
        price    = float(tr.get("成交價") or 0)
        fee      = float(tr.get("手續費") or 0)
        ttype    = tr.get("類型", "買入")

        if qty <= 0 or price <= 0:
            continue

        key = (name, currency)

        if ttype == "買入":
            # 買入每股成本 = (總金額 + 手續費) / 數量
            cost_per_share = (qty * price + fee) / qty
            lots[key].append({"qty": qty, "cost": cost_per_share})

        elif ttype == "賣出":
            # 賣出收入 = qty * price - fee
            sell_proceeds = qty * price - fee
            remaining_qty = qty
            sell_cost = 0.0

            while remaining_qty > 1e-9 and lots[key]:
                oldest = lots[key][0]
                if oldest["qty"] <= remaining_qty + 1e-9:
                    # 整批賣出
                    sell_cost += oldest["qty"] * oldest["cost"]
                    remaining_qty -= oldest["qty"]
                    lots[key].pop(0)
                else:
                    # 部分賣出
                    sell_cost += remaining_qty * oldest["cost"]
                    oldest["qty"] -= remaining_qty
                    remaining_qty = 0.0

            # 已實現盈虧
            realized_pnl[key] += sell_proceeds - sell_cost

    # 整理持倉
    holdings = []
    for (name, currency), lot_list in lots.items():
        total_qty = sum(l["qty"] for l in lot_list)
        if total_qty < 1e-6:
            continue  # 已全部賣出
        total_cost_val = sum(l["qty"] * l["cost"] for l in lot_list)
        avg_cost = total_cost_val / total_qty
        holdings.append({
            "名稱": name,
            "幣別": currency,
            "數量": round(total_qty, 6),
            "現價": 0.0,
            "平均成本": round(avg_cost, 6),
            "市值": 0.0,
            "盈虧": 0.0,
            "已實現盈虧": round(realized_pnl.get((name, currency), 0.0), 4),
        })

    return holdings

def get_realized_pnl_map(trades: list) -> dict:
    """回傳各股票已實現盈虧 {(name, ccy): pnl}"""
    from collections import defaultdict
    sorted_trades = sorted(trades, key=lambda t: t.get("日期", ""))
    lots = defaultdict(list)
    realized = defaultdict(float)

    for tr in sorted_trades:
        name     = tr.get("名稱", "").strip()
        currency = tr.get("幣別", "USD")
        qty      = float(tr.get("數量") or 0)
        price    = float(tr.get("成交價") or 0)
        fee      = float(tr.get("手續費") or 0)
        ttype    = tr.get("類型", "買入")
        if qty <= 0 or price <= 0:
            continue
        key = (name, currency)
        if ttype == "買入":
            lots[key].append({"qty": qty, "cost": (qty * price + fee) / qty})
        elif ttype == "賣出":
            proceeds = qty * price - fee
            rem = qty
            cost_basis = 0.0
            while rem > 1e-9 and lots[key]:
                ol = lots[key][0]
                if ol["qty"] <= rem + 1e-9:
                    cost_basis += ol["qty"] * ol["cost"]
                    rem -= ol["qty"]
                    lots[key].pop(0)
                else:
                    cost_basis += rem * ol["cost"]
                    ol["qty"] -= rem
                    rem = 0.0
            realized[key] += proceeds - cost_basis
    return dict(realized)

# ==================== 登入狀態 ====================
if "uid" not in st.session_state:
    st.session_state.uid = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None

if st.session_state.uid is None:
    params = st.query_params
    uid_param = params.get("uid", None)
    email_param = params.get("em", None)
    if uid_param and email_param:
        data = load_user_data(uid_param)
        if data:
            st.session_state.uid = uid_param
            st.session_state.user_email = email_param
            st.session_state.my_assets = data.get("assets", {})
            st.session_state.my_liabilities = data.get("liabilities", {})
            st.session_state.my_budget = data.get("budget", {})
            st.session_state.my_income_categories = data.get("income_categories", [])
            st.session_state.my_logs = data.get("logs", [])
            st.session_state.my_holdings = data.get("holdings", [])
            st.session_state.my_trades = data.get("trades", [])

# ==================== 登入/註冊頁 ====================
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
                    st.session_state.my_holdings = data.get("holdings", [])
                    st.session_state.my_trades = data.get("trades", [])
                    st.query_params["uid"] = st.session_state.uid
                    st.query_params["em"] = login_email
                    st.success("✅ 登入成功！")
                    st.rerun()
                else:
                    st.error(f"❌ {result.get('error', {}).get('message', '登入失敗')}")
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
                    st.session_state.my_holdings = []
                    st.session_state.my_trades = []
                    st.query_params["uid"] = st.session_state.uid
                    st.query_params["em"] = signup_email
                    st.success("✅ 註冊成功！歡迎使用！")
                    st.rerun()
                else:
                    st.error(f"❌ {result.get('error', {}).get('message', '註冊失敗')}")
    st.stop()

# ==================== 存檔 ====================
def save_now():
    save_user_data(st.session_state.uid, {
        "assets": st.session_state.my_assets,
        "liabilities": st.session_state.my_liabilities,
        "budget": st.session_state.my_budget,
        "income_categories": st.session_state.my_income_categories,
        "logs": st.session_state.my_logs,
        "trades": st.session_state.get("my_trades", [])
    })

# ==================== 計算持倉並合併舊現價 ====================
def refresh_holdings():
    computed = compute_holdings_from_trades(st.session_state.get("my_trades", []))
    old_prices = {(h["名稱"], h.get("幣別","USD")): float(h.get("現價") or 0)
                  for h in st.session_state.get("my_holdings", [])}
    for h in computed:
        key = (h["名稱"], h.get("幣別","USD"))
        old_p = old_prices.get(key, 0.0)
        if old_p > 0:
            h["現價"] = old_p
            h["市值"] = round(h["數量"] * old_p, 4)
            h["盈虧"] = round(h["數量"] * (old_p - h["平均成本"]), 4)
    st.session_state.my_holdings = computed

refresh_holdings()

# ==================== 核心財務計算 ====================
total_assets = sum(st.session_state.my_assets.values())
total_liabilities = sum(st.session_state.my_liabilities.values())

_holdings = st.session_state.get("my_holdings", [])
_fx = 7.80
_holdings_usd_mv = sum(float(h.get("市值") or 0) for h in _holdings if h.get("幣別","USD") == "USD")
_holdings_hkd_mv = sum(float(h.get("市值") or 0) for h in _holdings if h.get("幣別","USD") == "HKD")
holdings_total_value = _holdings_usd_mv * _fx + _holdings_hkd_mv
net_worth = total_assets - total_liabilities + holdings_total_value

df_current_logs = pd.DataFrame(st.session_state.my_logs) if st.session_state.my_logs else pd.DataFrame()
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

# ==================== 智能數字格式化（防截斷）====================
def fmt(val: float, prefix: str = "$") -> str:
    """自動縮短大數字：>=1M 顯示 1.2M，>=1K 顯示 29K，否則顯示完整"""
    abs_val = abs(val)
    sign = "-" if val < 0 else ""
    if abs_val >= 1_000_000:
        return f"{sign}{prefix}{abs_val/1_000_000:.1f}M"
    elif abs_val >= 100_000:
        return f"{sign}{prefix}{abs_val/1000:.0f}K"
    elif abs_val >= 10_000:
        return f"{sign}{prefix}{abs_val/1000:.1f}K"
    else:
        return f"{sign}{prefix}{abs_val:,.0f}"

# ==================== 頁面標題 ====================
st.title("💎 CLOUD FINANCE MASTER PLAN 2026")
st.caption("🚀 雲端收支全功能 — 收支雙引擎 · FIFO持倉 · AI理財建議 · 手機優化")

col_title, col_logout = st.columns([4, 1])
with col_logout:
    st.caption(f"👤 {st.session_state.user_email}")
    if st.button("登出", use_container_width=True):
        st.query_params.clear()
        for key in ["uid", "user_email", "my_assets", "my_liabilities",
                    "my_budget", "my_income_categories", "my_logs", "my_trades", "my_holdings"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

st.markdown("---")

m_col1, m_col2, m_col3, m_col4 = st.columns(4)
m_col1.metric("💰 本月收入", fmt(total_actual_income))
m_col2.metric("💸 本月支出", fmt(total_actual_expense))
m_col3.metric("📈 預計儲蓄", fmt(expected_savings), delta=f"儲蓄率 {savings_rate:.1f}%")
_nw_delta = f"含持倉 {fmt(holdings_total_value,'HK$')}" if holdings_total_value > 0 else None
m_col4.metric("👑 淨身家", fmt(net_worth, "HK$"), delta=_nw_delta)

st.markdown("")
m2_col1, m2_col2, m2_col3, m2_col4 = st.columns(4)
m2_col1.metric("🏦 總資產", fmt(total_assets, "HK$"))
m2_col2.metric("💳 總負債", fmt(total_liabilities, "HK$"),
               delta=f"-{(total_liabilities/total_assets*100):.1f}% 負債比" if total_assets > 0 else None,
               delta_color="inverse")
m2_col3.metric("📈 持倉市值", fmt(holdings_total_value, "HK$"),
               delta=f"US${fmt(_holdings_usd_mv)} HK${fmt(_holdings_hkd_mv)}" if _holdings else None,
               delta_color="off")
_net_pnl = sum(float(h.get("盈虧") or 0) * (_fx if h.get("幣別","USD")=="USD" else 1) for h in _holdings)
_net_pnl_sign = "+" if _net_pnl >= 0 else ""
m2_col4.metric("💹 持倉盈虧", fmt(_net_pnl, "HK$"),
               delta=f"{_net_pnl_sign}{fmt(abs(_net_pnl),'')}", delta_color="normal")
st.markdown("---")

# ==================== 側邊欄 ====================
st.sidebar.title("Menu 功能選單")
page_choice = st.sidebar.radio("切換功能頁面", [
    "📊 財務總覽 & 預算監控",
    "📋 歷史收支明細",
    "💸 每日單筆記帳 (收/支)",
    "📈 投資持倉記錄",
    "🤖 AI 理財建議",
    "📊 財務年度分析",
    "📤 批量上載 Excel/CSV 檔案",
    "⚙️ 自訂您的資產/預算初始值"
])
st.sidebar.markdown("---")
st.sidebar.info("💡 數據已雲端儲存，刷新頁面不會消失！")

all_accs = list(st.session_state.my_assets.keys()) + list(st.session_state.my_liabilities.keys())
if not all_accs:
    all_accs = ["現金", "銀行帳戶"]

# ══════════════════════════════════════════════════════
# 頁面 1: 財務總覽
# ══════════════════════════════════════════════════════
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
        st.subheader("🎯 預算使用進度")
        for cat, b_amount in st.session_state.my_budget.items():
            a_amount = actual_spent_map.get(cat, 0.0)
            if b_amount <= 0 and a_amount <= 0:
                continue
            use_rate = (a_amount / b_amount * 100) if b_amount > 0 else 100.0
            use_rate_capped = min(use_rate, 100)
            if use_rate >= 100:
                bar_color = "#E24B4A"; status = "🔴 超支"
            elif use_rate >= 80:
                bar_color = "#EF9F27"; status = "🟡 預警"
            else:
                bar_color = "#1D9E75"; status = "🟢"
            bar_html = (
                f"<div style='margin-bottom:10px'>"
                f"<div style='display:flex;justify-content:space-between;font-size:13px;margin-bottom:3px'>"
                f"<span><b>{cat}</b> {status}</span>"
                f"<span style='color:gray'>${a_amount:,.0f} / ${b_amount:,.0f}</span>"
                f"</div>"
                f"<div style='background:#1a2a3a;border-radius:6px;height:10px;overflow:hidden'>"
                f"<div style='width:{use_rate_capped}%;background:{bar_color};height:100%;border-radius:6px'></div>"
                f"</div></div>"
            )
            st.markdown(bar_html, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📈 收支趨勢")
    if not df_current_logs.empty:
        df_trend = df_current_logs.copy()
        df_trend["日期"] = pd.to_datetime(df_trend["日期"], errors="coerce")
        df_trend = df_trend.dropna(subset=["日期"])
        is_inc = (df_trend["類型"] == "收入 📥") | (df_trend["分類"] == "收入")
        df_inc = df_trend[is_inc].groupby("日期")["金額"].sum().reset_index(); df_inc["類型"] = "收入"
        df_exp = df_trend[~is_inc].groupby("日期")["金額"].sum().reset_index(); df_exp["類型"] = "支出"
        df_line = pd.concat([df_inc, df_exp], ignore_index=True)
        if not df_line.empty:
            fig_line = px.line(df_line, x="日期", y="金額", color="類型",
                               color_discrete_map={"收入": "#1D9E75", "支出": "#E24B4A"}, markers=True)
            fig_line.update_layout(template="plotly_dark", margin=dict(l=10, r=10, t=10, b=10),
                                   legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig_line, use_container_width=True)

    st.markdown("---")
    st.subheader("📊 本月 vs 上月支出比較")
    if not df_current_logs.empty:
        now_dt = datetime.now()
        this_m_start = datetime(now_dt.year, now_dt.month, 1)
        last_m = now_dt.month - 1 if now_dt.month > 1 else 12
        last_m_year = now_dt.year if now_dt.month > 1 else now_dt.year - 1
        last_m_start = datetime(last_m_year, last_m, 1)
        last_m_end = datetime(last_m_year, last_m, calendar.monthrange(last_m_year, last_m)[1], 23, 59, 59)
        df_cmp = df_current_logs.copy()
        df_cmp["日期_dt"] = pd.to_datetime(df_cmp["日期"], errors="coerce")
        is_exp_mask = ~((df_cmp["類型"] == "收入 📥") | (df_cmp["分類"] == "收入"))
        df_exp_only = df_cmp[is_exp_mask]
        this_m_data = df_exp_only[df_exp_only["日期_dt"] >= this_m_start].groupby("分類")["金額"].sum()
        last_m_data = df_exp_only[(df_exp_only["日期_dt"] >= last_m_start) & (df_exp_only["日期_dt"] <= last_m_end)].groupby("分類")["金額"].sum()
        all_cats = list(set(this_m_data.index.tolist() + last_m_data.index.tolist()))
        if all_cats:
            cmp_df = pd.DataFrame({"分類": all_cats, "本月": [this_m_data.get(c, 0) for c in all_cats], "上月": [last_m_data.get(c, 0) for c in all_cats]})
            cmp_df = cmp_df[(cmp_df["本月"] > 0) | (cmp_df["上月"] > 0)].sort_values("本月", ascending=False)
            cmp_melt = cmp_df.melt(id_vars="分類", var_name="月份", value_name="金額")
            fig_bar = px.bar(cmp_melt, x="分類", y="金額", color="月份", barmode="group",
                             color_discrete_map={"本月": "#378ADD", "上月": "#888780"})
            fig_bar.update_layout(template="plotly_dark", margin=dict(l=10, r=10, t=10, b=10),
                                  legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig_bar, use_container_width=True)

    st.info(f"📋 共有 **{len(st.session_state.my_logs)}** 筆記錄，詳細請前往「📋 歷史收支明細」。")

# ══════════════════════════════════════════════════════
# 頁面 2: 歷史收支明細
# ══════════════════════════════════════════════════════
elif page_choice == "📋 歷史收支明細":
    st.subheader("📋 歷史收支明細")

    if "editing_index" not in st.session_state:
        st.session_state.editing_index = None

    now = datetime.now()
    this_month_start = date(now.year, now.month, 1)
    last_month = now.month - 1 if now.month > 1 else 12
    last_month_year = now.year if now.month > 1 else now.year - 1
    last_month_start = date(last_month_year, last_month, 1)
    last_month_end = date(last_month_year, last_month, calendar.monthrange(last_month_year, last_month)[1])

    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    with f_col1:
        if st.button("本月", use_container_width=True): st.session_state.filter_mode = "本月"
    with f_col2:
        if st.button("上月", use_container_width=True): st.session_state.filter_mode = "上月"
    with f_col3:
        if st.button("全部", use_container_width=True): st.session_state.filter_mode = "全部"
    with f_col4:
        if st.button("自訂日期", use_container_width=True): st.session_state.filter_mode = "自訂"

    if "filter_mode" not in st.session_state:
        st.session_state.filter_mode = "全部"

    if st.session_state.filter_mode == "自訂":
        d_col1, d_col2 = st.columns(2)
        with d_col1: custom_start = st.date_input("開始日期", value=this_month_start, key="custom_start")
        with d_col2: custom_end = st.date_input("結束日期", value=date.today(), key="custom_end")
    else:
        custom_start = this_month_start; custom_end = date.today()

    sort_col1, sort_col2, export_col = st.columns([2, 2, 1])
    with sort_col1: sort_by = st.selectbox("排序方式", ["日期", "類型", "分類", "金額"], key="sort_by")
    with sort_col2: sort_order = st.radio("順序", ["新→舊 / 高→低", "舊→新 / 低→高"], key="sort_order", horizontal=True)
    sort_ascending = sort_order == "舊→新 / 低→高"

    st.caption(f"目前篩選：**{st.session_state.filter_mode}**")
    st.markdown("---")

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
        elif st.session_state.filter_mode == "本月" and log_date and log_date >= this_month_start:
            include = True
        elif st.session_state.filter_mode == "上月" and log_date and last_month_start <= log_date <= last_month_end:
            include = True
        elif st.session_state.filter_mode == "自訂" and log_date and custom_start <= log_date <= custom_end:
            include = True
        if include:
            filtered_logs.append((i, log, log_date))

    if sort_by == "日期": filtered_logs.sort(key=lambda x: x[2] or date.min, reverse=not sort_ascending)
    elif sort_by == "類型": filtered_logs.sort(key=lambda x: x[1].get("類型",""), reverse=not sort_ascending)
    elif sort_by == "分類": filtered_logs.sort(key=lambda x: x[1].get("分類",""), reverse=not sort_ascending)
    elif sort_by == "金額": filtered_logs.sort(key=lambda x: float(x[1].get("金額",0)), reverse=not sort_ascending)

    with export_col:
        if filtered_logs:
            import io
            export_df = pd.DataFrame([log for _, log, _ in filtered_logs])
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                export_df.to_excel(writer, index=False, sheet_name="收支明細")
            buf.seek(0)
            st.download_button("📥 匯出", data=buf,
                               file_name=f"收支明細_{datetime.now().strftime('%Y%m%d')}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               use_container_width=True)

    if not filtered_logs:
        st.info("此時間範圍內沒有記錄。")
    else:
        st.caption(f"共 {len(filtered_logs)} 筆記錄")
        h1,h2,h3,h4,h5,h6,h7 = st.columns([1.2,1.2,1,1.5,1,0.5,0.5])
        h1.markdown("**日期**"); h2.markdown("**類型**"); h3.markdown("**分類**")
        h4.markdown("**項目**"); h5.markdown("**金額**"); h6.markdown("✏️"); h7.markdown("🗑️")
        st.markdown("---")

        for idx, (i, log, _) in enumerate(filtered_logs):
            col_date,col_type,col_cat,col_item,col_amt,col_edit,col_del = st.columns([1.2,1.2,1,1.5,1,0.5,0.5])
            col_date.write(log.get("日期",""))
            col_type.write(log.get("類型",""))
            col_cat.write(log.get("分類",""))
            col_item.write(log.get("項目",""))
            col_amt.write(f'${log.get("金額",0):,.1f}')
            if col_edit.button("✏️", key=f"edit_{i}_{idx}"):
                st.session_state.editing_index = i
            if col_del.button("🗑️", key=f"del_{i}_{idx}"):
                st.session_state.my_logs.pop(i); save_now(); st.success("✅ 已刪除"); st.rerun()

            if st.session_state.editing_index == i:
                with st.form(key=f"edit_form_{i}_{idx}"):
                    st.markdown("**編輯記錄**")
                    e1,e2,e3 = st.columns(3)
                    with e1:
                        new_date = st.text_input("日期", value=log.get("日期",""), key=f"edate_{i}_{idx}")
                        new_type = st.selectbox("類型", ["支出 💸","收入 📥"], index=0 if log.get("類型")=="支出 💸" else 1, key=f"etype_{i}_{idx}")
                    with e2:
                        new_cat = st.text_input("分類", value=log.get("分類",""), key=f"ecat_{i}_{idx}")
                        new_subcat = st.text_input("子分類", value=log.get("子分類",""), key=f"esubcat_{i}_{idx}")
                    with e3:
                        new_item = st.text_input("項目", value=log.get("項目",""), key=f"eitem_{i}_{idx}")
                        new_amt = st.number_input("金額", value=float(log.get("金額",0)), min_value=0.0, key=f"eamt_{i}_{idx}")
                        new_acc = st.text_input("帳戶/備註", value=log.get("帳戶/備註",""), key=f"eacc_{i}_{idx}")
                    sb,cb = st.columns(2)
                    with sb:
                        if st.form_submit_button("💾 儲存修改", use_container_width=True):
                            st.session_state.my_logs[i] = {"日期":new_date,"類型":new_type,"分類":new_cat,"子分類":new_subcat,"項目":new_item,"金額":float(new_amt),"帳戶/備註":new_acc}
                            save_now(); st.session_state.editing_index = None; st.success("✅ 已儲存"); st.rerun()
                    with cb:
                        if st.form_submit_button("取消", use_container_width=True):
                            st.session_state.editing_index = None; st.rerun()
            st.divider()

# ══════════════════════════════════════════════════════
# 頁面 3: 單筆記帳
# ══════════════════════════════════════════════════════
elif page_choice == "💸 每日單筆記帳 (收/支)":
    st.subheader("📥 填寫日常單筆收支")
    with st.form("single_entry_form", clear_on_submit=True):
        c1,c2,c3 = st.columns(3)
        with c1:
            in_date = st.date_input("日期", datetime.now())
            in_type = st.selectbox("交易類型", ["支出 💸","收入 📥"])
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
                if in_acc in st.session_state.my_assets: st.session_state.my_assets[in_acc] += in_amount
                if in_acc in st.session_state.my_liabilities: st.session_state.my_liabilities[in_acc] -= in_amount
            else:
                if in_acc in st.session_state.my_assets: st.session_state.my_assets[in_acc] -= in_amount
                if in_acc in st.session_state.my_liabilities: st.session_state.my_liabilities[in_acc] += in_amount
            st.session_state.my_logs.append({"日期":in_date.strftime("%Y/%m/%d"),"類型":in_type,"分類":in_cat,"子分類":in_subcat,"項目":in_title,"金額":float(in_amount),"帳戶/備註":in_acc})
            save_now(); st.success(f"✅ 已記入：{in_title} ${in_amount}"); st.rerun()

# ══════════════════════════════════════════════════════
# 頁面 4: 投資持倉記錄（修正 FIFO）
# ══════════════════════════════════════════════════════
elif page_choice == "📈 投資持倉記錄":
    st.subheader("📈 投資持倉記錄")
    st.caption("交易記錄為唯一數據源 — FIFO 自動計算持倉（買入成本含手續費，賣出扣除手續費）")

    if "my_trades" not in st.session_state:
        st.session_state.my_trades = []

    # 自動更新按鈕
    top_right_col = st.columns([3,1])[1]
    with top_right_col:
        if YFINANCE_AVAILABLE:
            if st.button("🔄 自動更新股價", use_container_width=True):
                updated, failed = 0, []
                with st.spinner("正在抓取股價…"):
                    for h in st.session_state.my_holdings:
                        ticker = extract_ticker(h.get("名稱",""), h.get("幣別","USD"))
                        if ticker:
                            price, err = fetch_price(ticker)
                            if price:
                                qty = float(h.get("數量") or 0)
                                cost = float(h.get("平均成本") or 0)
                                h["現價"] = price; h["市值"] = round(qty*price,4); h["盈虧"] = round(qty*(price-cost),4)
                                updated += 1
                            else:
                                failed.append(f"{h.get('名稱','')}（{ticker}）: {err}")
                        else:
                            failed.append(f"{h.get('名稱','')}：無法識別 ticker，請在名稱前加股票代號如 `MU 美光`")
                save_now()
                if updated: st.success(f"✅ 更新 {updated} 筆")
                for f in failed: st.warning(f"⚠️ {f}")

    tab1, tab2 = st.tabs(["📊 持倉總覽", "📋 交易記錄"])

    # ── Tab1: 持倉總覽 ──
    with tab1:
        if st.session_state.my_holdings:
            st.markdown("#### 🌐 總持倉總覽")

            usd_h = [h for h in st.session_state.my_holdings if h.get("幣別","USD") == "USD"]
            hkd_h = [h for h in st.session_state.my_holdings if h.get("幣別","USD") == "HKD"]

            fx_col1, fx_col2 = st.columns([2,1])
            with fx_col1: display_ccy = st.radio("顯示幣別", ["HKD 港元","USD 美元"], horizontal=True, key="portfolio_ccy")
            with fx_col2: usd_to_hkd = st.number_input("USD→HKD 匯率", value=7.80, min_value=1.0, step=0.01, key="fx_rate")
            hkd_to_usd = 1.0 / usd_to_hkd

            def mv(h): return float(h.get("市值") or 0)
            def pnl(h): return float(h.get("盈虧") or 0)
            def cost_val(h): return float(h.get("數量") or 0) * float(h.get("平均成本") or 0)

            if display_ccy == "HKD 港元":
                sym = "HK$"
                total_mv_disp = sum(mv(h) for h in hkd_h) + sum(mv(h) for h in usd_h) * usd_to_hkd
                total_cost_disp = sum(cost_val(h) for h in hkd_h) + sum(cost_val(h) for h in usd_h) * usd_to_hkd
                total_pnl_disp = sum(pnl(h) for h in hkd_h) + sum(pnl(h) for h in usd_h) * usd_to_hkd
            else:
                sym = "USD $"
                total_mv_disp = sum(mv(h) for h in usd_h) + sum(mv(h) for h in hkd_h) * hkd_to_usd
                total_cost_disp = sum(cost_val(h) for h in usd_h) + sum(cost_val(h) for h in hkd_h) * hkd_to_usd
                total_pnl_disp = sum(pnl(h) for h in usd_h) + sum(pnl(h) for h in hkd_h) * hkd_to_usd

            pnl_pct = (total_pnl_disp / total_cost_disp * 100) if total_cost_disp > 0 else 0.0
            pnl_sign = "+" if total_pnl_disp >= 0 else ""

            # 已實現盈虧
            realized_map = get_realized_pnl_map(st.session_state.my_trades)
            total_realized = sum(v * (usd_to_hkd if k[1]=="USD" and display_ccy=="HKD 港元" else hkd_to_usd if k[1]=="HKD" and display_ccy=="USD 美元" else 1) for k,v in realized_map.items())

            t1,t2,t3,t4,t5 = st.columns(5)
            t1.metric("💼 持倉市值", f"{sym}{total_mv_disp:,.2f}")
            t2.metric("📊 持倉成本", f"{sym}{total_cost_disp:,.2f}")
            t3.metric("💰 未實現盈虧", f"{sym}{total_pnl_disp:,.2f}", delta=f"{pnl_sign}{pnl_pct:.2f}%", delta_color="normal")
            t4.metric("✅ 已實現盈虧", f"{sym}{total_realized:,.2f}", delta_color="normal")
            t5.metric("📌 持倉數目", f"{len(st.session_state.my_holdings)} 隻")

            # 圓餅圖
            pie_col1, pie_col2 = st.columns(2)
            usd_pie = pd.DataFrame([{"名稱":h["名稱"],"市值":mv(h)} for h in usd_h if mv(h)>0])
            hkd_pie = pd.DataFrame([{"名稱":h["名稱"],"市值":mv(h)} for h in hkd_h if mv(h)>0])
            with pie_col1:
                if not usd_pie.empty:
                    fig_u = px.pie(usd_pie, values="市值", names="名稱", hole=0.45,
                                   color_discrete_sequence=["#3b82f6","#60a5fa","#93c5fd","#1d4ed8","#2563eb"],
                                   title="🇺🇸 美股佔比")
                    fig_u.update_layout(template="plotly_dark", margin=dict(l=5,r=5,t=40,b=5))
                    fig_u.update_traces(textposition="inside", textinfo="percent+label")
                    st.plotly_chart(fig_u, use_container_width=True)
                else:
                    st.info("尚無美股持倉")
            with pie_col2:
                if not hkd_pie.empty:
                    fig_h = px.pie(hkd_pie, values="市值", names="名稱", hole=0.45,
                                   color_discrete_sequence=["#00d4aa","#34d399","#6ee7b7","#059669","#10b981"],
                                   title="🇭🇰 港股佔比")
                    fig_h.update_layout(template="plotly_dark", margin=dict(l=5,r=5,t=40,b=5))
                    fig_h.update_traces(textposition="inside", textinfo="percent+label")
                    st.plotly_chart(fig_h, use_container_width=True)
                else:
                    st.info("尚無港股持倉")

            st.markdown("---")

            def render_holdings_group(h_list, ccy_sym, ccy_label):
                if not h_list:
                    st.info(f"尚無 {ccy_label} 持倉"); return
                total_mv_g = sum(mv(h) for h in h_list)
                total_pnl_g = sum(pnl(h) for h in h_list)
                total_cost_g = sum(cost_val(h) for h in h_list)
                pnl_pct_g = (total_pnl_g / total_cost_g * 100) if total_cost_g > 0 else 0.0
                sm1,sm2,sm3 = st.columns(3)
                sm1.metric("💼 總市值", f"{ccy_sym}{total_mv_g:,.2f}")
                sm2.metric("📊 總成本", f"{ccy_sym}{total_cost_g:,.2f}")
                sm3.metric("💰 未實現盈虧", f"{ccy_sym}{total_pnl_g:,.2f}", delta=f"{'+'if total_pnl_g>=0 else ''}{pnl_pct_g:.2f}%", delta_color="normal")

                hh1,hh2,hh3,hh4,hh5,hh6 = st.columns([2.5,1,1,1,1.5,1.2])
                hh1.markdown("**名稱**"); hh2.markdown("**數量**"); hh3.markdown("**現價**")
                hh4.markdown("**均成本**"); hh5.markdown("**未實現盈虧**"); hh6.markdown("**已實現盈虧**")
                st.markdown("---")

                for h in h_list:
                    c1,c2,c3,c4,c5,c6 = st.columns([2.5,1,1,1,1.5,1.2])
                    pnl_h = float(h.get("盈虧") or 0)
                    qty = float(h.get("數量") or 0)
                    h_cost = float(h.get("平均成本") or 0)
                    h_price = float(h.get("現價") or 0)
                    pnl_p = (pnl_h/(qty*h_cost)*100) if (qty*h_cost)>0 else 0.0
                    clr = "#1D9E75" if pnl_h >= 0 else "#E24B4A"
                    sgn = "+" if pnl_h >= 0 else ""
                    real_pnl = float(h.get("已實現盈虧") or 0)
                    real_clr = "#1D9E75" if real_pnl >= 0 else "#E24B4A"
                    real_sgn = "+" if real_pnl >= 0 else ""
                    c1.write(h.get("名稱",""))
                    c2.write(f"{qty:,.4g}")
                    c3.write(f"{ccy_sym}{h_price:,.2f}" if h_price > 0 else "—")
                    c4.write(f"{ccy_sym}{h_cost:,.4f}")
                    c5.markdown(f'<span style="color:{clr};font-weight:600">{sgn}{ccy_sym}{pnl_h:,.2f}{"<br><small>"+sgn+str(round(pnl_p,1))+"%</small>" if h_price>0 else ""}</span>', unsafe_allow_html=True)
                    c6.markdown(f'<span style="color:{real_clr};font-weight:600">{real_sgn}{ccy_sym}{real_pnl:,.2f}</span>', unsafe_allow_html=True)
                    st.divider()

            st.markdown("### 🇺🇸 美股 / USD")
            render_holdings_group(usd_h, "USD $", "USD")
            st.markdown("---")
            st.markdown("### 🇭🇰 港股 / HKD")
            render_holdings_group(hkd_h, "HK$", "HKD")
        else:
            st.info("💡 尚無持倉，請到「📋 交易記錄」tab 新增買入交易。")

    # ── Tab2: 交易記錄 ──
    with tab2:
        st.write("#### 📝 新增交易")
        with st.form("add_trade_form", clear_on_submit=True):
            tr1,tr2,tr3,tr4 = st.columns([1.8,1,1,1])
            with tr1: tr_name = st.text_input("股票名稱", placeholder="例如：MU 美光科技")
            with tr2: tr_type = st.selectbox("交易類型", ["📈 買入","📉 賣出"])
            with tr3: tr_currency = st.selectbox("幣別", ["USD 🇺🇸","HKD 🇭🇰"])
            with tr4: tr_date = st.date_input("交易日期", datetime.now())
            tr5,tr6,tr7,tr8 = st.columns(4)
            with tr5: tr_qty = st.number_input("數量", min_value=0.0, step=0.01)
            with tr6: tr_price = st.number_input("成交價", min_value=0.0, step=0.01)
            with tr7: tr_fee = st.number_input("手續費", min_value=0.0, step=0.01)
            with tr8: tr_note = st.text_input("備註", placeholder="可空白")
            is_buy = "買" in tr_type
            if tr_qty > 0 and tr_price > 0:
                net_amt = tr_qty * tr_price + tr_fee if is_buy else tr_qty * tr_price - tr_fee
                st.caption(f"💡 成交金額：{tr_qty*tr_price:,.2f}　手續費後淨額：{net_amt:,.2f}")
            if st.form_submit_button("✅ 確認記錄", use_container_width=True):
                if tr_name.strip() and tr_qty > 0 and tr_price > 0:
                    tc = "USD" if tr_currency.startswith("USD") else "HKD"
                    net = tr_qty*tr_price + tr_fee if is_buy else tr_qty*tr_price - tr_fee
                    st.session_state.my_trades.append({
                        "日期": tr_date.strftime("%Y/%m/%d"),
                        "名稱": tr_name.strip(),
                        "類型": "買入" if is_buy else "賣出",
                        "幣別": tc,
                        "數量": tr_qty,
                        "成交價": tr_price,
                        "手續費": tr_fee,
                        "備註": tr_note,
                        "成交金額": round(net, 4),
                    })
                    save_now()
                    refresh_holdings()
                    st.success(f"✅ {'買入' if is_buy else '賣出'} {tr_name.strip()} × {tr_qty} @ {tr_price}")
                    st.rerun()
                else:
                    st.warning("請填寫名稱、數量及成交價")

        st.markdown("---")
        if st.session_state.my_trades:
            trades_df = pd.DataFrame(st.session_state.my_trades)
            f1,f2,f3 = st.columns(3)
            with f1: f_name = st.text_input("🔍 搜尋股票", key="tr_search")
            with f2: f_type = st.selectbox("交易類型", ["全部","買入","賣出"], key="tr_filter_type")
            with f3: f_cur = st.selectbox("幣別", ["全部","USD","HKD"], key="tr_filter_cur")
            filtered = trades_df.copy()
            if f_name: filtered = filtered[filtered["名稱"].str.contains(f_name, case=False, na=False)]
            if f_type != "全部": filtered = filtered[filtered["類型"] == f_type]
            if f_cur != "全部": filtered = filtered[filtered["幣別"] == f_cur]
            filtered = filtered.sort_values("日期", ascending=False).reset_index(drop=True)

            buy_df = filtered[filtered["類型"]=="買入"]
            sell_df = filtered[filtered["類型"]=="賣出"]
            total_buy = float(buy_df["成交金額"].sum()) if not buy_df.empty else 0.0
            total_sell = float(sell_df["成交金額"].sum()) if not sell_df.empty else 0.0

            s1,s2,s3,s4 = st.columns(4)
            s1.metric("📈 買入總額", f"{total_buy:,.2f}")
            s2.metric("📉 賣出總額", f"{total_sell:,.2f}")
            s3.metric("📋 交易筆數", f"{len(filtered)} 筆")
            s4.metric("📌 持倉股數", f"{len(st.session_state.my_holdings)} 隻")

            th1,th2,th3,th4,th5,th6,th7,th8,th9 = st.columns([1.2,1.8,0.8,0.7,0.8,1,1,0.9,0.5])
            th1.markdown("**日期**"); th2.markdown("**名稱**"); th3.markdown("**類型**")
            th4.markdown("**幣別**"); th5.markdown("**數量**"); th6.markdown("**成交價**")
            th7.markdown("**淨額**"); th8.markdown("**備註**"); th9.markdown("🗑️")
            st.markdown("---")

            for idx, row in filtered.iterrows():
                c1,c2,c3,c4,c5,c6,c7,c8,c9 = st.columns([1.2,1.8,0.8,0.7,0.8,1,1,0.9,0.5])
                clr = "#1D9E75" if row["類型"]=="買入" else "#E24B4A"
                c1.write(row["日期"]); c2.write(row["名稱"])
                c3.markdown(f'<span style="color:{clr};font-weight:600">{row["類型"]}</span>', unsafe_allow_html=True)
                c4.write(row["幣別"]); c5.write(f'{float(row["數量"]):,.4g}')
                c6.write(f'{float(row["成交價"]):,.4f}'); c7.write(f'{float(row["成交金額"]):,.4f}')
                c8.write(row.get("備註",""))
                match_idx = next((j for j,t in enumerate(st.session_state.my_trades)
                    if t["日期"]==row["日期"] and t["名稱"]==row["名稱"]
                    and abs(float(t["成交價"])-float(row["成交價"]))<1e-6
                    and abs(float(t["數量"])-float(row["數量"]))<1e-6), -1)
                if c9.button("🗑️", key=f"del_trade_{idx}"):
                    if match_idx >= 0:
                        st.session_state.my_trades.pop(match_idx)
                        save_now(); refresh_holdings(); st.rerun()
                st.divider()
        else:
            st.info("💡 尚無交易記錄，填寫上方表單加入。")

# ══════════════════════════════════════════════════════
# 頁面 5: AI 理財建議
# ══════════════════════════════════════════════════════
elif page_choice == "🤖 AI 理財建議":
    st.subheader("🤖 AI 理財建議")
    st.caption("根據你的真實財務數據，由 Claude AI 提供個人化建議")

    # 建立財務摘要給 AI
    _realized_map = get_realized_pnl_map(st.session_state.get("my_trades", []))
    _total_realized_usd = sum(v for k,v in _realized_map.items() if k[1]=="USD")
    _total_realized_hkd = sum(v for k,v in _realized_map.items() if k[1]=="HKD")

    holdings_summary_text = ""
    for h in st.session_state.get("my_holdings", []):
        pnl_h = float(h.get("盈虧") or 0)
        pnl_p = (pnl_h / (float(h.get("數量",0))*float(h.get("平均成本",1)))*100) if float(h.get("數量",0))*float(h.get("平均成本",1))>0 else 0
        holdings_summary_text += f"- {h.get('名稱','')} ({h.get('幣別','USD')}): 持{float(h.get('數量',0)):,.2f}股 均成本{float(h.get('平均成本',0)):,.4f} 現價{float(h.get('現價',0)):,.2f} 未實現{'+'if pnl_h>=0 else ''}{pnl_h:,.2f} ({pnl_p:+.1f}%)\n"

    fin_summary = f"""
用戶財務狀況（港幣為主）：
- 總資產：HK${total_assets:,.2f}
- 總負債：HK${total_liabilities:,.2f}
- 淨資產：HK${net_worth:,.2f}
- 本月收入：${total_actual_income:,.2f}
- 本月支出：${total_actual_expense:,.2f}
- 儲蓄率：{savings_rate:.1f}%
- 持倉市值（USD）：${_holdings_usd_mv:,.2f}
- 持倉市值（HKD）：HK${_holdings_hkd_mv:,.2f}
- 已實現盈虧（USD）：${_total_realized_usd:,.2f}
- 已實現盈虧（HKD）：HK${_total_realized_hkd:,.2f}
- 負債比：{(total_liabilities/total_assets*100) if total_assets>0 else 0:.1f}%

持倉明細：
{holdings_summary_text if holdings_summary_text else "（尚無持倉）"}

主要支出分類（本月）：
""" + "\n".join([f"- {k}：${v:,.2f}" for k,v in actual_spent_map.items() if v > 0])

    ai_mode = st.radio("選擇建議類型", 
        ["📊 整體財務健康評估", "💡 儲蓄改善建議", "📈 投資持倉分析", "🎯 月度預算優化"], 
        horizontal=True)
    
    custom_q = st.text_input("或輸入自訂問題（可空白）", placeholder="例如：我應該增持還是減持現有倉位？")

    if st.button("🤖 獲取 AI 建議", use_container_width=True):
        mode_prompts = {
            "📊 整體財務健康評估": "請根據以下財務數據，對用戶的整體財務健康狀況作出評估，包括：資產負債比例分析、儲蓄率評價、風險提示，以及3個具體可行的改善建議。請用繁體中文回答，語氣親切專業。",
            "💡 儲蓄改善建議": "請根據以下財務數據，分析用戶的支出結構，找出可以削減的開支項目，並提供具體的儲蓄行動計劃。目標是提升儲蓄率。請用繁體中文回答。",
            "📈 投資持倉分析": "請根據以下持倉數據，分析投資組合的風險分佈、個股表現，並提供調倉或加減倉的參考建議。注意提醒這只是參考，非投資建議。請用繁體中文回答。",
            "🎯 月度預算優化": "請根據以下財務數據，為用戶制定一個更優化的月度預算分配方案，並解釋每個預算類別應佔收入的合理比例。請用繁體中文回答。"
        }
        
        prompt = mode_prompts.get(ai_mode, "請分析以下財務狀況並提供建議。")
        if custom_q.strip():
            prompt = f"請用繁體中文回答以下問題：{custom_q.strip()}\n\n參考財務數據如下："
        
        full_prompt = f"{prompt}\n\n{fin_summary}"
        
        with st.spinner("🤖 AI 正在分析您的財務狀況…"):
            try:
                response = requests.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={"Content-Type": "application/json"},
                    json={
                        "model": "claude-sonnet-4-6",
                        "max_tokens": 1000,
                        "system": "你是一位專業的香港個人理財顧問，擅長分析用戶財務數據並提供實用建議。回答要具體、有條理，使用繁體中文，適當使用emoji讓內容更易讀。",
                        "messages": [{"role": "user", "content": full_prompt}]
                    }
                )
                data = response.json()
                ai_text = data["content"][0]["text"]
                st.markdown(f'<div class="ai-card">{ai_text.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"❌ AI 請求失敗：{e}")

    st.markdown("---")
    st.caption("⚠️ AI 建議僅供參考，不構成投資或財務建議。重大財務決定請諮詢專業顧問。")

# ══════════════════════════════════════════════════════
# 頁面 6: 財務年度分析
# ══════════════════════════════════════════════════════
elif page_choice == "📊 財務年度分析":
    st.subheader("📊 財務年度分析")

    now_dt = datetime.now()
    year_options = list(range(now_dt.year, now_dt.year - 5, -1))
    selected_year = st.selectbox("選擇年份", year_options, key="year_sel")

    if df_current_logs.empty:
        st.info("💡 尚無記帳數據。")
    else:
        df_yr = df_current_logs.copy()
        df_yr["日期_dt"] = pd.to_datetime(df_yr["日期"], errors="coerce")
        df_yr = df_yr[df_yr["日期_dt"].dt.year == selected_year].copy()
        df_yr["月份"] = df_yr["日期_dt"].dt.month

        if df_yr.empty:
            st.info(f"💡 {selected_year} 年沒有記帳數據。")
        else:
            is_inc_yr = (df_yr["類型"] == "收入 📥") | (df_yr["分類"] == "收入")
            df_inc_yr = df_yr[is_inc_yr].groupby("月份")["金額"].sum().reindex(range(1,13), fill_value=0)
            df_exp_yr = df_yr[~is_inc_yr].groupby("月份")["金額"].sum().reindex(range(1,13), fill_value=0)
            df_sav_yr = df_inc_yr - df_exp_yr

            months = [f"{m}月" for m in range(1,13)]

            # 年度統計
            y1,y2,y3,y4 = st.columns(4)
            y1.metric("💰 年度總收入", f"${df_inc_yr.sum():,.0f}")
            y2.metric("💸 年度總支出", f"${df_exp_yr.sum():,.0f}")
            y3.metric("📈 年度儲蓄", f"${df_sav_yr.sum():,.0f}")
            avg_sav_rate = (df_sav_yr.sum() / df_inc_yr.sum() * 100) if df_inc_yr.sum() > 0 else 0
            y4.metric("📊 平均儲蓄率", f"{avg_sav_rate:.1f}%")

            st.markdown("---")

            # 月度收支柱狀圖
            st.markdown("#### 📅 月度收支概覽")
            fig_yr = go.Figure()
            fig_yr.add_trace(go.Bar(name="收入", x=months, y=df_inc_yr.values, marker_color="#1D9E75"))
            fig_yr.add_trace(go.Bar(name="支出", x=months, y=df_exp_yr.values, marker_color="#E24B4A"))
            fig_yr.add_trace(go.Scatter(name="儲蓄", x=months, y=df_sav_yr.values,
                                        mode="lines+markers", line=dict(color="#3b82f6", width=2),
                                        marker=dict(size=6)))
            fig_yr.update_layout(template="plotly_dark", barmode="group",
                                  margin=dict(l=10,r=10,t=10,b=10),
                                  legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig_yr, use_container_width=True)

            # 儲蓄率趨勢
            st.markdown("#### 📈 月度儲蓄率趨勢")
            sav_rate_monthly = []
            for m in range(1,13):
                inc = df_inc_yr[m]; exp = df_exp_yr[m]
                sav_rate_monthly.append((inc - exp) / inc * 100 if inc > 0 else 0)
            fig_sav = go.Figure()
            fig_sav.add_trace(go.Scatter(x=months, y=sav_rate_monthly, mode="lines+markers",
                                          line=dict(color="#00d4aa", width=2), fill="tozeroy",
                                          fillcolor="rgba(0,212,170,0.1)"))
            fig_sav.add_hline(y=20, line_dash="dash", line_color="#EF9F27",
                               annotation_text="建議儲蓄率 20%")
            fig_sav.update_layout(template="plotly_dark", yaxis_title="儲蓄率 (%)",
                                   margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig_sav, use_container_width=True)

            # 年度支出分類
            st.markdown("#### 📊 年度支出分類分析")
            exp_cat = df_yr[~is_inc_yr].groupby("分類")["金額"].sum().sort_values(ascending=False)
            if not exp_cat.empty:
                col_pie, col_bar = st.columns(2)
                with col_pie:
                    fig_ep = px.pie(values=exp_cat.values, names=exp_cat.index, hole=0.4,
                                    color_discrete_sequence=px.colors.sequential.Mint)
                    fig_ep.update_layout(template="plotly_dark", margin=dict(l=5,r=5,t=10,b=5))
                    st.plotly_chart(fig_ep, use_container_width=True)
                with col_bar:
                    fig_eb = px.bar(x=exp_cat.values, y=exp_cat.index, orientation="h",
                                    color=exp_cat.values, color_continuous_scale="RdYlGn_r")
                    fig_eb.update_layout(template="plotly_dark", showlegend=False,
                                          margin=dict(l=10,r=10,t=10,b=10), yaxis_title="")
                    st.plotly_chart(fig_eb, use_container_width=True)

            # 月度明細表
            st.markdown("#### 📋 月度明細")
            detail_df = pd.DataFrame({
                "月份": months,
                "收入": [f"${v:,.0f}" for v in df_inc_yr.values],
                "支出": [f"${v:,.0f}" for v in df_exp_yr.values],
                "儲蓄": [f"${v:,.0f}" for v in df_sav_yr.values],
                "儲蓄率": [f"{r:.1f}%" for r in sav_rate_monthly],
            })
            st.dataframe(detail_df, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════
# 頁面 7: 批量上載
# ══════════════════════════════════════════════════════
elif page_choice == "📤 批量上載 Excel/CSV 檔案":
    st.subheader("📤 批量匯入記帳明細")
    st.info("💡 請確保 Excel/CSV 標題包含：【日期】【分類】【項目】【金額】")
    upload_file = st.file_uploader("上傳您的檔案", type=["csv","xlsx"])
    if upload_file is not None:
        try:
            if upload_file.name.endswith('.csv'):
                try: df_imported = pd.read_csv(upload_file, encoding='utf-8-sig')
                except: df_imported = pd.read_csv(upload_file, encoding='big5')
            else:
                df_imported = pd.read_excel(upload_file, engine="openpyxl", dtype=str)
            df_imported.columns = df_imported.columns.astype(str).str.strip()
            df_imported = df_imported.dropna(how='all')
            if not df_imported.empty:
                col_mapping = {}
                for col in df_imported.columns:
                    c = str(col).strip()
                    if "日期" in c: col_mapping[col] = "日期"
                    elif "子分類" in c: col_mapping[col] = "子分類"
                    elif "分類" in c: col_mapping[col] = "分類"
                    elif "項目" in c: col_mapping[col] = "項目"
                    elif "金額" in c: col_mapping[col] = "金額"
                    elif "備註" in c or "帳戶" in c: col_mapping[col] = "帳戶/備註"
                df_imported = df_imported.rename(columns=col_mapping)
                required = ["日期","分類","項目","金額"]
                if not all(x in df_imported.columns for x in required):
                    st.error("❌ 格式不符！必須包含：日期、分類、項目、金額")
                    st.write("偵測到欄位：", list(df_imported.columns))
                else:
                    df_imported["金額"] = df_imported["金額"].astype(str).str.replace('$','').str.replace(',','').str.strip()
                    df_imported["金額"] = pd.to_numeric(df_imported["金額"], errors='coerce').fillna(0.0)
                    df_imported = df_imported[df_imported["金額"] > 0]
                    st.success(f"✅ 識別成功！共 {len(df_imported)} 筆")
                    st.dataframe(df_imported[["日期","分類","項目","金額"]], use_container_width=True, hide_index=True)
                    if st.button("🔥 確定併入帳本"):
                        for _, row in df_imported.iterrows():
                            rc = str(row.get("分類","")).strip()
                            rt = "收入 📥" if rc in st.session_state.my_income_categories or "收入" in rc or "薪資" in rc else "支出 💸"
                            st.session_state.my_logs.append({"日期":str(row.get("日期","")),"類型":rt,"分類":rc,"子分類":str(row.get("子分類","批量匯入")),"項目":str(row.get("項目","")),"金額":float(row.get("金額",0)),"帳戶/備註":str(row.get("帳戶/備註","Excel匯入"))})
                        save_now(); st.success("🚀 已合併並儲存！"); st.rerun()
        except Exception as e:
            st.error(f"❌ 讀取失敗：{e}")

# ══════════════════════════════════════════════════════
# 頁面 8: 設定
# ══════════════════════════════════════════════════════
elif page_choice == "⚙️ 自訂您的資產/預算初始值":
    st.subheader("⚙️ 個人化財務設定後台")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🚨 清空所有記帳記錄", type="primary", use_container_width=True):
            st.session_state.my_logs = []; save_now(); st.rerun()
    with col_btn2:
        if st.button("✨ 套用系統預設預算值", type="secondary", use_container_width=True):
            st.session_state.my_budget = {"飲食":3000.0,"租金":7000.0,"交通":1000.0,"其他支出":500.0}
            save_now(); st.rerun()

    st.markdown("---")
    st.write("### ➕ 自訂收入分類")
    cat_cols = st.columns(min(len(st.session_state.my_income_categories), 4))
    for idx, cat in enumerate(st.session_state.my_income_categories):
        with cat_cols[idx % 4]:
            st.markdown(f"`{cat}`")
            if st.button(f"✕ 刪除", key=f"del_cat_{idx}"):
                if len(st.session_state.my_income_categories) > 1:
                    st.session_state.my_income_categories.pop(idx); save_now(); st.rerun()
                else:
                    st.warning("至少保留一個分類！")
    new_cat = st.text_input("新增收入分類名稱")
    if st.button("新增分類 🚀"):
        if new_cat.strip() and new_cat.strip() not in st.session_state.my_income_categories:
            st.session_state.my_income_categories.append(new_cat.strip()); save_now(); st.success(f"✅ 已新增：{new_cat.strip()}"); st.rerun()
        else:
            st.warning("⚠️ 輸入無效或已存在！")

    st.markdown("---")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.write("### 🟢 資產帳戶餘額")
        for k, v in list(st.session_state.my_assets.items()):
            new_val = st.number_input(f"【{k}】", value=float(v), key=f"asset_input_{k}")
            if new_val != v: st.session_state.my_assets[k] = new_val; save_now()
        st.markdown("")
        new_asset_name = st.text_input("新增資產帳戶名稱", key="new_asset_name")
        if st.button("➕ 新增帳戶"):
            if new_asset_name.strip() and new_asset_name.strip() not in st.session_state.my_assets:
                st.session_state.my_assets[new_asset_name.strip()] = 0.0; save_now(); st.success(f"✅ 已新增"); st.rerun()
            else:
                st.warning("⚠️ 名稱無效或已存在！")
        st.markdown("---")
        st.write("### 🔴 負債初始欠款")
        for k, v in list(st.session_state.my_liabilities.items()):
            new_val = st.number_input(f"【{k}】", value=float(v), key=f"lia_input_{k}")
            if new_val != v: st.session_state.my_liabilities[k] = new_val; save_now()
    with col_s2:
        st.write("### 🎯 每月預算上限")
        for cat, b_val in list(st.session_state.my_budget.items()):
            new_budget = st.number_input(f"【{cat}】", value=float(b_val), min_value=0.0, step=100.0, key=f"budget_input_{cat}")
            if new_budget != b_val: st.session_state.my_budget[cat] = new_budget; save_now()
