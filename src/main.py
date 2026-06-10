import os
import sys
import yaml
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import chatwork
import slack_collector
import slack_notifier


def load_config() -> dict:
    config_path = Path(__file__).parent.parent / "config.yml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def main() -> None:
    config = load_config()

    cw_account_id = int(os.environ["CHATWORK_ACCOUNT_ID"])
    slack_user_id = os.environ["SLACK_USER_ID"]
    exclude_reactions = config.get("slack", {}).get("exclude_reactions", [])

    print("Chatwork 収集中...")
    cw_items = chatwork.get_unreplied(cw_account_id)
    print(f"  → {len(cw_items)} 件")

    print("Slack 収集中...")
    sl_items = slack_collector.get_unreplied(slack_user_id, exclude_reactions)
    workspace_url = slack_collector.get_workspace_url()
    print(f"  → {len(sl_items)} 件")

    gmail_items = []
    if all(os.environ.get(k) for k in ("GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET", "GMAIL_REFRESH_TOKEN")):
        import gmail_collector
        print("Gmail 収集中...")
        try:
            gmail_items = gmail_collector.get_unreplied()
            print(f"  → {len(gmail_items)} 件")
        except Exception as e:
            print(f"  ⚠️ Gmail 取得失敗: {e}")

    print("ポスくん送信中...")
    slack_notifier.send_report(slack_user_id, cw_items, sl_items, workspace_url, gmail_items)
    print("完了！")


if __name__ == "__main__":
    main()
