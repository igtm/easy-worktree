# wt migrate コマンドによる既存の通常リポジトリからの bare 化サポート

## Summary

既存の標準的な git リポジトリ（non-bare）を、`easy-worktree` が推奨する bare リポジトリベースのワークツリー構成へ、安全かつ自動で移行（マイグレーション）する `wt migrate` コマンドを追加する提案。

## Problem

すでに手元にクローン済みの大きなリポジトリがあり、そこで通常のブランチ切り替え運用を行っていたユーザーが、新たに `easy-worktree` を使った bare 運用に切り替えたい場合、現状では以下のいずれかが必要になります。

1. `wt clone --bare <url>` で最初からクローンし直す（巨大リポジトリでは時間がかかり、ローカルの未pushブランチも引き継げない）
2. 手動で `.git` を `repo.git` に移動し、`git config core.bare true` を設定し、元のファイルを削除した上で `wt add main main` のように再構築する（手順が複雑で破壊的操作を伴い、ミスしやすい）

この導入時のハードルが、`easy-worktree` のモダンな bare 運用への移行を妨げています。

## Proposal

現在の通常リポジトリのルートで `wt migrate`（または `wt init --migrate-to-bare` など）を実行するだけで、以下の操作を自動で安全に行う機能を提案します。

1. **事前チェック**: ワークツリーが dirty でないか、移行先パスが競合しないかを確認。
2. **bare ディレクトリの準備**: カレントディレクトリを `repo-tmp/` に一時退避し、その中の `.git` を `repo.git` として最上位に配置。
3. **bare 化設定**: `repo.git` 内の config を `core.bare = true` に書き換え。
4. **メインワークツリーの再構築**: 元の `repo-tmp/` の中身（`.git`以外）を `repo/` （またはデフォルトブランチ名のディレクトリ）として再配置し、`repo.git` に紐づく最初のワークツリーとして `git worktree add` 的なリンク処理を行う。
5. **.wt の初期化**: 新しいメインワークツリー内に `.wt` 構成を作成。

実行イメージ:
```bash
$ cd my-repo
$ wt migrate
Migrating to bare repository structure...
- Converted .git to my-repo.git (bare)
- Linked current files as worktree 'my-repo/main'
- Initialized easy-worktree
Migration completed! You can now use `wt add` to create new worktrees.
```

## Inspiration

- Git LFS の `git lfs migrate` （既存履歴を LFS に一括移行する機能）
- 既存ツール（Git Town など）が初回にリポジトリを自動診断してセットアップを促すスムーズなオンボーディング

## Expected Daily Benefit

日々の操作というよりは「オンボーディング時の摩擦」を劇的に減らす機能ですが、新しい開発マシンをセットアップする際や、チームメンバーに `easy-worktree` を勧める際に、「このコマンドを1発叩くだけで今の環境のまま bare 運用に移行できるよ」と言えるようになり、ツールの普及と利用ハードル低下に大きく貢献します。

## Scope and Non-Goals

- リモートリポジトリの URL を変更する機能は含まない。
- すでに `git worktree` で作られた既存のサブワークツリーのマイグレーションまでサポートするかどうかは要検討（まずはメインワークツリーのみの対応をスコープとする）。

## Risks or Open Questions

- **安全性とロールバック**: 途中で失敗した場合に、ファイルが消失したり `.git` が破損したりしないよう、アトミックな移動・バックアップの仕組みをどう実装するか。
- **カレントディレクトリの移動**: スクリプト実行中に親ディレクトリ名を変更したり移動したりするため、シェルのカレントディレクトリ追従（`cd`）がどう振る舞うか（サブシェルで実行を推奨するか、実行後に「`cd ../my-repo` を実行してください」とメッセージを出すか）。

## Suggested Rollout

1. まずは隠し機能（`wt init --experimental-migrate-bare`）として実装。
2. テストケースを十分に用意し（dirty な場合、未追跡ファイルがある場合、既に bare の場合などのエッジケース）、ローカルファイルの破壊リスクをゼロにする。
3. 安定性を確認後、`wt migrate` として公開し、`README.md` の「既存のリポジトリで使い始める場合」のセクションに追記する。
