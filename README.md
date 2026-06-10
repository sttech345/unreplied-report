# 📮 ポスくん — 未返信レポート Bot

毎朝8時に Chatwork・Slack・Gmail の未返信メッセージを収集して、Slack DM で教えてくれる Bot。

```
📮 ポスくんより、朝のお届け物です

【Chatwork】2件
  • 営業チーム ← 田中さん（06/09 14:32）
  • 開発MTG ← 鈴木さん（06/09 09:15）

【Slack】3件
  • #marketing_all ← 山田さん（06/09 15:01）
  • DM: 佐藤さん ← 佐藤さん（06/09 11:20）
  • #general ← 高橋さん（06/09 08:45）

【Gmail（⚑要返信）】1件
  • お見積りのご確認 ← 高橋商事（06/09 10:00）

返事、お待ちしてる方が 6件 いるみたいですよ〜 🌤️
```

各行はリンクになっており、クリックでそのメッセージに直接ジャンプできます。

## 特徴

- **PC 不要** — GitHub Actions で動くので、PC を起動していなくても毎朝届く
- **除外スタンプ** — ✅ などを付けたメッセージは「対応済み」として翌朝から除外
- **月曜は72時間ウィンドウ** — 金〜日の未返信も月曜朝に拾う
- **通知は自分だけ** — 自分の Slack DM にのみ届く

## セットアップ

**Claude Code に任せるのが一番簡単です。** Claude Code を起動して以下を貼り付けてください：

```
@https://raw.githubusercontent.com/sttech345/unreplied-report/master/CLAUDE.md を読んでセットアップして
```

Slack App の作成・API トークン取得・GitHub Secrets 登録などをステップごとに案内してくれます。
手動でセットアップする場合も [CLAUDE.md](CLAUDE.md) に全手順が記載されています。

詳しい紹介は [docs/posukun-guide.pdf](docs/posukun-guide.pdf)（1ページ）をどうぞ。

## カスタマイズ

`config.yml` で除外スタンプを変更できます：

```yaml
slack:
  exclude_reactions:
    - white_check_mark  # ✅
    - eyes              # 👀
    - ok_hand           # 👌
```

実行時刻は `.github/workflows/morning-report.yml` の cron で変更できます（UTC 基準、JST は +9 時間）。

## 構成

| ソース | 収集対象 |
|---|---|
| Chatwork | 1:1 ルームの未返信 ＋ グループの `[To:自分]` メンション |
| Slack | DM（Bot 除外）＋ チャンネルの自分宛てメンション |
| Gmail | `⚑要返信` ラベル付きスレッド（ラベリングは claude.ai ルーティン等で実施） |

## 今後の予定

- [ ] 週次サマリーモード
- [ ] 対象チャンネルを config.yml で絞り込む設定
- [ ] Slack グループ DM（mpim）対応
- [ ] @here / @channel メンション対応
