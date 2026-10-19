# AIウィークリー（動画収集係）

AI関連のYouTube動画を毎日集め、Google Gemini に「見て」もらって日本語の要点メモを残す仕組みです。
毎週土曜の朝、Claude がこのメモを読んで「AIウィークリー」にまとめ、Notion に追加します。

```
毎日 05:17（日本時間）  GitHub Actions が自動実行
  ├ 指定チャンネルの新着動画を確認（config.yml の channels）
  ├ キーワード検索で話題の動画を発掘（config.yml の discovery）
  └ Gemini が動画を見て要点メモを作成 → notes/ に保存

毎週土曜 09:51  Claude の定期実行
  ├ notes/ と logs/ を読む
  ├ 各社の公式発表で裏取り
  └ Notion のデータベース「AIウィークリー」に1ページ追加（書き方は digest/FORMAT.md）
```

PCは一切使いません。PCがスリープしていても動きます。

---

## 最初のセットアップ（1回だけ）

### 1. Gemini の APIキーを作る
1. [Google AI Studio](https://aistudio.google.com/) にGoogleアカウントでログイン
2. 「Get API key」→「APIキーを作成」
3. 表示されたキーをコピー（他人に見せない）

### 2. YouTube の APIキーを作る
1. [Google Cloud コンソール](https://console.cloud.google.com/) を開く
2. 画面上部のプロジェクト選択で、AI Studio が作ったプロジェクトを選ぶ（新規作成でもOK）
3. 「APIとサービス」→「ライブラリ」→「YouTube Data API v3」を検索 →「有効にする」
4. 「APIとサービス」→「認証情報」→「認証情報を作成」→「APIキー」
5. 作ったキーの「キーを制限」→「APIの制限」で「YouTube Data API v3」だけにチェック → 保存
6. キーをコピー

### 3. GitHub にキーを登録する
1. このリポジトリの「Settings」→「Secrets and variables」→「Actions」
2. 「New repository secret」で次の2つを登録
   - Name: `GEMINI_API_KEY` / Secret: 手順1のキー
   - Name: `YOUTUBE_API_KEY` / Secret: 手順2のキー

### 4. 初回テスト
1. 「Actions」タブ →「動画を集めて要点メモを作る」→「Run workflow」
2. 数分〜十数分で完了。`notes/` にメモ、`logs/` に実行ログが増えていれば成功

---

## ふだんの使い方

### チャンネルを追加・削除したい
`config.yml` の `channels` を編集して保存（コミット）するだけです。保存するとすぐ1回収集が動きます。
ハンドル（@から始まる名前）だけ書けば、チャンネルIDは自動で調べます。

### 発掘のキーワードを変えたい
`config.yml` の `discovery.queries` を編集します。

### うまく動かなかったとき
- GitHub から失敗通知メールが届きます（キーの設定ミス・全滅したときなど）
- `logs/` の当日のファイルに、何が起きたか日本語で書かれています
- Gemini の無料枠に達した日は途中で止まり、翌日に自動で続きから再開します
- 3回続けて処理できなかった動画（非公開・地域制限など）は諦めて、ログに記録します

---

## フォルダの中身

| 場所 | 中身 |
|---|---|
| `config.yml` | 設定（チャンネル・キーワード・上限など） |
| `notes/` | 動画ごとの要点メモ（`日付_動画ID.md`）と一覧 `index.json` |
| `logs/` | 日ごとの実行ログ |
| `data/state.json` | 処理済みの記録（触らなくてOK） |
| `scripts/collect.py` | 収集プログラム本体 |

## キーの置き場所（2026-10-19 設定）
- Google Cloud プロジェクト：**blog-analytics**（blog-analytics-493402）。支払い設定なし＝無料枠で動く
  - `ai-weekly-gemini`：Gemini API 専用キー（サービスアカウント ai-weekly-gemini にバインド、ロールなし）
  - `ai-weekly-youtube`：YouTube Data API v3 専用キー
- GitHub の Secrets：`GEMINI_API_KEY` / `YOUTUBE_API_KEY`
- 注意：このプロジェクトに支払い設定を追加すると、Gemini は有料扱いになる

## 注意
- Gemini の YouTube 動画読み込み機能はプレビュー版です。料金や上限が変わる可能性があります（無料枠は1日8時間まで、公開動画のみ）。
- 無料枠では、送った内容が Google のサービス改善に使われる場合があります。扱うのは公開動画だけなので、個人情報は含まれません。
