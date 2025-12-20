![hero](hero.png)

# easy-worktree

Git worktree を簡単に管理するための CLI ツール

## 概要

`easy-worktree` は git worktree の管理をシンプルにするためのツールです。
リポジトリのルートディレクトリをそのままメインの作業場所（main）として使いつつ、他のブランチでの作業が必要な場合はサブディレクトリ（デフォルトでは `.worktrees/`）に worktree を作成して管理します。

### 主な特徴

- **整理されたディレクトリ構成**: worktree は `.worktrees/` ディレクトリ（設定で変更可能）の下に作成されます。ルートディレクトリが散らかりません。
- **自動同期**: `.env` などの git 管理外ファイルを、ルートから各 worktree へ自動的にコピー・同期できます。
- **わかりやすい一覧表示**: `wt list` で worktree の一覧、ブランチ、状態（clean/dirty）、GitHub PR 情報を美しく表示します。
- **スマートなクリーンアップ**: マージ済みのブランチや古い worktree を簡単に削除できるようになります。
- **2文字ショートカット**: `ad`, `ls`, `st`, `sy`, `cl` といった短いコマンドで素早く操作できます。

## 前提条件

`easy-worktree` には以下が必要です：

- **Git**: 2.34 以上を推奨します。
- **GitHub CLI (gh)**: PR 関連機能（`wt list --pr`, `wt pr add`, `wt clean --merged`）を利用する場合に必要です。[インストール方法](https://cli.github.com/)。

## インストール

```bash
pip install easy-worktree
```

または開発版をインストール:

```bash
git clone https://github.com/igtm/easy-worktree.git
cd easy-worktree
pip install -e .
```

## 使い方

### リポジトリの準備

#### 新しくクローンする場合

```bash
wt clone https://github.com/user/repo.git
```

リポジトリをクローンし、`easy-worktree` 用の初期設定を自動で行います。

#### 既存のリポジトリで使い始める場合

```bash
cd my-repo/
wt init
```

現在のディレクトリをメインリポジトリ（ルート）として `easy-worktree` を初期化します。既存のリポジトリ構成はそのまま維持されます。

### worktree の操作

#### worktree を追加 (ショートカット: `ad`)

```bash
wt add feature-1
```

これにより、以下のディレクトリ構成が作成されます：

```
my-repo/ (main)
  .worktrees/
    feature-1/  # ここが新しい worktree
  .wt/
  ...
```

既存のブランチを指定して作成することもできます：

```bash
wt add feature-1 main
```

#### 一覧を表示 (ショートカット: `ls`)

```bash
wt list
wt ls --pr   # GitHub の PR 情報もあわせて表示
```


#### スタッシュと移動 (ショートカット: `st`)

現在の変更をスタッシュし、そのまま新しい worktree を作成して移動します。

```bash
wt stash feature-2
```

#### PR 管理

GitHub の PR を取得して worktree を作成します（`gh` CLI が必要です）。

```bash
wt pr add 123    # PR #123 を取得し 'pr@123' という名前で worktree を作成
```

#### 削除

```bash
wt rm feature-1
```

ディレクトリごと worktree を削除します。

### 便利な機能

#### 設定ファイルの同期 (ショートカット: `sy`)

`.env` ファイルなどの git 管理外ファイルを、ルートから worktree に手動で同期します。

```bash
wt sync .env
```


#### クリーンアップ (ショートカット: `cl`)

```bash
wt clean --merged
wt clean --closed  # クローズされた (未マージ) PRのworktreeを削除
wt clean --days 30
```


### 設定

`.wt/config.toml` で挙動をカスタマイズできます：

```toml
worktrees_dir = ".worktrees"   # worktree を作成するディレクトリ名
sync_files = [".env"]          # 自動同期するファイル一覧
auto_copy_on_add = true        # wt add 時にファイルを自動コピーするか
```

## Hook

`wt add` の後に自動実行されるスクリプトを記述できます。
テンプレートが `.wt/post-add` に作成されます。

## ライセンス

MIT License
