"""
send_daily_outfit.py — 朝のコーデ通知スクリプト

Windowsタスクスケジューラ等から単発で実行されることを想定しています。
"""
import os
import sys

# プロジェクトルートにパスを通す
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_manager import load_settings, get_items_by_category, load_history, save_history
from weather import get_today_weather, weather_emoji
from planner import generate_daily_outfit
from ntfy_client import send_ntfy_sh
from datetime import datetime, timedelta

def get_color_emoji(hex_color: str) -> str:
    """HEXカラーに近い色の絵文字（■系のバリエーション）を返す。"""
    import colorsys
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join([c*2 for c in hex_color])
    r, g, b = (int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    
    # 彩度が低い場合は白黒グレー
    if s < 0.15:
        if v > 0.8: return "▯" # 白に近い
        if v < 0.2: return "■" # 黒に近い
        return "■" # グレー

    # 色相で判定
    h_deg = h * 360
    if h_deg < 15 or h_deg >= 345: return "■" # 赤
    if 15 <= h_deg < 45: return "■"  # オレンジ
    if 45 <= h_deg < 75: return "■"  # 黄色
    if 75 <= h_deg < 165: return "■" # 緑
    if 165 <= h_deg < 255: return "■" # 青
    if 255 <= h_deg < 315: return "■" # 紫
    if 315 <= h_deg < 345: return "■" # ピンク
    return "■"

def main():
    settings = load_settings()
    # 環境変数を優先し、なければ設定ファイルから取得
    city = os.environ.get("WEATHER_CITY") or settings.get("city", "Tokyo")
    api_key = os.environ.get("OPENWEATHER_API_KEY") or settings.get("api_key", "")
    ntfy_topic = os.environ.get("NTFY_TOPIC") or settings.get("ntfy_topic", "")

    if not ntfy_topic:
        print("ntfy_topic is not set. Exiting.")
        return

    today_weather = get_today_weather(city, api_key)

    tops = get_items_by_category("tops")
    bottoms = get_items_by_category("bottoms")
    shoes = get_items_by_category("shoes")
    outers = get_items_by_category("outers")

    if not tops or not bottoms or not shoes:
        print("Not enough clothes registered. Exiting.")
        return

    # 履歴の読み込みと5日以内の使用済みアイテムIDの抽出
    history = load_history()
    five_days_ago = (datetime.now() - timedelta(days=5)).isoformat()
    
    used_item_ids = set()
    for entry in history:
        if entry.get("date") >= five_days_ago:
            used_item_ids.add(entry.get("top_id"))
            used_item_ids.add(entry.get("bottom_id"))
            used_item_ids.add(entry.get("shoe_id"))
            if entry.get("outer_id"):
                used_item_ids.add(entry.get("outer_id"))

    outfit = generate_daily_outfit(tops, bottoms, shoes, outers, today_weather.get("feels_like", today_weather["temp"]), used_items=used_item_ids)

    # 履歴への追加
    new_entry = {
        "date": datetime.now().isoformat(),
        "top_id": outfit.get("top_id"),
        "bottom_id": outfit.get("bottom_id"),
        "shoe_id": outfit.get("shoe_id"),
        "outer_id": outfit.get("outer_id")
    }
    history.append(new_entry)
    
    # 5日分より古い履歴を削除して保存
    cutoff_date = (datetime.now() - timedelta(days=5)).isoformat()
    history = [entry for entry in history if entry.get("date") >= cutoff_date]
    save_history(history)

    emoji = weather_emoji(today_weather["weather"])
    temp = today_weather["temp"]
    feels_like = today_weather.get("feels_like", temp)
    desc = today_weather["description"]

    # 肌着アドバイスの判定（体感温度ベース）
    if feels_like <= 10:
        undershirt_advice = "🧣 肌着: 必須！暖かいインナーを着よう"
    elif feels_like <= 15:
        undershirt_advice = "🩳 肌着: 着た方がいいよ"
    elif feels_like <= 20:
        undershirt_advice = "🩳 肌着: 薄手でもあると安心"
    else:
        undershirt_advice = "☀️ 肌着: なくてもOK"

    # 通知テキストの組み立て
    notify_text = (
        f"👗 今日の服献立\n"
        f"━━━━━━━━━━━━━━\n"
        f"{emoji} 気温{temp}℃ / 体感{feels_like}℃ — {desc}\n"
        f"{undershirt_advice}\n"
        f"━━━━━━━━━━━━━━\n"
    )

    t_emoji = get_color_emoji(outfit['top']['color'])
    b_emoji = get_color_emoji(outfit['bottom']['color'])
    s_emoji = get_color_emoji(outfit['shoe']['color'])

    if outfit.get("outer"):
        o_emoji = get_color_emoji(outfit['outer']['color'])
        # フランスの国旗みたいに集約表示 (■▯■) ※▯はトップスの色
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

    success, msg = send_ntfy_sh(ntfy_topic, "\n" + notify_text)
    if success:
        print("Notification sent successfully.")
    else:
        # Windowsのコマンドプロンプト等で絵文字表示エラーが出るのを防ぐ
        print(f"Failed to send notification: {msg}".encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding))

if __name__ == "__main__":
    main()
