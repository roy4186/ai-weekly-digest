---
video_id: "y5TEATUDDfc"
title: "Anthropic can't stop winning"
channel: "Theo - t3․gg"
company: ""
url: "https://www.youtube.com/watch?v=y5TEATUDDfc"
published: "2026-11-02 18:10 JST"
duration_min: 17
views: 210139
source: "discovery"
query: "Anthropic Claude"
model: "gemini-3.5-flash-lite"
processed_at: "2026-11-07 09:13 JST"
---

# Anthropic can't stop winning

```markdown
## 3行要約
- AnthropicがClaudeのサブスクリプションプランに「Ultra」ティアを新導入し、プラン名や制限を改定。
- スペースXとのコンピュート契約を背景に、Claude Codeなどの5時間制限を倍増し、ピークアワー制限も撤廃。
- 一方で、Agent SDK経由での利用時における制限の消費や「検証済み」要件を巡る仕様に課題や懸念も残る。

## 主な内容
- 00:16 Anthropicが新しい「Ultra」ティアを含むサブスクリプションプランの変更を発表した。
- 01:23 スポンサー企業としてAIコードレビュープラットフォーム「Greptile」を紹介。
- 02:31 Claudeのプラン改定における「5x」「20x」の名称は全体的な制限ではなく、5時間制限に対する倍率であったことを説明。
- 04:11 Claudeのサブスクリプションプラン構成（Free、Pro、Max、Ultra）とそれぞれの価格および制限の概要を解説。
- 05:39 T3 Codeの利用データをもとに、一日の時間帯によるプロンプト送信数の変動と計算資源の枯渇リスクについて解説。
- 08:24 2026年5月6日に発表されたスペースXとの大規模なコンピュート契約により、AnthropicがGPUの可用性を大幅に向上させたことを振り返る。
- 08:54 コンピュート能力の向上に伴い、Claude Codeの5時間レートリミットの倍増、ピークアワー制限の撤廃、APIレートリミットの引き上げが行われた。
- 09:40 5時間制限の撤廃が「検証済みUltraアカウント」を対象としていることについて、検証プロセスの不透明さや蒸留（ディスティレーション）対策との関連を議論。
- 11:58 Agent SDKやヘッドレスモード（`claude -p`）を使用すると、インタラクティブCLIよりも約1.8倍速く5時間制限を消費してしまうGitHub上のIssueを紹介。
- 13:48 Claude Codeのエントリポイント識別子（`CLAUDE_CODE_ENTRYPOINT`）の設定を変更することで、レートリミットの問題を回避・解決できるワークアラウンドを提示。

## 発表・新機能・数字
- 2026-11-02公開
- Claudeのサブスクリプションプラン：「Free」「Pro（20ドル/月）」「Max（100ドル/月）」「Ultra（200ドル/月）」
- Claude Codeの5時間レートリミットが倍増、ピークアワー制限の撤廃、Claude OpusモデルのAPIレートリミット引き上げ（最大入力トークン/分：30,000 → 500,000、最大出力トークン/分：6,000 → 80,000）
- スペースXとのコンピュート契約（2026年5月6日発表）
- Agent SDK・ヘッドレスモードはインタラクティブCLIに比べ約1.8倍の5時間制限を消費

## 関係する会社・製品
- Anthropic: Claude, Claude Code, Agent SDK
- Greptile: Greptile, TREX

## 誰に役立つか
Claudeの有料プランを利用している開発者、特にAPIやAgent SDK、Claude Codeを頻繁に利用するパワーユーザー。

## おすすめ度
★★★☆☆
Claudeのプラン変更やレートリミットに関する実用的な情報やトラブルシューティングが語られているが、話題が特定の開発者向けツールや仕様に特化しているため。

## 見どころ
- 08:24 スペースXとの計算資源（コンピュート）に関する契約が、実際の機能制限緩和にどう結びついたかの解説。
- 11:58 Agent SDKやCLIの利用時に発生するレートリミットの消費増加に関するGitHubのIssue検証と議論。
- 13:48 レートリミット問題を回避するための`CLAUDE_CODE_ENTRYPOINT`設定変更のワークアラウンド解説。
```
