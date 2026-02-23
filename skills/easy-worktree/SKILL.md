---
name: eaasy-worktree
description: easy-worktree リポジトリで `wt` コマンドを使って worktree を作成・切替・整理するための実践ガイドです。基本操作、主要オプション、よく使う運用フローをまとめています。
---

# eaasy-worktree Skill

このスキルは、このリポジトリで `wt` コマンドを使うときの最小手順と運用パターンを提供します。

## 使う場面

- 「新しい作業ブランチを別ディレクトリで始めたい」
- 「今の変更を退避して別 worktree へ移したい」
- 「PR 番号から作業環境をすぐ作りたい」
- 「古い worktree を安全に掃除したい」
- 「bare リポジトリ運用で `--git-dir` を使いたい」

## クイックスタート

```bash
# 既存リポジトリを初期化
wt init

# feature ブランチ用 worktree を作成
wt add feature-123

# 作成した worktree にジャンプ（サブシェル）
wt select feature-123

# 作業後は exit で戻る
exit
```

## 主要コマンド

- `wt init`
  - 現在の Git リポジトリを easy-worktree 管理として初期化します。
- `wt add <name> [base_branch] [--skip-setup|--no-setup] [--select [command...]]`
  - 新しい worktree を作成します。ショートカット: `wt ad ...`
- `wt select [<name>|-] [command...]`
  - worktree に切り替えます。ショートカット: `wt sl ...`
  - 引数なしで `fzf` 選択、`-` で直前の worktree に戻ります。
- `wt list [--pr] [--days N] [--merged] [--closed] [--all] [--sort ...] [--asc|--desc]`
  - worktree 一覧を表示します。ショートカット: `wt ls ...`
- `wt stash <name> [base_branch]`
  - 現在の変更を stash し、新規 worktree 側へ移します。ショートカット: `wt st ...`
- `wt rm <name> [-f|--force]`
  - worktree を削除します。
- `wt clean [--days N] [--merged] [--closed] [--all]`
  - 条件に合う不要 worktree をまとめて削除します。ショートカット: `wt cl ...`
- `wt pr add <number>`
  - PR から `pr@<number>` worktree を作成します（`gh` 必須）。
- `wt setup`
  - 設定に従って `.env` などをコピーし、hook を実行します。ショートカット: `wt su`
- `wt diff [<name>] [args...]`
  - 対象 worktree で diff を確認します。ショートカット: `wt df ...`
- `wt config [--global|--local] [key [value]]`
  - 設定の確認・更新を行います。

## よく使う運用フロー

### 1) 新規機能を並行開発する

```bash
wt add feat/search-ui main --select
```

- `main` から `feat/search-ui` を切って、そのまま作業に入れます。

### 2) 今の変更を別作業として切り出す

```bash
wt stash fix/login-bug
wt select fix/login-bug
```

- 現在の未コミット変更を新 worktree に移し、main 側を汚さず整理できます。

### 3) PR からレビュー/検証環境を作る

```bash
wt pr add 123
wt select pr@123
```

### 4) 古い worktree を掃除する

```bash
wt list --days 30
wt clean --merged
```

## bare リポジトリでの使い方

`--git-dir` をグローバル引数として付けます。

```bash
wt --git-dir=/path/to/sandbox.git init
wt --git-dir=/path/to/sandbox.git add feat/abc main
wt --git-dir=/path/to/sandbox.git list --pr
```

## 参照ドキュメント

- 全体仕様: `README.md`
- 日本語手順: `README_ja.md`
- 実装ベースのコマンド定義: `easy_worktree/__init__.py`
