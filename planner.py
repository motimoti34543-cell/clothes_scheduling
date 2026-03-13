"""
planner.py — コーディネート生成ロジック
気温フィルタリング＋色相性を考慮してコーデを自動提案する。
"""
import random
import colorsys


# =========================================================================
# 色相性判定
# =========================================================================

def hex_to_hsl(hex_color: str) -> tuple[float, float, float]:
    """HEXカラーをHSL（色相, 彩度, 明度）に変換"""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return h * 360, s, l


def is_neutral(hex_color: str) -> bool:
    """無彩色系（白・黒・グレー・ベージュなど低彩度の色）かどうか判定"""
    _, saturation, _ = hex_to_hsl(hex_color)
    return saturation < 0.15


def is_valid_color_combo(colors: list[str]) -> bool:
    """
    色の組み合わせの相性を判定する。
    - 無彩色は何にでも合う
    - 同系色（色相差30度以内）はOK
    - 補色（色相差150〜210度）は要注意だが完全NGではない
    - 3色全てが高彩度かつバラバラだとNG
    """
    if len(colors) < 2:
        return True

    chromatic_hues = []
    for c in colors:
        if not is_neutral(c):
            h, s, l = hex_to_hsl(c)
            chromatic_hues.append(h)

    # 有彩色が1個以下なら問題なし
    if len(chromatic_hues) <= 1:
        return True

    # 有彩色同士の色相差をチェック
    for i in range(len(chromatic_hues)):
        for j in range(i + 1, len(chromatic_hues)):
            diff = abs(chromatic_hues[i] - chromatic_hues[j])
            diff = min(diff, 360 - diff)
            # 色相差60〜150度（あまり調和しない範囲）で彩度が高い場合はNG
            if 60 < diff < 150:
                return False

    return True


# =========================================================================
# 気温フィルタリング
# =========================================================================

def filter_by_temp(items: list[dict], temp: float) -> list[dict]:
    """気温に合うアイテムだけをフィルタリングする。"""
    filtered = [
        i for i in items
        if i.get("min_temp", -999) <= temp <= i.get("max_temp", 999)
    ]
    # フィルタ結果が空なら全アイテムを返す（フォールバック）
    return filtered if filtered else items


# =========================================================================
# コーディネート生成
# =========================================================================

def generate_daily_outfit(
    tops: list[dict],
    bottoms: list[dict],
    shoes: list[dict],
    outers: list[dict],
    temp: float,
    used_items: set[str] | None = None,
) -> dict:
    """
    1日分のコーディネートを生成する。
    - 気温に合うアイテムをフィルタ
    - 色相性を考慮
    - 週で既に使用したアイテムを避ける
    - 気温に応じてアウターを選択 (目安: 22度以下でアウター候補があれば着る)
    """
    if used_items is None:
        used_items = set()

    t_pool = filter_by_temp(tops, temp)
    b_pool = filter_by_temp(bottoms, temp)
    s_pool = filter_by_temp(shoes, temp)
    o_pool = filter_by_temp(outers, temp) if temp <= 22 else []

    # 未使用のアイテムを優先する
    t_pool_unused = [i for i in t_pool if i["id"] not in used_items] or t_pool
    b_pool_unused = [i for i in b_pool if i["id"] not in used_items] or b_pool
    s_pool_unused = [i for i in s_pool if i["id"] not in used_items] or s_pool
    o_pool_unused = [i for i in o_pool if i["id"] not in used_items] or o_pool

    # フォールバックのために最低1つのアイテムを確保
    if not t_pool_unused: t_pool_unused = tops if tops else [{"id": "fallback", "color": "#ffffff", "name": "トップス"}]
    if not b_pool_unused: b_pool_unused = bottoms if bottoms else [{"id": "fallback", "color": "#ffffff", "name": "ボトムス"}]
    if not s_pool_unused: s_pool_unused = shoes if shoes else [{"id": "fallback", "color": "#ffffff", "name": "シューズ"}]

    for _ in range(200):
        top = random.choice(t_pool_unused)
        bottom = random.choice(b_pool_unused)
        shoe = random.choice(s_pool_unused)
        
        outer = None
        if o_pool_unused:
            outer = random.choice(o_pool_unused)

        # 色相性チェック (アウターがある場合はアウターの色も含める)
        colors_to_check = [top["color"], bottom["color"], shoe["color"]]
        if outer:
            colors_to_check.append(outer["color"])

        if not is_valid_color_combo(colors_to_check):
            continue

        return {
            "top": top,
            "bottom": bottom,
            "shoe": shoe,
            "outer": outer,
            "top_id": top.get("id"),
            "bottom_id": bottom.get("id"),
            "shoe_id": shoe.get("id"),
            "outer_id": outer.get("id") if outer else None,
        }

    # フォールバック: 条件緩和
    return {
        "top": t_pool_unused[0],
        "bottom": b_pool_unused[0],
        "shoe": s_pool_unused[0],
        "outer": o_pool_unused[0] if o_pool_unused else None,
        "top_id": t_pool_unused[0].get("id"),
        "bottom_id": b_pool_unused[0].get("id"),
        "shoe_id": s_pool_unused[0].get("id"),
        "outer_id": o_pool_unused[0].get("id") if o_pool_unused else None,
    }



def generate_weekly_outfits(
    tops: list[dict],
    bottoms: list[dict],
    shoes: list[dict],
    outers: list[dict],
    daily_temps: list[float],
) -> list[dict]:
    """
    一週間分のコーディネートを生成する。
    daily_temps: 各日の予想気温リスト（最大7日分）
    """
    outfits = []
    used_items = set()

    for i, temp in enumerate(daily_temps[:7]):
        outfit = generate_daily_outfit(tops, bottoms, shoes, outers, temp, used_items)
        outfits.append(outfit)
        
        # 使用したアイテムを記録（次回以降避けるため）
        if outfit["top_id"]: used_items.add(outfit["top_id"])
        if outfit["bottom_id"]: used_items.add(outfit["bottom_id"])
        if outfit["shoe_id"]: used_items.add(outfit["shoe_id"])
        if outfit["outer_id"]: used_items.add(outfit["outer_id"])

    return outfits
