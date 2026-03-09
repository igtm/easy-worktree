# `wt list --status` による全ワークツリーの変更状態（Dirty / Ahead / Behind）の一覧表示

## Summary
`wt list` コマンドに `--status`（または `-s`）オプションを追加し、存在するすべてのワークツリーについて、未コミットの変更があるか（Dirty）、ベースブランチ（リモート）と比べてコミットが進んでいるか・遅れているか（Ahead / Behind）を一覧で確認できるようにする提案。

## Problem
複数のタスクを並行して進めるため、`easy-worktree` で 5〜10 個のワークツリーを作成して切り替えていると、「どのタスクにまだコミットしていない書きかけのコードがあるか」「どのタスクがプッシュ待ちか」を忘れてしまうことがあります。
現状、これを確認するためには、`wt select` で一つずつワークツリーを移動して `git status` を実行するか、カスタムの bash スクリプトを書く必要があり、日々の認知負荷と操作の摩擦になっています。

## Proposal
`wt list` コマンドに、各ワークツリーの Git ステータスを並記するオプションを追加します。

**実行イメージ:**
```bash
$ wt list -s
  main        [clean]        (ahead 0, behind 0)
* feat-login  [dirty]        (ahead 2, behind 0)
  fix-typo    [clean]        (ahead 1, behind 0)  # プッシュ忘れ
  proposal    [untracked]    (ahead 0, behind 4)  # rebaseが必要
```

**機能要件:**
- 各ワークツリーのディレクトリ内で `git status --porcelain` および `git rev-list --count` 等の軽量なコマンドを非同期・並列に実行し、結果を集計して表示。
- 出力は既存の `wt list` の形式を拡張し、視認性の高い記号やカラーリング（Dirtyは赤、Cleanは緑など）を採用。
- `fzf` 等との連携も考慮し、スクリプトからパースしやすい `--json` や `--porcelain` フォーマットの出力もサポート。

## Inspiration
- `git branch -v` や `git branch -vv` の追跡ブランチとの差分表示。
- `lazygit` や GitKraken などGUIクライアントにおける、ローカルブランチ一覧での変更状態アイコン表示。
- `repo status` (Android AOSP ツール) や `mgitstatus` のような複数リポジトリ/ブランチの一括ステータス確認ツール。

## Expected Daily Benefit
「作業を中断して別のワークツリーに移った後、元の作業がどこまで進んでいたか」を一目で把握できるようになり、コミット漏れやプッシュ忘れを劇的に減らすことができます。特に金曜日の夕方や、連休明けに「どのタスクがどういう状態だったか」を思い出すための時間がほぼゼロになります。

## Scope and Non-Goals
- **スコープ内**: 既存の `wt list` に対する情報付加。ローカルの未コミット状態、およびリモートトラッキングブランチに対する Ahead/Behind の表示。
- **スコープ外**: この画面からのファイルごとの差分表示や、選択したワークツリーの直接的なコミット操作（それは `wt select` した後の `git` または `lazygit` の役割）。

## Risks or Open Questions
- **パフォーマンス**: ワークツリーの数が非常に多い（数十個）場合、各ディレクトリで Git コマンドを発行するため `wt list -s` の実行が遅くなる懸念。並列処理（Rustの `rayon` や Go の Goroutine 的なアプローチ）が必要か？
- **ネットワークアクセス**: `git fetch` は行わず、あくまでローカルにキャッシュされたリモート追跡ブランチ（`origin/xxx`）との比較にとどめるべきか。実行速度を優先し、フェッチはオプトインにするのが望ましい。

## Suggested Rollout
1. まずは同期的に各ワークツリーをループして `git status --porcelain` 相当の判定を行うシンプルな MVP を実装。
2. その後、表示のフォーマット（カラーリングやアラインメント）を調整。
3. （必要に応じて）並列実行化によるパフォーマンス改善。
