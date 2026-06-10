# ポスくん — 未返信レポート Bot

> **このファイルは Claude Code が読む設定ファイルです。**
> エンドユーザーの方は `docs/posukun-guide.md` を参照してください。
> 以下の手順内で「ユーザーに案内する」「貼り付けが確認できたら次に進む」などの指示は Claude Code 向けです。

---

## このツールでできること

毎朝8時に **Chatwork・Slack の未返信メッセージを自動で収集して、Slack DM に届けてくれる Bot** です。

```
📮 ポスくんより、朝のお届け物です

【Chatwork】2件
  • 営業チーム（リンク） ← 田中さん（06/09 14:32）
  • 開発MTG（リンク） ← 鈴木さん（06/09 09:15）

【Slack】3件
  • #marketing_all（リンク） ← 山田さん（06/09 15:01）
  • DM: 佐藤さん（リンク） ← 佐藤さん（06/09 11:20）
  • #general（リンク） ← 高橋さん（06/09 08:45）

返事、お待ちしてる方が 5件 いるみたいですよ〜 🌤️
```

GitHub Actions で動くので、PCを起動していなくても毎朝届きます。

---

## Claude Code へ：セットアップの進め方

このリポジトリを clone したユーザーがセットアップを依頼してきたら、以下の順番で進めてください。

### Step 1：前提確認

**PowerShell の開き方**：Windows のスタートメニューから「PowerShell」と検索して開いてください。以下のコマンドはすべて PowerShell に入力して実行します。

以下の前提条件をすべて満たしてから先に進んでください。

- [ ] **git がインストールされている**
  - PowerShell で `git --version` を実行。エラーが出る場合は https://git-scm.com からインストール
- [ ] **git の初期設定が済んでいる**
  - PowerShell で以下を実行し、名前とメールアドレスが設定されているか確認してください：
    ```powershell
    git config --global user.name
    git config --global user.email
    ```
  - 何も表示されない場合は以下を実行してください（`<>` 内を実際の情報に置き換えてください）：
    ```powershell
    git config --global user.name "<あなたの名前>"
    git config --global user.email "<あなたのメールアドレス>"
    ```
- [ ] **GitHub アカウントを持っている**
- [ ] **GitHub CLI（`gh`）がインストールされている**
  - PowerShell で `gh --version` を実行。エラーが出る場合は以下を実行：
    ```powershell
    winget install --id GitHub.cli
    ```
  - インストール後、PowerShell を一度閉じて開き直してください
- [ ] **GitHub CLI で認証済みになっている**
  - PowerShell で以下を実行して認証状態を確認：
    ```powershell
    gh auth status
    ```
  - 「You are not logged in」などと表示された場合は以下を実行し、ブラウザの案内に従って GitHub にログインしてください：
    ```powershell
    gh auth login
    ```
- [ ] **GitHub.com でこのリポジトリを fork 済み**
  - 元リポジトリ：**https://github.com/sttech345/unreplied-report**
  - fork とは：自分のアカウントにリポジトリをコピーすること
  - 上記 URL を開いて右上の「Fork」ボタンを押す
  - **fork したリポジトリは必ず Private に設定してください**（Settings → General → Danger Zone → Change visibility → Make private）。Public のままだと第三者がワークフローを実行できます。Secrets 登録（Step 4）前までに必ず Private にしてください。
- [ ] **fork したリポジトリを PC に clone 済み**
  - clone とは：GitHub 上のリポジトリを PC にダウンロードすること
  - PowerShell で以下を実行（`<あなたのGitHubユーザー名>` を実際のユーザー名に置き換えてください）：
    ```powershell
    cd $HOME
    gh repo clone <あなたのGitHubユーザー名>/unreplied-report
    ```
  - clone が完了すると `$HOME\unreplied-report` フォルダが作成されます
- [ ] **Chatwork アカウント（API トークン取得可能）**
- [ ] **Slack ワークスペースへの App インストール権限がある**
  - 権限がない場合、Step 2 手順5で「Install to Workspace」が「Request to Install」と表示されます。その場合はワークスペースのオーナーに承認を依頼してください。

### Step 2：Slack App を作る

ユーザーに以下を案内する。**この手順はブラウザ上での操作のため、Claude Code は自律実行できません。ユーザーが完了したらトークンを貼り付けてもらうまで次の Step に進まないでください。**

