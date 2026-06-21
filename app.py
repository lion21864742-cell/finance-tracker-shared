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
        "trades": [],
        "holdings_prices": {},
        "crypto_holdings": [],
        "savings_goal": 0.0,
        "savings_goal_name": "儲蓄目標"
    }

# ==================== 安全數字轉換 ====================
def safe_float(val, default=0.0):
    """安全地將任何值轉為 float，防止 None / '' / 異常格式導致 TypeError"""
    try:
        if val is None:
            return default
        return float(val)
    except (TypeError, ValueError):
        return default

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
    min-width: 0 !important;
    overflow: hidden !important;
}
[data-testid="stMetric"]:hover { border-color: rgba(0, 212, 170, 0.5) !important; transform: translateY(-2px) !important; }
[data-testid="stMetricValue"] {
    color: #f7fafc !important; font-weight: 700 !important;
    font-size: clamp(0.85rem, 2vw, 1.5rem) !important;
    white-space: nowrap !important; overflow: hidden !important; text-overflow: ellipsis !important;
}
[data-testid="stMetricLabel"] {
    color: #718096 !important; font-size: clamp(0.6rem, 1.2vw, 0.78rem) !important;
    text-transform: uppercase !important; letter-spacing: 0.05em !important;
    white-space: nowrap !important; overflow: hidden !important; text-overflow: ellipsis !important;
}
[data-testid="stMetricDelta"] { font-size: clamp(0.6rem, 1.1vw, 0.85rem) !important; }

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

.ai-card {
    background: linear-gradient(135deg, rgba(0,212,170,0.08), rgba(59,130,246,0.08));
    border: 1px solid rgba(0,212,170,0.25); border-radius: 14px;
    padding: 1.2rem 1.4rem; margin-bottom: 1rem; line-height: 1.7;
}

/* ══ iPad (<=1024px) ══ */
@media (max-width: 1024px) {
    [data-testid="stSidebar"] { min-width: 200px !important; max-width: 240px !important; }
    .main .block-container { padding-left: 0.8rem !important; padding-right: 0.8rem !important; }
    [data-testid="stMetric"] { padding: 0.8rem 0.7rem !important; border-radius: 12px !important; }
    h1 { font-size: 1.2rem !important; }
}

/* ══ 手機 (<=768px) ══ */
@media (max-width: 768px) {
    h1 { font-size: 1.1rem !important; }
    h2, h3 { font-size: 0.95rem !important; }
    .stButton > button { min-height: 2.8rem !important; font-size: 0.92rem !important; border-radius: 12px !important; }
    .stTextInput input, .stNumberInput input { font-size: 1rem !important; min-height: 2.6rem !important; }
    .main .block-container { padding-left: 0.4rem !important; padding-right: 0.4rem !important; padding-top: 0.5rem !important; }
    [data-testid="stMetric"] { padding: 0.7rem 0.6rem !important; border-radius: 10px !important; }
    .stTabs [data-baseweb="tab"] { padding: 0.4rem 0.6rem !important; font-size: 0.78rem !important; }
    [data-testid="stForm"] { padding: 0.6rem !important; }
}

/* ══ 超小屏 (<=480px) ══ */
@media (max-width: 480px) {
    h1 { font-size: 0.95rem !important; }
    [data-testid="stMetric"] { padding: 0.6rem 0.5rem !important; }
    .ai-card { padding: 0.8rem 0.9rem !important; font-size: 0.86rem !important; }
}
</style>
""", unsafe_allow_html=True)

# ==================== Stock helpers ====================
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
            return f"{int(num_match.group(1)):04d}.HK"
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

def normalize_stock_key(name: str, currency: str) -> str:
    """
    正規化股票 key，避免「6869 長飛」與「6869長飛」被當成兩隻股票。
    優先用 ticker（如 6869.HK / MU），否則用去空格名稱。
    """
    if not name:
        return ""
    ticker = extract_ticker(name, currency)
    if ticker:
        return ticker.upper()
    return "".join(name.split()).replace("\u3000", "")

# ==================== FIFO 持倉計算（normalize_stock_key 版本）====================
def compute_holdings_from_trades(trades: list) -> list:
    from collections import defaultdict

    sorted_trades = sorted(
        enumerate(trades),
        key=lambda x: (x[1].get("日期", ""), x[0])
    )
    sorted_trades = [t for _, t in sorted_trades]

    lots = defaultdict(list)          # key -> [{qty, cost}]
    realized_pnl = defaultdict(float) # key -> realized pnl
    currency_map = {}
    display_name = {}

    for tr in sorted_trades:
        raw_name = tr.get("名稱", "").strip()
        currency = tr.get("幣別", "USD")
        qty      = float(tr.get("數量") or 0)
        price    = float(tr.get("成交價") or 0)
        fee      = float(tr.get("手續費") or 0)
        ttype    = tr.get("類型", "買入")

        if qty <= 0 or price <= 0:
            continue

        key = normalize_stock_key(raw_name, currency)
        if not key:
            continue

        currency_map[key] = currency
        if key not in display_name:
            display_name[key] = raw_name

        if ttype == "買入":
            cost_per_share = (qty * price + fee) / qty
            lots[key].append({"qty": qty, "cost": cost_per_share})

        elif ttype == "賣出":
            proceeds = qty * price - fee
            remaining = qty
            sell_cost = 0.0
            while remaining > 1e-9 and lots[key]:
                oldest = lots[key][0]
                if oldest["qty"] <= remaining + 1e-9:
                    sell_cost += oldest["qty"] * oldest["cost"]
                    remaining -= oldest["qty"]
                    lots[key].pop(0)
                else:
                    sell_cost += remaining * oldest["cost"]
                    oldest["qty"] -= remaining
                    remaining = 0.0
            realized_pnl[key] += proceeds - sell_cost

    holdings = []
    for key, lot_list in lots.items():
        total_qty = sum(l["qty"] for l in lot_list)
        if total_qty < 1e-6:
            continue
        total_cost_val = sum(l["qty"] * l["cost"] for l in lot_list)
        avg_cost = total_cost_val / total_qty
        holdings.append({
            "名稱": display_name.get(key, key),
            "幣別": currency_map.get(key, "USD"),
            "數量": round(total_qty, 6),
            "現價": 0.0,
            "平均成本": round(avg_cost, 6),
            "市值": 0.0,
            "盈虧": 0.0,
            "已實現盈虧": round(realized_pnl.get(key, 0.0), 4),
            "_key": key,
        })
    return holdings

def get_realized_pnl_map(trades: list) -> dict:
    from collections import defaultdict
    sorted_trades = sorted(enumerate(trades), key=lambda x: (x[1].get("日期",""), x[0]))
    sorted_trades = [t for _, t in sorted_trades]
    lots = defaultdict(list)
    realized = defaultdict(float)
    for tr in sorted_trades:
        raw_name = tr.get("名稱","").strip()
        currency = tr.get("幣別","USD")
        qty   = float(tr.get("數量") or 0)
        price = float(tr.get("成交價") or 0)
        fee   = float(tr.get("手續費") or 0)
        ttype = tr.get("類型","買入")
        if qty <= 0 or price <= 0: continue
        key = normalize_stock_key(raw_name, currency)
        if not key: continue
        if ttype == "買入":
            lots[key].append({"qty": qty, "cost": (qty*price+fee)/qty})
        elif ttype == "賣出":
            proceeds = qty*price - fee
            rem = qty; cb = 0.0
            while rem > 1e-9 and lots[key]:
                ol = lots[key][0]
                if ol["qty"] <= rem + 1e-9:
                    cb += ol["qty"]*ol["cost"]; rem -= ol["qty"]; lots[key].pop(0)
                else:
                    cb += rem*ol["cost"]; ol["qty"] -= rem; rem = 0.0
            realized[key] += proceeds - cb
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
            st.session_state.my_holdings = []
            st.session_state.my_trades = data.get("trades", [])
            st.session_state.my_holdings_prices = data.get("holdings_prices", {})
            st.session_state.my_crypto = data.get("crypto_holdings", [])
            st.session_state.my_savings_goal = safe_float(data.get("savings_goal"), 0.0)
            st.session_state.my_savings_goal_name = data.get("savings_goal_name", "儲蓄目標")

# ==================== 登入/註冊 ====================
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
                    st.session_state.my_holdings = []
                    st.session_state.my_trades = data.get("trades", [])
                    st.session_state.my_holdings_prices = data.get("holdings_prices", {})
                    st.session_state.my_crypto = data.get("crypto_holdings", [])
                    st.session_state.my_savings_goal = safe_float(data.get("savings_goal"), 0.0)
                    st.session_state.my_savings_goal_name = data.get("savings_goal_name", "儲蓄目標")
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
                    st.session_state.my_holdings_prices = {}
                    st.session_state.my_crypto = []
                    st.session_state.my_savings_goal = 0.0
                    st.session_state.my_savings_goal_name = "儲蓄目標"
                    st.query_params["uid"] = st.session_state.uid
                    st.query_params["em"] = signup_email
                    st.success("✅ 註冊成功！歡迎使用！")
                    st.rerun()
                else:
                    st.error(f"❌ {result.get('error', {}).get('message', '註冊失敗')}")
    st.stop()

# ==================== 存檔（含現價）====================
def save_now():
    prices_map = {
        h.get("_key", f"{h['名稱']}|{h.get('幣別','USD')}"): float(h.get("現價") or 0)
        for h in st.session_state.get("my_holdings", [])
        if float(h.get("現價") or 0) > 0
    }
    save_user_data(st.session_state.uid, {
        "assets": st.session_state.my_assets,
        "liabilities": st.session_state.my_liabilities,
        "budget": st.session_state.my_budget,
        "income_categories": st.session_state.my_income_categories,
        "logs": st.session_state.my_logs,
        "trades": st.session_state.get("my_trades", []),
        "holdings_prices": prices_map,
        "crypto_holdings": st.session_state.get("my_crypto", []),
        "savings_goal": st.session_state.get("my_savings_goal", 0.0),
        "savings_goal_name": st.session_state.get("my_savings_goal_name", "儲蓄目標"),
    })

# ==================== refresh_holdings（保留現價）====================
def refresh_holdings():
    computed = compute_holdings_from_trades(st.session_state.get("my_trades", []))
    # session 中現有的現價
    session_prices = {
        h.get("_key", normalize_stock_key(h.get("名稱",""), h.get("幣別","USD"))): float(h.get("現價") or 0)
        for h in st.session_state.get("my_holdings", [])
    }
    # Firebase 儲存的現價（登入時讀取）
    saved_prices = st.session_state.get("my_holdings_prices", {})

    for h in computed:
        key = h.get("_key", "")
        old_p = session_prices.get(key, 0.0) or float(saved_prices.get(key, 0))
        if old_p > 0:
            h["現價"] = old_p
            h["市值"] = round(h["數量"] * old_p, 4)
            h["盈虧"] = round(h["數量"] * (old_p - h["平均成本"]), 4)
    st.session_state.my_holdings = computed

refresh_holdings()

# ==================== 新功能 Session State 初始化 ====================
if "my_crypto" not in st.session_state:
    st.session_state.my_crypto = []
if "my_savings_goal" not in st.session_state:
    st.session_state.my_savings_goal = 0.0
if "my_savings_goal_name" not in st.session_state:
    st.session_state.my_savings_goal_name = "儲蓄目標"

# ==================== 核心財務計算 ====================
total_assets = sum(st.session_state.my_assets.values())
total_liabilities = sum(st.session_state.my_liabilities.values())

_holdings = st.session_state.get("my_holdings", [])
_fx = 7.80
_holdings_usd_mv = sum(float(h.get("市值") or 0) for h in _holdings if h.get("幣別","USD") == "USD")
_holdings_hkd_mv = sum(float(h.get("市值") or 0) for h in _holdings if h.get("幣別","USD") == "HKD")
holdings_total_value = _holdings_usd_mv * _fx + _holdings_hkd_mv
net_worth = total_assets - total_liabilities + holdings_total_value

# ── 重複計算偵測：投資帳戶若已存有「同步」進去的持倉市值，
#    淨身家公式會把 holdings_total_value 加多一次 ──
_invest_acc_name = "投資帳戶 📈"
_invest_acc_val = float(st.session_state.my_assets.get(_invest_acc_name, 0) or 0)
_possible_double_count = (
    _invest_acc_name in st.session_state.my_assets
    and _invest_acc_val > 0
    and holdings_total_value > 0
    and abs(_invest_acc_val - holdings_total_value) < max(holdings_total_value * 0.5, 5000)
)

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

# ==================== 智能數字格式化（支援雙模式）====================
def fmt(val: float, prefix: str = "$") -> str:
    """完整數字模式：含千位分隔符，不簡寫。"""
    sign = "-" if val < 0 else ""
    return f"{sign}{prefix}{abs(val):,.0f}"

def fmt_compact(val: float, prefix: str = "$") -> str:
    """簡化模式：大數字用 K / M 簡寫。"""
    abs_val = abs(val)
    sign = "-" if val < 0 else ""
    if abs_val >= 1_000_000:
        return f"{sign}{prefix}{abs_val/1_000_000:.2f}M"
    elif abs_val >= 10_000:
        return f"{sign}{prefix}{abs_val/1000:.1f}K"
    else:
        return f"{sign}{prefix}{abs_val:,.0f}"

def fmt_by_mode(val: float, prefix: str = "$") -> str:
    if st.session_state.get("display_mode", "完整數字") == "簡化 (K/M)":
        return fmt_compact(val, prefix)
    return fmt(val, prefix)

def metric_card(label: str, value: str, delta: str = None, delta_color: str = "#00d4aa"):
    """自訂 HTML 指標卡，完全控制顯示格式，避免 st.metric 自動壓縮數字。"""
    delta_html = f'<div style="font-size:13px;color:{delta_color};margin-top:4px">{delta}</div>' if delta else ""
    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);border-radius:12px;padding:14px 18px;height:100%">
      <div style="font-size:13px;color:#a0aec0;margin-bottom:6px">{label}</div>
      <div style="font-size:26px;font-weight:700;color:#f7fafc;word-break:break-word">{value}</div>
      {delta_html}
    </div>
    """, unsafe_allow_html=True)

