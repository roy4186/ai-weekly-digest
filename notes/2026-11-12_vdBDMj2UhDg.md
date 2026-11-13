---
video_id: "vdBDMj2UhDg"
title: "How to enable PR security reviews with Codex Security"
channel: "OpenAI"
company: "openai"
url: "https://www.youtube.com/watch?v=vdBDMj2UhDg"
published: "2026-11-12 06:10 JST"
duration_min: 7
views: 2633
source: "channel"
query: ""
model: "gemini-3.5-flash-lite"
processed_at: "2026-11-13 10:45 JST"
---

# How to enable PR security reviews with Codex Security

## 3行要約
- Codex Securityを用いたGitHubでのPR（プルリクエスト）セキュリティレビューの設定方法を解説。
- 手動レビューだけでなく、自動レビューの設定や脆弱性の修正手順を実演。
- リポジトリや組織全体でセキュリティチェックを自動化し、本番環境への脆弱性混入を防止する。

## 主な内容
- 00:01 登壇者の自己紹介（Dan Shanahan、OpenAIのCyber Deployment Engineer）。
- 00:33 GitHubのレポジトリ設定画面と「ChatGPT Codex Connector」のインストール確認。
- 01:24 PR内で「@codex security review」とコメントし、手動でセキュリティレビューをリクエスト。
- 02:04 CodexにPRのリンクを渡し、発見された脆弱性の修正コードを作成・コミットさせる。
- 02:41 再度セキュリティレビューをリクエストし、問題が解消されたことを確認。
- 03:22 Codexアプリの「Code Review」設定から、自動レビューの有効化やトリガーを設定。
- 04:34 リポジトリ単位での自動セキュリティレビュー設定と、脅威モデルファイル（`docs/threat-model.md`）の指定。
- 05:25 新しいPRを作成し、自動でセキュリティレビューが実行される様子を実演。

## 発表・新機能・数字
- 特になし

## 関係する会社・製品
- OpenAI / ChatGPT Codex Connector, Codex, Codex Security

## 誰に役立つか
GitHubを使用しているソフトウェア開発者、セキュリティエンジニア、DevOpsエンジニア。

## おすすめ度
★★★★☆（Codexを使ったGitHub連携によるセキュリティレビューの具体的な手順がわかりやすく解説されているため）

## 見どころ
- 01:24 PRのコメント欄でCodexに手動レビューを依頼する手順
- 02:04 Codexにセキュリティ上の脆弱性を修正させる手順
- 03:22 設定画面から自動レビューやトリガー条件を構成する手順
