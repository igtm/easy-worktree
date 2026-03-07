# `wt rename` コマンドの追加

## Summary
現在のworktree（または指定したworktree）のディレクトリ名とGitブランチ名を同時にリネームし、Gitの内部リンクを自動修復する `wt rename` コマンドを追加する。

## Problem
開発を進める中で、要件の変化やタイポによりブランチ名を変更したくなることは頻繁に発生する（例: `feature/foo` から `fix/foo` に変えたいなど）。
Git標準の `git branch -m` を使えばブランチ名の変更自体は簡単に行えるが、worktree を使用している場合、**ディレクトリ名（例: `.worktrees/feature/foo`）は古い名前のまま残ってしまう**。
これにより、以下の問題が生じる。
- 「ターミナルのパス」と「実際のブランチ名」が一致せず、認知的負荷（気持ち悪さ）や混乱を招く。
- `.worktrees/` 以下のパスに依存するスクリプトやエディタの設定が意図せず壊れる・または古い名前を使い続けることになる。
- 手動でディレクトリ名を変更しようとすると、`mv` した上で `git worktree repair` を実行してGit側の参照を直す必要があり、非常に手間がかかる。結局「古い名前のまま我慢する」か「一度 worktree を削除して作り直す」という運用になりがちである。

## Proposal
`wt rename <new_name>` コマンドを追加する。

**挙動:**
1. 現在のworktreeのブランチ名を `<new_name>` にリネームする (`git branch -m <new_name>`)。
2. 対応するworktreeのディレクトリをリネームする (`mv .worktrees/<old_name> .worktrees/<new_name>`)。
3. Gitの内部リンク（`.git/worktrees/` 以下の情報など）を修復する (`git worktree repair`)。
4. 設定ファイル（`metadata` など、easy-worktree が管理する内部状態）があれば更新する。

**引数の仕様:**
- `wt rename <new_name>`: 現在のworktreeをリネームする。
- `wt rename <old_name> <new_name>`: 指定したworktreeをリネームする。

## Inspiration
- `git branch -m` の手軽さ。
- Git Town の `git town rename-branch` (ブランチ名変更時の各種同期機能)。

## Expected Daily Benefit
タイポの修正や、WIP状態で適当に付けたブランチ名をPR作成前に整理したいときなど、**「ブランチ名を変えたいがディレクトリ名との不一致が面倒だから我慢する」という日々の小さな摩擦が完全に解消される**。
再作成（`wt rm` & `wt add`）を伴わないため、未コミットのファイルやエディタのローカルヒストリーなども維持したままクリーンに名前を整理できる。

## Scope and Non-Goals
- **リモートブランチのリネーム**: 既に `origin` に push されているブランチのリモート側リネーム（古いブランチの削除と新しいブランチのpush）まではスコープ外とする（複雑になりすぎるため）。ローカルのディレクトリ名とブランチ名の同期解決にフォーカスする。
- **main/base worktree のリネーム**: このコマンドは `.worktrees/` 以下に作成されたサブ worktree のみを対象とする。

## Risks or Open Questions
- **大文字・小文字のみの変更**: macOS や Windows などの Case-insensitive なファイルシステムで `foo` を `Foo` に変更する場合、単純な `mv` が失敗したり挙動が不安定になる可能性があるため、一時ディレクトリを経由するなどの考慮が必要。
- **エディタ・IDEのプロセス**: リネーム時に VSCode などが古いディレクトリを掴んでいると、ファイルシステム上のロックで失敗したり、エディタ側でファイルが見つからなくなる現象が起きる。コマンド実行前に「エディタ等のディレクトリ参照が切れる」ことをWarningとして出すか？

## Suggested Rollout
1. `wt rename <new_name>` （現在のworktreeを対象とする形式）のみを先に実装し、ローカルでの動作確認と `git worktree repair` の安定性を検証する。
2. Case-insensitive OS への対応を追加する。
3. `wt rename <old_name> <new_name>` のシグネチャをサポートする。