# ==================== 頁面標題 ====================
st.title("💎 CLOUD FINANCE MASTER PLAN 2026")
st.caption("🚀 雲端收支全功能 — FIFO持倉 · 加密資產 · 智能提醒 · 收支預測 · 多幣別匯率 · AI理財建議")

col_title, col_logout = st.columns([4, 1])
with col_logout:
    st.caption(f"👤 {st.session_state.user_email}")
    if st.button("登出", use_container_width=True):
        st.query_params.clear()
        for key in ["uid", "user_email", "my_assets", "my_liabilities",
                    "my_budget", "my_income_categories", "my_logs",
                    "my_trades", "my_holdings", "my_holdings_prices"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

st.markdown("---")

# ── 顯示模式切換 ──
mode_col1, mode_col2 = st.columns([3, 1])
with mode_col2:
    if "display_mode" not in st.session_state:
        st.session_state.display_mode = "完整數字"
    st.radio(
        "數字顯示模式", ["完整數字", "簡化 (K/M)"],
        horizontal=True, label_visibility="collapsed",
        key="display_mode"
    )

m_col1, m_col2, m_col3, m_col4 = st.columns(4)
with m_col1:
    metric_card("💰 本月收入", fmt_by_mode(total_actual_income))
with m_col2:
    metric_card("💸 本月支出", fmt_by_mode(total_actual_expense))
with m_col3:
    metric_card("📈 預計儲蓄", fmt_by_mode(expected_savings), delta=f"↑ 儲蓄率 {savings_rate:.1f}%")
with m_col4:
    _nw_delta = f"↑ 含持倉 {fmt_by_mode(holdings_total_value,'HK$')}" if holdings_total_value > 0 else None
    metric_card("👑 淨身家", fmt_by_mode(net_worth, "HK$"), delta=_nw_delta)

st.markdown("")
m2_col1, m2_col2, m2_col3, m2_col4 = st.columns(4)
with m2_col1:
    metric_card("🏦 總資產", fmt_by_mode(total_assets, "HK$"))
with m2_col2:
    _liab_delta = f"↓ {(total_liabilities/total_assets*100):.1f}% 負債比" if total_assets > 0 else None
    metric_card("💳 總負債", fmt_by_mode(total_liabilities, "HK$"), delta=_liab_delta, delta_color="#E24B4A")
with m2_col3:
    _mv_delta = f"US{fmt_by_mode(_holdings_usd_mv)} ・ HK{fmt_by_mode(_holdings_hkd_mv)}" if _holdings else None
    metric_card("📈 持倉市值", fmt_by_mode(holdings_total_value, "HK$"), delta=_mv_delta, delta_color="#a0aec0")
with m2_col4:
    _net_pnl = sum(float(h.get("盈虧") or 0) * (_fx if h.get("幣別","USD")=="USD" else 1) for h in _holdings)
    _pnl_sign = "+" if _net_pnl >= 0 else ""
    metric_card("💹 持倉盈虧", fmt_by_mode(_net_pnl, "HK$"),
                delta=f"↑ {_pnl_sign}{fmt_by_mode(abs(_net_pnl),'')}" if _net_pnl>=0 else f"↓ {fmt_by_mode(abs(_net_pnl),'')}",
                delta_color="#00d4aa" if _net_pnl>=0 else "#E24B4A")
st.markdown("---")

# ── 重複計算警示 ──
if _possible_double_count:
    st.warning(f"""
⚠️ **偵測到可能的重複計算！**

你的「{_invest_acc_name}」帳戶餘額為 **HK${_invest_acc_val:,.0f}**，與目前持倉市值
**HK${holdings_total_value:,.0f}** 非常接近——這通常是因為你曾使用「投資持倉記錄」頁的
「同步入資產帳戶」功能，把持倉市值存入了此帳戶。

但系統的「淨身家」公式會**自動即時加總**持倉市值，如果「{_invest_acc_name}」裡也存了同一筆錢，
就會**被計算兩次**，導致總資產/淨身家虛高。
    """)
    fix_col1, fix_col2 = st.columns([1, 2])
    with fix_col1:
        if st.button(f"🔧 一鍵修正：將「{_invest_acc_name}」歸零", use_container_width=True, type="primary"):
            st.session_state.my_assets[_invest_acc_name] = 0.0
            save_now()
            st.success(f"✅ 已將「{_invest_acc_name}」設為 0，持倉市值現在只會由系統自動計算一次。")
            st.rerun()
    with fix_col2:
        st.caption("修正後，「投資帳戶 📈」只用作存放其他非持倉相關的投資現金（如未投入的資金），股票/加密資產市值會由系統自動加總，無需手動同步。")
    st.markdown("---")

# ==================== 側邊欄 ====================
st.sidebar.title("Menu 功能選單")
page_choice = st.sidebar.radio("切換功能頁面", [
    "📊 財務總覽 & 預算監控",
    "📋 歷史收支明細",
    "💸 每日單筆記帳 (收/支)",
    "📈 投資持倉記錄",
    "💹 加密資產持倉",
    "🔔 智能提醒中心",
    "📉 未來3月收支預測",
    "💱 多幣別匯率",
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
            st.markdown(
                f"<div style='margin-bottom:10px'>"
                f"<div style='display:flex;justify-content:space-between;font-size:13px;margin-bottom:3px'>"
                f"<span><b>{cat}</b> {status}</span>"
                f"<span style='color:gray'>${a_amount:,.0f} / ${b_amount:,.0f}</span></div>"
                f"<div style='background:#1a2a3a;border-radius:6px;height:10px;overflow:hidden'>"
                f"<div style='width:{use_rate_capped}%;background:{bar_color};height:100%;border-radius:6px'></div>"
                f"</div></div>", unsafe_allow_html=True)

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
            fig_line.update_layout(template="plotly_dark", margin=dict(l=10,r=10,t=10,b=10),
                                   legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("💡 數據不足，記帳後自動呈現趨勢圖。")
    else:
        st.info("💡 尚無記帳數據。")

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
            cmp_df = pd.DataFrame({"分類": all_cats,
                                   "本月": [this_m_data.get(c,0) for c in all_cats],
                                   "上月": [last_m_data.get(c,0) for c in all_cats]})
            cmp_df = cmp_df[(cmp_df["本月"]>0)|(cmp_df["上月"]>0)].sort_values("本月", ascending=False)
            cmp_melt = cmp_df.melt(id_vars="分類", var_name="月份", value_name="金額")
            fig_bar = px.bar(cmp_melt, x="分類", y="金額", color="月份", barmode="group",
                             color_discrete_map={"本月":"#378ADD","上月":"#888780"})
            fig_bar.update_layout(template="plotly_dark", margin=dict(l=10,r=10,t=10,b=10),
                                  legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("💡 暫無可比較的支出數據。")
    else:
        st.info("💡 尚無記帳數據。")

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
    with sort_col1: sort_by = st.selectbox("排序方式", ["日期","類型","分類","金額"], key="sort_by")
    with sort_col2: sort_order = st.radio("順序", ["新→舊 / 高→低","舊→新 / 低→高"], key="sort_order", horizontal=True)
    sort_ascending = sort_order == "舊→新 / 低→高"

    st.caption(f"目前篩選：**{st.session_state.filter_mode}**")
    st.markdown("---")

    logs = st.session_state.my_logs
    filtered_logs = []
    for i, log in enumerate(logs):
        try: log_date = datetime.strptime(str(log.get("日期","")), "%Y/%m/%d").date()
        except: log_date = None
        include = False
        if st.session_state.filter_mode == "全部" or log_date is None: include = True
        elif st.session_state.filter_mode == "本月" and log_date and log_date >= this_month_start: include = True
        elif st.session_state.filter_mode == "上月" and log_date and last_month_start <= log_date <= last_month_end: include = True
        elif st.session_state.filter_mode == "自訂" and log_date and custom_start <= log_date <= custom_end: include = True
        if include: filtered_logs.append((i, log, log_date))

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
            col_date.write(log.get("日期","")); col_type.write(log.get("類型",""))
            col_cat.write(log.get("分類","")); col_item.write(log.get("項目",""))
            col_amt.write(f'${log.get("金額",0):,.1f}')
            if col_edit.button("✏️", key=f"edit_{i}_{idx}"): st.session_state.editing_index = i
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
            in_cat = st.selectbox("分類", st.session_state.my_income_categories if in_type=="收入 📥" else list(st.session_state.my_budget.keys()))
            in_subcat = st.text_input("子分類 (如：外食、零食)")
        with c3:
            in_title = st.text_input("項目名稱")
            in_amount = st.number_input("金額 ($)", min_value=0.0, step=1.0)
            in_acc = st.selectbox("帳戶", all_accs)
        if st.form_submit_button("確認記入 🚀") and in_amount > 0:
            if in_type == "收入 📥":
                if in_acc in st.session_state.my_assets: st.session_state.my_assets[in_acc] += in_amount
                if in_acc in st.session_state.my_liabilities: st.session_state.my_liabilities[in_acc] -= in_amount
            else:
                if in_acc in st.session_state.my_assets: st.session_state.my_assets[in_acc] -= in_amount
                if in_acc in st.session_state.my_liabilities: st.session_state.my_liabilities[in_acc] += in_amount
            st.session_state.my_logs.append({"日期":in_date.strftime("%Y/%m/%d"),"類型":in_type,"分類":in_cat,"子分類":in_subcat,"項目":in_title,"金額":float(in_amount),"帳戶/備註":in_acc})
            save_now(); st.success(f"✅ 已記入：{in_title} ${in_amount}"); st.rerun()

# ══════════════════════════════════════════════════════
# 頁面 4: 投資持倉記錄
# ══════════════════════════════════════════════════════
elif page_choice == "📈 投資持倉記錄":
    st.subheader("📈 投資持倉記錄")
    st.caption("交易為唯一數據源 — FIFO自動計算 · 現價登入後持久保留")

    if "my_trades" not in st.session_state:
        st.session_state.my_trades = []

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
                            failed.append(f"{h.get('名稱','')}：請在名稱前加代號，如 `MU 美光` 或 `6869 長飛`")
                save_now()
                if updated: st.success(f"✅ 更新 {updated} 筆")
                for f in failed: st.warning(f"⚠️ {f}")
        else:
            st.info("安裝 `yfinance` 可啟用自動更新")

    tab1, tab2 = st.tabs(["📊 持倉總覽", "📋 交易記錄"])

    # ── Tab1 ──
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
            def cv(h): return float(h.get("數量") or 0) * float(h.get("平均成本") or 0)

            if display_ccy == "HKD 港元":
                sym = "HK$"
                total_mv_d = sum(mv(h) for h in hkd_h) + sum(mv(h) for h in usd_h)*usd_to_hkd
                total_cost_d = sum(cv(h) for h in hkd_h) + sum(cv(h) for h in usd_h)*usd_to_hkd
                total_pnl_d = sum(pnl(h) for h in hkd_h) + sum(pnl(h) for h in usd_h)*usd_to_hkd
                note = f"（USD 部分以 {usd_to_hkd:.2f} 換算）"
            else:
                sym = "USD $"
                total_mv_d = sum(mv(h) for h in usd_h) + sum(mv(h) for h in hkd_h)*hkd_to_usd
                total_cost_d = sum(cv(h) for h in usd_h) + sum(cv(h) for h in hkd_h)*hkd_to_usd
                total_pnl_d = sum(pnl(h) for h in usd_h) + sum(pnl(h) for h in hkd_h)*hkd_to_usd
                note = f"（HKD 部分以 {hkd_to_usd:.4f} 換算）"

            pnl_pct = (total_pnl_d / total_cost_d * 100) if total_cost_d > 0 else 0.0
            realized_map = get_realized_pnl_map(st.session_state.my_trades)
            total_realized = sum(
                v * (usd_to_hkd if k.endswith(".HK") is False and display_ccy=="HKD 港元"
                     else hkd_to_usd if display_ccy=="USD 美元" else 1)
                for k,v in realized_map.items()
            )

            t1,t2,t3,t4,t5 = st.columns(5)
            t1.metric("💼 持倉市值", f"{sym}{total_mv_d:,.2f}")
            t2.metric("📊 持倉成本", f"{sym}{total_cost_d:,.2f}")
            t3.metric("💰 未實現盈虧", f"{sym}{total_pnl_d:,.2f}", delta=f"{'+'if total_pnl_d>=0 else ''}{pnl_pct:.2f}%", delta_color="normal")
            t4.metric("✅ 已實現盈虧", f"{sym}{total_realized:,.2f}", delta_color="normal")
            t5.metric("📌 持倉數目", f"{len(st.session_state.my_holdings)} 隻")
            st.caption(note)

            # ══ 同步資產帳戶 ══
            st.markdown("---")
            st.markdown("#### 🏦 同步入資產帳戶")
            st.caption("公式：帳戶新值 = 原有資本 + 已實現盈虧（FIFO配對的真實獲利/虧損） + 現持倉市值")
            st.caption("💡 改用「已實現盈虧」而非「賣出−買入」，避免未賣出持倉的買入成本被誤判為虧損。")
            st.error("⚠️ **注意重複計算**：系統的「淨身家」會自動即時加總持倉市值。若使用「方案 B」把持倉市值同步入帳戶，"
                     "之後「財務總覽」頁會把持倉市值**算兩次**。建議只使用「方案 A」（不含持倉市值），"
                     "或同步後到「財務總覽」頁查看是否出現重複計算警示。")

            # 已實現盈虧（FIFO配對後的真實獲利，已轉換為 HKD）
            realized_map_sync = get_realized_pnl_map(st.session_state.my_trades)
            sync_fx = usd_to_hkd
            total_realized_hkd = sum(
                v * (sync_fx if not k.endswith(".HK") else 1)
                for k, v in realized_map_sync.items()
            )
            holdings_mv_hkd = (
                sum(float(h.get("市值",0)) for h in st.session_state.my_holdings if h.get("幣別","USD")=="USD") * sync_fx
                + sum(float(h.get("市值",0)) for h in st.session_state.my_holdings if h.get("幣別","USD")=="HKD")
            )

            sa1, sa2 = st.columns(2)
            real_sign = "+" if total_realized_hkd >= 0 else ""
            sa1.metric("✅ 已實現盈虧（HKD）", f"HK${total_realized_hkd:,.2f}",
                       delta=f"{real_sign}{total_realized_hkd:,.0f}", delta_color="normal",
                       help="所有已賣出股票的真實獲利/虧損（FIFO配對計算）")
            sa2.metric("💹 現持倉市值（HKD）", f"HK${holdings_mv_hkd:,.2f}",
                       help="未賣出股票按現價計算的市值")

            st.markdown("")
            asset_accs = list(st.session_state.my_assets.keys())
            if not asset_accs:
                st.warning("⚠️ 尚未設定資產帳戶，請到「⚙️ 自訂資產/預算初始值」新增帳戶。")
            else:
                target_acc = st.selectbox("選擇要同步的資產帳戶", asset_accs, key="sync_target_acc")
                original_bal = float(st.session_state.my_assets.get(target_acc, 0))

                # 方案 A：原資本 + 已實現盈虧（已套現的真實獲利，不含未賣出持倉）
                new_val_cash = original_bal + total_realized_hkd
                # 方案 B：原資本 + 已實現盈虧 + 現持倉市值（總投資資產值，含未賣出部分）
                new_val_total = original_bal + total_realized_hkd + holdings_mv_hkd

                st.markdown(f"""
                <div style="background:rgba(0,212,170,0.07);border:1px solid rgba(0,212,170,0.25);border-radius:12px;padding:14px 18px;margin-bottom:12px">
                <div style="font-size:13px;color:#a0aec0;margin-bottom:8px">帳戶：<b style="color:#e2e8f0">{target_acc}</b> ｜ 原有餘額：<b style="color:#e2e8f0">HK${original_bal:,.2f}</b></div>
                <div style="display:flex;gap:32px;flex-wrap:wrap">
                  <div>
                    <div style="font-size:11px;color:#718096;text-transform:uppercase;letter-spacing:0.05em">方案 A｜原資本 + 已實現盈虧</div>
                    <div style="font-size:22px;font-weight:700;color:#00d4aa">HK${new_val_cash:,.2f}</div>
                    <div style="font-size:11px;color:#718096">適合：只記錄已套現的真實獲利，不計未賣出持倉</div>
                  </div>
                  <div>
                    <div style="font-size:11px;color:#718096;text-transform:uppercase;letter-spacing:0.05em">方案 B｜原資本 + 已實現盈虧 + 持倉市值</div>
                    <div style="font-size:22px;font-weight:700;color:#3b82f6">HK${new_val_total:,.2f}</div>
                    <div style="font-size:11px;color:#718096">適合：仍有持倉，計算總投資資產值（最完整）</div>
                  </div>
                </div>
                </div>
                """, unsafe_allow_html=True)

                btn1, btn2 = st.columns(2)
                with btn1:
                    if st.button(f"💵 套用方案 A（HK${new_val_cash:,.2f}）", use_container_width=True, key="btn_sync_cash"):
                        st.session_state.my_assets[target_acc] = new_val_cash
                        save_now()
                        st.success(f"✅ 【{target_acc}】已更新為 HK${new_val_cash:,.2f}（原資本 {original_bal:,.0f} + 已實現盈虧 {total_realized_hkd:,.0f}）")
                        st.rerun()
                with btn2:
                    if st.button(f"📊 套用方案 B（HK${new_val_total:,.2f}）", use_container_width=True, key="btn_sync_total"):
                        st.session_state.my_assets[target_acc] = new_val_total
                        save_now()
                        st.success(f"✅ 【{target_acc}】已更新為 HK${new_val_total:,.2f}（含現持倉市值）")
                        st.rerun()

            st.markdown("---")

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
                else: st.info("尚無美股持倉")
            with pie_col2:
                if not hkd_pie.empty:
                    fig_h = px.pie(hkd_pie, values="市值", names="名稱", hole=0.45,
                                   color_discrete_sequence=["#00d4aa","#34d399","#6ee7b7","#059669","#10b981"],
                                   title="🇭🇰 港股佔比")
                    fig_h.update_layout(template="plotly_dark", margin=dict(l=5,r=5,t=40,b=5))
                    fig_h.update_traces(textposition="inside", textinfo="percent+label")
                    st.plotly_chart(fig_h, use_container_width=True)
                else: st.info("尚無港股持倉")

            st.markdown("---")

            def render_group(h_list, ccy_sym, ccy_label):
                if not h_list: st.info(f"尚無 {ccy_label} 持倉"); return
                total_mv_g = sum(mv(h) for h in h_list)
                total_pnl_g = sum(pnl(h) for h in h_list)
                total_cv_g = sum(cv(h) for h in h_list)
                pnl_pct_g = (total_pnl_g/total_cv_g*100) if total_cv_g > 0 else 0.0
                sm1,sm2,sm3 = st.columns(3)
                sm1.metric("💼 總市值", f"{ccy_sym}{total_mv_g:,.2f}")
                sm2.metric("📊 總成本", f"{ccy_sym}{total_cv_g:,.2f}")
                sm3.metric("💰 未實現盈虧", f"{ccy_sym}{total_pnl_g:,.2f}",
                           delta=f"{'+'if total_pnl_g>=0 else ''}{pnl_pct_g:.2f}%", delta_color="normal")
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
            render_group(usd_h, "USD $", "USD")
            st.markdown("---")
            st.markdown("### 🇭🇰 港股 / HKD")
            render_group(hkd_h, "HK$", "HKD")
        else:
            st.info("💡 尚無持倉，請到「📋 交易記錄」tab 新增買入交易。")
        st.caption("💡 持倉由交易記錄自動計算（FIFO），現價更新後登入仍可保留。")

    # ── Tab2 ──
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
                net_amt = tr_qty*tr_price + tr_fee if is_buy else tr_qty*tr_price - tr_fee
                st.caption(f"💡 成交金額：{tr_qty*tr_price:,.2f}　淨額：{net_amt:,.2f}")
            if st.form_submit_button("✅ 確認記錄", use_container_width=True):
                if tr_name.strip() and tr_qty > 0 and tr_price > 0:
                    tc = "USD" if tr_currency.startswith("USD") else "HKD"
                    net = tr_qty*tr_price + tr_fee if is_buy else tr_qty*tr_price - tr_fee
                    st.session_state.my_trades.append({
                        "日期": tr_date.strftime("%Y/%m/%d"), "名稱": tr_name.strip(),
                        "類型": "買入" if is_buy else "賣出", "幣別": tc,
                        "數量": tr_qty, "成交價": tr_price, "手續費": tr_fee,
                        "備註": tr_note, "成交金額": round(net, 4),
                    })
                    save_now(); refresh_holdings()
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

            # 修正：分幣別計算，避免 USD/HKD 直接相加造成數字失真
            _fx_disp = st.session_state.get("fx_rate", 7.80)
            def _sum_hkd(d):
                if d.empty: return 0.0
                usd_part = d[d["幣別"]=="USD"]["成交金額"].sum() if "幣別" in d.columns else 0.0
                hkd_part = d[d["幣別"]=="HKD"]["成交金額"].sum() if "幣別" in d.columns else 0.0
                return float(usd_part)*_fx_disp + float(hkd_part)

            total_buy_usd = float(buy_df[buy_df["幣別"]=="USD"]["成交金額"].sum()) if not buy_df.empty and "幣別" in buy_df.columns else 0.0
            total_buy_hkd_raw = float(buy_df[buy_df["幣別"]=="HKD"]["成交金額"].sum()) if not buy_df.empty and "幣別" in buy_df.columns else 0.0
            total_sell_usd = float(sell_df[sell_df["幣別"]=="USD"]["成交金額"].sum()) if not sell_df.empty and "幣別" in sell_df.columns else 0.0
            total_sell_hkd_raw = float(sell_df[sell_df["幣別"]=="HKD"]["成交金額"].sum()) if not sell_df.empty and "幣別" in sell_df.columns else 0.0
            total_buy = _sum_hkd(buy_df)   # 統一換算為 HKD 顯示
            total_sell = _sum_hkd(sell_df)

            s1,s2,s3,s4 = st.columns(4)
            s1.metric("📈 買入總額 (HKD換算)", f"{total_buy:,.2f}")
            s2.metric("📉 賣出總額 (HKD換算)", f"{total_sell:,.2f}")
            s3.metric("📋 交易筆數", f"{len(filtered)} 筆")
            s4.metric("📌 持倉股數", f"{len(st.session_state.my_holdings)} 隻")
            if total_buy_usd > 0 or total_sell_usd > 0:
                st.caption(f"💡 原幣明細 — 買入：USD ${total_buy_usd:,.2f} + HKD ${total_buy_hkd_raw:,.2f} ｜ 賣出：USD ${total_sell_usd:,.2f} + HKD ${total_sell_hkd_raw:,.2f}（匯率 {_fx_disp:.2f}）")

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
# 頁面 5: 加密資產持倉
# ══════════════════════════════════════════════════════
elif page_choice == "💹 加密資產持倉":
    st.subheader("💹 加密資產持倉")
    st.caption("由 CoinGecko API 自動獲取即時幣價 · 無需 API Key")

    if "my_crypto" not in st.session_state:
        st.session_state.my_crypto = []

    def fetch_crypto_prices(coin_ids: list) -> dict:
        """使用 CoinGecko 免費 API 批量獲取幣價（USD）"""
        if not coin_ids:
            return {}
        try:
            ids_str = ",".join(coin_ids)
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_str}&vs_currencies=usd,hkd&include_24hr_change=true"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return {}

    COIN_LIST = {
        "Bitcoin": "bitcoin", "Ethereum": "ethereum", "BNB": "binancecoin",
        "Solana": "solana", "XRP": "ripple", "USDT": "tether", "USDC": "usd-coin",
        "Cardano": "cardano", "Avalanche": "avalanche-2", "Dogecoin": "dogecoin",
        "Polkadot": "polkadot", "Chainlink": "chainlink", "Litecoin": "litecoin",
        "Uniswap": "uniswap", "Polygon": "matic-network", "自訂幣種": "__custom__"
    }

    st.markdown("#### ➕ 新增加密貨幣持倉")
    with st.form("add_crypto_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns([2,1.5,1.5,1])
        with c1:
            coin_select = st.selectbox("選擇幣種", list(COIN_LIST.keys()))
            custom_id = st.text_input("自訂 CoinGecko ID（選自訂時填寫）", placeholder="例如：shiba-inu")
        with c2:
            crypto_qty = st.number_input("持倉數量", min_value=0.0, step=0.0001, format="%.6f")
        with c3:
            crypto_cost = st.number_input("平均成本 (USD)", min_value=0.0, step=0.01)
        with c4:
            crypto_ccy = st.selectbox("計價幣別", ["USD", "HKD"])
        if st.form_submit_button("✅ 新增持倉", use_container_width=True):
            if crypto_qty > 0 and crypto_cost >= 0:
                coin_id = custom_id.strip() if coin_select == "自訂幣種" else COIN_LIST[coin_select]
                coin_name = custom_id.strip() if coin_select == "自訂幣種" else coin_select
                st.session_state.my_crypto.append({
                    "名稱": coin_name, "coin_id": coin_id,
                    "數量": crypto_qty, "平均成本_USD": crypto_cost,
                    "幣別": crypto_ccy, "現價_USD": 0.0, "現價_HKD": 0.0,
                })
                save_now()
                st.success(f"✅ 已新增 {coin_name} × {crypto_qty}")
                st.rerun()

    if st.session_state.my_crypto:
        st.markdown("---")
        if st.button("🔄 更新全部幣價（CoinGecko）", use_container_width=True):
            coin_ids = list(set(c["coin_id"] for c in st.session_state.my_crypto if c.get("coin_id")))
            with st.spinner("正在從 CoinGecko 獲取最新幣價…"):
                price_data = fetch_crypto_prices(coin_ids)
            if price_data:
                for c in st.session_state.my_crypto:
                    cid = c.get("coin_id","")
                    if cid in price_data:
                        c["現價_USD"] = float(price_data[cid].get("usd", 0))
                        c["現價_HKD"] = float(price_data[cid].get("hkd", 0))
                        c["24h變動%"] = float(price_data[cid].get("usd_24h_change", 0))
                save_now()
                st.success(f"✅ 已更新 {len(price_data)} 個幣種價格")
                st.rerun()
            else:
                st.warning("⚠️ 無法連接 CoinGecko，請稍後再試")

        total_crypto_usd = 0.0
        total_crypto_cost = 0.0
        st.markdown("#### 📊 加密資產總覽")
        hdr = st.columns([2, 1.2, 1.2, 1.2, 1.5, 1.2, 0.6])
        for h, t in zip(hdr, ["**幣種**","**數量**","**現價(USD)**","**均成本(USD)**","**未實現盈虧**","**24h變動**","🗑️"]):
            h.markdown(t)
        st.markdown("---")

        for idx, c in enumerate(st.session_state.my_crypto):
            qty = float(c.get("數量", 0))
            cost = float(c.get("平均成本_USD", 0))
            price = float(c.get("現價_USD", 0))
            chg24 = float(c.get("24h變動%", 0))
            mv_usd = qty * price
            pnl_usd = qty * (price - cost)
            pnl_pct = (pnl_usd / (qty * cost) * 100) if qty * cost > 0 else 0
            total_crypto_usd += mv_usd
            total_crypto_cost += qty * cost
            pnl_clr = "#1D9E75" if pnl_usd >= 0 else "#E24B4A"
            chg_clr = "#1D9E75" if chg24 >= 0 else "#E24B4A"
            sgn = "+" if pnl_usd >= 0 else ""
            chg_sgn = "+" if chg24 >= 0 else ""

            col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 1.2, 1.2, 1.2, 1.5, 1.2, 0.6])
            col1.write(f"**{c.get('名稱','')}**")
            col2.write(f"{qty:,.6g}")
            col3.write(f"${price:,.4f}" if price > 0 else "—")
            col4.write(f"${cost:,.4f}")
            col5.markdown(f'<span style="color:{pnl_clr};font-weight:600">{sgn}${pnl_usd:,.2f} ({sgn}{pnl_pct:.1f}%)</span>', unsafe_allow_html=True)
            col6.markdown(f'<span style="color:{chg_clr}">{chg_sgn}{chg24:.2f}%</span>' if price > 0 else "—", unsafe_allow_html=True)
            if col7.button("🗑️", key=f"del_crypto_{idx}"):
                st.session_state.my_crypto.pop(idx)
                save_now(); st.rerun()
            st.divider()

        total_pnl_usd = total_crypto_usd - total_crypto_cost
        pnl_pct_total = (total_pnl_usd / total_crypto_cost * 100) if total_crypto_cost > 0 else 0
        m1, m2, m3 = st.columns(3)
        m1.metric("💼 加密持倉市值", f"${total_crypto_usd:,.2f} USD")
        m2.metric("📊 加密持倉成本", f"${total_crypto_cost:,.2f} USD")
        m3.metric("💰 未實現盈虧", f"${total_pnl_usd:,.2f}",
                  delta=f"{'+'if total_pnl_usd>=0 else ''}{pnl_pct_total:.2f}%",
                  delta_color="normal")
    else:
        st.info("💡 尚未新增加密貨幣持倉，使用上方表單新增。")

# ══════════════════════════════════════════════════════
# 頁面 6: 智能提醒中心
# ══════════════════════════════════════════════════════
elif page_choice == "🔔 智能提醒中心":
    st.subheader("🔔 智能提醒中心")
    st.caption("預算超支警報 · 儲蓄目標追蹤 · 財務健康提示")

    # ─── 儲蓄目標設定 ───
    st.markdown("### 🎯 儲蓄目標設定")
    sg_col1, sg_col2, sg_col3 = st.columns([2,2,1])
    with sg_col1:
        new_goal_name = st.text_input("目標名稱", value=st.session_state.my_savings_goal_name, key="goal_name_input")
    with sg_col2:
        new_goal_amt = st.number_input("目標金額 (HK$)", value=safe_float(st.session_state.my_savings_goal),
                                        min_value=0.0, step=1000.0, key="goal_amt_input")
    with sg_col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("💾 儲存目標", use_container_width=True):
            st.session_state.my_savings_goal = new_goal_amt
            st.session_state.my_savings_goal_name = new_goal_name.strip() or "儲蓄目標"
            save_now()
            st.success("✅ 目標已儲存！")
            st.rerun()

    goal = safe_float(st.session_state.my_savings_goal)
    if goal > 0:
        progress_pct = min(expected_savings / goal * 100, 100) if goal > 0 else 0
        prog_clr = "#1D9E75" if progress_pct >= 80 else "#EF9F27" if progress_pct >= 40 else "#E24B4A"
        st.markdown(f"""
        <div style="margin:12px 0">
        <div style="display:flex;justify-content:space-between;margin-bottom:6px">
          <span style="font-weight:600">{st.session_state.my_savings_goal_name}</span>
          <span style="color:{prog_clr};font-weight:700">{progress_pct:.1f}%</span>
        </div>
        <div style="background:#1a2a3a;border-radius:8px;height:14px;overflow:hidden">
          <div style="width:{progress_pct}%;background:{prog_clr};height:100%;border-radius:8px;transition:width 0.5s"></div>
        </div>
        <div style="display:flex;justify-content:space-between;font-size:12px;color:#718096;margin-top:4px">
          <span>已存 HK${expected_savings:,.0f}</span>
          <span>目標 HK${goal:,.0f}</span>
        </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ─── 預算超支警報 ───
    st.markdown("### 🚨 預算超支警報")
    alerts = []
    warnings_list = []
    ok_list = []
    for cat, budget_val in st.session_state.my_budget.items():
        actual = actual_spent_map.get(cat, 0.0)
        if budget_val <= 0 and actual <= 0:
            continue
        if budget_val > 0:
            rate = actual / budget_val * 100
            if rate >= 100:
                alerts.append((cat, actual, budget_val, rate))
            elif rate >= 80:
                warnings_list.append((cat, actual, budget_val, rate))
            else:
                ok_list.append((cat, actual, budget_val, rate))
        else:
            alerts.append((cat, actual, 0, 100))

    if alerts:
        st.error(f"🔴 發現 **{len(alerts)}** 個預算超支項目！")
        for cat, actual, bgt, rate in alerts:
            over = actual - bgt
            st.markdown(f"""
            <div style="background:rgba(226,75,74,0.1);border:1px solid rgba(226,75,74,0.4);border-radius:10px;padding:12px 16px;margin-bottom:8px">
            <div style="display:flex;justify-content:space-between;align-items:center">
              <span style="font-weight:600;color:#E24B4A">🔴 {cat}</span>
              <span style="color:#E24B4A;font-weight:700">超出 ${over:,.0f}（{rate:.0f}%）</span>
            </div>
            <div style="font-size:12px;color:#a0aec0;margin-top:4px">實際支出 ${actual:,.0f} / 預算 ${bgt:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✅ 目前沒有超支項目")

    if warnings_list:
        st.warning(f"🟡 **{len(warnings_list)}** 個項目即將達到預算上限")
        for cat, actual, bgt, rate in warnings_list:
            remain = bgt - actual
            st.markdown(f"""
            <div style="background:rgba(239,159,39,0.1);border:1px solid rgba(239,159,39,0.4);border-radius:10px;padding:10px 16px;margin-bottom:6px">
            <div style="display:flex;justify-content:space-between">
              <span style="font-weight:600;color:#EF9F27">🟡 {cat}</span>
              <span style="color:#EF9F27">剩餘 ${remain:,.0f}（已用 {rate:.0f}%）</span>
            </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # ─── 財務健康提示 ───
    st.markdown("### 💡 財務健康提示")
    tips = []
    if savings_rate < 10 and total_actual_income > 0:
        tips.append(("🔴 儲蓄率偏低", f"本月儲蓄率僅 {savings_rate:.1f}%，建議目標 20% 以上。請檢視可削減的非必要支出。"))
    elif savings_rate < 20 and total_actual_income > 0:
        tips.append(("🟡 儲蓄率待改善", f"本月儲蓄率 {savings_rate:.1f}%，距離理想的 20% 仍有空間。"))
    else:
        tips.append(("🟢 儲蓄率良好", f"本月儲蓄率 {savings_rate:.1f}%，表現優秀！請繼續保持。"))

    if total_assets > 0 and (total_liabilities / total_assets) > 0.5:
        tips.append(("🔴 負債比率偏高", f"負債佔資產 {total_liabilities/total_assets*100:.1f}%，建議優先清償高息負債。"))

    if holdings_total_value > 0 and (holdings_total_value / net_worth) > 0.7 if net_worth > 0 else False:
        tips.append(("🟡 投資集中度偏高", f"持倉市值佔淨資產逾 70%，建議適當分散資產。"))

    if total_actual_income == 0:
        tips.append(("ℹ️ 尚無收入記錄", "本月尚未記錄收入，請前往「每日單筆記帳」新增收入記錄。"))

    for title, desc in tips:
        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);border-radius:10px;padding:12px 16px;margin-bottom:8px">
        <div style="font-weight:600;margin-bottom:4px">{title}</div>
        <div style="color:#a0aec0;font-size:13px">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════
# 頁面 7: 未來3月收支預測
# ══════════════════════════════════════════════════════
elif page_choice == "📉 未來3月收支預測":
    st.subheader("📉 未來3月收支預測")
    st.caption("基於過去數據自動計算月均收支，預測未來3個月財務走勢")

    if df_current_logs.empty:
        st.info("💡 尚無記帳數據，記帳後自動生成預測。")
    else:
        df_pred = df_current_logs.copy()
        df_pred["日期_dt"] = pd.to_datetime(df_pred["日期"], errors="coerce")
        df_pred = df_pred.dropna(subset=["日期_dt"])
        df_pred["年月"] = df_pred["日期_dt"].dt.to_period("M")

        is_inc_p = (df_pred["類型"] == "收入 📥") | (df_pred["分類"] == "收入")
        monthly_inc = df_pred[is_inc_p].groupby("年月")["金額"].sum()
        monthly_exp = df_pred[~is_inc_p].groupby("年月")["金額"].sum()
        monthly_sav = monthly_inc.subtract(monthly_exp, fill_value=0)

        if len(monthly_inc) == 0:
            st.info("💡 暫無足夠數據進行預測（需至少1個月記錄）。")
        else:
            avg_inc = float(monthly_inc.mean())
            avg_exp = float(monthly_exp.mean()) if len(monthly_exp) > 0 else 0.0
            avg_sav = avg_inc - avg_exp

            now_p = pd.Period(datetime.now(), freq="M")
            future_months = [now_p + i for i in range(1, 4)]
            future_labels = [str(m) for m in future_months]

            inc_pred = [avg_inc] * 3
            exp_pred = [avg_exp] * 3
            sav_pred = [avg_sav] * 3

            p1, p2, p3 = st.columns(3)
            p1.metric("📈 預測月均收入", f"${avg_inc:,.0f}", help="基於所有月份平均")
            p2.metric("📉 預測月均支出", f"${avg_exp:,.0f}", help="基於所有月份平均")
            p3.metric("💰 預測月均儲蓄", f"${avg_sav:,.0f}",
                      delta=f"{'+'if avg_sav>=0 else ''}{(avg_sav/avg_inc*100) if avg_inc>0 else 0:.1f}%",
                      delta_color="normal")
            st.markdown("---")

            # 歷史 + 預測圖
            hist_labels = [str(p) for p in monthly_inc.index.union(monthly_exp.index)]
            hist_inc = [float(monthly_inc.get(p, 0)) for p in monthly_inc.index.union(monthly_exp.index)]
            hist_exp = [float(monthly_exp.get(p, 0)) for p in monthly_inc.index.union(monthly_exp.index)]
            hist_sav = [i - e for i, e in zip(hist_inc, hist_exp)]

            fig_pred = go.Figure()
            fig_pred.add_trace(go.Bar(name="歷史收入", x=hist_labels, y=hist_inc, marker_color="#1D9E75", opacity=0.7))
            fig_pred.add_trace(go.Bar(name="歷史支出", x=hist_labels, y=hist_exp, marker_color="#E24B4A", opacity=0.7))
            fig_pred.add_trace(go.Bar(name="預測收入", x=future_labels, y=inc_pred,
                                       marker_color="#1D9E75", marker_pattern_shape="/", opacity=0.9))
            fig_pred.add_trace(go.Bar(name="預測支出", x=future_labels, y=exp_pred,
                                       marker_color="#E24B4A", marker_pattern_shape="/", opacity=0.9))
            fig_pred.add_trace(go.Scatter(name="歷史儲蓄", x=hist_labels, y=hist_sav,
                                           mode="lines+markers", line=dict(color="#3b82f6", width=2)))
            fig_pred.add_trace(go.Scatter(name="預測儲蓄", x=future_labels, y=sav_pred,
                                           mode="lines+markers", line=dict(color="#3b82f6", width=2, dash="dot"),
                                           marker=dict(symbol="diamond", size=10)))
            fig_pred.update_layout(template="plotly_dark", barmode="group",
                                    margin=dict(l=10, r=10, t=10, b=10),
                                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig_pred, use_container_width=True)

            # 預測明細表
            st.markdown("#### 📋 未來3個月預測明細")
            st.dataframe(pd.DataFrame({
                "月份": future_labels,
                "預測收入": [f"${v:,.0f}" for v in inc_pred],
                "預測支出": [f"${v:,.0f}" for v in exp_pred],
                "預測儲蓄": [f"${v:,.0f}" for v in sav_pred],
                "儲蓄率": [f"{(v/i*100) if i>0 else 0:.1f}%" for v, i in zip(sav_pred, inc_pred)],
                "累計儲蓄": [f"${sum(sav_pred[:i+1]):,.0f}" for i in range(3)],
            }), use_container_width=True, hide_index=True)

            st.caption(f"💡 預測基於過去 {len(monthly_inc)} 個月平均數據，實線為歷史，虛線為預測。")

            # 支出分類預測
            st.markdown("---")
            st.markdown("#### 📊 預測支出分類")
            exp_by_cat = df_pred[~is_inc_p].groupby(["年月", "分類"])["金額"].sum().unstack(fill_value=0)
            avg_by_cat = exp_by_cat.mean().sort_values(ascending=False)
            if not avg_by_cat.empty:
                top_cats = avg_by_cat[avg_by_cat > 0]
                fig_cat = px.bar(x=top_cats.values, y=top_cats.index, orientation="h",
                                 title="月均支出分類（預測基準）",
                                 color=top_cats.values, color_continuous_scale="RdYlGn_r")
                fig_cat.update_layout(template="plotly_dark", showlegend=False,
                                       margin=dict(l=10, r=10, t=40, b=10))
                st.plotly_chart(fig_cat, use_container_width=True)

# ══════════════════════════════════════════════════════
# 頁面 8: 多幣別匯率
# ══════════════════════════════════════════════════════
elif page_choice == "💱 多幣別匯率":
    st.subheader("💱 多幣別即時匯率")
    st.caption("由 exchangerate-api 提供免費匯率數據 · 支援 HKD 基礎換算")

    CURRENCIES = {
        "美元 USD 🇺🇸": "USD", "港元 HKD 🇭🇰": "HKD", "人民幣 CNY 🇨🇳": "CNY",
        "英鎊 GBP 🇬🇧": "GBP", "歐元 EUR 🇪🇺": "EUR", "日圓 JPY 🇯🇵": "JPY",
        "韓圜 KRW 🇰🇷": "KRW", "澳元 AUD 🇦🇺": "AUD", "加元 CAD 🇨🇦": "CAD",
        "新加坡元 SGD 🇸🇬": "SGD", "新台幣 TWD 🇹🇼": "TWD", "瑞士法郎 CHF 🇨🇭": "CHF",
    }

    @st.cache_data(ttl=300)  # 快取5分鐘
    def fetch_fx_rates(base: str = "HKD") -> dict:
        try:
            url = f"https://open.er-api.com/v6/latest/{base}"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data.get("result") == "success":
                    return data.get("rates", {})
        except Exception:
            pass
        # 後備靜態匯率（HKD基準）
        return {
            "USD": 0.1282, "CNY": 0.9285, "GBP": 0.1009, "EUR": 0.1176,
            "JPY": 19.08, "KRW": 175.2, "AUD": 0.1985, "CAD": 0.1773,
            "SGD": 0.1725, "TWD": 4.185, "CHF": 0.1149, "HKD": 1.0
        }

    base_label = st.selectbox("基準幣別", list(CURRENCIES.keys()), index=0)
    base_ccy = CURRENCIES[base_label]

    col_refresh, col_amount = st.columns([1, 2])
    with col_refresh:
        refresh_fx = st.button("🔄 更新匯率", use_container_width=True)
    with col_amount:
        input_amount = st.number_input("換算金額", value=100.0, min_value=0.01, step=10.0)

    if refresh_fx:
        st.cache_data.clear()

    rates = fetch_fx_rates(base_ccy)

    if rates:
        st.markdown(f"#### 📊 以 **{base_label}** 為基準")
        st.caption(f"💡 匯率每5分鐘自動緩存，點擊「更新匯率」強制刷新")

        display_ccys = [c for c in CURRENCIES.values() if c != base_ccy]
        cols_per_row = 4
        rows = [display_ccys[i:i+cols_per_row] for i in range(0, len(display_ccys), cols_per_row)]

        for row in rows:
            cols = st.columns(len(row))
            for col, ccy in zip(cols, row):
                rate = rates.get(ccy, 0)
                converted = input_amount * rate if rate > 0 else 0
                label = next(k for k, v in CURRENCIES.items() if v == ccy)
                col.metric(
                    label=label,
                    value=f"{converted:,.2f}",
                    delta=f"1 {base_ccy} = {rate:.4f} {ccy}" if rate > 0 else "N/A"
                )

        # 常用換算表
        st.markdown("---")
        st.markdown("#### 🔄 常用金額快速換算")
        common_amounts = [100, 500, 1000, 5000, 10000, 50000]
        top_ccys = ["USD", "HKD", "CNY", "JPY", "EUR", "GBP"]
        top_ccys_filtered = [c for c in top_ccys if c != base_ccy][:5]

        table_data = {"金額": [f"{a:,}" for a in common_amounts]}
        for ccy in top_ccys_filtered:
            rate = rates.get(ccy, 0)
            table_data[ccy] = [f"{a*rate:,.2f}" if rate > 0 else "—" for a in common_amounts]
        st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
    else:
        st.error("❌ 無法獲取匯率數據，請檢查網路連接。")

    # 側欄快速匯率顯示
    st.sidebar.markdown("---")
    sidebar_rates_data = fetch_fx_rates("HKD")
    if sidebar_rates_data:
        st.sidebar.markdown("**💱 即時匯率（HKD基準）**")
        for ccy in ["USD", "CNY", "JPY", "EUR", "GBP"]:
            r = sidebar_rates_data.get(ccy, 0)
            if r > 0:
                st.sidebar.caption(f"1 HKD = {r:.4f} {ccy}")

# ══════════════════════════════════════════════════════
# 頁面 9: AI 理財建議
# ══════════════════════════════════════════════════════
elif page_choice == "🤖 AI 理財建議":
    st.subheader("🤖 AI 理財建議")
    st.caption("根據你的真實財務數據，由 Claude AI 提供個人化建議")

    _realized_map = get_realized_pnl_map(st.session_state.get("my_trades", []))
    _total_realized_usd = sum(v for k,v in _realized_map.items() if k.endswith(".HK") is False and not k.startswith("0"))
    _total_realized_hkd = sum(v for k,v in _realized_map.items() if k.endswith(".HK"))

    holdings_text = ""
    for h in st.session_state.get("my_holdings", []):
        pnl_h = float(h.get("盈虧") or 0)
        qty = float(h.get("數量",0)); hc = float(h.get("平均成本",1))
        pnl_p = (pnl_h/(qty*hc)*100) if qty*hc>0 else 0
        holdings_text += f"- {h.get('名稱','')} ({h.get('幣別','USD')}): {qty:,.2f}股 均成本{hc:,.4f} 現價{float(h.get('現價',0)):,.2f} 未實現{'+'if pnl_h>=0 else ''}{pnl_h:,.2f} ({pnl_p:+.1f}%)\n"

    fin_summary = f"""用戶財務狀況：
- 總資產：HK${total_assets:,.2f} | 總負債：HK${total_liabilities:,.2f} | 淨資產：HK${net_worth:,.2f}
- 本月收入：${total_actual_income:,.2f} | 本月支出：${total_actual_expense:,.2f} | 儲蓄率：{savings_rate:.1f}%
- 持倉市值(USD)：${_holdings_usd_mv:,.2f} | 持倉市值(HKD)：HK${_holdings_hkd_mv:,.2f}
- 已實現盈虧(USD)：${_total_realized_usd:,.2f} | 已實現盈虧(HKD)：HK${_total_realized_hkd:,.2f}
- 負債比：{(total_liabilities/total_assets*100) if total_assets>0 else 0:.1f}%
持倉明細：
{holdings_text if holdings_text else "（尚無持倉）"}
主要支出（本月）：
""" + "\n".join([f"- {k}：${v:,.2f}" for k,v in actual_spent_map.items() if v > 0])

    ai_mode = st.radio("選擇建議類型",
        ["📊 整體財務健康評估","💡 儲蓄改善建議","📈 投資持倉分析","🎯 月度預算優化"],
        horizontal=True)
    custom_q = st.text_input("或輸入自訂問題（可空白）", placeholder="例如：我應該增持還是減持現有倉位？")

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

    # 檢查是否有 API Key
    try:
        anthropic_key = st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        anthropic_key = st.session_state.get("anthropic_api_key_input", "")

    tab_free, tab_api = st.tabs(["🆓 免費方式（複製到 Claude.ai）", "⚡ 自動 API（需付費 Key）"])

    with tab_free:
        st.info("💡 完全免費！按下方按鈕複製財務摘要，貼到 [claude.ai](https://claude.ai) 聊天視窗即可獲得 AI 建議，無需 API Key。")
        st.text_area("📋 點擊右上角複製圖示，複製以下內容貼到 Claude.ai：",
                     value=full_prompt, height=280, key="copy_prompt_area")
        st.markdown("""
        <a href="https://claude.ai/new" target="_blank">
        <button style="width:100%;padding:12px;background:#00d4aa;color:#0a0e14;border:none;
        border-radius:8px;font-weight:700;font-size:15px;cursor:pointer;margin-top:8px">
        🚀 開啟 Claude.ai（在新視窗貼上內容）
        </button>
        </a>
        """, unsafe_allow_html=True)
        st.caption("步驟：① 複製上方文字框內容 → ② 按綠色按鈕開啟 Claude.ai → ③ 貼上並送出")

    with tab_api:
        if not anthropic_key:
            st.warning("⚠️ 尚未設定 API Key。如想使用自動分析（按一下立即在本頁顯示結果），可在下方輸入，"
                      "或在 Streamlit Secrets 設定 `ANTHROPIC_API_KEY`。這是**付費功能**（每次約 $0.01-0.05 美金）。")
        if st.button("🤖 獲取 AI 建議（自動分析）", use_container_width=True, disabled=not bool(anthropic_key)):
            with st.spinner("🤖 AI 正在分析您的財務狀況…"):
                try:
                    response = requests.post(
                        "https://api.anthropic.com/v1/messages",
                        headers={
                            "Content-Type": "application/json",
                            "x-api-key": anthropic_key,
                            "anthropic-version": "2023-06-01",
                        },
                        json={
                            "model": "claude-sonnet-4-6",
                            "max_tokens": 1200,
                            "system": "你是一位專業的香港個人理財顧問，擅長分析用戶財務數據並提供實用建議。回答要具體、有條理，使用繁體中文，適當使用emoji讓內容更易讀。",
                            "messages": [{"role": "user", "content": full_prompt}]
                        },
                        timeout=30
                    )
                    data = response.json()
                    if "error" in data:
                        err_msg = data["error"].get("message", str(data["error"]))
                        st.error(f"❌ API 錯誤：{err_msg}")
                    elif "content" in data and data["content"]:
                        ai_text = data["content"][0].get("text", "（AI 未返回內容）")
                        st.markdown(f'<div class="ai-card">{ai_text.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
                    else:
                        st.error(f"❌ 未預期的回應格式：{data}")
                except requests.exceptions.Timeout:
                    st.error("❌ 請求超時，請稍後再試。")
                except Exception as e:
                    st.error(f"❌ AI 請求失敗：{e}")

        st.markdown("---")
        with st.expander("🔑 API Key 設定", expanded=False):
            st.caption("如 Streamlit Secrets 中已設定 `ANTHROPIC_API_KEY`，無需在此填寫。")
            api_key_input = st.text_input("Anthropic API Key", type="password",
                                           value=st.session_state.get("anthropic_api_key_input",""),
                                           key="api_key_field", placeholder="sk-ant-...")
            if st.button("💾 儲存 Key（僅本次會話）", use_container_width=True):
                st.session_state["anthropic_api_key_input"] = api_key_input
                st.success("✅ API Key 已儲存（不會上傳至雲端）")
                st.rerun()

    st.markdown("---")
    st.caption("⚠️ AI 建議僅供參考，不構成投資或財務建議。重大財務決定請諮詢專業顧問。")

# ══════════════════════════════════════════════════════
# 頁面 6: 財務年度分析
# ══════════════════════════════════════════════════════
elif page_choice == "📊 財務年度分析":
    st.subheader("📊 財務年度分析")
    now_dt = datetime.now()
    selected_year = st.selectbox("選擇年份", list(range(now_dt.year, now_dt.year-5, -1)), key="year_sel")

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

            y1,y2,y3,y4 = st.columns(4)
            y1.metric("💰 年度總收入", f"${df_inc_yr.sum():,.0f}")
            y2.metric("💸 年度總支出", f"${df_exp_yr.sum():,.0f}")
            y3.metric("📈 年度儲蓄", f"${df_sav_yr.sum():,.0f}")
            avg_sav_rate = (df_sav_yr.sum()/df_inc_yr.sum()*100) if df_inc_yr.sum()>0 else 0
            y4.metric("📊 平均儲蓄率", f"{avg_sav_rate:.1f}%")
            st.markdown("---")

            st.markdown("#### 📅 月度收支概覽")
            fig_yr = go.Figure()
            fig_yr.add_trace(go.Bar(name="收入", x=months, y=df_inc_yr.values, marker_color="#1D9E75"))
            fig_yr.add_trace(go.Bar(name="支出", x=months, y=df_exp_yr.values, marker_color="#E24B4A"))
            fig_yr.add_trace(go.Scatter(name="儲蓄", x=months, y=df_sav_yr.values,
                                         mode="lines+markers", line=dict(color="#3b82f6", width=2)))
            fig_yr.update_layout(template="plotly_dark", barmode="group",
                                  margin=dict(l=10,r=10,t=10,b=10),
                                  legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig_yr, use_container_width=True)

            st.markdown("#### 📈 月度儲蓄率趨勢")
            sav_rate_monthly = [(df_inc_yr[m]-df_exp_yr[m])/df_inc_yr[m]*100 if df_inc_yr[m]>0 else 0 for m in range(1,13)]
            fig_sav = go.Figure()
            fig_sav.add_trace(go.Scatter(x=months, y=sav_rate_monthly, mode="lines+markers",
                                          line=dict(color="#00d4aa", width=2), fill="tozeroy",
                                          fillcolor="rgba(0,212,170,0.1)"))
            fig_sav.add_hline(y=20, line_dash="dash", line_color="#EF9F27", annotation_text="建議儲蓄率 20%")
            fig_sav.update_layout(template="plotly_dark", yaxis_title="儲蓄率 (%)", margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig_sav, use_container_width=True)

            st.markdown("#### 📊 年度支出分類")
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

            st.markdown("#### 📋 月度明細")
            st.dataframe(pd.DataFrame({
                "月份": months,
                "收入": [f"${v:,.0f}" for v in df_inc_yr.values],
                "支出": [f"${v:,.0f}" for v in df_exp_yr.values],
                "儲蓄": [f"${v:,.0f}" for v in df_sav_yr.values],
                "儲蓄率": [f"{r:.1f}%" for r in sav_rate_monthly],
            }), use_container_width=True, hide_index=True)

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
    new_cat = st.text_input("新增收入分類名稱", key="add_new_income_cat_input")
    if st.button("新增分類 🚀"):
        if new_cat.strip() and new_cat.strip() not in st.session_state.my_income_categories:
            st.session_state.my_income_categories.append(new_cat.strip()); save_now()
            st.success(f"✅ 已新增：{new_cat.strip()}"); st.rerun()
        else:
            st.warning("⚠️ 輸入無效或已存在！")

    st.markdown("---")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.write("### 🟢 資產帳戶餘額")
        for k, v in list(st.session_state.my_assets.items()):
            arow1, arow2, arow3 = st.columns([3, 0.7, 0.7])
            with arow1:
                new_val = st.number_input(f"【{k}】", value=float(v), key=f"asset_input_{k}")
                if new_val != v:
                    st.session_state.my_assets[k] = new_val; save_now()
            with arow2:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("✏️", key=f"rename_asset_btn_{k}", help="重新命名", use_container_width=True):
                    st.session_state[f"renaming_asset_{k}"] = True
            with arow3:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_asset_btn_{k}", help="刪除帳戶", use_container_width=True):
                    if len(st.session_state.my_assets) > 1:
                        del st.session_state.my_assets[k]
                        save_now(); st.success(f"✅ 已刪除「{k}」"); st.rerun()
                    else:
                        st.warning("⚠️ 至少保留一個資產帳戶！")

            if st.session_state.get(f"renaming_asset_{k}", False):
                with st.form(key=f"rename_asset_form_{k}"):
                    rn_col1, rn_col2, rn_col3 = st.columns([3, 1, 1])
                    new_name = rn_col1.text_input("新名稱", value=k, key=f"rename_asset_input_{k}", label_visibility="collapsed")
                    confirm_rn = rn_col2.form_submit_button("✅ 確認", use_container_width=True)
                    cancel_rn = rn_col3.form_submit_button("✕ 取消", use_container_width=True)
                    if confirm_rn:
                        new_name = new_name.strip()
                        if new_name and new_name != k and new_name not in st.session_state.my_assets:
                            st.session_state.my_assets[new_name] = st.session_state.my_assets.pop(k)
                            # 同步更新 logs / trades 等引用此帳戶名稱的記錄
                            for log in st.session_state.get("my_logs", []):
                                if log.get("帳戶/備註") == k:
                                    log["帳戶/備註"] = new_name
                            save_now()
                            st.session_state[f"renaming_asset_{k}"] = False
                            st.success(f"✅ 已重新命名為「{new_name}」"); st.rerun()
                        elif new_name in st.session_state.my_assets:
                            st.warning("⚠️ 此名稱已存在！")
                        else:
                            st.warning("⚠️ 名稱無效！")
                    if cancel_rn:
                        st.session_state[f"renaming_asset_{k}"] = False
                        st.rerun()
        st.markdown("")
        new_asset_name = st.text_input("新增資產帳戶名稱", placeholder="例如：投資帳戶 📈", key="new_asset_name")
        if st.button("➕ 新增帳戶"):
            if new_asset_name.strip() and new_asset_name.strip() not in st.session_state.my_assets:
                st.session_state.my_assets[new_asset_name.strip()] = 0.0; save_now()
                st.success(f"✅ 已新增"); st.rerun()
            else:
                st.warning("⚠️ 名稱無效或已存在！")
        st.markdown("---")
        st.write("### 🔴 負債初始欠款")
        for k, v in list(st.session_state.my_liabilities.items()):
            lrow1, lrow2, lrow3, lrow4 = st.columns([2.6, 0.7, 0.7, 0.7])
            with lrow1:
                new_val = st.number_input(f"【{k}】", value=float(v), key=f"lia_input_{k}")
                if new_val != v:
                    st.session_state.my_liabilities[k] = new_val; save_now()
            with lrow2:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("💵", key=f"repay_lia_btn_{k}", help="還款（直接扣減負債）", use_container_width=True):
                    st.session_state[f"repaying_lia_{k}"] = True
            with lrow3:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("✏️", key=f"rename_lia_btn_{k}", help="重新命名", use_container_width=True):
                    st.session_state[f"renaming_lia_{k}"] = True
            with lrow4:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_lia_btn_{k}", help="刪除帳戶", use_container_width=True):
                    if len(st.session_state.my_liabilities) > 1:
                        del st.session_state.my_liabilities[k]
                        save_now(); st.success(f"✅ 已刪除「{k}」"); st.rerun()
                    else:
                        st.warning("⚠️ 至少保留一個負債帳戶！")

            if st.session_state.get(f"repaying_lia_{k}", False):
                with st.form(key=f"repay_lia_form_{k}"):
                    rp_col1, rp_col2, rp_col3, rp_col4 = st.columns([2, 1, 1, 1])
                    repay_amt = rp_col1.number_input(
                        "還款金額", min_value=0.0, max_value=float(v) if v > 0 else None,
                        step=100.0, key=f"repay_amt_{k}", label_visibility="collapsed",
                        placeholder="輸入還款金額"
                    )
                    deduct_from = rp_col2.selectbox(
                        "扣自帳戶", list(st.session_state.my_assets.keys()) if st.session_state.my_assets else ["（無資產帳戶）"],
                        key=f"repay_from_{k}", label_visibility="collapsed"
                    )
                    confirm_rp = rp_col3.form_submit_button("✅ 確認還款", use_container_width=True)
                    cancel_rp = rp_col4.form_submit_button("✕ 取消", use_container_width=True)
                    if confirm_rp:
                        if repay_amt > 0:
                            new_liab_val = max(0.0, float(v) - repay_amt)
                            st.session_state.my_liabilities[k] = new_liab_val
                            # 同步從選定資產帳戶扣除（如有效帳戶）
                            if deduct_from in st.session_state.my_assets:
                                st.session_state.my_assets[deduct_from] = float(
                                    st.session_state.my_assets.get(deduct_from, 0)
                                ) - repay_amt
                            # 記錄一筆支出log，方便日後查帳
                            st.session_state.my_logs.append({
                                "日期": datetime.now().strftime("%Y/%m/%d"),
                                "類型": "支出 💸", "分類": "其他支出", "子分類": "還款",
                                "項目": f"還款：{k}", "金額": float(repay_amt),
                                "帳戶/備註": deduct_from if deduct_from in st.session_state.my_assets else "未指定帳戶"
                            })
                            save_now()
                            st.session_state[f"repaying_lia_{k}"] = False
                            st.success(f"✅ 已還款 HK${repay_amt:,.2f}，「{k}」餘額：HK${new_liab_val:,.2f}")
                            st.rerun()
                        else:
                            st.warning("⚠️ 請輸入大於 0 的還款金額！")
                    if cancel_rp:
                        st.session_state[f"repaying_lia_{k}"] = False
                        st.rerun()

            if st.session_state.get(f"renaming_lia_{k}", False):
                with st.form(key=f"rename_lia_form_{k}"):
                    rl_col1, rl_col2, rl_col3 = st.columns([3, 1, 1])
                    new_lname = rl_col1.text_input("新名稱", value=k, key=f"rename_lia_input_{k}", label_visibility="collapsed")
                    confirm_rl = rl_col2.form_submit_button("✅ 確認", use_container_width=True)
                    cancel_rl = rl_col3.form_submit_button("✕ 取消", use_container_width=True)
                    if confirm_rl:
                        new_lname = new_lname.strip()
                        if new_lname and new_lname != k and new_lname not in st.session_state.my_liabilities:
                            st.session_state.my_liabilities[new_lname] = st.session_state.my_liabilities.pop(k)
                            save_now()
                            st.session_state[f"renaming_lia_{k}"] = False
                            st.success(f"✅ 已重新命名為「{new_lname}」"); st.rerun()
                        elif new_lname in st.session_state.my_liabilities:
                            st.warning("⚠️ 此名稱已存在！")
                        else:
                            st.warning("⚠️ 名稱無效！")
                    if cancel_rl:
                        st.session_state[f"renaming_lia_{k}"] = False
                        st.rerun()
        new_lia_name = st.text_input("新增負債帳戶名稱", placeholder="例如：車貸 🚗", key="new_lia_name")
        if st.button("➕ 新增負債帳戶"):
            if new_lia_name.strip() and new_lia_name.strip() not in st.session_state.my_liabilities:
                st.session_state.my_liabilities[new_lia_name.strip()] = 0.0; save_now()
                st.success(f"✅ 已新增"); st.rerun()
            else:
                st.warning("⚠️ 名稱無效或已存在！")
    with col_s2:
        st.write("### 🎯 每月預算上限")
        for cat, b_val in list(st.session_state.my_budget.items()):
            new_budget = st.number_input(f"【{cat}】", value=float(b_val), min_value=0.0, step=100.0, key=f"budget_input_{cat}")
            if new_budget != b_val: st.session_state.my_budget[cat] = new_budget; save_now()
