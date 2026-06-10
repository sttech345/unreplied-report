import os
import time
import requests
from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=9))
_user_cache: dict[str, str] = {}


def _get(endpoint: str, params: dict = None, token: str = None) -> dict:
    t = token or os.environ["SLACK_USER_TOKEN"]
    for attempt in range(4):
        resp = requests.get(
            f"https://slack.com/api/{endpoint}",
            headers={"Authorization": f"Bearer {t}"},
            params=params or {},
        )
        data = resp.json()
        if data.get("error") == "ratelimited":
            wait = int(resp.headers.get("Retry-After", 2)) + 1
            time.sleep(wait)
            continue
        if not data.get("ok"):
            raise RuntimeError(f"Slack API error [{endpoint}]: {data.get('error')}")
        return data
    raise RuntimeError(f"Slack API ratelimited [{endpoint}]: gave up after retries")


_bot_cache: dict[str, bool] = {}


def _get_user_name(user_id: str) -> str:
    if user_id in _user_cache:
        return _user_cache[user_id]
    try:
        data = _get("users.info", {"user": user_id})
        user = data.get("user", {})
        name = user.get("real_name") or user.get("name", user_id)
        _bot_cache[user_id] = user.get("is_bot", False) or user.get("is_app_user", False)
    except Exception:
        name = user_id
        _bot_cache[user_id] = False
    _user_cache[user_id] = name
    return name


def _is_bot(user_id: str) -> bool:
    if user_id not in _bot_cache:
        _get_user_name(user_id)
    return _bot_cache.get(user_id, False)


def _has_exclude_reaction(message: dict, user_id: str, exclude_reactions: list[str]) -> bool:
    """指定リアクションをユーザー自身がつけているか確認"""
    for reaction in message.get("reactions", []):
        if reaction["name"] in exclude_reactions and user_id in reaction.get("users", []):
            return True
    return False


def _paginate_channels(channel_types: str) -> list[dict]:
    channels = []
    cursor = None
    while True:
        params = {"types": channel_types, "exclude_archived": "true", "limit": 200}
        if cursor:
            params["cursor"] = cursor
        data = _get("conversations.list", params)
        channels.extend(data.get("channels", []))
        cursor = data.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break
    return channels


def get_workspace_url() -> str:
    data = _get("auth.test")
    return data.get("url", "https://slack.com/").rstrip("/")


def get_unreplied(user_id: str, exclude_reactions: list[str]) -> list[dict]:
    """メンション・DMの未返信メッセージをSlackから収集する"""
    now = datetime.now(timezone.utc)
    hours = 72 if now.weekday() == 0 else 24  # 月曜は金〜日をカバー
    since_ts = (now - timedelta(hours=hours)).timestamp()
    results = []

    results.extend(_get_dm_unreplied(user_id, since_ts, exclude_reactions))
    results.extend(_get_mention_unreplied(user_id, since_ts, exclude_reactions))

    return results


def _get_dm_unreplied(user_id: str, since_ts: float, exclude_reactions: list[str]) -> list[dict]:
    results = []
    dm_channels = _paginate_channels("im")

    for ch in dm_channels:
        ch_id = ch["id"]
        partner_id = ch.get("user", "")
        if partner_id == user_id:
            continue
        if _is_bot(partner_id):
            continue

        try:
            history = _get("conversations.history", {
                "channel": ch_id,
                "oldest": str(since_ts),
                "limit": 30,
            })
        except Exception:
            continue

        messages = [m for m in history.get("messages", []) if m.get("type") == "message"]
        if not messages:
            continue

        # 自分の最終返信時刻
        last_from_me = max(
            (float(m["ts"]) for m in messages if m.get("user") == user_id),
            default=0.0,
        )

        unreplied = [
            m for m in messages
            if m.get("user") != user_id
            and float(m.get("ts", 0)) > last_from_me
            and not _has_exclude_reaction(m, user_id, exclude_reactions)
        ]

        if not unreplied:
            continue

        oldest = min(unreplied, key=lambda m: float(m["ts"]))
        send_time = datetime.fromtimestamp(float(oldest["ts"]), tz=JST)
        sender_name = _get_user_name(partner_id) if partner_id else "不明"

        results.append({
            "channel_name": f"DM: {sender_name}",
            "channel_id": ch_id,
            "ts": oldest["ts"],
            "sender": sender_name,
            "body": oldest.get("text", "")[:80].replace("\n", " "),
            "time": send_time.strftime("%m/%d %H:%M"),
            "count": len(unreplied),
        })

    return results


def _get_mention_unreplied(user_id: str, since_ts: float, exclude_reactions: list[str]) -> list[dict]:
    results = []
    mention_tag = f"<@{user_id}>"
    channels = _paginate_channels("public_channel,private_channel")

    for ch in channels:
        if not ch.get("is_member"):
            continue

        ch_id = ch["id"]
        ch_name = ch.get("name", ch_id)

        try:
            history = _get("conversations.history", {
                "channel": ch_id,
                "oldest": str(since_ts),
                "limit": 100,
            })
        except Exception:
            continue

        for msg in history.get("messages", []):
            if mention_tag not in msg.get("text", ""):
                continue
            if msg.get("user") == user_id:
                continue
            if _has_exclude_reaction(msg, user_id, exclude_reactions):
                continue

            # スレッドで自分が返信済みか確認
            if msg.get("reply_count", 0) > 0:
                try:
                    thread = _get("conversations.replies", {
                        "channel": ch_id,
                        "ts": msg["ts"],
                    })
                    replies = thread.get("messages", [])[1:]
                    if any(r.get("user") == user_id for r in replies):
                        continue
                except Exception:
                    pass

            send_time = datetime.fromtimestamp(float(msg["ts"]), tz=JST)
            sender_name = _get_user_name(msg.get("user", "")) if msg.get("user") else "不明"

            results.append({
                "channel_name": f"#{ch_name}",
                "channel_id": ch_id,
                "ts": msg["ts"],
                "sender": sender_name,
                "body": msg.get("text", "")[:80].replace("\n", " "),
                "time": send_time.strftime("%m/%d %H:%M"),
                "count": 1,
            })

    return results
