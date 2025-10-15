#!/usr/bin/env python3
"""
Git worktree を簡単に管理するための CLI ツール
"""
import os
import subprocess
import sys
from pathlib import Path
import re
from datetime import datetime
import json


# 言語判定
def is_japanese() -> bool:
    """LANG環境変数から日本語かどうかを判定"""
    lang = os.environ.get('LANG', '')
    return 'ja' in lang.lower()


# メッセージ辞書
MESSAGES = {
    'error': {
        'en': 'Error: {}',
        'ja': 'エラー: {}'
    },
    'usage': {
        'en': 'Usage: wt clone <repository_url>',
        'ja': '使用方法: wt clone <repository_url>'
    },
    'usage_add': {
        'en': 'Usage: wt add <work_name> [<base_branch>] [--alias <name>]',
        'ja': '使用方法: wt add <作業名> [<base_branch>] [--alias <名前>]'
    },
    'usage_rm': {
        'en': 'Usage: wt rm <work_name>',
        'ja': '使用方法: wt rm <作業名>'
    },
    'base_not_found': {
        'en': '_base/ directory not found',
        'ja': '_base/ ディレクトリが見つかりません'
    },
    'run_in_wt_dir': {
        'en': 'Please run inside WT_<repository_name>/ directory',
        'ja': 'WT_<repository_name>/ ディレクトリ内で実行してください'
    },
    'already_exists': {
        'en': '{} already exists',
        'ja': '{} はすでに存在します'
    },
    'cloning': {
        'en': 'Cloning: {} -> {}',
        'ja': 'クローン中: {} -> {}'
    },
    'completed_clone': {
        'en': 'Completed: cloned to {}',
        'ja': '完了: {} にクローンしました'
    },
    'not_git_repo': {
        'en': 'Current directory is not a git repository',
        'ja': '現在のディレクトリは git リポジトリではありません'
    },
    'run_at_root': {
        'en': 'Please run at repository root directory {}',
        'ja': 'リポジトリのルートディレクトリ {} で実行してください'
    },
    'creating_dir': {
        'en': 'Creating {}...',
        'ja': '{} を作成中...'
    },
    'moving': {
        'en': 'Moving {} -> {}...',
        'ja': '{} -> {} に移動中...'
    },
    'completed_move': {
        'en': 'Completed: moved to {}',
        'ja': '完了: {} に移動しました'
    },
    'use_wt_from': {
        'en': 'Use wt command from {} from next time',
        'ja': '次回から {} で wt コマンドを使用してください'
    },
    'fetching': {
        'en': 'Fetching latest information from remote...',
        'ja': 'リモートから最新情報を取得中...'
    },
    'creating_worktree': {
        'en': 'Creating worktree: {}',
        'ja': 'worktree を作成中: {}'
    },
    'completed_worktree': {
        'en': 'Completed: created worktree at {}',
        'ja': '完了: {} に worktree を作成しました'
    },
    'removing_worktree': {
        'en': 'Removing worktree: {}',
        'ja': 'worktree を削除中: {}'
    },
    'completed_remove': {
        'en': 'Completed: removed {}',
        'ja': '完了: {} を削除しました'
    },
    'creating_branch': {
        'en': "Creating new branch '{}' from '{}'",
        'ja': "'{}' から新しいブランチ '{}' を作成"
    },
    'default_branch_not_found': {
        'en': 'Could not find default branch (main/master)',
        'ja': 'デフォルトブランチ (main/master) が見つかりません'
    },
    'running_hook': {
        'en': 'Running post-add hook: {}',
        'ja': 'post-add hook を実行中: {}'
    },
    'hook_not_executable': {
        'en': 'Warning: hook is not executable: {}',
        'ja': '警告: hook が実行可能ではありません: {}'
    },
    'hook_failed': {
        'en': 'Warning: hook exited with code {}',
        'ja': '警告: hook が終了コード {} で終了しました'
    },
    'usage_clean': {
        'en': 'Usage: wt clean [--dry-run] [--days N] [--all]',
        'ja': '使用方法: wt clean [--dry-run] [--days N] [--all]'
    },
    'usage_alias': {
        'en': 'Usage: wt alias <name> <worktree> | wt alias --list | wt alias --remove <name>',
        'ja': '使用方法: wt alias <名前> <worktree> | wt alias --list | wt alias --remove <名前>'
    },
    'alias_updated': {
        'en': 'Updated alias: {} -> {}',
        'ja': 'エイリアスを更新しました: {} -> {}'
    },
    'no_clean_targets': {
        'en': 'No worktrees to clean',
        'ja': 'クリーンアップ対象の worktree がありません'
    },
    'clean_target': {
        'en': 'Will remove: {} (created: {}, clean)',
        'ja': '削除対象: {} (作成日時: {}, 変更なし)'
    },
    'clean_confirm': {
        'en': 'Remove {} worktree(s)? [y/N]: ',
        'ja': '{} 個の worktree を削除しますか？ [y/N]: '
    },
    'alias_created': {
        'en': 'Created alias: {} -> {}',
        'ja': 'エイリアスを作成しました: {} -> {}'
    },
    'alias_removed': {
        'en': 'Removed alias: {}',
        'ja': 'エイリアスを削除しました: {}'
    },
    'alias_not_found': {
        'en': 'Alias not found: {}',
        'ja': 'エイリアスが見つかりません: {}'
    },
    'worktree_name': {
        'en': 'Worktree',
        'ja': 'Worktree'
    },
    'branch_name': {
        'en': 'Branch',
        'ja': 'ブランチ'
    },
    'created_at': {
        'en': 'Created',
        'ja': '作成日時'
    },
    'last_commit': {
        'en': 'Last Commit',
        'ja': '最終コミット'
    },
    'status_label': {
        'en': 'Status',
        'ja': '状態'
    }
}


