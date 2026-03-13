"""
app.py — 服献立アプリ（Wardrobe Planner）
Streamlit でスマホ対応のコーディネート提案アプリ
"""
import streamlit as st
from datetime import datetime
import html

from data_manager import (
    load_items, add_item, remove_item,
    get_items_by_category, load_settings, save_settings,
)
from weather import get_today_weather, get_weather_forecast, weather_emoji
from planner import generate_daily_outfit, generate_weekly_outfits
from ntfy_client import send_ntfy_sh
from data_manager import update_item

def get_color_emoji(hex_color: str) -> str:
    """HEXカラーに近い色の絵文字を返す。"""
    import colorsys
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join([c*2 for c in hex_color])
    try:
        r, g, b = (int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        if s < 0.15:
            if v > 0.8: return "▯"
            return "■"
        h_deg = h * 360
        if h_deg < 15 or h_deg >= 345: return "■"
        if 15 <= h_deg < 45: return "■"
        if 45 <= h_deg < 75: return "■"
        if 75 <= h_deg < 165: return "■"
        if 165 <= h_deg < 255: return "■"
        if 255 <= h_deg < 315: return "■"
        return "■"
    except: return "■"

# =========================================================================
# ページ設定
# =========================================================================
st.set_page_config(
    page_title="👗 服献立",
    page_icon="👗",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# =========================================================================
# カスタムCSS — スマホ対応 & プレミアムデザイン
# =========================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;600;700&display=swap');

:root {
    --bg-primary: #0F0F1A;
    --bg-card: #1A1A2E;
    --bg-card-hover: #222240;
    --accent: #7C3AED;
    --accent-light: #A78BFA;
    --accent-glow: rgba(124, 58, 237, 0.3);
    --text-primary: #F1F1F6;
    --text-secondary: #9CA3AF;
    --border: rgba(255, 255, 255, 0.08);
    --success: #34D399;
    --warning: #FBBF24;
}

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Noto Sans JP', sans-serif !important;
    background: var(--bg-primary) !important;
    color: var(--text-primary) !important;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1A1A2E 0%, #16213E 100%) !important;
}

[data-testid="stSidebar"] * {
    color: var(--text-primary) !important;
}

/* ヘッダー非表示 */
header[data-testid="stHeader"] {
    display: none !important;
}

/* タブスタイル */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background: var(--bg-card);
    border-radius: 12px;
    padding: 4px;
    border: 1px solid var(--border);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    padding: 10px 16px;
    font-weight: 600;
    color: var(--text-secondary) !important;
    background: transparent;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, var(--accent), #6D28D9) !important;
    color: white !important;
    box-shadow: 0 4px 15px var(--accent-glow);
}

/* カード */
.outfit-card {
    background: linear-gradient(135deg, var(--bg-card), var(--bg-card-hover));
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 20px;
    margin: 10px 0;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    transition: transform 0.2s;
}
.outfit-card:hover {
    transform: translateY(-2px);
}

/* カラーブロック */
.color-block {
    display: inline-block;
    width: 48px;
    height: 48px;
    border-radius: 12px;
    border: 2px solid rgba(255,255,255,0.15);
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    vertical-align: middle;
    margin: 4px;
}

/* 大きいカラーブロック（今日のコーデ用） */
.color-block-lg {
    display: inline-block;
    width: 64px;
    height: 64px;
    border-radius: 16px;
    border: 3px solid rgba(255,255,255,0.15);
    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    vertical-align: middle;
    margin: 6px;
    position: relative;
}

/* 重ね着（アウター）の表現: フランス国旗スタイル */
.french-flag-lg {
    display: inline-block;
    width: 64px;
    height: 64px;
    border-radius: 16px;
    border: 3px solid rgba(255,255,255,0.15);
    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    vertical-align: middle;
    margin: 6px;
}
.french-flag-sm {
    display: inline-block;
    width: 48px;
    height: 48px;
    border-radius: 12px;
    border: 2px solid rgba(255,255,255,0.15);
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    vertical-align: middle;
    margin: 4px;
}

