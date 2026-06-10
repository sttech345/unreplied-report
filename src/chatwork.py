import os
import requests
from datetime import datetime, timedelta, timezone

BASE_URL = "https://api.chatwork.com/v2"
JST = timezone(timedelta(hours=9))


def _headers() -> dict:
    return {"X-ChatWorkToken": os.environ["CHATWORK_API_TOKEN"]}


def get_unreplied(account_id: int) -> list[dict]:
    """未返信メッセージをChatworkから収集する（月曜は72時間、それ以外は24時間）"""
    now = datetime.now(timezone.utc)
    hours = 72 if now.weekday() == 0 else 24  # 月曜は金〜日をカバー
    since_ts = int((now - timedelta(hours=hours)).timestamp())

    rooms_resp = requests.get(f"{BASE_URL}/rooms", headers=_headers())
    rooms_resp.raise_for_status()
    rooms = rooms_resp.json()

    results = []

    for room in rooms:
        room_id = room["room_id"]
        room_name = room["name"]

        try:
            msgs_resp = requests.get(
                f"{BASE_URL}/rooms/{room_id}/messages",
                headers=_headers(),
                params={"force": 1},
            )
            msgs_resp.raise_for_status()
            messages = msgs_resp.json()
        except Exception:
            continue

        if not isinstance(messages, list) or not messages:
            continue

        recent = [m for m in messages if m.get("send_time", 0) >= since_ts]
        if not recent:
            continue

        room_type = room.get("type", "group")
        to_me_tag = f"[To:{account_id}]"

        # 自分の最終返信時刻
        last_from_me = max(
            (m["send_time"] for m in recent if m.get("account", {}).get("account_id") == account_id),
            default=0,
        )

        # directは全メッセージ対象、groupは[To:自分]宛のみ
        def is_target(m: dict) -> bool:
            if m.get("account", {}).get("account_id") == account_id:
                return False
            if m.get("send_time", 0) <= last_from_me:
                return False
            if room_type == "direct":
                return True
            return to_me_tag in m.get("body", "")

        unreplied = [m for m in recent if is_target(m)]

        if not unreplied:
            continue

        oldest = min(unreplied, key=lambda m: m["send_time"])
        send_time = datetime.fromtimestamp(oldest["send_time"], tz=JST)

        results.append({
            "room_name": room_name,
            "room_id": room_id,
            "sender": oldest.get("account", {}).get("name", "不明"),
            "body": oldest.get("body", "")[:80].replace("\n", " "),
            "time": send_time.strftime("%m/%d %H:%M"),
            "count": len(unreplied),
        })

    return results