def msg(key: str, *args) -> str:
    """言語に応じたメッセージを取得"""
    lang = 'ja' if is_japanese() else 'en'
    message = MESSAGES.get(key, {}).get(lang, key)
    if args:
        return message.format(*args)
    return message


def run_command(cmd: list[str], cwd: Path = None, check: bool = True) -> subprocess.CompletedProcess:
    """コマンドを実行"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        print(msg('error', e.stderr), file=sys.stderr)
        sys.exit(1)


def get_repository_name(url: str) -> str:
    """リポジトリ URL から名前を抽出"""
    # URL から .git を削除して最後の部分を取得
    match = re.search(r'/([^/]+?)(?:\.git)?$', url)
    if match:
        return match.group(1)
    # ローカルパスの場合
    return Path(url).name


def create_hook_template(base_dir: Path):
    """post-add hook のテンプレートと .wt/ 内のファイルを作成"""
    wt_dir = base_dir / ".wt"

    # .wt ディレクトリを作成
    wt_dir.mkdir(exist_ok=True)

    # post-add hook テンプレート
    hook_file = wt_dir / "post-add"
    if not hook_file.exists():
        template = """#!/bin/bash
# Post-add hook for easy-worktree
# This script is automatically executed after creating a new worktree
#
# Available environment variables:
#   WT_WORKTREE_PATH  - Path to the created worktree
#   WT_WORKTREE_NAME  - Name of the worktree
#   WT_BASE_DIR       - Path to the _base/ directory
#   WT_BRANCH         - Branch name
#   WT_ACTION         - Action name (add)
#
# Example: Install dependencies and copy configuration files
#
# set -e
#
# echo "Initializing worktree: $WT_WORKTREE_NAME"
#
# # Install npm packages
# if [ -f package.json ]; then
#     npm install
# fi
#
# # Copy .env file
# if [ -f "$WT_BASE_DIR/.env.example" ]; then
#     cp "$WT_BASE_DIR/.env.example" .env
# fi
#
# echo "Setup completed!"
"""
        hook_file.write_text(template)
        # 実行権限を付与
        hook_file.chmod(0o755)

    # .gitignore
    gitignore_file = wt_dir / ".gitignore"
    if not gitignore_file.exists():
        gitignore_content = "post-add.local\n"
        gitignore_file.write_text(gitignore_content)

    # README.md (言語に応じて)
    readme_file = wt_dir / "README.md"
    if not readme_file.exists():
        if is_japanese():
            readme_content = """# easy-worktree フック

このディレクトリには、easy-worktree (wt コマンド) のフックスクリプトが格納されています。

## wt コマンドとは

`wt` は Git worktree を簡単に管理するための CLI ツールです。複数のブランチで同時に作業する際に、ブランチごとに独立したディレクトリ（worktree）を作成・管理できます。

### 基本的な使い方

```bash
# リポジトリをクローン
wt clone <repository_url>

# 新しい worktree を作成（新規ブランチ）
wt add <作業名>

# 既存ブランチから worktree を作成
wt add <作業名> <既存ブランチ名>

# エイリアスを作成（current エイリアスで現在の作業を切り替え）
wt add <作業名> --alias current

# worktree 一覧を表示
wt list

# worktree を削除
wt rm <作業名>
```

詳細は https://github.com/igtm/easy-worktree を参照してください。

## エイリアスとは

エイリアスは、worktree へのシンボリックリンク（symbolic link）です。同じエイリアス名で異なる worktree を指すことで、固定されたパスで複数のブランチを切り替えられます。

