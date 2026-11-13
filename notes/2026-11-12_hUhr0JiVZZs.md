---
video_id: "hUhr0JiVZZs"
title: "How to run your first Codex Security scan"
channel: "OpenAI"
company: "openai"
url: "https://www.youtube.com/watch?v=hUhr0JiVZZs"
published: "2026-11-12 06:10 JST"
duration_min: 7
views: 26009
source: "channel"
query: ""
model: "gemini-3.5-flash-lite"
processed_at: "2026-11-13 10:44 JST"
---

# How to run your first Codex Security scan

## 3行要約
- OpenAIのサイバーデプロイメントエンジニアが、Codex Securityプラグインのインストールとセキュリティスキャンの実行方法を解説。
- Codex Securityを用いた脆弱性の検出、修正パッチの生成、GitHubへのPull Request作成までの手順を紹介。
- Codex Security CLIをnpmでインストールし、CI/CD環境などでのスキャン自動化・スケール手法を実演。

## 主な内容
- 00:00 イントロダクション（Dan Shanahan氏によるCodex Securityの概要説明）
- 00:33 Codexの設定画面でDaybreak Blueへのアクセスを確認
- 00:56 プラグインメニューからCodex Securityプラグインを検索してインストール
- 01:31 Codex Securityのプラグインを開き、新しいスキャンを開始
- 02:30 スキャンが開始され、脅威モデルの構築やコードレビューが実行される様子
- 03:00 検出された脆弱性の詳細、攻撃パス、修正パッチの生成とレビュー
- 04:24 GitHubのPull Request上で修正内容を確認しマージの準備を進める手順
- 05:15 Codex Security CLIを `npm install -g @openai/codex-security` でインストール
- 05:28 CLIを使ってローカルリポジトリで `codex-security scan .` を実行しスキャンを自動化・スケールさせる方法

## 発表・新機能・数字
- 製品・機能: Daybreak Blue、Codex Securityプラグイン、Codex Security CLI

## 関係する会社・製品
- OpenAI: Codex, Codex Security, Daybreak Blue

## 誰に役立つか
ソフトウェア開発者、セキュリティエンジニア、DevSecOps担当者

## おすすめ度
★★★★☆
Codex Securityを使ったセキュリティスキャンから修正パッチ作成、CLIによる自動化までの流れが実演を通じて非常に分かりやすく学べるため。

## 見どころ
- 03:00 検出された脆弱性の詳細や攻撃パス、修正パッチの生成プロセス
- 05:15 CLIを使ったスキャンの実行とCI/CDパイプラインへの組み込み方法の解説
