import os
import requests


def _post(endpoint: str, payload: dict) -> dict:
    token = os.environ["SLACK_BOT_TOKEN"]
    resp = requests.post(
        f"https://slack.com/api/{endpoint}",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"Slack API error [{endpoint}]: {data.get('error')}")
    return data


def send_report(user_id: str, chatwork_items: list[dict], slack_items: list[dict], workspace_url: str = "", gmail_items: list[dict] | None = None) -> None:
    dm = _post("conversations.open", {"users": user_id})
    channel_id = dm["channel"]["id"]

    _post("chat.postMessage", {
        "channel": channel_id,
        "text": _build_message(chatwork_items, slack_items, workspace_url, gmail_items or []),
        "mrkdwn": True,
    })


def _slack_link(workspace_url: str, channel_id: str, ts: str) -> str:
    p_ts = ts.replace(".", "")
    return f"{workspace_url}/archives/{channel_id}/p{p_ts}"


def _build_message(chatwork_items: list[dict], slack_items: list[dict], workspace_url: str = "", gmail_items: list[dict] | None = None) -> str:
    gmail_items = gmail_items or []
    total = len(chatwork_items) + len(slack_items) + len(gmail_items)

    if total == 0:
        return (
            "📮 ポスくんより、朝のお届け物です\n\n"
            "今日は未返信のお手紙、ないみたいですよ〜 🌤️\n"
            "素晴らしい！今日もよい一日を！"
        )

    lines = ["📮 ポスくんより、朝のお届け物です\n"]

    if chatwork_items:
        lines.append(f"*【Chatwork】{len(chatwork_items)}件*")
        for item in chatwork_items:
            url = f"https://www.chatwork.com/#!rid{item['room_id']}"
            lines.append(f"  • <{url}|{item['room_name']}> ← {item['sender']}（{item['time']}）")
        lines.append("")

    if slack_items:
        lines.append(f"*【Slack】{len(slack_items)}件*")
        for item in slack_items:
            if workspace_url and item.get("channel_id") and item.get("ts"):
                url = _slack_link(workspace_url, item["channel_id"], item["ts"])
                lines.append(f"  • <{url}|{item['channel_name']}> ← {item['sender']}（{item['time']}）")
            else:
                lines.append(f"  • {item['channel_name']} ← {item['sender']}（{item['time']}）")
        lines.append("")

    if gmail_items:
        lines.append(f"*【Gmail（⚑要返信）】{len(gmail_items)}件*")
        for item in gmail_items:
            lines.append(f"  • <{item['url']}|{item['subject']}> ← {item['sender']}（{item['time']}）")
        lines.append("")

    lines.append(f"返事、お待ちしてる方が *{total}件* いるみたいですよ〜 🌤️")

    return "\n".join(lines)