/* 天気カード */
.weather-card {
    background: linear-gradient(135deg, #1e3a5f, #2d1b69);
    border-radius: 20px;
    padding: 24px;
    text-align: center;
    margin: 10px 0;
    box-shadow: 0 8px 32px rgba(30, 58, 95, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.1);
}
.weather-card .temp {
    font-size: 48px;
    font-weight: 700;
    background: linear-gradient(135deg, #60A5FA, #A78BFA);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.weather-card .desc {
    font-size: 16px;
    color: var(--text-secondary);
    margin-top: 4px;
}

/* 週間グリッド */
.week-grid {
    display: grid;
    grid-template-columns: 56px repeat(7, 1fr);
    gap: 4px;
    margin: 16px 0;
}
.week-grid .header {
    text-align: center;
    font-weight: 700;
    font-size: 13px;
    padding: 8px 4px;
    color: var(--accent-light);
}
.week-grid .label {
    display: flex;
    align-items: center;
    font-size: 11px;
    font-weight: 600;
    color: var(--text-secondary);
    padding-left: 4px;
}
.week-grid .cell {
    aspect-ratio: 1;
    border-radius: 10px;
    border: 2px solid rgba(255,255,255,0.08);
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);
    transition: transform 0.15s;
    position: relative;
}
.week-grid .cell:hover {
    transform: scale(1.1);
    z-index: 1;
}

/* 服リストアイテム */
.item-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    background: var(--bg-card);
    border-radius: 12px;
    margin: 6px 0;
    border: 1px solid var(--border);
}
.item-color-dot {
    width: 28px;
    height: 28px;
    border-radius: 8px;
    border: 2px solid rgba(255,255,255,0.15);
    flex-shrink: 0;
}
.item-name {
    flex: 1;
    font-weight: 500;
    font-size: 14px;
}
.item-temp {
    font-size: 12px;
    color: var(--text-secondary);
}

/* コピーボタン */
.copy-area {
    background: var(--bg-card);
    border: 1px dashed var(--accent);
    border-radius: 12px;
    padding: 16px;
    font-size: 14px;
    white-space: pre-line;
    line-height: 1.8;
}

/* ボタン調整 */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    border: 1px solid var(--border) !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    box-shadow: 0 4px 15px var(--accent-glow) !important;
}

/* ヘッダータイトル */
.app-title {
    text-align: center;
    padding: 16px 0 8px;
}
.app-title h1 {
    font-size: 28px;
    font-weight: 700;
    background: linear-gradient(135deg, #A78BFA, #60A5FA, #34D399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}
.app-title p {
    color: var(--text-secondary);
    font-size: 13px;
    margin: 4px 0 0;
}

/* Selectbox / Input */
.stSelectbox > div > div,
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
}

/* divider */
.fancy-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
    margin: 20px 0;
}

/* 通知テキスト */
.notify-text {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    font-size: 15px;
    line-height: 2;
}
</style>
""", unsafe_allow_html=True)


# =========================================================================
# ヘッダー
# =========================================================================
st.markdown("""
<div class="app-title">
    <h1>👗 服献立</h1>
    <p>毎朝の服選びをゼロに</p>
