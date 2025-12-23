![hero](hero.png)

# easy-worktree

Git worktree を簡単に管理するための CLI ツール

## 概要

`easy-worktree` は git worktree の管理をシンプルにするためのツールです。
リポジトリのルートディレクトリをそのままメインの作業場所（main）として使いつつ、他のブランチでの作業が必要な場合はサブディレクトリ（デフォルトでは `.worktrees/`）に worktree を作成して管理します。

### 主な特徴

- **スマートな切り替え**: `wt select` で作業ディレクトリを瞬時に切り替え。特別な設定なしで新しいシェルとして「ジャンプ」できます。
- **自動セットアップ**: `.env` などのファイルをルートから各 worktree へ自動的にコピー・初期化できます。
- **わかりやすい一覧表示**: `wt list` で worktree の一覧、ブランチ、状態（clean/dirty）、GitHub PR 情報を美しく表示します。
- **スマートなクリーンアップ**: マージ済みのブランチや古い worktree を簡単に削除できるようになります。
- **2文字ショートカット**: `ad`, `ls`, `sl`, `su`, `st`, `cl` といった短いコマンドで素早く操作できます。

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

#### セットアップをスキップする

自動セットアップ（ファイルのコピーや hook の実行）を行わずに worktree を作成したい場合は、`--skip-setup` フラグを使用します：

```bash
wt add feature-1 --skip-setup
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

#### ワークツリーを切り替える (ショートカット: `sl`)

```bash
wt select feature-1
```

`wt select` を実行すると、そのワークツリーのディレクトリへ**自動的に「ジャンプ」**します（新しいシェルが起動します）。

- **プロンプト**: `(wt:feature-1)` のように表示されます。
- **ターミナルタイトル**: ウィンドウのタイトル（ターミナルのタブ名など）が `wt:feature-1` に更新されます。
- **Tmux**: tmux 内で実行している場合、ウィンドウ名が `wt:feature-1` に更新されます。

元のディレクトリに戻りたい場合は `exit` を実行するか `Ctrl-D` を押してください。

※ すでに `wt` のサブシェル内にいる状態で再度実行すると、ネストを警告するメッセージが表示されます。ネストを避けるには一度 `exit` してから切り替えることをお勧めします。

引数なしで実行すると `fzf` によるインタラクティブな選択が可能です。

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

#### ワークツリーの初期化 (ショートカット: `su`)

`.env` ファイルなどのコピーや `post-add` フックの実行を、現在のワークツリーに対して行います。

```bash
wt setup
```

#### 可視化と外部ツールとの連携

`wt select` でワークツリーに切り替えた際、以下の機能が自動的に有効になります：
- **ターミナルタイトル**: ウィンドウやタブのタイトルが `wt:ワークツリー名` に更新されます。
- **Tmux**: tmux 内にいる場合、ウィンドウ名が自動的に `wt:ワークツリー名` に変更されます。

また、`wt current` (または `cur`) コマンドを使って、外部ツールに現在のワークツリー情報を表示できます。

##### Tmux ステータスバー
`.tmux.conf` に以下を追加して、ステータスラインに常時表示できます。
```tmux
set -g status-right "#(wt current) | %Y-%m-%d %H:%M"
```

##### Zsh / Bash プロンプト
環境変数 `$WT_SESSION_NAME` を利用してプロンプトをカスタマイズできます。

**Zsh (.zshrc)**:
```zsh
RPROMPT='${WT_SESSION_NAME:+"(wt:$WT_SESSION_NAME)"} '"$RPROMPT"
```

**Bash (.bashrc)**:
```bash
PS1='$(if [ -n "$WT_SESSION_NAME" ]; then echo "($WT_SESSION_NAME) "; fi)'$PS1
```

##### Starship
`starship.toml` にカスタムモジュールを追加します。
```toml
[custom.easy_worktree]
command = "wt current"
when = 'test -n "$WT_SESSION_NAME"'
format = "via [$symbol$output]($style) "
symbol = "🌳 "
style = "bold green"
```

##### Powerlevel10k
`.p10k.zsh` にカスタムセグメントを定義することで、綺麗に統合できます。

1. `POWERLEVEL9K_LEFT_PROMPT_ELEMENTS` に `easy_worktree` を追加。
2. 以下の関数を定義：
```zsh
function prompt_easy_worktree() {
  if [[ -n $WT_SESSION_NAME ]]; then
    p10k segment -f 255 -b 28 -i '🌳' -t "wt:$WT_SESSION_NAME"
  fi
}
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
setup_files = [".env"]          # 自動セットアップでコピーするファイル一覧
```

#### ローカル設定の上書き

`.wt/config.local.toml` を作成すると、設定をローカルでのみ上書きできます。このファイルは自動的に `.gitignore` に追加され、リポジトリにはコミットされません。

## Hook

`wt add` の後に自動実行されるスクリプトを記述できます。
テンプレートが `.wt/post-add` に作成されます。

## ライセンス

MIT License
