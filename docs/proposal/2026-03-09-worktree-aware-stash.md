# `wt stash` コマンドによる Worktree 単位の Stash 管理

## Summary
標準の `git stash` をラップし、Stash メッセージに自動で対象の Worktree（ブランチ名）を記録することで、「現在の Worktree に属する Stash だけを一覧・操作」できるようにする `wt stash` コマンドを追加する。

## Problem
Git の worktree 機能の仕様上、`git stash` で保存された Stash はリポジトリ全体（すべての worktree）でグローバルに共有される。
そのため、複数の worktree を行ったり来たりしながら頻繁に `git stash` と `git stash pop` を繰り返していると、`git stash list` に無数の変更が混ざって表示され、「この Stash はどの作業ブランチのものだったか？」が全く分からなくなる。
結果として、別の worktree の変更を誤って現在の worktree に `pop` してしまい、コンフリクトや意図せぬコードの混入を招く事故が起こりやすい。

## Proposal
`wt stash` を新しいサブコマンドとして提供し、内部で Worktree コンテキストを付与した上で標準の `git stash` を呼び出す。

主な提供コマンド（想定）:
- `wt stash [push] [message]`:
  内部で `git stash push -m "[<branch-name>] <message>"` を実行する。
- `wt stash list`:
  内部で `git stash list` を実行し、メッセージのプレフィックス `[<branch-name>]` が現在の Worktree に一致するものだけをフィルタリングして美しく表示する。（または全て表示しつつ、他ブランチのものは暗い色にするなど）
- `wt stash pop`:
  `git stash list` から「現在の Worktree に関連づけられた最新の Stash」を自動判定し、そのインデックス（例: `stash@{2}`）を安全に `pop` する。

## Inspiration
- **Git Town / Magit**: ブランチのコンテキストを保持してよしなに操作をラップするアプローチ。
- **direnv**: ディレクトリ（≒ Worktree）に入った時に、その環境にだけ閉じた状態を提供する思想。

## Expected Daily Benefit
複数の Worktree（タスク）を並行して進めている際に、作業途中の状態を一時退避するハードルが劇的に下がる。
「別のブランチの変更を誤って適用してしまう」という Worktree 運用における代表的な事故（摩擦）を未然に防ぎ、安心して `stash` と `pop` を多用できるようになる。

## Scope and Non-Goals
- 独自の Stash ストレージ機構を新設することはしない。あくまで標準の `git stash` 機構をラップし、メッセージのプレフィックスとしてタグ付けするだけの軽量な実装に留める。
- コミットとして WIP を残すアプローチ（例: `git commit -m "WIP"`）を強制することはしない。WIP コミット派と Stash 派の両方がいるため、Stash 派の DX 向上をターゲットとする。

## Risks or Open Questions
- すでにユーザーが手動で独自の `[prefix]` を付けて stash を行っていた場合、`wt stash list` のフィルタリングロジックが誤爆する可能性がある。
- 標準の `git stash` コマンドで作成した「プレフィックス無し」の Stash を `wt stash list` でどう扱うか？（「Untagged」として常に表示するか、隠すか）

## Suggested Rollout
1. まず `wt stash push` と `wt stash list` のシンプルなラッパーとして実装する。
2. 次に `wt stash pop` の自動インデックス解決を追加し、安全性を確認する。
3. （オプション）インタラクティブな `wt stash pop -i` で、現在の worktree に属する stash を `fzf` で選んで復元できるようにする。