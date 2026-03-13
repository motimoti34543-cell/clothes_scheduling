"""
data_manager.py — 服データの永続化（JSONファイル）
"""
import json
import os
import uuid

DATA_FILE = os.path.join(os.path.dirname(__file__), "wardrobe_data.json")

# ---------------------------------------------------------------------------
# デフォルトのサンプルデータ
# ---------------------------------------------------------------------------
DEFAULT_DATA = {
    "items": [
        {"id": "s1", "name": "白Tシャツ",   "category": "tops",    "color": "#FFFFFF", "color_name": "白",   "min_temp": 20, "max_temp": 35},
        {"id": "s2", "name": "黒Tシャツ",   "category": "tops",    "color": "#222222", "color_name": "黒",   "min_temp": 20, "max_temp": 35},
        {"id": "s3", "name": "青シャツ",     "category": "tops",    "color": "#4A90D9", "color_name": "青",   "min_temp": 15, "max_temp": 28},
        {"id": "s4", "name": "ベージュニット", "category": "tops",  "color": "#D4B896", "color_name": "ベージュ", "min_temp": 5, "max_temp": 18},
        {"id": "s5", "name": "グレーパーカー", "category": "tops",  "color": "#888888", "color_name": "グレー", "min_temp": 5, "max_temp": 15},
        {"id": "s6", "name": "黒パンツ",     "category": "bottoms", "color": "#1A1A1A", "color_name": "黒",   "min_temp": 0, "max_temp": 35},
        {"id": "s7", "name": "デニム",       "category": "bottoms", "color": "#4169E1", "color_name": "ブルー", "min_temp": 5, "max_temp": 30},
        {"id": "s8", "name": "ベージュチノ", "category": "bottoms", "color": "#C8B899", "color_name": "ベージュ", "min_temp": 10, "max_temp": 30},
        {"id": "s9", "name": "白スニーカー", "category": "shoes",   "color": "#F5F5F5", "color_name": "白",   "min_temp": 5, "max_temp": 35},
        {"id": "s10","name": "黒ブーツ",     "category": "shoes",   "color": "#1A1A1A", "color_name": "黒",   "min_temp": 0, "max_temp": 20},
        {"id": "s11","name": "ブラウンローファー", "category": "shoes", "color": "#8B4513", "color_name": "ブラウン", "min_temp": 10, "max_temp": 30},
        {"id": "s12","name": "ネイビージャケット", "category": "outers", "color": "#1B2A47", "color_name": "ネイビー", "min_temp": 10, "max_temp": 22},
        {"id": "s13","name": "グレーカーディガン", "category": "outers", "color": "#9E9E9E", "color_name": "グレー", "min_temp": 15, "max_temp": 25},
        {"id": "s14","name": "ベージュコート", "category": "outers", "color": "#D4C4A8", "color_name": "ベージュ", "min_temp": -5, "max_temp": 15},
    ],
    "city": "Tokyo",
    "api_key": "",
}


def _load() -> dict:
    """JSONファイルからデータを読み込む。なければデフォルトを返す。"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_DATA.copy()


def _save(data: dict):
    """データをJSONファイルに保存する。"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_items() -> list[dict]:
    """全服アイテムを返す。"""
    return _load().get("items", [])


def save_items(items: list[dict]):
    """服アイテムリストを保存する。"""
    data = _load()
    data["items"] = items
    _save(data)


def add_item(name: str, category: str, color: str, color_name: str, min_temp: int, max_temp: int) -> dict:
    """服を追加して保存する。"""
    data = _load()
    item = {
        "id": str(uuid.uuid4())[:8],
        "name": name,
        "category": category,
        "color": color,
        "color_name": color_name,
        "min_temp": min_temp,
        "max_temp": max_temp,
    }
    data["items"].append(item)
    _save(data)
    return item


def remove_item(item_id: str):
    """IDで服を削除する。"""
    data = _load()
    data["items"] = [i for i in data["items"] if i["id"] != item_id]
    _save(data)


def update_item(item_id: str, name: str, category: str, color: str, color_name: str, min_temp: int, max_temp: int):
    """指定されたIDの服データを更新して保存する。"""
    data = _load()
    for item in data["items"]:
        if item["id"] == item_id:
            item["name"] = name
            item["category"] = category
            item["color"] = color
            item["color_name"] = color_name
            item["min_temp"] = min_temp
            item["max_temp"] = max_temp
            break
    _save(data)


def get_items_by_category(category: str) -> list[dict]:
    """カテゴリで服をフィルタリングして返す。"""
    return [i for i in load_items() if i["category"] == category]


def load_settings() -> dict:
    """都市名・APIキー・ntfy.shのトピック名などの設定を返す。"""
    data = _load()
    return {
        "city": data.get("city", "Tokyo"),
        "api_key": data.get("api_key", ""),
        "ntfy_topic": data.get("ntfy_topic", ""),
    }


def save_settings(city: str, api_key: str, ntfy_topic: str = ""):
    """設定を保存する。"""
    data = _load()
    data["city"] = city
    data["api_key"] = api_key
    data["ntfy_topic"] = ntfy_topic
    _save(data)
