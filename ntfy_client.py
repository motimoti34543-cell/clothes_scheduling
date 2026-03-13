"""
notifier.py — ntfy.sh で通知を送信する
"""
import requests


def send_ntfy_sh(topic: str, message: str) -> tuple[bool, str]:
    """
    ntfy.shでメッセージを送信する。

    Args:
        topic: ntfy.sh のトピック名（例: my-wardrobe-2026）
        message: 送信するメッセージ

    Returns:
        (成功フラグ, ステータスメッセージ)
    """
    if not topic:
        return False, "ntfyのトピック名が設定されていません。「👕 服管理」タブで設定してください。"

    url = f"https://ntfy.sh/{topic}"
    import base64
    
    # RFC 2047 ベース64エンコードを利用するか、ntfy独自の仕様に従う。
    # ntfy.sh ではヘッダにUTF-8文字列をそのまま入れると環境・ライブラリによってはエラーになるため、
    # =?utf-8?b?...?= フォーマットを使用する
    title_bytes = "服献立アプリ".encode('utf-8')
    title_b64 = base64.b64encode(title_bytes).decode('ascii')
    
    headers = {
        "Title": f"=?utf-8?B?{title_b64}?=",
        "Tags": "dress"
    }

    try:
        # dataにはutf-8エンコードされたbytesを渡す
        resp = requests.post(url, data=message.encode('utf-8'), headers=headers, timeout=10)
        if resp.status_code == 200:
            return True, "✅ スマホに送信しました！"
        else:
            return False, f"❌ 送信に失敗しました（ステータス: {resp.status_code}）"
    except requests.exceptions.Timeout:
        return False, "❌ タイムアウトしました。ネットワーク接続を確認してください。"
    except Exception as e:
        return False, f"❌ エラーが発生しました: {str(e)}"
