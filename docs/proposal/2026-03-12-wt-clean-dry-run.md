# `wt clean` の削除対象を事前に確認する `--dry-run` オプション

## Summary
`wt clean` コマンドに `--dry-run` (または `-n`, `--dry`) オプションを追加し、実際にワークツリーを削除することなく、「どのワークツリーが削除対象として判定されたか」の一覧を出力する機能を提供する。

## Problem
`wt clean --merged` や `wt clean --all`、`wt clean --days 30` などの一括クリーンアップコマンドは非常に便利だが、ユーザーにとっては「自分がまだ作業中だと思っていたワークツリーが誤って消されてしまわないか」という不安（破壊的変更への恐怖）が伴う。
現状でも確認プロンプト（`y/N`）は出るが、削除対象が多数ある場合や、自動化スクリプト・CI環境で安全に動作確認したい場合において、対象を「事前に一覧として安全に確認する」専用のモードが存在しない。このため、クリーンアップコマンドの実行を躊躇してしまう、という心理的な摩擦がある。

## Proposal
`wt clean` の各フィルタリングオプション（`--merged`, `--all`, `--days`, `--closed` など）と併用できる `--dry-run` オプションを追加する。

**使用例:**
```bash
$ wt clean --merged --dry-run
[Dry Run] The following worktrees would be deleted:
  - feature-A (merged in PR #12)
  - fix-bug-B (merged in main)
[Dry Run] 2 worktrees would be cleaned. No changes were made.
```

**挙動:**
- 削除対象となるワークツリーの条件判定ロジックは通常実行と全く同じものを使用する。
- 実際に `git worktree remove` やディレクトリの削除を実行する直前で処理をバイパスし、対象のリストだけを標準出力にプリントして正常終了する。
- `--dry-run` が指定された場合は、インタラクティブな確認プロンプト（`y/N`）はスキップする。

## Inspiration
- `git clean --dry-run` (または `-n`)
- `rm -rf` に対する事前の `ls` 確認
- Unix 系ツールの一般的な `--dry-run` の慣習

## Expected Daily Benefit
- 「誤って必要なブランチを消してしまうかもしれない」という心理的ハードルが下がり、定期的な `wt clean` の実行が習慣化しやすくなる。
- 不要なワークツリーが溜まりにくくなり、ディスク容量の節約や `wt list` / `wt select` の一覧性の向上に直結する。
- シェルスクリプトや alias（例: `wt clean --merged -y` を組み込んだ cron 処理）を組む際の事前のテストが容易になる。

## Scope and Non-Goals
- **Scope**: `wt clean` における対象ワークツリーの抽出と、削除処理のバイパス、および結果のコンソール表示。
- **Non-Goals**: ゴミ箱機能（一度削除したものを復元できる機能）の実装。これは複雑すぎるため、まずは「消す前に確認できる」ことで安全性を担保する。

## Risks or Open Questions
- 出力フォーマットについて: スクリプトからパースしやすいように、`--dry-run --quiet` の場合はパスや名前だけを1行ずつ出力するような考慮が必要か。まずは人間が読んで安心できるフォーマットを優先でよいか。
- `gh` API のレート制限: `--merged` 等の判定に API を叩く場合、`--dry-run` を頻繁に実行すると制限に引っかかる可能性がある点に注意（これは既存の `wt clean` にも共通する課題）。

## Suggested Rollout
1. `clean` コマンドのパーサーに `--dry-run` (ショートオプション `-n`) を追加。
2. コアの削除処理において、フラグが True の場合は `shutil.rmtree` や `git worktree remove` の呼び出しをスキップするよう分岐を追加。
3. ロガーまたは `print` を用いて、Dry-run 時の専用出力メッセージを実装。