</div>
<div class="fancy-divider"></div>
""", unsafe_allow_html=True)


# =========================================================================
# メインコンテンツ — タブ
# =========================================================================
settings = load_settings()
city = settings["city"]
api_key = settings["api_key"]

tab_today, tab_week, tab_notify, tab_manage = st.tabs(["🎯 今日のコーデ", "📅 一週間", "📋 通知", "👕 服管理"])

# -------------------------------------------------------------------------
# Tab 1: 今日のコーデ
# -------------------------------------------------------------------------
with tab_today:
    today_weather = get_today_weather(city, api_key)

    emoji = weather_emoji(today_weather["weather"])
    escaped_city = html.escape(city)
    escaped_desc = html.escape(today_weather["description"])
    
    st.markdown(f"""
    <div class="weather-card">
        <div style="font-size:48px;">{emoji}</div>
        <div class="temp">{today_weather["temp"]}℃</div>
        <div class="desc">{escaped_city} — {escaped_desc}</div>
        <div style="color:var(--text-secondary);font-size:13px;margin-top:8px;">
            ↓ {today_weather["temp_min"]}℃ / ↑ {today_weather["temp_max"]}℃
        </div>
    </div>
    """, unsafe_allow_html=True)

    # コーデ生成
    tops = get_items_by_category("tops")
    bottoms = get_items_by_category("bottoms")
    shoes = get_items_by_category("shoes")
    outers = get_items_by_category("outers")

    if not tops or not bottoms or not shoes:
        st.warning("⚠️ トップス・ボトムス・靴それぞれ最低1つ登録してください（サイドバーから）")
    else:
        # セッション固定（リロードでコーデが変わらないように）
        cache_key = f"today_outfit_{datetime.now().strftime('%Y-%m-%d')}"
        if cache_key not in st.session_state or st.session_state.get("_regenerate"):
            outfit = generate_daily_outfit(tops, bottoms, shoes, outers, today_weather.get("feels_like", today_weather["temp"]))
            st.session_state[cache_key] = outfit
            st.session_state["_regenerate"] = False
        else:
            outfit = st.session_state[cache_key]

        st.markdown('<div class="outfit-card">', unsafe_allow_html=True)
        st.markdown("#### 👔 今日のおすすめコーデ")

        # アウターがある場合の重ね着UI用 (フランス国旗風 Outer | Top | Outer)
        if outfit.get("outer"):
            oc = outfit["outer"]["color"]
            tc = outfit["top"]["color"]
            bg_style = f"background: linear-gradient(90deg, {oc} 33%, {tc} 33%, {tc} 67%, {oc} 67%);"
        else:
            bg_style = f"background: {outfit['top']['color']};"

        # カラーブロック表示
        # エスケープ処理
        t_name = html.escape(outfit['top']['name'])
        o_name = html.escape(outfit['outer']['name']) if outfit.get('outer') else ""
        b_name = html.escape(outfit['bottom']['name'])
        s_name = html.escape(outfit['shoe']['name'])
        t_cname = html.escape(outfit['top'].get('color_name', ''))
        b_cname = html.escape(outfit['bottom'].get('color_name', ''))
        s_cname = html.escape(outfit['shoe'].get('color_name', ''))

        st.markdown(f"""
        <div style="text-align:center;margin:20px 0;">
            <div>
                <span class="{'french-flag-lg' if outfit.get('outer') else 'color-block-lg'}" style="{bg_style}" title="{t_name} {('+ '+o_name) if outfit.get('outer') else ''}">
                </span>
                <span class="color-block-lg" style="background:{outfit['bottom']['color']};"></span>
                <span class="color-block-lg" style="background:{outfit['shoe']['color']};"></span>
            </div>
            <div style="display:flex;justify-content:center;gap:38px;margin-top:8px;font-size:12px;color:var(--text-secondary);">
                <span>トップス</span>
                <span>ボトムス</span>
                <span>シューズ</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div style="text-align:center;">
                <div class="{'french-flag-sm' if outfit.get('outer') else 'color-block'}" style="{bg_style}" title="{t_name} {('+ '+o_name) if outfit.get('outer') else ''}">
                </div>
                <div style="font-weight:600;margin-top:6px;">{t_name}</div>
                <div style="font-size:11px;color:var(--text-secondary);">{t_cname}</div>
                <div style="font-size:10px;color:var(--accent-light); margin-top:4px;">
                    {("🧥 " + o_name) if outfit.get('outer') else ""}
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div style="text-align:center;">
                <div class="color-block" style="background:{outfit['bottom']['color']};"></div>
                <div style="font-weight:600;margin-top:6px;">{b_name}</div>
                <div style="font-size:11px;color:var(--text-secondary);">{b_cname}</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div style="text-align:center;">
                <div class="color-block" style="background:{outfit['shoe']['color']};"></div>
                <div style="font-weight:600;margin-top:6px;">{s_name}</div>
                <div style="font-size:11px;color:var(--text-secondary);">{s_cname}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # 再生成ボタン
        if st.button("🔄 別のコーデを提案", use_container_width=True):
            st.session_state["_regenerate"] = True
            st.rerun()


