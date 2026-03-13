# `wt add --issue` コマンドによる GitHub Issue からの worktree 自動作成

## Summary
`wt add --issue <issue-number>` (または `wt issue add <number>`) を実行することで、GitHub CLI (`gh`) を通じて Issue のタイトルを取得し、自動的に適切なブランチ・ワークツリー名（例: `issue-123-fix-login`）を生成してセットアップする機能を追加する提案。

## Problem
新しいタスク（Issue）に着手する際、開発者は以下のような手順を踏んでいます。
1. ブラウザや `gh issue view` で対象 Issue の番号とタイトルを確認する
2. チームの命名規則に従ってブランチ名を考える（例: `fix/123-login-bug`, `issue-123` など）
3. `wt add fix/123-login-bug` を手打ちで実行する

この手順には以下の摩擦があります。
- ブランチ名に Issue のタイトルを含めたい場合、手動でケバブケース（kebab-case）に変換して入力する手間がかかる。
- 番号だけのブランチ名（`123`）にしてしまうと、後から `wt list` で見たときに何の作業用ワークツリーか一目で分かりにくい。
- チーム内でブランチ名のフォーマットがブレやすい。

## Proposal
`wt add` コマンドに `--issue` オプションを追加し、GitHub Issue からのワークツリー作成を自動化します。

```bash
# Issue #123 からワークツリーを作成
wt add --issue 123
```

**動作のフロー**:
1. `gh issue view 123 --json title` などを内部で呼び出し、Issue 情報を取得。
2. タイトル文字列をサニタイズし、ケバブケースに変換（例: "Fix login bug" -> `fix-login-bug`）。
3. 指定されたフォーマット（デフォルトは `{id}-{title}` などを想定）でブランチ名 `123-fix-login-bug` を生成。
4. その名前で `wt add 123-fix-login-bug` の処理を実行。

**設定によるカスタマイズ**:
`.wt/config.toml` にフォーマット設定を追加できるようにします。
```toml
[github]
issue_branch_format = "issue/{id}-{title}"
```

## Inspiration
- **`gh pr checkout` / `gh issue develop`**: GitHub CLI の `gh issue develop` コマンドは Issue からブランチを作成しますが、これを worktree 管理に統合した形です。
- **GitLab / Jira integration**: 多くの企業向けツールが「Issueからブランチを作成」ボタンを提供していますが、CLI 上でシームレスに `wt` の管理下に置けることが強みになります。

## Expected Daily Benefit
- **タイピングと手間の削減**: 長いブランチ名や Issue タイトルの英訳・ケバブケース変換を手作業で行う必要がなくなり、即座にコーディングを開始できます。
- **視認性の向上**: `wt list` や `wt select` で表示されるワークツリー名に Issue タイトルが自動で含まれるため、何の作業をしているか一目で把握でき、コンテキストスイッチが容易になります。
- **命名規則の統一**: プロジェクト内でブランチ名のフォーマット（`issue/{id}` など）を統一しやすくなります。

## Scope and Non-Goals
- **スコープ**: `gh` CLI が利用可能な環境で、Issue 情報の取得とブランチ名の自動生成・worktree 作成を行うこと。
- **非目標**: Issue のステータス変更（In Progress への移動など）や、担当者のアサイン。これらは `gh` 側の責務であり、`easy-worktree` には含めません。

## Risks or Open Questions
- **日本語タイトルの扱い**: GitHub Issue のタイトルが日本語の場合、そのままブランチ名にすると扱いづらいため、サニタイズ処理で英数字のみを残すか、ローマ字変換を入れるか、あるいは日本語タイトル時は ID のみをフォールバックとして使うかの仕様決定が必要です。
  - 案: デフォルトでは日本語文字を除外し、残った英数字を使用。空になる場合は `issue-123` のようにフォールバックする。
- **`gh` への依存**: 既に PR 機能で `gh` に依存しているため大きな問題ではありませんが、エラーハンドリング（未ログイン、Issueが存在しない等）を適切に行う必要があります。

## Suggested Rollout
1. まずは `wt add --issue <number>` の基本的な実装を追加し、デフォルトのフォーマット (`{id}-{sanitized-title}`) で作成できるようにする。
2. 次に、日本語タイトルのサニタイズ処理の洗練（フォールバック処理の実装）を行う。
3. 最後に `.wt/config.toml` によるフォーマットのカスタマイズ機能を追加する。