1. [api.slack.com/apps](https://api.slack.com/apps) → **Create New App → From scratch**
2. App Name: 任意（例：`ポスくん`）、ワークスペースを選択
3. 左メニュー **App Home** を開きます。「Your App's Presence in Slack」セクションの「Edit」をクリックし、Display Name と Default Name を入力して保存してください。**この操作をしないと Install to Workspace が完了できない場合があります。**
4. 左メニュー **OAuth & Permissions** → ページを下にスクロールすると「Scopes」セクションがあります

**スコープの追加方法：**「Add an OAuth Scope」ボタンをクリックし、スコープ名を1つずつ検索して追加してください。

> **なぜ2種類のスコープが必要か：** Bot トークンは Slack DM に通知を投稿するために使います。User トークンはあなたの Slack の DM やチャンネルのメッセージを読み取るために使います。どちらも必要です。

**Bot Token Scopes（投稿用）**
- `chat:write`
- `im:write`

**User Token Scopes（読み取り用）**
- `channels:history`（パブリックチャンネルの履歴を読む）
- `channels:read`（パブリックチャンネルの一覧を取得）
- `groups:history`（プライベートチャンネルの履歴を読む）
- `groups:read`（プライベートチャンネルの一覧を取得。`groups:history` とは別物なので両方必要）
- `im:history`（1対1 DM の履歴を読む）
- `im:read`（1対1 DM の一覧を取得）
- `reactions:read`（★ **除外スタンプ機能に必須。忘れると config.yml の設定が無視されます**）
- `users:read`（ユーザー情報を取得）

5. **スコープをすべて追加し終わってから** Install to Workspace を押してください。先に Install してしまった場合はスコープ追加後に **Reinstall to Workspace** を押せば大丈夫です。

   > **「Request to Install」と表示された場合：** ワークスペースのオーナーによる承認が必要です。ボタンを押すと承認依頼が送信されます。承認されるまでこの手順を待ってください。

6. Install 後、OAuth & Permissions ページの「OAuth Tokens for Your Workspace」セクションに2つのトークンが表示されます。それぞれコピーして控えてください：
   - **Bot User OAuth Token**（`xoxb-...`）
   - **User OAuth Token**（`xoxp-...`）

> **スコープを後から追加した場合：** 必ず **Reinstall to Workspace** を押す。押さないと新しいスコープが反映されない。

> **セキュリティ注意：** User OAuth Token（xoxp-...）はあなた本人として行動できる強力なトークンです。コードファイルや config.yml に直接書いてコミットしないでください。誤ってコミット・公開した場合は api.slack.com/apps からすぐにトークンを再発行してください。

---

**以下の2つのトークンをこのチャットに貼り付けてください。貼り付けが確認できたら Step 3 に進みます。**

- Bot User OAuth Token（`xoxb-...`）：
- User OAuth Token（`xoxp-...`）：

### Step 3：Chatwork API トークンを取得

ユーザーに案内する。**この手順もブラウザ上での操作です。完了したら値を貼り付けてもらうまで Step 4 に進まないでください。**

Chatwork 右上アイコン → **「API設定」** からトークンをコピーする。

Chatwork アカウント ID の確認方法：Chatwork の右上アイコン → **「プロフィール設定」** を開くと、ブラウザの URL 末尾に数字が表示されます。それがアカウント ID です。あるいは PowerShell で以下を実行しても確認できます（`<token>` を実際のトークンに置き換えてください）：

```powershell
Invoke-RestMethod -Uri "https://api.chatwork.com/v2/me" -Headers @{"X-ChatWorkToken" = "<token>"} | Select-Object -ExpandProperty account_id
```

---

**以下の2つの値をこのチャットに貼り付けてください。貼り付けが確認できたら Step 4 に進みます。**

- Chatwork API トークン：
- Chatwork アカウント ID：

### Step 3.5：Gmail の設定（オプション）

Gmail 対応を使わない場合はこの Step をスキップしてください。Chatwork・Slack のみでも動作します。

**事前に必要なもの：**
- Google アカウント（Gmail）
- Google Cloud Console へのアクセス権

**手順：**

1. [console.cloud.google.com](https://console.cloud.google.com) を開く
2. プロジェクトを作成（例：`morning-report`）
3. 左メニュー **「APIとサービス」→「ライブラリ」** から **Gmail API** を検索して有効化
4. **「APIとサービス」→「認証情報」→「認証情報を作成」→「OAuth クライアント ID」** を選択
   - アプリケーションの種類：**デスクトップアプリ**
   - 名前：任意（例：`posukun`）
5. 作成後に表示される **クライアント ID** と **クライアント シークレット** を控える
6. **OAuth 同意画面** → 「テストユーザー」に自分の Gmail アドレスを追加

**refresh_token の取得（一度だけ実施）：**

PowerShell で以下を実行してください（`<CLIENT_ID>` と `<CLIENT_SECRET>` を置き換えてください）：

```powershell
pip install google-auth-oauthlib
```

```python
# get_token.py として保存して実行
from google_auth_oauthlib.flow import InstalledAppFlow
import json

flow = InstalledAppFlow.from_client_config(
    {
        "installed": {
            "client_id": "<CLIENT_ID>",
            "client_secret": "<CLIENT_SECRET>",
            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    },
    scopes=["https://www.googleapis.com/auth/gmail.modify"],
)
creds = flow.run_local_server(port=0)
print("REFRESH_TOKEN:", creds.refresh_token)
```

```powershell
python get_token.py
```

ブラウザが開くので Gmail アカウントでログインして承認してください。表示された `REFRESH_TOKEN` の値を控えます。

---

**以下の3つの値をこのチャットに貼り付けてください。貼り付けが確認できたら Step 4 に進みます。**

- Gmail クライアント ID：
- Gmail クライアント シークレット：
- Gmail refresh_token：

> **ラベリングについて：** `⚑要返信` ラベルは claude.ai のルーティン機能で付与される前提です。ルーティンが動いていない場合、Gmail 欄は 0 件になります。

### Step 4：GitHub Secrets を登録

> **GitHub Secrets とは：** パスワードやトークンなどの機密情報を安全に保管する仕組みです。コードファイルに直接書くと情報が外部に漏れるリスクがあるため、Secrets に登録してプログラムから読み取る方式を使っています。

**まず PowerShell でリポジトリのフォルダに移動してください：**

```powershell
cd $HOME\unreplied-report
```

移動できたら、以下を実行して登録先が自分の fork で Private になっていることを確認してください：

```powershell
gh repo view --json owner,visibility --jq '"owner: \(.owner.login)  visibility: \(.visibility)"'
```

オーナー名が自分の GitHub ユーザー名で、visibility が `PRIVATE` であれば OK です。

---

**Slack ユーザー ID の取得：**

以下を実行してください（`<xoxp-...>` を Step 2 で取得した User OAuth Token に置き換えてください）：

```powershell
$env:SLACK_USER_TOKEN = "<xoxp-...>"
$result = Invoke-RestMethod -Uri "https://slack.com/api/auth.test" -Headers @{Authorization="Bearer $env:SLACK_USER_TOKEN"}
if ($result.ok) { $result.user_id } else { Write-Host "エラー: $($result.error) — トークンを確認してください" }
```

`U01ABC12345` のような `U` で始まる文字列が表示されれば成功です。

---

以下のコマンドを1つずつ実行してください。実行すると入力プロンプトが表示されるので、トークンを貼り付けて Enter を押してください。**貼り付けた文字は画面に表示されませんが、正しく入力されています。**

```powershell
gh secret set CHATWORK_API_TOKEN
gh secret set CHATWORK_ACCOUNT_ID
gh secret set SLACK_BOT_TOKEN
gh secret set SLACK_USER_TOKEN
gh secret set SLACK_USER_ID
```

Gmail を使う場合は追加で以下も実行してください：

```powershell
gh secret set GMAIL_CLIENT_ID
gh secret set GMAIL_CLIENT_SECRET
gh secret set GMAIL_REFRESH_TOKEN
```

> **なぜ引数なしで実行するのか：** `--body "<トークン>"` の形式でコマンドに直接書くと PowerShell の履歴ファイルにトークンが平文で記録されます。引数なしの上記方式ではそのリスクを回避できます。

### Step 5：動作確認

以下を順番に実行してください：

```powershell
gh workflow run posukun-morning-report
```

```powershell
$runId = (gh run list --workflow=posukun-morning-report --limit=1 --json databaseId | ConvertFrom-Json)[0].databaseId
gh run watch $runId --exit-status
```

成功すれば Slack DM にポスくんからメッセージが届きます。**未返信が0件の場合は「今日は未返信のお手紙、ないみたいですよ〜 🌤️」というメッセージが届きます。これも正常動作です。**

**失敗した場合：** GitHub リポジトリの Actions タブ → 該当の実行をクリック → ログを確認してください。エラー内容をチャットに貼り付けていただければ対処方法を案内します。

---

## カスタマイズ（config.yml）

**トークンなどの機密情報は config.yml に書かないでください。**

```yaml
slack:
  # この絵文字リアクションを自分がつけたメッセージは未返信扱いにしない
  # Slack絵文字名（コロンなし）で指定する
  exclude_reactions:
    - white_check_mark  # ✅ 対応済み
    - eyes              # 👀 確認済み
    - ok_hand           # 👌 了解
```

> `reactions:read` スコープがないとこの設定は無視されます。Step 2 で追加されているか確認してください。

設定変更後は以下を実行するか、GitHub.com 上でファイルを直接編集してください：

```powershell
git add config.yml
git commit -m "設定変更"
git push origin master
```

---

## 実行スケジュール

`.github/workflows/morning-report.yml` の cron を変更する：

```yaml
- cron: '0 23 * * 0-4'   # UTC 23:00 = JST 8:00 月〜金（デフォルト）
- cron: '30 22 * * 0-4'  # JST 7:30 にしたい場合
```

GitHub Actions の cron は UTC 基準。JST は UTC+9。数分〜15分の遅延あり。

手動実行は GitHub の Actions タブ → `posukun-morning-report` → **Run workflow** でいつでも可能。

---

## よくあるエラーと対処

| エラー | 原因 | 対処 |
|---|---|---|
| `missing_scope` | Slack スコープが足りない | OAuth & Permissions でスコープ追加 → Reinstall |
| `ratelimited`（Slack） | API 呼び出し過多 | 最大4回リトライします。それでも失敗する場合はしばらく待ってから再実行 |
| `429`（Chatwork） | ルーム数が多い場合に発生 | しばらく待ってから再実行 |
| ワークフローが `gh workflow list` に出ない | YAML の改行コードが CRLF になっている | `git config --global core.autocrlf false` を実行後、ファイルを LF で保存し直して push |
| `exclude_reactions` が効かない | `reactions:read` スコープ未付与 | Step 2 の User Token Scopes に `reactions:read` を追加して Reinstall |
| Bot の DM が未返信に出る | Slack の BOT ユーザー | 自動除外済み（`is_bot` フラグで判定） |

---

## 既知の制限事項と懸念点

以下は現時点で**未解決・修正保留中**の問題です。動作に影響するケースがあるため把握しておいてください。

### ✅ Slack / Chatwork：月曜は72時間ウィンドウ（対応済み）

月曜日のみ収集対象を「過去72時間」に拡大しており、金〜日曜の未返信を拾います。火〜土は通常の24時間ウィンドウです。

- **長期休暇明け**：連休が月〜金にまたがる場合は見落としが発生します。休暇前に除外スタンプを整理しておくことを推奨します。

### ⚠️ Slack：@here / @channel メンション未対応（未解決）

チャンネル全体向けの `@here` / `@channel` は自分への直接メンションとして検出されないため収集対象外です。重要な `@here` は Slack のリマインダー機能等で個別に管理してください。

### ⚠️ Chatwork：[To:ID] 以外のメンション形式未対応（未解決）

グループルームで `[To:account_id]` 形式以外のメンション（`[rp aid=xxx]` 返信リプライなど）は検出されません。相手に `[To:ID]` 形式でのメンションを依頼するか、Chatwork 側でリマインダーを設定してください。

### ⚠️ Gmail（将来対応時）：メーリングリスト宛てメールの漏れ（未調査）

`ml-xxx@example.co.jp` のようなメーリングリスト宛てのメールは、自分宛て直接メールとして受信トレイに届かない場合があります。Gmail 対応時には単純なクエリ検索では判別できないため、**Claude がメール本文を読んで「要返信かどうか」を判断してラベルを付与する方式**が必要になります（前回実装方針）。

---

## ローカルでのデバッグ実行

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

環境変数をセットして実行：

```powershell
$env:CHATWORK_API_TOKEN  = "<Chatwork APIトークン>"
$env:CHATWORK_ACCOUNT_ID = "<ChatworkアカウントID>"
$env:SLACK_BOT_TOKEN     = "<xoxb-...>"
$env:SLACK_USER_TOKEN    = "<xoxp-...>"
$env:SLACK_USER_ID       = "<Uxxxxxxxxxx>"
python src/main.py
```

---

## コード構成

```
unreplied-report/
├── .github/workflows/
│   └── morning-report.yml   # GitHub Actions（cron設定）
├── docs/
│   └── posukun-guide.md     # エンドユーザー向けガイド
├── src/
│   ├── main.py              # エントリーポイント
│   ├── chatwork.py          # Chatwork 未返信収集
│   ├── slack_collector.py   # Slack DM・メンション収集
│   └── slack_notifier.py    # ポスくんのメッセージ投稿
├── config.yml               # カスタマイズ設定（ここだけ触ればOK）
└── requirements.txt
```

### 収集ロジック

| ソース | 対象 |
|---|---|
| Chatwork direct（1:1） | 相手が最後に送っているもの |
| Chatwork group | `[To:自分のID]` 宛で未返信のもの |
| Slack DM（人間のみ） | 相手が最後に送っているもの。BOT は自動除外 |
| Slack チャンネル | `<@自分のID>` メンションで未返信・自分の送信は除外 |

---

## 今後の拡張予定

- [x] Gmail 未返信対応（⚑要返信ラベル検索方式で対応済み）
- [ ] 週次サマリーモード
- [ ] 対象チャンネルを config.yml で絞り込む設定
- [ ] Slack グループ DM（mpim）収集対応
- [ ] @here / @channel メンション対応
