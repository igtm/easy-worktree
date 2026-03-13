# wt bisect 向けの一時的 sandbox worktree 作成機能

## Summary
`git bisect` を実行する際、現在開発中で build cache (node_modules, target, __pycache__ など) が構築されている worktree をそのまま使うと、キャッシュや依存関係が破壊されて復旧に時間がかかります。
これを避けるため、`git bisect` や一時的な動作検証のためだけの「使い捨て worktree」を安全・簡単に生成し、用が済んだらワンコマンドで削除できる機能（`wt sandbox` または `wt bisect`）を提案します。

## Problem
1. **Build cache の破壊**: `git bisect` をメインの worktree で実行すると、古いコミットにチェックアウトされるたびにビルド成果物や依存ライブラリの状態が変わり、元のブランチに戻した際にも再ビルド（数百秒かかることも）が必要になります。
2. **LSP の混乱**: エディタで開いたままのディレクトリで `git bisect` のような激しい checkout を行うと、ファイルツリーの変更によって LSP (Language Server Protocol) やインデクサがフリーズしたり、キャッシュが壊れたりすることがあります。
3. **安全な退避先の欠如**: 別の worktree を手動で作ってそこで bisect を行えば解決しますが、`git worktree add ../tmp-bisect` と入力し、終わったあとに削除とブランチの掃除を手動で行うのは、`easy-worktree` が目指す滑らかな DX に反する面倒な作業です。

## Proposal
使い捨ての環境を提供する `wt sandbox` (または特化型の `wt bisect`) コマンドを新設します。

```bash
# 一時worktreeを作成し、そこに移動する
wt sandbox --start

# 内部的には以下のような処理を行う
# 1. 一時的なパス (例: `<repo>-worktrees/.wt-sandbox-XXXXXX`) に detached worktree を作成
# 2. サブシェルまたは cd 連携機構でそのディレクトリへ移動
# 3. ユーザーはそこで安全に `git bisect start ...` などを実行してバグ調査を行う
```

用が済んだら終了コマンドを実行します。
```bash
# bisect完了後、元のworktreeへ戻り、一時worktreeを削除
wt sandbox --clean
```

## Inspiration
- **Git Town / lazygit**: 特定の重い操作に対して別ウィンドウや専用のビューを用意し、現在の作業コンテキストを汚染しないアプローチ。
- **一時コンテナ環境**: Docker 等における `--rm` オプション付きの使い捨てコンテナでのテスト実行思想。

## Expected Daily Benefit
- バグ調査（bisect）や「ちょっと古いコミットでビルドが通るか確認したい」時の心理的・時間的ハードルが劇的に下がります。
- メインの開発 worktree (LSPのキャッシュ、ローカルのビルド済みバイナリ) が無傷で保たれるため、検証完了後すぐに元の開発を再開できます。
- 日常的な「ちょっと作業を中断して検証環境を作りたい」需要を完璧に満たせます。

## Scope and Non-Goals
- **Scope**: 使い捨て worktree のライフサイクル管理（作成、移動、確実な削除）。
- **Non-Goal**: `git bisect` コマンド自体のラップや自動実行（ユーザーはあくまで標準の git bisect をサンドボックス内で叩く前提とし、ツールの責務を小さく保ちます）。

## Risks or Open Questions
- **ディレクトリ名の衝突**: 複数のターミナルから同時にサンドボックスを作りたい場合の命名規則（PIDやランダムハッシュ、タイムスタンプを付与するか？）。
- **クリーンアップ漏れの防止**: ユーザーが `--clean` を忘れて放置した場合、`wt clean` で一括検知・削除できるように統合するべきか。

## Suggested Rollout
1. 最小実装として `wt sandbox` コマンドを作り、自動で `.wt-sandbox-<timestamp>` ディレクトリに HEAD の状態でチェックアウトする機能を提供する。
2. 次に `wt sandbox --clean` を実装し、現在のディレクトリが sandbox であればそれを削除して前の worktree に戻る挙動を作る。
3. ドキュメントのベストプラクティスとして、「bisect を安全に行う方法」を紹介する。
