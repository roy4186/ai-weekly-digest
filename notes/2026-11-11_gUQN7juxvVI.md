---
video_id: "gUQN7juxvVI"
title: "Codex Security: From Vulnerability to Verified Fix | DevDay 2026"
channel: "OpenAI"
company: "openai"
url: "https://www.youtube.com/watch?v=gUQN7juxvVI"
published: "2026-11-11 10:24 JST"
duration_min: 21
views: 359
source: "channel"
query: ""
model: "gemini-3.6-flash"
processed_at: "2026-11-12 11:06 JST"
---

# Codex Security: From Vulnerability to Verified Fix | DevDay 2026

## 3行要約
- OpenAIのCyber Productsチーム（Ian WebsterとKyle Brown）が、AIを活用してソフトウェアの脆弱性発見から修正・検証までを行う「Codex Security」を発表。
- OpenAI内部の「The Defense Factory」での運用において、初日に53件の重要課題を修正し、重複率36%、ロールバック率1%未満という高精度なセキュリティ修正を達成。
- Open SourceのCLI/Plugin/SDKに加え、自動化されたワークフローを提供する「Codex Security Cloud」を新たにローンチ。

## 主な内容
- 00:23 - Ian WebsterとKyle Brownが登壇し、Codex Securityの概要とDevDayでの発表内容を紹介。
- 01:13 - サイバーセキュリティの現状（Defender's window）と、最先端フロンティアモデルによる防御側の優位性について解説。
- 02:13 - OpenAI社内で構築・運用されている「The Defense Factory」の成果数字を発表。
- 04:29 - AIセキュリティエージェント運用の5ステップ（Contextualize, Scan, Enrich, Patch, Integrate）を開設。
- 05:25 - エージェントに背景知識を与える知識ベース（SECURITY.mdやWAF設定、アーキテクチャ情報等）の重要性を説明。
- 08:30 - CLIを使用した「Codex Security」によるコードベースのDeep Scanデモを実施。
- 09:07 - 発見された重複課題の集約（Deduplication）、優先順位付け（Prioritization）、担当者割り振り（Assignment）のプロセスを紹介。
- 12:41 - 修正パッチの自動生成（Patch）と、脆弱性が解消されたかを再攻撃でテストする自動検証（Verify）の手順。
- 16:17 - 評価ベンチマーク「Patch benchmark」でのモデル比較（GPT-5.6 Sol vs GPT-6 Astra）と人間の精度との対比。
- 19:15 - ChatGPTのプラグインマーケットプレイスで提供される「Codex Security Cloud」のUIおよび自動セキュリティスキャンデモ。
- 20:32 - インストール方法（`npm i -g @openai/codex-security`）およびCodex Security Cloudの公開予定について案内。

## 発表・新機能・数字
- **The Defense Factory（OpenAI社内実績）**:初日に53件のクリティカルな脆弱性を修正、ロールバック率 1%未満（実際は0.81%）、重複識別率 36%。
- **Codex Security Cloud**: ターンキー方式で継続的セキュリティループ（Continuous security loop）を実行する新規クラウドサービス。Daybreakクラスモデル（Daybreak Blue等）をバックエンドに使用。
- **モデル比較ベンチマーク（Patch benchmark）**: GPT-6 Astra（medium reasoning）はGPT-5.6 Sol（xhigh）と比較して、半分のコストで高いスコアを獲得。人間の標準ベンチマークは約50%。
- **配布形態**: オープンソース（Apache 2.0ライセンス）のCLI/Plugin/SDKはnpm（`npm i -g @openai/codex-security`）にて配布。

## 関係する会社・製品
- **OpenAI**: Codex Security, Codex Security Cloud, Daybreak, GPT-5.6 Sol, GPT-6 Astra

## 誰に役立つか
- ソフトウェア開発者・エンジニア
- セキュリティエンジニア・DevSecOps担当者
- 大規模コードベースの脆弱性管理・自動修正ラインを構築したい開発組織

## おすすめ度
★★★★★
AIを活用した最新の脆弱性検出から修正パッチ生成・テスト自動化の実践事例と具体ツールが簡潔に解説されています。

## 見どころ
- 08:30 - CLIコマンドを使用したDeep ScanとリアルタイムでのAIエージェントによる脆弱性調査・検証のデモ。
- 16:17 - 最新モデル（GPT-6 Astra）が自動パッチ生成において人間や旧モデルを上回るパフォーマンスを示すベンチマーク結果。
- 19:15 - ChatGPTからリポジトリを連携して自動でCI/CD的セキュリティチェックとPR作成を行うCodex Security Cloudの操作画面。
