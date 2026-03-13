# `wt select` 時に存在しない Worktree が指定された場合の自動作成プロンプト

## Summary
`wt select <name>` を実行した際、指定された名前の Worktree が存在しない場合に即座にエラーで終了するのではなく、「Worktree が見つかりません。新しく作成しますか？ [Y/n]」とプロンプトを出し、承認されたら `wt add <name> --select` を自動実行する機能を追加する。

## Problem
開発中、ふと新しい機能や修正に取り掛かろうとしたとき、無意識に `wt select new-feature` と打ってしまうことがある。現在、対象が存在しない場合はエラーとなり、ユーザーは改めて `wt add new-feature --select` を打ち直さなければならない。このわずかな「コマンドの打ち直し」は、思考のフローを分断する摩擦となっている。

## Proposal
`wt select <name>` の処理において、`<name>` に一致する Worktree が見つからない場合のフォールバック処理を実装する。

1. Worktree が存在しない場合、エラー終了する前にインタラクティブな確認プロンプトを表示する。
   `Worktree 'new-feature' does not exist. Do you want to create it? [Y/n]`
2. `y` または `Enter` (デフォルト) が入力された場合、内部で `wt add <name> --select` と同等の処理を実行し、そのまま新しい Worktree のサブシェルに移行する。
3. `n` が入力された場合、または非対話環境 (TTY ではない) の場合は、従来通りエラー終了する。

## Inspiration
- `git checkout <branch>` はブランチがないとエラーになるが、`oh-my-zsh` プラグイン等では存在しないディレクトリへの `cd` で自動作成を提案するような拡張がある。
- `zoxide` (z) などのモダンなナビゲーションツールは、ユーザーの意図を汲み取って最も近いアクションをフォールバックとして提供する。

## Expected Daily Benefit
- 「移動したい」というユーザーの意図から、「無ければ作る」という運用までをシームレスに繋ぐことで、コマンドの打ち直し（`wt select` -> エラー -> `wt add ... --select`）の手間がゼロになる。
- 認知負荷が下がり、常に `wt select <branch>` さえ叩けば、既存でも新規でも作業を開始できるようになる。

## Scope and Non-Goals
- **Scope**: `wt select <name>` にのみ適用。引数なしの `wt select` (fzf モード) には適用しない（fzf 上での新規作成は別の UI/UX 課題となるため）。
- **Non-Goals**: 既存の Git ブランチ名とのファジーマッチングや、typo の自動修正までは踏み込まない（あくまで完全一致で「無い」場合に新規作成を促すのみ）。

## Risks or Open Questions
- **Typo の扱い**: 単なる typo で `wt select featrue-A` と打った場合に作成プロンプトが出てしまう。間違えて `y` を押すと不要な Worktree ができてしまうが、`wt clean` や `wt rm` で簡単に消せるため、リスクは許容範囲と考えられる。
- **ベースブランチの指定**: 自動作成時に `base_branch` を指定できない。デフォルトのベースブランチ（通常は `main` や `master`）から分岐する仕様で割り切るか、プロンプトでベースブランチを尋ねるか。初期実装では「デフォルトのベースブランチからの分岐」で割り切るのがシンプルで良い。

## Suggested Rollout
1. `wt select` のロジック内で、Worktree 検索失敗時の分岐を追加。
2. `sys.stdin.isatty()` をチェックし、対話環境でのみ `input()` によるプロンプトを表示。
3. `y` の場合は `add_worktree()` に処理を委譲し、そのまま `--select` フローへ合流する。