### エイリアスの便利な使い方

**VSCode ワークスペースでの活用**

`current` などの固定エイリアスを VSCode のワークスペースとして開くことで、worktree を切り替えても VSCode を開き直す必要がなくなります。

```bash
# 最初の作業
wt add feature-a --alias current
code current  # VSCode で current を開く

# 別の作業に切り替え（VSCode は開いたまま）
wt add feature-b --alias current
# current エイリアスが feature-b を指すようになる
```

このように、エイリアスを使うことで：
- VSCode のワークスペース設定が維持される
- 拡張機能の設定やウィンドウレイアウトが保持される
- ブランチ切り替えのたびにエディタを開き直す手間が不要

## post-add フック

`post-add` フックは、worktree 作成後に自動実行されるスクリプトです。

### 使用例

- 依存関係のインストール（npm install, pip install など）
- 設定ファイルのコピー（.env ファイルなど）
- ディレクトリの初期化
- VSCode ワークスペースの作成

### 利用可能な環境変数

- `WT_WORKTREE_PATH`: 作成された worktree のパス
- `WT_WORKTREE_NAME`: worktree の名前
- `WT_BASE_DIR`: _base/ ディレクトリのパス
- `WT_BRANCH`: ブランチ名
- `WT_ACTION`: アクション名（常に "add"）

### post-add.local について

`post-add.local` は、個人用のローカルフックです。このファイルは `.gitignore` に含まれているため、リポジトリにコミットされません。チーム全体で共有したいフックは `post-add` に、個人的な設定は `post-add.local` に記述してください。

`post-add` が存在する場合のみ、`post-add.local` も自動的に実行されます。
"""
        else:
            readme_content = """# easy-worktree Hooks

This directory contains hook scripts for easy-worktree (wt command).

## What is wt command?

`wt` is a CLI tool for easily managing Git worktrees. When working on multiple branches simultaneously, you can create and manage independent directories (worktrees) for each branch.

### Basic Usage

```bash
# Clone a repository
wt clone <repository_url>

# Create a new worktree (new branch)
wt add <work_name>

# Create a worktree from an existing branch
wt add <work_name> <existing_branch_name>

# Create an alias (use "current" alias to switch between tasks)
wt add <work_name> --alias current

# List worktrees
wt list

# Remove a worktree
wt rm <work_name>
```

For more details, see https://github.com/igtm/easy-worktree

## What are Aliases?

Aliases are symbolic links to worktrees. By pointing the same alias name to different worktrees, you can switch between multiple branches using a fixed path.

### Smart Use of Aliases

**Using with VSCode Workspace**

By opening a fixed alias like `current` as a VSCode workspace, you can switch worktrees without needing to reopen VSCode.

```bash
# First task
wt add feature-a --alias current
code current  # Open current in VSCode

# Switch to another task (VSCode stays open)
wt add feature-b --alias current
# The current alias now points to feature-b
```

Benefits of using aliases:
- VSCode workspace settings are preserved
- Extension settings and window layouts are maintained
- No need to reopen the editor when switching branches

## post-add Hook

The `post-add` hook is a script that runs automatically after creating a worktree.

### Use Cases

- Install dependencies (npm install, pip install, etc.)
- Copy configuration files (.env files, etc.)
- Initialize directories
- Create VSCode workspaces

### Available Environment Variables

- `WT_WORKTREE_PATH`: Path to the created worktree
- `WT_WORKTREE_NAME`: Name of the worktree
- `WT_BASE_DIR`: Path to the _base/ directory
- `WT_BRANCH`: Branch name
- `WT_ACTION`: Action name (always "add")

### About post-add.local

`post-add.local` is for personal local hooks. This file is included in `.gitignore`, so it won't be committed to the repository. Use `post-add` for hooks you want to share with the team, and `post-add.local` for your personal settings.

