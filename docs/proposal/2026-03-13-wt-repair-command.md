# `wt repair` コマンドによるリンク修復の自動化

## Summary
リポジトリのディレクトリ移動などにより、Git worktree の内部パスが破損した際に、すべてのワークツリーを自動的にスキャンして修復する `wt repair` コマンドを追加する機能。

## Problem
Git worktree はメインリポジトリの `.git` ディレクトリへの絶対パスまたは相対パスを各ワークツリー内の `.git` ファイル（ファイルとして存在するもの）に保存している。そのため、ユーザーが親ディレクトリの名前を変更したり、リポジトリ全体を別の場所に移動（またはリポジトリと `.worktrees/` ディレクトリの相対関係を変更）したりすると、ワークツリー内部での git コマンドが `fatal: not a git repository` となり壊れてしまう。
これを直すには `git worktree repair` コマンドを使う必要があるが、壊れたワークツリーのパスをすべて引数として手動で渡す必要があり、数が多くなると非常に手間がかかる。

## Proposal
`wt repair` コマンドを導入する。
実行すると、`easy-worktree` は設定ファイル (`wt.toml` など) に基づいて `worktrees_dir` (デフォルト: `.worktrees/`) 内のすべてのワークツリーディレクトリを自動的にスキャンし、すべてのパスを収集したうえで、背後で自動的に `git worktree repair <path1> <path2> ...` を実行する。
これにより、ユーザーはパスの指定などを一切気にせず、1コマンドで全ワークツリーのリンク状態を修復できる。

## Inspiration
- `git worktree repair` の強力な修復機能
- 手間を減らすラッパーとしての Homebrew や npm の修復/クリーンアップコマンド（`brew doctor` などにおける自動修復アプローチ）

## Expected Daily Benefit
リポジトリの整理やディレクトリ構造の見直しといったリファクタリング作業を行った直後に発生する、「ワークツリーが壊れてしまった」というパニックや復旧の手間（摩擦）をゼロにする。発生頻度は低いが、いざ起きたときの DX 悪化を防ぐ「いざという時の安心感」を提供する。

## Scope and Non-Goals
- **Scope**: 管理下のワークツリーディレクトリを走査し、`git worktree repair` を実行してパスの整合性を復旧すること。また、メインリポジトリ内で実行した場合のリンク元情報の修復。
- **Non-Goals**: Git のオブジェクト破損（corrupted objects）の修復や、コミット履歴の復旧を行うことではない。あくまで worktree のパス連携（administrative path linkages）の修復に特化する。

## Risks or Open Questions
- すでにディレクトリごと削除されてしまった「幽霊ワークツリー」の扱い。これらは `git worktree prune` の対象となるため、`wt repair` の実行前後に自動で `prune` をかけるべきか、あるいは別コマンドとして `wt prune` のようなものを用意すべきか検討が必要。
- bare リポジトリ運用時におけるパス解決の挙動（bare リポジトリが移動された場合の特殊な repair 対応）。

## Suggested Rollout
1. `wt repair` コマンドを実装し、単純に現在の `worktrees_dir` 内のディレクトリを対象に `git worktree repair` を呼び出す MVP を提供。
2. その後、存在しないワークツリーのクリーンアップ (`prune`) を統合するか、オプション (`--prune`) として追加する。
