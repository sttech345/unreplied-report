# 📮 ポスくん — 未返信レポート Bot

毎朝8時に Chatwork・Slack の未返信メッセージを収集して、Slack DM で教えてくれる Bot。

```
📮 ポスくんより、朝のお届け物です

【Chatwork】
  • `開発チーム`（2件）
    田中さん（06/09 14:32）「例の件、どうなりましたか…」

【Slack】
  • `#general`
    山田さん（06/09 15:01）「<@U...> 確認お願いします…」

返事、お待ちしてる方が 3件 いるみたいですよ〜 🌤️
```

---

## セットアップ

### 1. Slack App を作る

[api.slack.com/apps](https://api.slack.com/apps) で新規アプリを作成する。

**Bot Token Scopes（ポスくん投稿用）**
- `chat:write`
- `im:write`

**User Token Scopes（メッセージ読み取り用）**
- `channels:history`
- `groups:history`
- `im:history`
- `mpim:history`
- `channels:read`
- `groups:read`
- `im:read`
- `users:read`

ワークスペースにインストールして以下を控えておく：
- **Bot User OAuth Token**（`xoxb-...`）→ `SLACK_BOT_TOKEN`
- **User OAuth Token**（`xoxp-...`）→ `SLACK_USER_TOKEN`

### 2. GitHub Secrets を設定する

リポジトリの Settings → Secrets and variables → Actions に追加：

| Secret 名 | 内容 |
|---|---|
| `CHATWORK_API_TOKEN` | Chatwork の API トークン |
| `CHATWORK_ACCOUNT_ID` | 自分の Chatwork アカウント ID |
| `SLACK_BOT_TOKEN` | Slack Bot Token（`xoxb-...`） |
| `SLACK_USER_TOKEN` | Slack User Token（`xoxp-...`） |
| `SLACK_USER_ID` | 自分の Slack ユーザー ID（`U...`） |

### 3. 動作確認

GitHub Actions の画面から `workflow_dispatch` で手動実行できる。

---

## 除外スタンプの設定

`config.yml` で、このリアクションを自分がつけたメッセージは未返信扱いにしない、と設定できる。

```yaml
slack:
  exclude_reactions:
    - white_check_mark  # ✅
    - eyes              # 👀
    - ok_hand           # 👌
```

Slack 絵文字名（コロンなし）で指定する。変更後はコミットするだけで反映される。

---

## 今後の予定

- [ ] Gmail 対応
- [ ] 週次サマリーモード
