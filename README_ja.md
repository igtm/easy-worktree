# easy-worktree

Git worktree を簡単に管理するための CLI ツール

## 概要

`easy-worktree` は git worktree の面倒な部分を慣習で決めることで、考えることを少なくするツールです。

### 主な特徴

- **決まったディレクトリ構成**: `WT_<repository_name>/` の中に `_base/` ディレクトリを作り、これがリポジトリの本体となります
- **簡単な worktree 管理**: `_base/` から worktree を作成・削除
- **自動的なブランチ更新**: worktree 作成時に `git fetch --all` を自動実行

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

### 新しいリポジトリをクローン

```bash
wt clone https://github.com/user/repo.git
```

これにより以下の構成が作成されます：

```
WT_repo/
  _base/  # リポジトリの本体（基本的にいじらない）
```

### 既存のリポジトリを easy-worktree 構成に変換

```bash
cd my-repo/
wt init
```

現在のディレクトリが `../WT_my-repo/_base/` に移動されます。

### worktree を追加

```bash
cd WT_repo/
wt add feature-1
```

これにより以下の構成になります：

```
WT_repo/
  _base/
  feature-1/  # 作業用 worktree
```

ブランチ名を指定することもできます：

```bash
wt add feature-1 main
```

worktree 作成と同時にエイリアスを設定：

```bash
wt add feature-123 --alias current    # feature-123 を作成して current エイリアスを設定
```

### worktree 一覧を表示

```bash
wt list
```

### worktree を削除

```bash
wt rm feature-1
# または
wt remove feature-1
```

### 初期化 hook（post-add）

worktree 作成後に自動的に実行されるスクリプトを設定できます。

**Hook の配置場所**: `_base/.wt/post-add`

**自動作成**: `wt clone` または `wt init` を実行すると、テンプレートファイルが自動的に `_base/.wt/post-add` に作成されます（既に存在する場合は上書きしません）。このファイルを編集して、プロジェクト固有の初期化処理を記述してください。

```bash
# Hook スクリプトの編集例
vim WT_repo/_base/.wt/post-add
```

```bash
#!/bin/bash
set -e

echo "Initializing worktree: $WT_WORKTREE_NAME"

# npm パッケージのインストール
if [ -f package.json ]; then
    npm install
fi

# .env ファイルのコピー
if [ -f "$WT_BASE_DIR/.env.example" ]; then
    cp "$WT_BASE_DIR/.env.example" .env
fi

echo "Setup completed!"
```

実行権限を忘れずに：

```bash
chmod +x WT_repo/_base/.wt/post-add
```

**利用可能な環境変数**:
- `WT_WORKTREE_PATH`: 作成された worktree のパス
- `WT_WORKTREE_NAME`: worktree の名前
- `WT_BASE_DIR`: `_base/` ディレクトリのパス
- `WT_BRANCH`: ブランチ名
- `WT_ACTION`: アクション名（`add`）

Hook は新しく作成された worktree ディレクトリ内で実行されます。

### worktree 一覧を詳細表示

```bash
wt list --verbose           # 作成日時、最終コミット、状態を表示
wt list --sort age          # 作成日時順にソート
wt list --sort name         # 名前順にソート
```

### 未使用の worktree をクリーンアップ

変更がない（clean状態の）worktree を一括削除できます。

```bash
wt clean --dry-run          # 削除対象を確認（実際には削除しない）
wt clean --days 30          # 30日以上前に作成された clean worktree を削除
wt clean --all              # すべての clean worktree を削除（確認なし）
```

### worktree のエイリアスを作成

よく使う worktree にシンボリックリンクでショートカットを作成できます。

```bash
wt alias current feature-123    # current という名前でエイリアス作成
wt alias dev feature-xyz        # dev という名前でエイリアス作成
wt alias current hoge3          # 既存のエイリアスを自動的に上書き
wt alias --list                 # エイリアス一覧を表示
wt alias --remove current       # エイリアスを削除
```

### 全 worktree の状態を確認

すべての worktree の git status を一度に確認できます。

```bash
wt status                   # 全 worktree の状態を表示
wt status --dirty           # 変更がある worktree のみ表示
wt status --short           # 簡潔な表示
```

### その他の git worktree コマンド

`wt` は他の git worktree コマンドもサポートしています：

```bash
wt prune
wt lock <worktree>
wt unlock <worktree>
```

## ディレクトリ構成

```
WT_<repository_name>/     # プロジェクトのルートディレクトリ
  _base/                   # git リポジトリの本体
  feature-1/               # worktree 1
  bugfix-123/              # worktree 2
  ...
```

`WT_<repository_name>/` または worktree ディレクトリ内から `wt` コマンドを実行できます。

## 必要要件

- Python >= 3.11
- Git

## ライセンス

MIT License

## 貢献

Issue や Pull Request を歓迎します！
