# wt protect コマンドの追加

## Summary
重要な worktree を誤って削除（`wt rm` や `wt clean`）しないように保護（ロック）する `wt protect` / `wt unprotect` コマンドを追加する提案。

## Problem
`wt clean` を対話的（あるいは自動）に実行したり、誤って `wt rm <name>` を実行した際、長期間保持しておきたい重要な worktree（例えば `main` や、環境構築に時間がかかった検証環境など）をうっかり消してしまうリスクがある。
Git 自体には `git worktree lock` というコマンドが存在し、移動メディア等にある worktree の自動 prune を防ぐ機能があるが、`easy-worktree` の `wt rm` や `wt clean` のロジックでは「ユーザーが意図して消したくない worktree」を明示的に保護・スキップする仕組みが整備されていない。

## Proposal
- `wt protect <worktree-name>`: 指定した worktree に保護フラグを付与する。
- `wt unprotect <worktree-name>`: 保護フラグを解除する。
- `wt rm` や `wt clean` の実行時、対象が protected な worktree である場合は「Protected worktree cannot be removed. Run 'wt unprotect' first.」などのメッセージを出力し、削除をブロックする。
- `wt list` の出力において、保護された worktree にはアイコン（例: 🔒）や専用のマークを表示して視認性を高める。

## Inspiration
- `git worktree lock` / `git worktree unlock`
- クラウドインフラにおけるリソース保護機能（例: AWS EC2 の Termination Protection や Terraform の `prevent_destroy`）
- GitHub の Branch protection rules

## Expected Daily Benefit
- 定常的に保持しておくべきベースブランチ（`main`, `develop`）や、長期検証用で消されると困る環境を `wt clean` による一括削除対象から安全に除外できる。
- ターミナル上でうっかり `wt rm` を叩いた時のヒューマンエラーによる時間損失（環境再構築、ビルドキャッシュのやり直しなど）を防げる。
- 心理的安全性（「これを叩いても大事な環境は消えない」という安心感）の向上。

## Scope and Non-Goals
- **Scope**: `wt rm`, `wt clean` コマンドにおける保護チェックの追加。保護状態のトグルコマンド（`protect` / `unprotect`）、および `wt list` での表示。
- **Non-Goals**: Git の commit や push レベルでの操作ブロック（それは GitHub や Git hooks の管轄）。あくまで「ローカルの worktree ディレクトリ自体の削除」の保護に留める。

## Risks or Open Questions
- **保護フラグの記録方法**: `git worktree lock` をラップしてそのまま利用すべきか？ それとも `easy-worktree` 独自でマーカー（例: `config.toml` の `protected_worktrees` リストや、`.git/worktrees/<name>/easy-worktree-protected` のようなファイル）を管理すべきか。`git worktree lock` は「パスがマウントされていない時の自動 prune を防ぐ」目的が主であるため、ユーザーレベルの削除保護とは意味合いを分けて独自管理する方が柔軟かもしれない。
- 強制削除オプション（`wt rm -f`）で保護を無視（または override）できるようにするかどうか。

## Suggested Rollout
1. 保護状態を記録・判定する内部 API の実装。
2. `wt protect` / `wt unprotect` コマンドの実装。
3. `wt list` の表示への組み込み（保護マークの追加）。
4. `wt rm` / `wt clean` 実行時のブロックロジックの追加。