# -------------------------------------------------------------------------
# Tab 2: 一週間のコーデ
# -------------------------------------------------------------------------
with tab_week:
    forecast = get_weather_forecast(city, api_key)

    tops = get_items_by_category("tops")
    bottoms = get_items_by_category("bottoms")
    shoes = get_items_by_category("shoes")
    outers = get_items_by_category("outers")

    if not tops or not bottoms or not shoes:
        st.warning("⚠️ トップス・ボトムス・靴それぞれ最低1つ登録してください")
    else:
        daily_temps = [f.get("feels_like", f["temp"]) for f in forecast]

        week_cache = f"week_outfits_{datetime.now().strftime('%Y-%m-%d')}"
        if week_cache not in st.session_state or st.session_state.get("_regen_week"):
            weekly = generate_weekly_outfits(tops, bottoms, shoes, outers, daily_temps)
            st.session_state[week_cache] = weekly
            st.session_state["_regen_week"] = False
        else:
            weekly = st.session_state[week_cache]

        # --- 天気バー ---
        st.markdown("#### 📊 一週間の天気")
        weather_cols = st.columns(len(forecast))
        for idx, f in enumerate(forecast):
            with weather_cols[idx]:
                em = weather_emoji(f["weather"])
                st.markdown(f"""
                <div style="text-align:center;font-size:12px;">
                    <div style="font-weight:700;color:var(--accent-light);">{f['day_name']}</div>
                    <div style="font-size:24px;">{em}</div>
                    <div style="font-weight:600;">{f['temp']}℃</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('<div class="fancy-divider"></div>', unsafe_allow_html=True)

        # --- カラーグリッド ---
        st.markdown("#### 🎨 コーデカラーグリッド")

        num_days = len(forecast)
        header_html = f'<div class="week-grid" style="grid-template-columns: 56px repeat({num_days}, 1fr);">'
        header_html += '<div class="header"></div>'
        for f in forecast:
            header_html += f'<div class="header">{f["day_name"]}<br><span style="font-size:10px;color:var(--text-secondary);">{f["date"][5:]}</span></div>'

        # トップス行
        header_html += '<div class="label">👕</div>'
        for i in range(num_days):
            if i < len(weekly):
                o = weekly[i]
                t_name = html.escape(o["top"]["name"])
                o_name = html.escape(o["outer"]["name"]) if o.get("outer") else ""
                if o.get("outer"):
                    oc = o["outer"]["color"]
                    tc = o["top"]["color"]
                    bg_style = f"background: linear-gradient(90deg, {oc} 33%, {tc} 33%, {tc} 67%, {oc} 67%);"
                else:
                    bg_style = f"background: {o['top']['color']};"
                header_html += f'<div class="cell" style="{bg_style}" title="{t_name} {("+ "+o_name) if o.get("outer") else ""}"></div>'
            else:
                header_html += '<div class="cell" style="background:transparent;border:1px dashed var(--border);"></div>'

        # ボトムス行
        header_html += '<div class="label">👖</div>'
        for i in range(num_days):
            if i < len(weekly):
                o = weekly[i]
                b_name = html.escape(o["bottom"]["name"])
                header_html += f'<div class="cell" style="background:{o["bottom"]["color"]};" title="{b_name}"></div>'
            else:
                header_html += '<div class="cell" style="background:transparent;border:1px dashed var(--border);"></div>'

        # 靴行
        header_html += '<div class="label">👟</div>'
        for i in range(num_days):
            if i < len(weekly):
                o = weekly[i]
                s_name = html.escape(o["shoe"]["name"])
                header_html += f'<div class="cell" style="background:{o["shoe"]["color"]};" title="{s_name}"></div>'
            else:
                header_html += '<div class="cell" style="background:transparent;border:1px dashed var(--border);"></div>'

        header_html += '</div>'
        st.markdown(header_html, unsafe_allow_html=True)

        # --- 各日の詳細 ---
        st.markdown('<div class="fancy-divider"></div>', unsafe_allow_html=True)
        st.markdown("#### 📝 詳細")

        for idx, (o, f) in enumerate(zip(weekly, forecast)):
            em = weather_emoji(f["weather"])
            t_name = html.escape(o['top']['name'])
            o_name = html.escape(o['outer']['name']) if o.get('outer') else ""
            b_name = html.escape(o['bottom']['name'])
            s_name = html.escape(o['shoe']['name'])
            
            if o.get("outer"):
                oc = o["outer"]["color"]
                tc = o["top"]["color"]
                bg_style = f"background: linear-gradient(90deg, {oc} 33%, {tc} 33%, {tc} 67%, {oc} 67%);"
                top_cls = "french-flag-sm"
            else:
                bg_style = f"background: {o['top']['color']};"
                top_cls = "color-block"
                
            st.markdown(f"""
            <div class="outfit-card">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <span style="font-weight:700;font-size:16px;">{f["day_name"]}曜日</span>
                        <span style="color:var(--text-secondary);font-size:12px;margin-left:8px;">{f["date"]}</span>
                    </div>
                    <div style="font-size:14px;">{em} {f["temp"]}℃</div>
                </div>
                <div style="display:flex;gap:12px;margin-top:12px;">
                    <div style="flex:1;text-align:center;">
                        <div class="{top_cls}" style="{bg_style}" title="{t_name} {('+ '+o_name) if o.get('outer') else ''}">
                        </div>
                        <div style="font-size:12px;margin-top:4px;">{t_name}</div>
                        <div style="font-size:10px;color:var(--accent-light);">
                            {("🧥 " + o_name) if o.get('outer') else ""}
                        </div>
                    </div>
                    <div style="flex:1;text-align:center;">
                        <div class="color-block" style="background:{o['bottom']['color']};"></div>
                        <div style="font-size:12px;margin-top:4px;">{b_name}</div>
                    </div>
                    <div style="flex:1;text-align:center;">
                        <div class="color-block" style="background:{o['shoe']['color']};"></div>
                        <div style="font-size:12px;margin-top:4px;">{s_name}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        if st.button("🔄 一週間のコーデを再生成", use_container_width=True):
            st.session_state["_regen_week"] = True
            st.rerun()


# -------------------------------------------------------------------------
# Tab 3: 通知
# -------------------------------------------------------------------------
with tab_notify:
    st.markdown("#### 📋 今日のコーデを共有")
    st.markdown("下のテキストをコピーして、LINEやメモに貼り付けられます。")

    today_weather = get_today_weather(city, api_key)
    tops = get_items_by_category("tops")
    bottoms = get_items_by_category("bottoms")
    shoes = get_items_by_category("shoes")
    outers = get_items_by_category("outers")

    if not tops or not bottoms or not shoes:
        st.warning("⚠️ 服を登録してください")
    else:
        cache_key = f"today_outfit_{datetime.now().strftime('%Y-%m-%d')}"
        if cache_key in st.session_state:
            outfit = st.session_state[cache_key]
        else:
            outfit = generate_daily_outfit(tops, bottoms, shoes, outers, today_weather.get("feels_like", today_weather["temp"]))
            st.session_state[cache_key] = outfit

        emoji = weather_emoji(today_weather["weather"])
        date_str = datetime.now().strftime("%m/%d")
        day_name = ["月", "火", "水", "木", "金", "土", "日"][datetime.now().weekday()]

        t_emoji = get_color_emoji(outfit['top']['color'])
        b_emoji = get_color_emoji(outfit['bottom']['color'])
        s_emoji = get_color_emoji(outfit['shoe']['color'])

        notify_text = (
            f"👗 {date_str}({day_name}) の服献立\n"
            f"━━━━━━━━━━━━━━\n"
            f"{emoji} {today_weather['temp']}℃ — {today_weather['description']}\n"
            f"━━━━━━━━━━━━━━\n"
        )

        if outfit.get("outer"):
            o_emoji = get_color_emoji(outfit['outer']['color'])
            french_flag = f"{o_emoji}▯{o_emoji}"
            notify_text += f"🧥 重ね着: {outfit['outer']['name']} + {outfit['top']['name']} ({french_flag})\n"
        else:
            notify_text += f"👕 トップス: {outfit['top']['name']} ({t_emoji})\n"

        notify_text += (
            f"👖 ボトムス: {outfit['bottom']['name']} ({b_emoji})\n"
            f"👟 シューズ: {outfit['shoe']['name']} ({s_emoji})\n"
            f"━━━━━━━━━━━━━━\n"
            f"Have a nice day! ✨"
        )

        st.markdown(f'<div class="notify-text">{notify_text}</div>', unsafe_allow_html=True)

        st.code(notify_text, language=None)

        st.markdown("""
        <div style="text-align:center;margin-top:12px;">
            <p style="color:var(--text-secondary);font-size:12px;">
                💡 上のテキストブロック右上のコピーボタンをクリック！
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="fancy-divider"></div>', unsafe_allow_html=True)
        st.markdown("#### 📱 スマホに通知 (ntfy.sh)")

        ntfy_topic = load_settings().get("ntfy_topic", "")
        if not ntfy_topic:
            st.info("🔑 ntfy.shのトピック名が未設定です。「👕 服管理」タブで設定してください。")
        else:
            if st.button("📩 スマホに今日のコーデを送信", use_container_width=True):
                ok, msg = send_ntfy_sh(ntfy_topic, "\n" + notify_text)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

# -------------------------------------------------------------------------
# Tab 4: 服管理
# -------------------------------------------------------------------------
with tab_manage:
    st.markdown("#### ⚙️ 設定")

    settings = load_settings()
    new_city = st.text_input("🏙️ 都市名", value=settings["city"], help="例: Tokyo, Osaka, Nagoya")
    new_api_key = st.text_input("🔑 OpenWeatherMap API Key", value=settings["api_key"], type="password",
                                help="無料で取得: https://openweathermap.org/api")
    new_ntfy_topic = st.text_input("📩 ntfy.sh トピック名", value=settings.get("ntfy_topic", ""),
                                   help="スマホアプリで購読するトピック名（他とかぶらない名前）")

    if st.button("💾 設定を保存", use_container_width=True):
        save_settings(new_city, new_api_key, new_ntfy_topic)
        st.success("✅ 保存しました！")
        st.rerun()

    st.markdown('<div class="fancy-divider"></div>', unsafe_allow_html=True)

    # --- 服を登録 ---
    st.markdown("#### ➕ 服を登録")

    cat_map = {"トップス": "tops", "ボトムス": "bottoms", "靴": "shoes", "アウター": "outers"}
    cat_label = st.selectbox("カテゴリ", list(cat_map.keys()))
    new_name = st.text_input("服の名前", placeholder="例: 白Tシャツ")
    new_color = st.color_picker("色", "#4A90D9")
    new_color_name = st.text_input("色の名前", placeholder="例: ブルー")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        new_min = st.number_input("適温 (下限℃)", value=10, step=1)
    with col_t2:
        new_max = st.number_input("適温 (上限℃)", value=30, step=1)

    if st.button("➕ 登録する", use_container_width=True):
        if new_name:
            add_item(new_name, cat_map[cat_label], new_color, new_color_name or "—", int(new_min), int(new_max))
            st.success(f"✅「{new_name}」を追加しました！")
            st.rerun()
        else:
            st.warning("服の名前を入力してください")

    st.markdown('<div class="fancy-divider"></div>', unsafe_allow_html=True)

    # --- 登録済みの服 ---
    st.markdown("#### 📦 登録済みの服")

    all_items = load_items()
    if not all_items:
        st.info("まだ服が登録されていません。上のフォームから追加してください。")
    else:
        for cat_ja, cat_en in cat_map.items():
            cat_items = [i for i in all_items if i["category"] == cat_en]
            if cat_items:
                st.markdown(f"**{cat_ja}** ({len(cat_items)})")
                for item in cat_items:
                    with st.expander(f"📦 {item['name']}"):
                        cols = st.columns([1, 4])
                        with cols[0]:
                            st.markdown(
                                f'<div class="item-color-dot" style="background:{item["color"]}; width:100%; height:40px;"></div>',
                                unsafe_allow_html=True,
                            )
                        with cols[1]:
                            st.markdown(f"`{item.get('min_temp', '?')}〜{item.get('max_temp', '?')}℃` | {item.get('color_name', '')}")
                        
                        st.markdown("---")
                        # 編集フォーム
                        edit_name = st.text_input("服の名前", value=item["name"], key=f"name_{item['id']}")
                        edit_color = st.color_picker("色", value=item["color"], key=f"color_{item['id']}")
                        edit_color_name = st.text_input("色の名前", value=item.get("color_name", ""), key=f"cname_{item['id']}")
                        ec1, ec2 = st.columns(2)
                        with ec1:
                            edit_min = st.number_input("下限℃", value=item.get("min_temp", 10), step=1, key=f"min_{item['id']}")
                        with ec2:
                            edit_max = st.number_input("上限℃", value=item.get("max_temp", 30), step=1, key=f"max_{item['id']}")
                            
                        bc1, bc2 = st.columns(2)
                        with bc1:
                            if st.button("💾 更新", key=f"upd_{item['id']}", use_container_width=True):
                                update_item(item["id"], edit_name, item["category"], edit_color, edit_color_name, int(edit_min), int(edit_max))
                                st.success("✅ 更新しました！")
                                st.rerun()
                        with bc2:
                            if st.button("🗑️ 削除", key=f"del_{item['id']}", use_container_width=True):
                                remove_item(item["id"])
                                st.rerun()


st.markdown("""
<div class="fancy-divider"></div>
<div style="text-align:center;padding:16px;color:var(--text-secondary);font-size:11px;">
    服献立 — Wardrobe Planner &nbsp;|&nbsp; 天気データ: OpenWeatherMap
</div>
""", unsafe_allow_html=True)