`post-add.local` is automatically executed only when `post-add` exists.
"""
        readme_file.write_text(readme_content)


def find_base_dir() -> Path | None:
    """現在のディレクトリまたは親ディレクトリから _base/ を探す"""
    current = Path.cwd()

    # 現在のディレクトリに _base/ がある場合
    base_dir = current / "_base"
    if base_dir.exists() and base_dir.is_dir():
        return base_dir

    # 親ディレクトリに _base/ がある場合（worktree の中にいる場合）
    base_dir = current.parent / "_base"
    if base_dir.exists() and base_dir.is_dir():
        return base_dir

    return None


def cmd_clone(args: list[str]):
    """wt clone <repository_url> - Clone a repository"""
    if len(args) < 1:
        print(msg('usage'), file=sys.stderr)
        sys.exit(1)

    repo_url = args[0]
    repo_name = get_repository_name(repo_url)

    # WT_<repository_name>/_base にクローン
    parent_dir = Path(f"WT_{repo_name}")
    base_dir = parent_dir / "_base"

    if base_dir.exists():
        print(msg('error', msg('already_exists', base_dir)), file=sys.stderr)
        sys.exit(1)

    parent_dir.mkdir(exist_ok=True)

    print(msg('cloning', repo_url, base_dir))
    run_command(["git", "clone", repo_url, str(base_dir)])
    print(msg('completed_clone', base_dir))

    # post-add hook テンプレートを作成
    create_hook_template(base_dir)


def cmd_init(args: list[str]):
    """wt init - Move existing git repository to WT_<repo>/_base/"""
    current_dir = Path.cwd()

    # 現在のディレクトリが git リポジトリか確認
    result = run_command(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=current_dir,
        check=False
    )

    if result.returncode != 0:
        print(msg('error', msg('not_git_repo')), file=sys.stderr)
        sys.exit(1)

    git_root = Path(result.stdout.strip())

    # カレントディレクトリがリポジトリのルートでない場合はエラー
    if git_root != current_dir:
        print(msg('error', msg('run_at_root', git_root)), file=sys.stderr)
        sys.exit(1)

    # リポジトリ名を取得（remote origin から、なければディレクトリ名）
    result = run_command(
        ["git", "remote", "get-url", "origin"],
        cwd=current_dir,
        check=False
    )

    if result.returncode == 0 and result.stdout.strip():
        repo_name = get_repository_name(result.stdout.strip())
    else:
        # リモートがない場合は現在のディレクトリ名を使用
        repo_name = current_dir.name

    # 親ディレクトリと新しいパスを決定
    parent_of_current = current_dir.parent
    wt_parent_dir = parent_of_current / f"WT_{repo_name}"
    new_base_dir = wt_parent_dir / "_base"

    # すでに WT_<repo> が存在するかチェック
    if wt_parent_dir.exists():
        print(msg('error', msg('already_exists', wt_parent_dir)), file=sys.stderr)
        sys.exit(1)

    # WT_<repo>/ ディレクトリを作成
    print(msg('creating_dir', wt_parent_dir))
    wt_parent_dir.mkdir(exist_ok=True)

    # 現在のディレクトリを WT_<repo>/_base/ に移動
    print(msg('moving', current_dir, new_base_dir))
    current_dir.rename(new_base_dir)

    print(msg('completed_move', new_base_dir))
    print(msg('use_wt_from', wt_parent_dir))

    # post-add hook テンプレートを作成
    create_hook_template(new_base_dir)


def run_post_add_hook(worktree_path: Path, work_name: str, base_dir: Path, branch: str = None):
    """worktree 作成後の hook を実行"""
    # .wt/post-add を探す
    hook_path = base_dir / ".wt" / "post-add"

    if not hook_path.exists() or not hook_path.is_file():
        return  # hook がなければ何もしない

    if not os.access(hook_path, os.X_OK):
        print(msg('hook_not_executable', hook_path), file=sys.stderr)
        return

    # 環境変数を設定
    env = os.environ.copy()
    env.update({
        'WT_WORKTREE_PATH': str(worktree_path),
        'WT_WORKTREE_NAME': work_name,
        'WT_BASE_DIR': str(base_dir),
        'WT_BRANCH': branch or work_name,
        'WT_ACTION': 'add'
    })

    print(msg('running_hook', hook_path))
    try:
        result = subprocess.run(
            [str(hook_path)],
            cwd=worktree_path,  # worktree 内で実行
            env=env,
            check=False
        )

        if result.returncode != 0:
            print(msg('hook_failed', result.returncode), file=sys.stderr)
    except Exception as e:
        print(msg('error', str(e)), file=sys.stderr)


def cmd_add(args: list[str]):
    """wt add <work_name> [<base_branch>] - Add a worktree"""
    if len(args) < 1:
        print(msg('usage_add'), file=sys.stderr)
        sys.exit(1)

    base_dir = find_base_dir()
    if not base_dir:
        print(msg('error', msg('base_not_found')), file=sys.stderr)
        print(msg('run_in_wt_dir'), file=sys.stderr)
        sys.exit(1)

    # --alias オプションをチェック
    alias_name = None
    if '--alias' in args:
        alias_index = args.index('--alias')
        if alias_index + 1 < len(args):
            alias_name = args[alias_index + 1]
            # --alias とその値を削除
            args.pop(alias_index)
            args.pop(alias_index)
        else:
            print(msg('error', 'Missing alias name after --alias'), file=sys.stderr)
            sys.exit(1)

    work_name = args[0]

    # worktree のパスを決定（_base の親ディレクトリに作成）
    worktree_path = base_dir.parent / work_name

    if worktree_path.exists():
        print(msg('error', msg('already_exists', worktree_path)), file=sys.stderr)
        sys.exit(1)

    # ブランチを最新に更新
    print(msg('fetching'))
    run_command(["git", "fetch", "--all"], cwd=base_dir)

    # _base/ を base branch の最新に更新
    # 現在のブランチを取得
    result = run_command(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=base_dir,
        check=False
    )
    if result.returncode == 0:
        current_branch = result.stdout.strip()
        # リモートブランチが存在する場合は pull
        result = run_command(
            ["git", "rev-parse", "--verify", f"origin/{current_branch}"],
            cwd=base_dir,
            check=False
        )
        if result.returncode == 0:
            run_command(["git", "pull", "origin", current_branch], cwd=base_dir, check=False)

    # ブランチ名が指定されている場合は既存ブランチをチェックアウト
    # 指定されていない場合は新しいブランチを作成
    branch_name = None
    if len(args) >= 2:
        # 既存ブランチをチェックアウト
        branch_name = args[1]
        print(msg('creating_worktree', worktree_path))
        result = run_command(
            ["git", "worktree", "add", str(worktree_path), branch_name],
            cwd=base_dir,
            check=False
        )
    else:
        # ブランチ名として work_name を使用
        branch_name = work_name

        # ローカルまたはリモートにブランチが既に存在するかチェック
        check_local = run_command(
            ["git", "rev-parse", "--verify", branch_name],
            cwd=base_dir,
            check=False
        )
        check_remote = run_command(
            ["git", "rev-parse", "--verify", f"origin/{branch_name}"],
            cwd=base_dir,
            check=False
        )

        if check_local.returncode == 0 or check_remote.returncode == 0:
            # 既存ブランチを使用
            if check_remote.returncode == 0:
                # リモートブランチが存在する場合
                print(msg('creating_worktree', worktree_path))
                result = run_command(
                    ["git", "worktree", "add", str(worktree_path), f"origin/{branch_name}"],
                    cwd=base_dir,
                    check=False
                )
            else:
                # ローカルブランチのみ存在する場合
                print(msg('creating_worktree', worktree_path))
                result = run_command(
                    ["git", "worktree", "add", str(worktree_path), branch_name],
                    cwd=base_dir,
                    check=False
                )
        else:
            # 新しいブランチを作成
            # デフォルトブランチを探す（origin/main または origin/master）
            result = run_command(
                ["git", "symbolic-ref", "refs/remotes/origin/HEAD", "--short"],
                cwd=base_dir,
                check=False
            )

            if result.returncode == 0 and result.stdout.strip():
                base_branch = result.stdout.strip()
            else:
                # symbolic-ref が失敗した場合は手動でチェック
                result_main = run_command(
                    ["git", "rev-parse", "--verify", "origin/main"],
                    cwd=base_dir,
                    check=False
                )
                result_master = run_command(
                    ["git", "rev-parse", "--verify", "origin/master"],
                    cwd=base_dir,
                    check=False
                )

                if result_main.returncode == 0:
                    base_branch = "origin/main"
                elif result_master.returncode == 0:
                    base_branch = "origin/master"
                else:
                    print(msg('error', msg('default_branch_not_found')), file=sys.stderr)
                    sys.exit(1)

            print(msg('creating_branch', base_branch, work_name))
            result = run_command(
                ["git", "worktree", "add", "-b", work_name, str(worktree_path), base_branch],
                cwd=base_dir,
                check=False
            )

    if result.returncode == 0:
        print(msg('completed_worktree', worktree_path))

        # エイリアスを作成
        if alias_name:
            alias_path = base_dir.parent / alias_name

            # 既存かどうかをチェック
            is_updating = alias_path.is_symlink()

            # 既存のシンボリックリンクを削除
            if alias_path.is_symlink():
                alias_path.unlink()
            elif alias_path.exists():
                # シンボリックリンクではないファイル/ディレクトリが存在
                print(msg('error', f'{alias_name} exists but is not a symlink'), file=sys.stderr)
                # post-add hook を実行
                run_post_add_hook(worktree_path, work_name, base_dir, branch_name)
                sys.exit(0)  # worktree は作成できたので正常終了

            # シンボリックリンクを作成
            alias_path.symlink_to(worktree_path, target_is_directory=True)

            if is_updating:
                print(msg('alias_updated', alias_name, work_name))
            else:
                print(msg('alias_created', alias_name, work_name))

        # post-add hook を実行
        run_post_add_hook(worktree_path, work_name, base_dir, branch_name)
    else:
        # エラーメッセージを表示
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        sys.exit(1)


def get_worktree_info(base_dir: Path) -> list[dict]:
    """worktree の詳細情報を取得"""
    result = run_command(
        ["git", "worktree", "list", "--porcelain"],
        cwd=base_dir
    )

    worktrees = []
    current = {}

    for line in result.stdout.strip().split('\n'):
        if not line:
            if current:
                worktrees.append(current)
                current = {}
            continue

        if line.startswith('worktree '):
            current['path'] = line.split(' ', 1)[1]
        elif line.startswith('HEAD '):
            current['head'] = line.split(' ', 1)[1]
        elif line.startswith('branch '):
            current['branch'] = line.split(' ', 1)[1].replace('refs/heads/', '')
        elif line.startswith('detached'):
            current['branch'] = 'DETACHED'

    if current:
        worktrees.append(current)

    # 各 worktree の詳細情報を取得
    for wt in worktrees:
        path = Path(wt['path'])

        # 作成日時（ディレクトリの作成時刻）
        if path.exists():
            stat_info = path.stat()
            wt['created'] = datetime.fromtimestamp(stat_info.st_ctime)

        # 最終コミット日時
        result = run_command(
            ["git", "log", "-1", "--format=%ct", wt.get('head', 'HEAD')],
            cwd=base_dir,
            check=False
        )
        if result.returncode == 0 and result.stdout.strip():
            wt['last_commit'] = datetime.fromtimestamp(int(result.stdout.strip()))

        # git status（変更があるか）
        result = run_command(
            ["git", "status", "--porcelain"],
            cwd=path,
            check=False
        )
        wt['is_clean'] = result.returncode == 0 and not result.stdout.strip()

    return worktrees


def cmd_list(args: list[str]):
    """wt list - List worktrees"""
    base_dir = find_base_dir()
    if not base_dir:
        print(msg('error', msg('base_not_found')), file=sys.stderr)
        sys.exit(1)

    # --verbose または --sort オプションがある場合は詳細表示
    verbose = '--verbose' in args or '-v' in args
    sort_by = None

    # ソートオプションを取得
    for i, arg in enumerate(args):
        if arg == '--sort' and i + 1 < len(args):
            sort_by = args[i + 1]

    if not verbose and not sort_by:
        # 通常の git worktree list を実行
        result = run_command(["git", "worktree", "list"] + args, cwd=base_dir)
        print(result.stdout, end='')
        return

    # 詳細情報を取得
    worktrees = get_worktree_info(base_dir)

    # ソート
    if sort_by == 'age' or sort_by == 'created':
        worktrees.sort(key=lambda x: x.get('created', datetime.min))
    elif sort_by == 'name':
        worktrees.sort(key=lambda x: Path(x['path']).name)

    # 表示
    if verbose:
        # ヘッダー
        print(f"{msg('worktree_name'):<30} {msg('branch_name'):<25} {msg('created_at'):<20} {msg('last_commit'):<20} {msg('status_label')}")
        print("-" * 110)

        for wt in worktrees:
            name = Path(wt['path']).name
            branch = wt.get('branch', 'N/A')
            created = wt.get('created').strftime('%Y-%m-%d %H:%M') if wt.get('created') else 'N/A'
            last_commit = wt.get('last_commit').strftime('%Y-%m-%d %H:%M') if wt.get('last_commit') else 'N/A'
            status = 'clean' if wt.get('is_clean') else 'modified'

            print(f"{name:<30} {branch:<25} {created:<20} {last_commit:<20} {status}")
    else:
        # 通常表示（ソートのみ）
        for wt in worktrees:
            print(wt['path'])


def cmd_remove(args: list[str]):
    """wt rm/remove <work_name> - Remove a worktree"""
    if len(args) < 1:
        print(msg('usage_rm'), file=sys.stderr)
        sys.exit(1)

    base_dir = find_base_dir()
    if not base_dir:
        print(msg('error', msg('base_not_found')), file=sys.stderr)
        sys.exit(1)

    work_name = args[0]

    # worktree を削除
    print(msg('removing_worktree', work_name))
    result = run_command(
        ["git", "worktree", "remove", work_name],
        cwd=base_dir,
        check=False
    )

    if result.returncode == 0:
        print(msg('completed_remove', work_name))
    else:
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        sys.exit(1)


def cmd_clean(args: list[str]):
    """wt clean - Remove old/unused worktrees"""
    base_dir = find_base_dir()
    if not base_dir:
        print(msg('error', msg('base_not_found')), file=sys.stderr)
        sys.exit(1)

    # オプションを解析
    dry_run = '--dry-run' in args
    clean_all = '--all' in args
    days = None

    for i, arg in enumerate(args):
        if arg == '--days' and i + 1 < len(args):
            try:
                days = int(args[i + 1])
            except ValueError:
                print(msg('error', 'Invalid days value'), file=sys.stderr)
                sys.exit(1)

    # worktree 情報を取得
    worktrees = get_worktree_info(base_dir)

    # エイリアスで使われている worktree を取得
    parent_dir = base_dir.parent
    aliased_worktrees = set()
    for item in parent_dir.iterdir():
        if item.is_symlink() and item.name != '_base':
            target = item.resolve()
            aliased_worktrees.add(target)

    # 削除対象を抽出（_baseは除外）
    targets = []
    now = datetime.now()

    for wt in worktrees:
        path = Path(wt['path'])

        # _base は除外
        if path.name == '_base':
            continue

        # エイリアスで使われている worktree は除外
        if path in aliased_worktrees:
            continue

        # clean状態のものだけが対象
        if not wt.get('is_clean'):
            continue

        # 日数指定がある場合はチェック
        if days is not None:
            created = wt.get('created')
            if created:
                age_days = (now - created).days
                if age_days < days:
                    continue

        targets.append(wt)

    if not targets:
        print(msg('no_clean_targets'))
        return

    # 削除対象を表示
    for wt in targets:
        path = Path(wt['path'])
        created = wt.get('created').strftime('%Y-%m-%d %H:%M') if wt.get('created') else 'N/A'
        print(msg('clean_target', path.name, created))

    if dry_run:
        print(f"\n(--dry-run mode, no changes made)")
        return

    # 確認
    if not clean_all:
        try:
            response = input(msg('clean_confirm', len(targets)))
            if response.lower() not in ['y', 'yes']:
                print("Cancelled.")
                return
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.")
            return

    # 削除実行
    for wt in targets:
        path = Path(wt['path'])
        print(msg('removing_worktree', path.name))
        result = run_command(
            ["git", "worktree", "remove", str(path)],
            cwd=base_dir,
            check=False
        )

        if result.returncode == 0:
            print(msg('completed_remove', path.name))
        else:
            if result.stderr:
                print(result.stderr, file=sys.stderr)


def cmd_alias(args: list[str]):
    """wt alias - Manage worktree aliases"""
    base_dir = find_base_dir()
    if not base_dir:
        print(msg('error', msg('base_not_found')), file=sys.stderr)
        sys.exit(1)

    parent_dir = base_dir.parent

    # --list オプション
    if '--list' in args or len(args) == 0:
        # エイリアス一覧を表示（シンボリックリンクを探す）
        aliases = []
        for item in parent_dir.iterdir():
            if item.is_symlink() and item.name != '_base':
                target = item.resolve()
                aliases.append((item.name, target.name))

        if aliases:
            for alias, target in sorted(aliases):
                print(f"{alias} -> {target}")
        else:
            print("No aliases found.")
        return

    # --remove オプション
    if '--remove' in args:
        if len(args) < 2:
            print(msg('usage_alias'), file=sys.stderr)
            sys.exit(1)

        alias_name = args[args.index('--remove') + 1]
        alias_path = parent_dir / alias_name

        if not alias_path.exists():
            print(msg('error', msg('alias_not_found', alias_name)), file=sys.stderr)
            sys.exit(1)

        if not alias_path.is_symlink():
            print(msg('error', f'{alias_name} is not an alias'), file=sys.stderr)
            sys.exit(1)

        alias_path.unlink()
        print(msg('alias_removed', alias_name))
        return

    # エイリアス作成
    if len(args) < 2:
        print(msg('usage_alias'), file=sys.stderr)
        sys.exit(1)

    alias_name = args[0]
    worktree_name = args[1]

    alias_path = parent_dir / alias_name
    worktree_path = parent_dir / worktree_name

    # worktree が存在するかチェック
    if not worktree_path.exists():
        print(msg('error', f'Worktree not found: {worktree_name}'), file=sys.stderr)
        sys.exit(1)

    # エイリアスがすでに存在する場合は上書き
    if alias_path.exists():
        if alias_path.is_symlink():
            alias_path.unlink()
            alias_path.symlink_to(worktree_path, target_is_directory=True)
            print(msg('alias_updated', alias_name, worktree_name))
        else:
            print(msg('error', f'{alias_name} exists but is not a symlink'), file=sys.stderr)
            sys.exit(1)
    else:
        # シンボリックリンクを作成
        alias_path.symlink_to(worktree_path, target_is_directory=True)
        print(msg('alias_created', alias_name, worktree_name))


def cmd_status(args: list[str]):
    """wt status - Show status of all worktrees"""
    base_dir = find_base_dir()
    if not base_dir:
        print(msg('error', msg('base_not_found')), file=sys.stderr)
        sys.exit(1)

    # オプション
    show_dirty_only = '--dirty' in args
    short = '--short' in args

    worktrees = get_worktree_info(base_dir)

    for wt in worktrees:
        path = Path(wt['path'])

        # dirty only モードの場合、clean なものはスキップ
        if show_dirty_only and wt.get('is_clean'):
            continue

        # git status を取得
        result = run_command(
            ["git", "status", "--short" if short else "--short"],
            cwd=path,
            check=False
        )

        status_output = result.stdout.strip()

        # ヘッダー
        print(f"\n{'='*60}")
        print(f"Worktree: {path.name}")
        print(f"Branch: {wt.get('branch', 'N/A')}")
        print(f"Path: {path}")
        print(f"{'='*60}")

        if status_output:
            print(status_output)
        else:
            print("(clean - no changes)")


def cmd_passthrough(args: list[str]):
    """Passthrough other git worktree commands"""
    base_dir = find_base_dir()
    if not base_dir:
        print(msg('error', msg('base_not_found')), file=sys.stderr)
        sys.exit(1)

    result = run_command(["git", "worktree"] + args, cwd=base_dir, check=False)
    print(result.stdout, end='')
    if result.stderr:
        print(result.stderr, end='', file=sys.stderr)
    sys.exit(result.returncode)


def show_help():
    """Show help message"""
    if is_japanese():
        print("easy-worktree - Git worktree を簡単に管理するための CLI ツール")
        print()
        print("使用方法:")
        print("  wt <command> [options]")
        print()
        print("コマンド:")
        print("  clone <repository_url>                   - リポジトリをクローン")
        print("  init                                      - 既存リポジトリを WT_<repo>/_base/ に移動")
        print("  add <作業名> [<base_branch>] [--alias <名前>] - worktree を追加（デフォルト: 新規ブランチ作成）")
        print("  list [--verbose] [--sort age|name] - worktree 一覧を表示")
        print("  rm <作業名>                         - worktree を削除")
        print("  remove <作業名>                     - worktree を削除")
        print("  clean [--dry-run] [--days N]       - 未使用の worktree を削除")
        print("  alias <名前> <worktree>            - worktree のエイリアスを作成/更新")
        print("  alias --list                        - エイリアス一覧を表示")
        print("  alias --remove <名前>              - エイリアスを削除")
        print("  status [--dirty] [--short]         - 全 worktree の状態を表示")
        print("  <git-worktree-command>             - その他の git worktree コマンド")
        print()
        print("オプション:")
        print("  -h, --help     - このヘルプメッセージを表示")
        print("  -v, --version  - バージョン情報を表示")
    else:
        print("easy-worktree - Simple CLI tool for managing Git worktrees")
        print()
        print("Usage:")
        print("  wt <command> [options]")
        print()
        print("Commands:")
        print("  clone <repository_url>                       - Clone a repository")
        print("  init                                          - Move existing repo to WT_<repo>/_base/")
        print("  add <work_name> [<base_branch>] [--alias <name>] - Add a worktree (default: create new branch)")
        print("  list [--verbose] [--sort age|name]  - List worktrees")
        print("  rm <work_name>                       - Remove a worktree")
        print("  remove <work_name>                   - Remove a worktree")
        print("  clean [--dry-run] [--days N]        - Remove unused worktrees")
        print("  alias <name> <worktree>             - Create or update an alias for a worktree")
        print("  alias --list                         - List aliases")
        print("  alias --remove <name>               - Remove an alias")
        print("  status [--dirty] [--short]          - Show status of all worktrees")
        print("  <git-worktree-command>              - Other git worktree commands")
        print()
        print("Options:")
        print("  -h, --help     - Show this help message")
        print("  -v, --version  - Show version information")


def show_version():
    """Show version information"""
    print("easy-worktree version 0.0.7")


def main():
    """メインエントリポイント"""
    # ヘルプとバージョンのオプションは _base/ なしでも動作する
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    # -h, --help オプション
    if command in ["-h", "--help"]:
        show_help()
        sys.exit(0)

    # -v, --version オプション
    if command in ["-v", "--version"]:
        show_version()
        sys.exit(0)

    if command == "clone":
        cmd_clone(args)
    elif command == "init":
        cmd_init(args)
    elif command == "add":
        cmd_add(args)
    elif command == "list":
        cmd_list(args)
    elif command in ["rm", "remove"]:
        cmd_remove(args)
    elif command == "clean":
        cmd_clean(args)
    elif command == "alias":
        cmd_alias(args)
    elif command == "status":
        cmd_status(args)
    else:
        # その他のコマンドは git worktree にパススルー
        cmd_passthrough([command] + args)


if __name__ == "__main__":
    main()
