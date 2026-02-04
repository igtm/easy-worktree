#!/usr/bin/env python3
"""
Git worktree を簡単に管理するための CLI ツール
"""

import os
import subprocess
import shutil
import sys
from pathlib import Path
import re
from datetime import datetime, timezone
import toml


# 言語判定
def is_japanese() -> bool:
    """LANG環境変数から日本語かどうかを判定"""
    lang = os.environ.get("LANG", "")
    return "ja" in lang.lower()


# メッセージ辞書
MESSAGES = {
    "error": {"en": "Error: {}", "ja": "エラー: {}"},
    "usage": {
        "en": "Usage: wt clone <repository_url>",
        "ja": "使用方法: wt clone <repository_url>",
    },
    "usage_add": {
        "en": "Usage: wt add (ad) <work_name> [<base_branch>] [--no-setup] [--select]",
        "ja": "使用方法: wt add (ad) <作業名> [<base_branch>] [--no-setup] [--select]",
    },
    "usage_rm": {"en": "Usage: wt rm <work_name>", "ja": "使用方法: wt rm <作業名>"},
    "base_not_found": {
        "en": "Main repository directory not found",
        "ja": "メインリポジトリのディレクトリが見つかりません",
    },
    "run_in_wt_dir": {
        "en": "Please run inside WT_<repository_name>/ directory",
        "ja": "WT_<repository_name>/ ディレクトリ内で実行してください",
    },
    "already_exists": {"en": "{} already exists", "ja": "{} はすでに存在します"},
    "cloning": {"en": "Cloning: {} -> {}", "ja": "クローン中: {} -> {}"},
    "completed_clone": {
        "en": "Completed: cloned to {}",
        "ja": "完了: {} にクローンしました",
    },
    "not_git_repo": {
        "en": "Current directory is not a git repository",
        "ja": "現在のディレクトリは git リポジトリではありません",
    },
    "run_at_root": {
        "en": "Please run at repository root directory {}",
        "ja": "リポジトリのルートディレクトリ {} で実行してください",
    },
    "creating_dir": {"en": "Creating {}...", "ja": "{} を作成中..."},
    "moving": {"en": "Moving {} -> {}...", "ja": "{} -> {} に移動中..."},
    "completed_move": {"en": "Completed: moved to {}", "ja": "完了: {} に移動しました"},
    "use_wt_from": {
        "en": "Use wt command from {} from next time",
        "ja": "次回から {} で wt コマンドを使用してください",
    },
    "fetching": {
        "en": "Fetching latest information from remote...",
        "ja": "リモートから最新情報を取得中...",
    },
    "creating_worktree": {"en": "Creating worktree: {}", "ja": "worktree を作成中: {}"},
    "completed_worktree": {
        "en": "Completed: created worktree at {}",
        "ja": "完了: {} に worktree を作成しました",
    },
    "removing_worktree": {"en": "Removing worktree: {}", "ja": "worktree を削除中: {}"},
    "completed_remove": {
        "en": "Completed: removed {}",
        "ja": "完了: {} を削除しました",
    },
    "creating_branch": {
        "en": "Creating new branch '{}' from '{}'",
        "ja": "ブランチ '{}' を '{}' から作成しています",
    },
    "default_branch_not_found": {
        "en": "Could not find default branch (main/master)",
        "ja": "デフォルトブランチ (main/master) が見つかりません",
    },
    "running_hook": {
        "en": "Running post-add hook: {}",
        "ja": "post-add hook を実行中: {}",
    },
    "hook_not_executable": {
        "en": "Warning: hook is not executable: {}",
        "ja": "警告: hook が実行可能ではありません: {}",
    },
    "hook_failed": {
        "en": "Warning: hook exited with code {}",
        "ja": "警告: hook が終了コード {} で終了しました",
    },
    "usage_clean": {
        "en": "Usage: wt clean (cl) [--days N] [--merged] [--closed] [--all]",
        "ja": "使用方法: wt clean (cl) [--days N] [--merged] [--closed] [--all]",
    },
    "alias_updated": {
        "en": "Updated alias: {} -> {}",
        "ja": "エイリアスを更新しました: {} -> {}",
    },
    "no_clean_targets": {
        "en": "No worktrees to clean",
        "ja": "クリーンアップ対象の worktree がありません",
    },
    "clean_target": {
        "en": "Will remove: {} (created: {}, clean)",
        "ja": "削除対象: {} (作成日時: {}, 変更なし)",
    },
    "clean_confirm": {
        "en": "Remove {} worktree(s)? [y/N]: ",
        "ja": "{} 個の worktree を削除しますか？ [y/N]: ",
    },
    "alias_removed": {"en": "Removed alias: {}", "ja": "エイリアスを削除しました: {}"},
    "alias_not_found": {
        "en": "Alias not found: {}",
        "ja": "エイリアスが見つかりません: {}",
    },
    "worktree_name": {"en": "Worktree", "ja": "Worktree"},
    "branch_name": {"en": "Branch", "ja": "ブランチ"},
    "created_at": {"en": "Created", "ja": "作成日時"},
    "last_commit": {"en": "Last Commit", "ja": "最終コミット"},
    "status_label": {"en": "Status", "ja": "状態"},
    "changes_label": {"en": "Changes", "ja": "変更"},
    "syncing": {"en": "Syncing: {} -> {}", "ja": "同期中: {} -> {}"},
    "completed_sync": {
        "en": "Completed sync of {} files",
        "ja": "{} 個のファイルを同期しました",
    },
    "usage_pr": {
        "en": "Usage: wt pr add <number>",
        "ja": "使用方法: wt pr add <number>",
    },
    "usage_setup": {
        "en": "Usage: wt setup (su)",
        "ja": "使用方法: wt setup (su)",
    },
    "usage_stash": {
        "en": "Usage: wt stash (st) <work_name> [<base_branch>]",
        "ja": "使用方法: wt stash (st) <work_name> [<base_branch>]",
    },
    "stashing_changes": {
        "en": "Stashing local changes...",
        "ja": "ローカルの変更をスタッシュ中...",
    },
    "popping_stash": {
        "en": "Moving changes to new worktree...",
        "ja": "変更を新しい worktree に移動中...",
    },
    "nothing_to_stash": {
        "en": "No local changes to stash.",
        "ja": "スタッシュする変更がありません",
    },
    "select_switched": {
        "en": "Switched worktree to: {}",
        "ja": "作業ディレクトリを切り替えました: {}",
    },
    "select_not_found": {
        "en": "Worktree not found: {}",
        "ja": "worktree が見つかりません: {}",
    },
    "select_no_last": {
        "en": "No previous selection found",
        "ja": "以前の選択が見つかりません",
    },
    "setting_up": {"en": "Setting up: {} -> {}", "ja": "セットアップ中: {} -> {}"},
    "completed_setup": {
        "en": "Completed setup of {} files",
        "ja": "{} 個のファイルをセットアップしました",
    },
    "suggest_setup": {
        "en": "Some setup files are missing. Run 'wt setup' to initialize this worktree.",
        "ja": "一部のセットアップファイルが不足しています。'wt setup' を実行して初期化してください。",
    },
    "nesting_error": {
        "en": "Error: Already in a wt subshell ({}). Please 'exit' before switching.",
        "ja": "エラー: すでに wt のサブシェル ({}) 内にいます。切り替える前に 'exit' してください。",
    },
    "jump_instruction": {
        "en": "Jumping to '{}' ({}). Type 'exit' or Ctrl-D to return.",
        "ja": "'{}' ({}) にジャンプします。戻るには 'exit' または Ctrl-D を入力してください。",
    },
}


def msg(key: str, *args) -> str:
    """言語に応じたメッセージを取得"""
    lang = "ja" if is_japanese() else "en"
    message = MESSAGES.get(key, {}).get(lang, key)
    if args:
        return message.format(*args)
    return message


def run_command(
    cmd: list[str], cwd: Path = None, check: bool = True
) -> subprocess.CompletedProcess:
    """コマンドを実行"""
    try:
        # print(f"DEBUG: Running command: {cmd} cwd={cwd}", file=sys.stderr)
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        print(msg("error", e.stderr), file=sys.stderr)
        sys.exit(1)


def get_repository_name(url: str) -> str:
    """リポジトリ URL から名前を抽出"""
    # URL から .git を削除して最後の部分を取得
    match = re.search(r"/([^/]+?)(?:\.git)?$", url)
    if match:
        name = match.group(1)
        # サービス名などが含まれる場合のクリーンアップ
        return name.split(":")[-1]
    # ローカルパスの場合
    return Path(url).stem


def load_config(base_dir: Path) -> dict:
    """設定ファイルを読み込む"""
    config_file = base_dir / ".wt" / "config.toml"
    local_config_file = base_dir / ".wt" / "config.local.toml"
    
    default_config = {
        "worktrees_dir": ".worktrees",
        "setup_files": [".env"],
    }

    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                user_config = toml.load(f)
                default_config.update(user_config)
        except Exception as e:
            print(msg("error", f"Failed to load config: {e}"), file=sys.stderr)

    if local_config_file.exists():
        try:
            with open(local_config_file, "r", encoding="utf-8") as f:
                local_config = toml.load(f)
                default_config.update(local_config)
        except Exception as e:
            print(msg("error", f"Failed to load local config: {e}"), file=sys.stderr)

    return default_config


def save_config(base_dir: Path, config: dict):
    """設定ファイルを保存する"""
    wt_dir = base_dir / ".wt"
    wt_dir.mkdir(exist_ok=True)
    config_file = wt_dir / "config.toml"

    with open(config_file, "w", encoding="utf-8") as f:
        toml.dump(config, f)


def create_hook_template(base_dir: Path):
    """post-add hook のテンプレートと .wt/ 内のファイルを作成"""
    wt_dir = base_dir / ".wt"

    # .wt ディレクトリを作成
    wt_dir.mkdir(exist_ok=True)

    # config.toml
    config_file = wt_dir / "config.toml"
    if not config_file.exists():
        save_config(
            base_dir,
            {
                "worktrees_dir": ".worktrees",
                "setup_files": [".env"],
            },
        )

    # .gitignore (repository root) に worktrees_dir を追加
    config = load_config(base_dir)
    worktrees_dir_name = config.get("worktrees_dir", ".worktrees")
    root_gitignore = base_dir / ".gitignore"

    entries = [f"{worktrees_dir_name}/"]

    if root_gitignore.exists():
        content = root_gitignore.read_text(encoding="utf-8")
        updated = False
        for entry in entries:
            if entry not in content:
                if content and not content.endswith("\n"):
                    content += "\n"
                content += f"{entry}\n"
                updated = True
        if updated:
            root_gitignore.write_text(content, encoding="utf-8")
    else:
        root_gitignore.write_text("\n".join(entries) + "\n", encoding="utf-8")

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
#   WT_BASE_DIR       - Path to the main repository directory
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
    
    ignores = ["post-add.local", "config.local.toml", "last_selection"]
    
    if not gitignore_file.exists():
        gitignore_content = "\n".join(ignores) + "\n"
        gitignore_file.write_text(gitignore_content)
    else:
        content = gitignore_file.read_text()
        updated = False
        for ignore in ignores:
            if ignore not in content:
                if content and not content.endswith("\n"):
                    content += "\n"
                content += f"{ignore}\n"
                updated = True
        if updated:
            gitignore_file.write_text(content)


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

# セットアップ（フック実行など）をスキップして作成
wt add <作業名> --skip-setup

# 既存ブランチから worktree を作成
wt add <作業名> <既存ブランチ名>

# worktree 一覧を表示
wt list

# worktree を削除
wt rm <作業名>
```

詳細は https://github.com/igtm/easy-worktree を参照してください。

## 設定 (config.toml)

`.wt/config.toml` で以下の設定が可能です。

```toml
worktrees_dir = ".worktrees"   # worktree を作成するディレクトリ名
setup_files = [".env"]          # 自動セットアップでコピーするファイル一覧
```

### ローカル設定 (config.local.toml)

`config.local.toml` を作成すると、設定をローカルでのみ上書きできます。このファイルは自動的に `.gitignore` に追加され、リポジトリにはコミットされません。

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
- `WT_BASE_DIR`: メインリポジトリディレクトリのパス
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

# Skip setup (hook execution etc)
wt add <work_name> --skip-setup

# Create a worktree from an existing branch
wt add <work_name> <existing_branch_name>

# List worktrees
wt list

# Remove a worktree
wt remove <work_name>
```

For more details, see https://github.com/igtm/easy-worktree

## Configuration (config.toml)

You can customize behavior in `.wt/config.toml`:

```toml
worktrees_dir = ".worktrees"   # Directory where worktrees are created
setup_files = [".env"]          # Files to auto-copy during setup
```

### Local Configuration (config.local.toml)

You can create `config.local.toml` to override settings locally. This file is automatically added to `.gitignore` and serves as a local override that won't be committed.

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
- `WT_BASE_DIR`: Path to the main repository directory
- `WT_BRANCH`: Branch name
- `WT_ACTION`: Action name (always "add")

### About post-add.local

`post-add.local` is for personal local hooks. This file is included in `.gitignore`, so it won't be committed to the repository. Use `post-add` for hooks you want to share with the team, and `post-add.local` for your personal settings.

`post-add.local` is automatically executed only when `post-add` exists.
"""
        readme_file.write_text(readme_content)


def find_base_dir() -> Path | None:
    """現在のディレクトリまたは親ディレクトリから git root を探す"""
    # ワークツリーでもメインリポジトリのルートを見つけられるように
    try:
        # --git-common-dir はメインリポジトリの .git ディレクトリを返す
        result = run_command(["git", "rev-parse", "--git-common-dir"], check=False)
        if result.returncode == 0:
            git_common_dir = Path(result.stdout.strip())
            if not git_common_dir.is_absolute():
                # 相対パスの場合は CWD からのパス
                git_common_dir = (Path.cwd() / git_common_dir).resolve()
            
            # .git ディレクトリの親がベースディレクトリ
            if git_common_dir.name == ".git":
                return git_common_dir.parent
            else:
                # ベアリポジトリなどの場合はそのディレクトリ自体
                return git_common_dir
    except Exception:
        pass

    try:
        result = run_command(["git", "rev-parse", "--show-toplevel"], check=False)
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except Exception:
        pass

    # fallback
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / ".git").exists():
            return parent

    return None


def cmd_clone(args: list[str]):
    """wt clone <repository_url> [dest_dir] - Clone a repository"""
    if len(args) < 1:
        print(msg("usage"), file=sys.stderr)
        sys.exit(1)

    repo_url = args[0]
    repo_name = get_repository_name(repo_url)

    dest_dir = Path(args[1]) if len(args) > 1 else Path(repo_name)

    if dest_dir.exists():
        print(msg("error", msg("already_exists", dest_dir)), file=sys.stderr)
        sys.exit(1)

    print(msg("cloning", repo_url, dest_dir), file=sys.stderr)
    run_command(["git", "clone", repo_url, str(dest_dir)])
    print(msg("completed_clone", dest_dir), file=sys.stderr)

    # post-add hook と設定ファイルを作成
    create_hook_template(dest_dir)


def cmd_init(args: list[str]):
    """wt init - Initialize easy-worktree in current git repository"""
    current_dir = Path.cwd()

    # 現在のディレクトリが git リポジトリか確認
    result = run_command(
        ["git", "rev-parse", "--show-toplevel"], cwd=current_dir, check=False
    )

    if result.returncode != 0:
        print(msg("error", msg("not_git_repo")), file=sys.stderr)
        sys.exit(1)

    git_root = Path(result.stdout.strip())

    # post-add hook と設定ファイルを作成
    create_hook_template(git_root)


def get_default_branch(base_dir: Path) -> str:
    """Detect default branch (main/master)"""
    # 1. Try origin/HEAD
    result = run_command(
        ["git", "rev-parse", "--abbrev-ref", "origin/HEAD"], cwd=base_dir, check=False
    )
    if result.returncode == 0:
        return result.stdout.strip().replace("origin/", "")

    # 2. Try common names
    for b in ["main", "master"]:
        if (
            run_command(
                ["git", "rev-parse", "--verify", b], cwd=base_dir, check=False
            ).returncode
            == 0
        ):
            return b

    # 3. Fallback to current HEAD
    result = run_command(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=base_dir, check=False
    )
    if result.returncode == 0:
        return result.stdout.strip()

    return None


def run_post_add_hook(
    worktree_path: Path, work_name: str, base_dir: Path, branch: str = None
):
    """worktree 作成後の hook を実行"""
    # .wt/post-add を探す
    hook_path = base_dir / ".wt" / "post-add"

    if not hook_path.exists() or not hook_path.is_file():
        return  # hook がなければ何もしない

    if not os.access(hook_path, os.X_OK):
        print(msg("hook_not_executable", hook_path), file=sys.stderr)
        return

    # 環境変数を設定
    env = os.environ.copy()
    env.update(
        {
            "WT_WORKTREE_PATH": str(worktree_path),
            "WT_WORKTREE_NAME": work_name,
            "WT_BASE_DIR": str(base_dir),
            "WT_BRANCH": branch or work_name,
            "WT_ACTION": "add",
        }
    )

    print(msg("running_hook", hook_path), file=sys.stderr)
    try:
        result = subprocess.run(
            [str(hook_path)],
            cwd=worktree_path,  # worktree 内で実行
            env=env,
            stdout=sys.stderr,  # stdout を stderr にリダイレクト (cd 連携のため)
            stderr=sys.stderr,
            check=False,
        )

        if result.returncode != 0:
            print(msg("hook_failed", result.returncode), file=sys.stderr)
    except Exception as e:
        print(msg("error", str(e)), file=sys.stderr)


def add_worktree(
    work_name: str,
    branch_to_use: str = None,
    new_branch_base: str = None,
    base_dir: Path = None,
    skip_setup: bool = False,
) -> Path:
    """Core logic to add a worktree, reused by cmd_add and cmd_stash"""
    if not base_dir:
        base_dir = find_base_dir()
    if not base_dir:
        print(msg("error", msg("base_not_found")), file=sys.stderr)
        print(msg("run_in_wt_dir"), file=sys.stderr)
        sys.exit(1)

    # settings loading
    config = load_config(base_dir)
    worktrees_dir_name = config.get("worktrees_dir", ".worktrees")
    worktrees_dir = base_dir / worktrees_dir_name
    worktrees_dir.mkdir(exist_ok=True)

    # worktree path decision
    worktree_path = worktrees_dir / work_name

    if worktree_path.exists():
        print(msg("error", msg("already_exists", worktree_path)), file=sys.stderr)
        sys.exit(1)

    # update branch
    print(msg("fetching"), file=sys.stderr)
    run_command(["git", "fetch", "--all"], cwd=base_dir)

    # main update to base branch latest
    result = run_command(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=base_dir, check=False
    )
    if result.returncode == 0:
        current_branch = result.stdout.strip()
        result = run_command(
            ["git", "rev-parse", "--verify", f"origin/{current_branch}"],
            cwd=base_dir,
            check=False,
        )
        if result.returncode == 0:
            run_command(
                ["git", "pull", "origin", current_branch], cwd=base_dir, check=False
            )

    # create branch / checkout
    final_branch_name = None
    if new_branch_base:
        # create new branch from base
        final_branch_name = work_name
        print(
            msg("creating_branch", final_branch_name, new_branch_base), file=sys.stderr
        )
        result = run_command(
            [
                "git",
                "worktree",
                "add",
                "-b",
                final_branch_name,
                str(worktree_path),
                new_branch_base,
            ],
            cwd=base_dir,
            check=False,
        )
    elif branch_to_use:
        # checkout specified branch
        final_branch_name = branch_to_use
        print(msg("creating_worktree", worktree_path), file=sys.stderr)
        result = run_command(
            ["git", "worktree", "add", str(worktree_path), final_branch_name],
            cwd=base_dir,
            check=False,
        )
    else:
        # auto detect
        # use work_name as branch name
        final_branch_name = work_name

        check_local = run_command(
            ["git", "rev-parse", "--verify", final_branch_name],
            cwd=base_dir,
            check=False,
        )
        check_remote = run_command(
            ["git", "rev-parse", "--verify", f"origin/{final_branch_name}"],
            cwd=base_dir,
            check=False,
        )

        if check_local.returncode == 0 or check_remote.returncode == 0:
            if check_remote.returncode == 0:
                print(msg("creating_worktree", worktree_path), file=sys.stderr)
                result = run_command(
                    [
                        "git",
                        "worktree",
                        "add",
                        str(worktree_path),
                        f"origin/{final_branch_name}",
                    ],
                    cwd=base_dir,
                    check=False,
                )
            else:
                print(msg("creating_worktree", worktree_path), file=sys.stderr)
                result = run_command(
                    ["git", "worktree", "add", str(worktree_path), final_branch_name],
                    cwd=base_dir,
                    check=False,
                )
        else:
            # find default branch
            result_sym = run_command(
                ["git", "symbolic-ref", "refs/remotes/origin/HEAD", "--short"],
                cwd=base_dir,
                check=False,
            )

            detected_base = None
            if result_sym.returncode == 0 and result_sym.stdout.strip():
                detected_base = result_sym.stdout.strip()
            else:
                # search in order: remote/local main/master
                for b in ["origin/main", "origin/master", "main", "master"]:
                    if (
                        run_command(
                            ["git", "rev-parse", "--verify", b],
                            cwd=base_dir,
                            check=False,
                        ).returncode
                        == 0
                    ):
                        detected_base = b
                        break

                if not detected_base:
                    # fallback to current branch
                    res_curr = run_command(
                        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                        cwd=base_dir,
                        check=False,
                    )
                    if res_curr.returncode == 0:
                        detected_base = res_curr.stdout.strip()

                if not detected_base:
                    print(
                        msg("error", msg("default_branch_not_found")), file=sys.stderr
                    )
                    sys.exit(1)

            print(
                msg("creating_branch", final_branch_name, detected_base),
                file=sys.stderr,
            )
            result = run_command(
                [
                    "git",
                    "worktree",
                    "add",
                    "-b",
                    final_branch_name,
                    str(worktree_path),
                    detected_base,
                ],
                cwd=base_dir,
                check=False,
            )

    if result.returncode == 0:
        if not skip_setup:
            # automatic sync
            setup_files = config.get("setup_files", [])
            for file_name in setup_files:
                src = base_dir / file_name
                dst = worktree_path / file_name
                if src.exists():
                    print(msg("setting_up", src, dst), file=sys.stderr)
                    import shutil

                    shutil.copy2(src, dst)

            # post-add hook
            run_post_add_hook(worktree_path, work_name, base_dir, final_branch_name)
        
        return worktree_path
    else:
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        sys.exit(1)


def cmd_add(args: list[str]):
    """wt add <work_name> [<base_branch>] [--no-setup] [--select] - Add a worktree"""
    if len(args) < 1:
        print(msg("usage_add"), file=sys.stderr)
        sys.exit(1)

    # parse options
    clean_args = []
    skip_setup = False
    select = False
    
    for arg in args:
        if arg in ["--skip-setup", "--no-setup"]:
            skip_setup = True
        elif arg == "--select":
            select = True
        else:
            clean_args.append(arg)
            
    if not clean_args:
        print(msg("usage_add"), file=sys.stderr)
        sys.exit(1)

    work_name = clean_args[0]
    branch_to_use = clean_args[1] if len(clean_args) >= 2 else None

    base_dir = find_base_dir()
    wt_path = add_worktree(work_name, branch_to_use=branch_to_use, skip_setup=skip_setup, base_dir=base_dir)

    if select and wt_path:
        wt_dir = base_dir / ".wt"
        # Ensure .wt directory and its management files exists
        create_hook_template(base_dir)
        last_sel_file = wt_dir / "last_selection"
        
        # Get current selection name
        current_sel = os.environ.get("WT_SESSION_NAME")
        if not current_sel:
            cwd = Path.cwd().resolve()
            worktrees = get_worktree_info(base_dir)
            resolved_base = base_dir.resolve()
            for wt in worktrees:
                p = Path(wt["path"]).resolve()
                if cwd == p or cwd.is_relative_to(p):
                    current_sel = "main" if p == resolved_base else p.name
                    break
        
        switch_selection(work_name, base_dir, current_sel, last_sel_file)


def cmd_stash(args: list[str]):
    """wt stash <work_name> [<base_branch>] - Stash changes and move to new worktree"""
    if len(args) < 1:
        print(msg("usage_stash"), file=sys.stderr)
        sys.exit(1)

    base_dir = find_base_dir()
    if not base_dir:
        print(msg("error", msg("base_not_found")), file=sys.stderr)
        sys.exit(1)

    # 変更があるかチェック
    result = run_command(["git", "status", "--porcelain"], cwd=base_dir, check=False)
    has_changes = bool(result.stdout.strip())

    if has_changes:
        print(msg("stashing_changes"), file=sys.stderr)
        # stash する
        # -u (include untracked)
        run_command(
            ["git", "stash", "push", "-u", "-m", f"easy-worktree stash for {args[0]}"],
            cwd=base_dir,
        )
    else:
        print(msg("nothing_to_stash"), file=sys.stderr)

    # 新しい worktree を作成
    work_name = args[0]

    # base_branch が指定されていない場合は現在のブランチをベースにする
    # 指定されている場合はそれをベースにする
    new_branch_base = args[1] if len(args) >= 2 else None
    if not new_branch_base:
        res = run_command(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=base_dir, check=False
        )
        if res.returncode == 0:
            new_branch_base = res.stdout.strip()

    # aliasはサポートしないでおく（とりあえずシンプルに）
    # wt stash は常に新しいブランチを作成する振る舞いにする
    wt_path = add_worktree(
        work_name, new_branch_base=new_branch_base, base_dir=base_dir
    )

    if has_changes and wt_path:
        print(msg("popping_stash"), file=sys.stderr)
        # 新しい worktree で stash pop
        run_command(["git", "stash", "pop"], cwd=wt_path)


def cmd_pr(args: list[str]):
    """wt pr <add|co> <number> - Pull Request management"""
    if len(args) < 2:
        print(msg("usage_pr"), file=sys.stderr)
        sys.exit(1)

    subcommand = args[0]
    pr_number = args[1]

    # Ensure pr_number is a digit
    if not pr_number.isdigit():
        print(msg("error", f"PR number must be a digit: {pr_number}"), file=sys.stderr)
        sys.exit(1)

    base_dir = find_base_dir()
    if not base_dir:
        print(msg("error", msg("base_not_found")), file=sys.stderr)
        sys.exit(1)

    if subcommand == "add":
        # Check if gh command exists
        if shutil.which("gh") is None:
            print(
                msg("error", "GitHub CLI (gh) is required for this command"),
                file=sys.stderr,
            )
            sys.exit(1)

        print(f"Verifying PR #{pr_number}...", file=sys.stderr)
        # Verify PR exists using gh
        verify_cmd = ["gh", "pr", "view", pr_number, "--json", "number"]
        result = run_command(verify_cmd, cwd=base_dir, check=False)
        if result.returncode != 0:
            print(
                msg("error", f"PR #{pr_number} not found (or access denied)"),
                file=sys.stderr,
            )
            sys.exit(1)

        branch_name = f"pr-{pr_number}"
        worktree_name = f"pr@{pr_number}"

        print(f"Fetching PR #{pr_number} contents...", file=sys.stderr)
        # Fetch PR head to a local branch
        # git fetch origin pull/ID/head:local-branch
        fetch_cmd = ["git", "fetch", "origin", f"pull/{pr_number}/head:{branch_name}"]
        # We might want to handle case where origin doesn't exist or pull ref is different,
        # but origin pull/ID/head is standard for GitHub.
        run_command(fetch_cmd, cwd=base_dir)

        print(f"Creating worktree {worktree_name}...", file=sys.stderr)
        add_worktree(worktree_name, branch_to_use=branch_name, base_dir=base_dir)

    elif subcommand == "co":
        # Just a shortcut for checkout pr@<number>
        cmd_checkout([f"pr@{pr_number}"])
    else:
        print(msg("usage_pr"), file=sys.stderr)
        sys.exit(1)


def get_worktree_info(base_dir: Path) -> list[dict]:
    """worktree の詳細情報を取得"""
    result = run_command(["git", "worktree", "list", "--porcelain"], cwd=base_dir)

    worktrees = []
    current = {}

    for line in result.stdout.strip().split("\n"):
        if not line:
            if current:
                worktrees.append(current)
                current = {}
            continue

        if line.startswith("worktree "):
            current["path"] = line.split(" ", 1)[1]
        elif line.startswith("HEAD "):
            current["head"] = line.split(" ", 1)[1]
        elif line.startswith("branch "):
            current["branch"] = line.split(" ", 1)[1].replace("refs/heads/", "")
        elif line.startswith("detached"):
            current["branch"] = "DETACHED"

    if current:
        worktrees.append(current)

    # 各 worktree の詳細情報を取得
    for wt in worktrees:
        path = Path(wt["path"])

        # 作成日時（ディレクトリの作成時刻）
        if path.exists():
            stat_info = path.stat()
            wt["created"] = datetime.fromtimestamp(stat_info.st_ctime)

        # 最終コミット日時
        result = run_command(
            ["git", "log", "-1", "--format=%ct", wt.get("head", "HEAD")],
            cwd=base_dir,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            wt["last_commit"] = datetime.fromtimestamp(int(result.stdout.strip()))

        # git status（変更があるか）
        result = run_command(["git", "status", "--porcelain"], cwd=path, check=False)
        wt["is_clean"] = result.returncode == 0 and not result.stdout.strip()
        wt["has_untracked"] = "??" in result.stdout

        # Diff stats取得
        result_diff = run_command(
            ["git", "diff", "HEAD", "--shortstat"], cwd=path, check=False
        )

        insertions = 0
        deletions = 0
        if result_diff.returncode == 0 and result_diff.stdout.strip():
            out = result_diff.stdout.strip()
            m_plus = re.search(r"(\d+) insertion", out)
            m_minus = re.search(r"(\d+) deletion", out)
            if m_plus:
                insertions = int(m_plus.group(1))
            if m_minus:
                deletions = int(m_minus.group(1))

        wt["insertions"] = insertions
        wt["deletions"] = deletions

    return worktrees

    if result.returncode == 0:
        return result.stdout.strip()
    return ""


def get_pr_info(branch: str, cwd: Path = None) -> str:
    """Get rich GitHub PR information for the branch"""
    if not branch or branch == "HEAD" or branch == "DETACHED":
        return ""

    # Check if gh command exists
    if shutil.which("gh") is None:
        return ""

    import json

    cmd = [
        "gh",
        "pr",
        "list",
        "--head",
        branch,
        "--state",
        "all",
        "--json",
        "state,isDraft,url,createdAt,number",
    ]
    result = run_command(cmd, cwd=cwd, check=False)

    if result.returncode != 0 or not result.stdout.strip():
        return ""

    try:
        prs = json.loads(result.stdout)
        if not prs:
            return ""

        pr = prs[0]
        state = pr["state"]
        is_draft = pr["isDraft"]
        url = pr["url"]
        created_at_str = pr["createdAt"]
        number = pr["number"]

        # Parse created_at
        # ISO format: 2024-03-20T12:00:00Z
        try:
            # Localize to local timezone
            dt_aware = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            dt_local = dt_aware.astimezone().replace(tzinfo=None)
            rel_time = get_relative_time(dt_local)
        except Exception:
            rel_time = "N/A"

        # Symbols and Colors
        GREEN = "\033[32m"
        GRAY = "\033[90m"
        MAGENTA = "\033[35m"
        RED = "\033[31m"
        RESET = "\033[0m"

        if is_draft:
            symbol = f"{GRAY}◌{RESET}"
        elif state == "OPEN":
            symbol = f"{GREEN}●{RESET}"
        elif state == "MERGED":
            symbol = f"{MAGENTA}✔{RESET}"
        else:  # CLOSED
            symbol = f"{RED}✘{RESET}"

        # Hyperlink for #NUMBER
        # ANSI sequence for hyperlink: ESC ] 8 ; ; URL ESC \ TEXT ESC ] 8 ; ; ESC \
        link_start = f"\x1b]8;;{url}\x1b\\"
        link_end = "\x1b]8;;\x1b\\"

        return f"{symbol} {link_start}#{number}{link_end} ({rel_time})"

    except Exception:
        return ""


def get_relative_time(dt: datetime) -> str:
    """Get relative time string"""
    if not dt:
        return "N/A"

    now = datetime.now()
    diff = now - dt

    seconds = diff.total_seconds()
    days = diff.days

    if days < 0:
        return "just now"

    if days == 0:
        if seconds < 60:
            return "just now"
        if seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes}m ago"
        hours = int(seconds / 3600)
        return f"{hours}h ago"

    if days == 1:
        return "yesterday"

    if days < 30:
        return f"{days}d ago"

    if days < 365:
        months = int(days / 30)
        return f"{months}mo ago"

    years = int(days / 365)
    return f"{years}y ago"


def cmd_list(args: list[str]):
    """wt list - List worktrees"""
    base_dir = find_base_dir()
    if not base_dir:
        print(msg("error", msg("base_not_found")), file=sys.stderr)
        sys.exit(1)

    # --quiet / -q オプション（xargs 用）
    quiet = "--quiet" in args or "-q" in args
    show_pr = "--pr" in args

    worktrees = get_worktree_info(base_dir)

    # ソート: 作成日時の降順（最新が上）
    worktrees.sort(key=lambda x: x.get("created", datetime.min), reverse=True)

    # PR infoの取得
    if show_pr:
        for wt in worktrees:
            branch = wt.get("branch", "")
            if branch:
                wt["pr_info"] = get_pr_info(branch, cwd=base_dir)

    # 相対時間の計算
    for wt in worktrees:
        wt["relative_time"] = get_relative_time(wt.get("created"))

    if quiet:
        for wt in worktrees:
            print(
                Path(wt["path"]).name
                if Path(wt["path"]).name != base_dir.name
                else "main"
            )
        return

    # "Changes" カラムの表示文字列作成
    GREEN = "\033[32m"
    RED = "\033[31m"
    GRAY = "\033[90m"
    RESET = "\033[0m"

    for wt in worktrees:
        plus = wt.get("insertions", 0)
        minus = wt.get("deletions", 0)
        untracked = wt.get("has_untracked", False)

        parts = []
        clean_parts = []
        if plus > 0:
            parts.append(f"{GREEN}+{plus}{RESET}")
            clean_parts.append(f"+{plus}")
        if minus > 0:
            parts.append(f"{RED}-{minus}{RESET}")
            clean_parts.append(f"-{minus}")
        if untracked:
            parts.append(f"{GRAY}??{RESET}")
            clean_parts.append("??")

        if not parts:
            wt["changes_display"] = "-"
            wt["changes_clean_len"] = 1
        else:
            wt["changes_display"] = " ".join(parts)
            wt["changes_clean_len"] = len(" ".join(clean_parts))

    # カラム幅の計算
    name_w = (
        max(
            len(msg("worktree_name")),
            max((len(Path(wt["path"]).name) for wt in worktrees), default=0),
        )
        + 2
    )
    branch_w = (
        max(
            len(msg("branch_name")),
            max((len(wt.get("branch", "N/A")) for wt in worktrees), default=0),
        )
        + 2
    )
    time_w = (
        max(
            len("Created"),
            max((len(wt.get("relative_time", "")) for wt in worktrees), default=0),
        )
        + 2
    )
    status_w = (
        max(
            len(msg("changes_label")),
            max((wt["changes_clean_len"] for wt in worktrees), default=0),
        )
        + 2
    )
    pr_w = 0
    if show_pr:
        # PR info contains ANSI codes, so calculate real length
        import re

        # More robust ANSI escape regex including hyperlinks
        ansi_escape = re.compile(
            r"""
            \x1B(?:
                [@-Z\\-_]
            |
                \[[0-9]*[ -/]*[@-~]
            |
                \][0-9]*;.*?(\x1B\\|\x07)
            )
        """,
            re.VERBOSE,
        )

        def clean_len(s):
            return len(ansi_escape.sub("", s))

        pr_w = (
            max(
                3,
                max((clean_len(wt.get("pr_info", "")) for wt in worktrees), default=0),
            )
            + 2
        )

    # ヘッダー (色付き)
    CYAN = "\033[36m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    base_header = f"{msg('worktree_name'):<{name_w}} {msg('branch_name'):<{branch_w}} {'Created':<{time_w}} {msg('changes_label'):<{status_w}}"
    if show_pr:
        header = f"{BOLD}{base_header}   PR{RESET}"
        separator_len = len(base_header) + 5
    else:
        header = f"{BOLD}{base_header.rstrip()}{RESET}"
        separator_len = len(base_header.rstrip())

    print(header)
    print("-" * separator_len)

    for wt in worktrees:
        path = Path(wt["path"])
        name_display = path.name if path != base_dir else f"{CYAN}(main){RESET}"
        name_clean_len = len(path.name) if path != base_dir else 6
        name_padding = " " * (name_w - name_clean_len)

        branch = wt.get("branch", "N/A")
        rel_time = wt.get("relative_time", "N/A")
        changes_display = wt.get("changes_display", "no changes")
        changes_clean_len = wt.get("changes_clean_len", 1)

        # ANSI コード分を補正して表示
        changes_padding = " " * (status_w - changes_clean_len)

        print(
            f"{name_display}{name_padding} {branch:<{branch_w}} {rel_time:<{time_w}} {changes_display}{changes_padding}",
            end="",
        )
        if show_pr:
            print(f"   {wt.get('pr_info', '')}", end="")
        print()


def cmd_remove(args: list[str]):
    """wt rm/remove <work_name> - Remove a worktree"""
    if len(args) < 1:
        print(msg("usage_rm"), file=sys.stderr)
        sys.exit(1)

    base_dir = find_base_dir()
    if not base_dir:
        print(msg("error", msg("base_not_found")), file=sys.stderr)
        sys.exit(1)

    # Parse flags and find worktree name
    flags = []
    work_name = None
    for arg in args:
        if arg in ["-f", "--force"]:
            flags.append(arg)
        elif not work_name:
            work_name = arg
        else:
            # Additional non-flag arguments are currently ignored or could be treated as error
            pass

    if not work_name:
        print(msg("usage_rm"), file=sys.stderr)
        sys.exit(1)

    # worktree を削除
    print(msg("removing_worktree", work_name), file=sys.stderr)
    result = run_command(
        ["git", "worktree", "remove"] + flags + [work_name], cwd=base_dir, check=False
    )

    if result.returncode == 0:
        pass
    else:
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        sys.exit(1)


def cmd_checkout(args: list[str]):
    """wt co/checkout <work_name> - Get path to a worktree (for cd)"""
    if len(args) < 1:
        return

    work_name = args[0]
    base_dir = find_base_dir()
    if not base_dir:
        print(msg("error", msg("base_not_found")), file=sys.stderr)
        sys.exit(1)

    worktrees = get_worktree_info(base_dir)
    for wt in worktrees:
        p = Path(wt["path"])
        if p.name == work_name or (p == base_dir and work_name == "main"):
            print(str(p))
            return

    print(msg("error", msg("select_not_found", work_name)), file=sys.stderr)
    sys.exit(1)


def cmd_select(args: list[str]):
    """wt sl/select [<name>|-] - Manage/Switch worktree selection"""
    base_dir = find_base_dir()
    if not base_dir:
        print(msg("error", msg("base_not_found")), file=sys.stderr)
        sys.exit(1)

    wt_dir = base_dir / ".wt"
    # Ensure .wt directory and its management files (.gitignore etc) exist
    create_hook_template(base_dir)
    last_sel_file = wt_dir / "last_selection"

    # Get current selection name based on CWD or environment
    current_sel = os.environ.get("WT_SESSION_NAME")
    if not current_sel:
        cwd = Path.cwd().resolve()
        worktrees = get_worktree_info(base_dir)
        resolved_base = base_dir.resolve()
        for wt in worktrees:
            wt_path = Path(wt["path"]).resolve()
            if cwd == wt_path or cwd.is_relative_to(wt_path):
                current_sel = "main" if wt_path == resolved_base else wt_path.name
                break

    worktrees = get_worktree_info(base_dir)
    names = []
    for wt in worktrees:
        p = Path(wt["path"])
        name = "main" if p == base_dir else p.name
        names.append(name)

    if not args:
        # Interactive mode or list with highlight
        if shutil.which("fzf") and sys.stdin.isatty():
            # Run fzf
            try:
                # Prepare input for fzf with current highlighted
                fzf_input = ""
                for name in names:
                    if name == current_sel:
                        fzf_input += f"{name} (*)\n"
                    else:
                        fzf_input += f"{name}\n"

                process = subprocess.Popen(
                    ["fzf", "--height", "40%", "--reverse", "--header", "Select Worktree"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    text=True,
                )
                stdout, _ = process.communicate(input=fzf_input)

                if process.returncode == 0 and stdout.strip():
                    selected = stdout.strip().split(" ")[0]
                    switch_selection(selected, base_dir, current_sel, last_sel_file)
                return
            except Exception as e:
                print(f"fzf error: {e}", file=sys.stderr)
                # Fallback to listing

        # List with highlight
        YELLOW = "\033[33m"
        RESET = "\033[0m"
        BOLD = "\033[1m"

        for name in names:
            if name == current_sel:
                print(f"{YELLOW}{BOLD}{name}{RESET}")
            else:
                print(name)
        return

    target = args[0]

    if target == "-":
        if not last_sel_file.exists():
            print(msg("error", msg("select_no_last")), file=sys.stderr)
            sys.exit(1)
        target = last_sel_file.read_text().strip()
        if not target:
            print(msg("error", msg("select_no_last")), file=sys.stderr)
            sys.exit(1)

    if target not in names:
        print(msg("error", msg("select_not_found", target)), file=sys.stderr)
        sys.exit(1)

    switch_selection(target, base_dir, current_sel, last_sel_file)


def cmd_current(args: list[str]):
    """wt current (cur) - Show name of the current worktree"""
    name = os.environ.get("WT_SESSION_NAME")
    if not name:
        base_dir = find_base_dir()
        if not base_dir:
            return
        cwd = Path.cwd().resolve()
        worktrees = get_worktree_info(base_dir)
        resolved_base = base_dir.resolve()
        for wt in worktrees:
            wt_path = Path(wt["path"]).resolve()
            if cwd == wt_path:
                name = "main" if wt_path == resolved_base else wt_path.name
                break
    if name:
        print(name)


def switch_selection(target, base_dir, current_sel, last_sel_file):
    """Switch selection and update last_selection"""
    # Calculate target path
    target_path = base_dir
    if target != "main":
        config = load_config(base_dir)
        worktrees_dir_name = config.get("worktrees_dir", ".worktrees")
        target_path = base_dir / worktrees_dir_name / target

    if not target_path.exists():
        print(msg("error", msg("select_not_found", target)), file=sys.stderr)
        sys.exit(1)

    if target != current_sel:
        # Save last selection
        if current_sel:
            last_sel_file.write_text(current_sel)

        print(msg("select_switched", target), file=sys.stderr)

    # Check for setup files
    config = load_config(base_dir)
    setup_files = config.get("setup_files", [])
    missing = False
    for f in setup_files:
        if not (target_path / f).exists():
            missing = True
            break
    if missing:
        print(f"\033[33m{msg('suggest_setup')}\033[0m", file=sys.stderr)

    if sys.stdout.isatty():
        # Check for nesting
        current_session = os.environ.get("WT_SESSION_NAME")
        if current_session:
            print(
                f"\033[31m{msg('nesting_error', current_session)}\033[0m", file=sys.stderr
            )
            sys.exit(1)

        # Subshell jump
        shell = os.environ.get("SHELL", "/bin/sh")
        print(msg("jump_instruction", target, target_path), file=sys.stderr)

        os.chdir(target_path)
        os.environ["WT_SESSION_NAME"] = target
        # Prepend to PS1 for visibility (if supported by shell)
        ps1 = os.environ.get("PS1", "$ ")
        if not ps1.startswith("(wt:"):
            os.environ["PS1"] = f"(wt:{target}) {ps1}"

        # Set terminal title
        sys.stderr.write(f"\033]0;wt:{target}\007")
        sys.stderr.flush()

        # Update tmux window name if inside tmux
        if os.environ.get("TMUX"):
            subprocess.run(["tmux", "rename-window", f"wt:{target}"], check=False)

        os.execl(shell, shell)
    else:
        # Output path for script/backtick use
        print(str(target_path.absolute()))


def cmd_setup(args: list[str]):
    """wt setup - Initialize current worktree (copy setup_files and run hooks)"""
    base_dir = find_base_dir()
    if not base_dir:
        print(msg("error", msg("base_not_found")), file=sys.stderr)
        sys.exit(1)

    current_dir = Path.cwd()
    target_path = current_dir

    config = load_config(base_dir)
    setup_files = config.get("setup_files", [])

    import shutil
    count = 0
    for f in setup_files:
        src = base_dir / f
        dst = target_path / f
        if src.exists() and src != dst:
            print(msg("setting_up", src, dst), file=sys.stderr)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            count += 1

    if count > 0:
        print(msg("completed_setup", count), file=sys.stderr)

    # Run post-add hook
    work_name = target_path.name
    if target_path == base_dir:
        work_name = "main"

    # Get branch name for the current worktree
    branch = None
    result = run_command(["git", "branch", "--show-current"], cwd=target_path, check=False)
    if result.returncode == 0:
        branch = result.stdout.strip()

    run_post_add_hook(target_path, work_name, base_dir, branch)


def cmd_clean(args: list[str]):
    """wt clean - Remove old/unused/merged worktrees"""
    base_dir = find_base_dir()
    if not base_dir:
        print(msg("error", msg("base_not_found")), file=sys.stderr)
        sys.exit(1)

    # オプションを解析
    # オプションを解析
    clean_all = "--all" in args
    clean_merged = "--merged" in args
    clean_closed = "--closed" in args
    days = None

    for i, arg in enumerate(args):
        if arg == "--days" and i + 1 < len(args):
            try:
                days = int(args[i + 1])
            except ValueError:
                print(msg("error", "Invalid days value"), file=sys.stderr)
                sys.exit(1)

    # worktree 情報を取得
    worktrees = get_worktree_info(base_dir)

    # エイリアスで使われている worktree を取得
    # 今回の構成では root 内のシンボリックリンクを探す
    aliased_worktrees = set()
    for item in base_dir.iterdir():
        if item.is_symlink():
            try:
                target = item.resolve()
                aliased_worktrees.add(target)
            except Exception:
                pass

    # マージ済みブランチを取得
    merged_branches = set()
    merged_pr_branches = set()

    # デフォルトブランチを取得して、それに対してマージされているかを確認
    default_branch = get_default_branch(base_dir)
    default_branch_sha = None
    if default_branch:
        res_sha = run_command(
            ["git", "rev-parse", default_branch], cwd=base_dir, check=False
        )
        if res_sha.returncode == 0:
            default_branch_sha = res_sha.stdout.strip()

    if clean_merged and default_branch:
        # Local merged branches (merged into default_branch)
        result = run_command(
            ["git", "branch", "--merged", default_branch], cwd=base_dir, check=False
        )
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                # Extract branch name, removing '*', '+', and whitespace
                line = line.strip()
                if line.startswith("* ") or line.startswith("+ "):
                    line = line[2:].strip()
                if line:
                    merged_branches.add(line)

        # GitHub merged PRs
        if shutil.which("gh"):
            import json

            # Get last 100 merged PRs
            pr_cmd = [
                "gh",
                "pr",
                "list",
                "--state",
                "merged",
                "--limit",
                "100",
                "--json",
                "headRefName",
            ]
            pr_res = run_command(pr_cmd, cwd=base_dir, check=False)
            if pr_res.returncode == 0:
                try:
                    pr_data = json.loads(pr_res.stdout)
                    for pr in pr_data:
                        merged_pr_branches.add(pr["headRefName"])
                except:
                    pass

    # Closed PRs
    closed_pr_branches = set()
    if clean_closed:
        if shutil.which("gh"):
            import json

            # Get last 100 closed PRs
            pr_cmd = [
                "gh",
                "pr",
                "list",
                "--state",
                "closed",
                "--limit",
                "100",
                "--json",
                "headRefName",
            ]
            pr_res = run_command(pr_cmd, cwd=base_dir, check=False)
            if pr_res.returncode == 0:
                try:
                    pr_data = json.loads(pr_res.stdout)
                    for pr in pr_data:
                        closed_pr_branches.add(pr["headRefName"])
                except:
                    pass

    # 削除対象を抽出
    targets = []
    now = datetime.now()

    for wt in worktrees:
        path = Path(wt["path"])

        # base (git root) は除外
        if path == base_dir:
            continue

        # エイリアスで使われている worktree は除外
        if path in aliased_worktrees:
            continue

        reason = None
        # マージ済みの場合は無条件で対象（ただし dirty でないこと）
        is_merged = (
            wt.get("branch") in merged_branches
            or wt.get("branch") in merged_pr_branches
        )
        if clean_merged and is_merged:
            # Check safeguard: if branch points to same SHA as default branch and NOT in merged_pr_branches
            # it might be a new branch that hasn't diverged yet.
            if default_branch_sha and wt.get("branch") not in merged_pr_branches:
                wt_sha = run_command(
                    ["git", "rev-parse", wt.get("branch")], cwd=base_dir, check=False
                ).stdout.strip()
                if wt_sha == default_branch_sha:
                    # Skip deletion for fresh branches
                    continue

            if wt.get("is_clean"):
                reason = "merged"

        is_closed = wt.get("branch") in closed_pr_branches
        if not reason and clean_closed and is_closed:
            if wt.get("is_clean"):
                reason = "closed"

        # 通常のクリーンアップ対象
        if not reason and wt.get("is_clean"):
            if days is not None:
                created = wt.get("created")
                if created:
                    age_days = (now - created).days
                    if age_days >= days:
                        reason = f"older than {days} days"
            elif clean_all:
                reason = "clean"

        if reason:
            wt["reason"] = reason
            targets.append(wt)

    if not targets:
        print(msg("no_clean_targets"), file=sys.stderr)
        return

    # 削除対象を表示
    for wt in targets:
        path = Path(wt["path"])
        created = (
            wt.get("created").strftime("%Y-%m-%d %H:%M") if wt.get("created") else "N/A"
        )
        print(
            f"{path.name} (reason: {wt['reason']}, created: {created})", file=sys.stderr
        )

    # 確認
    if not clean_all:
        try:
            response = input(msg("clean_confirm", len(targets)))
            if response.lower() not in ["y", "yes"]:
                print("Cancelled.")
                return
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.")
            return

    # 削除実行
    for wt in targets:
        path = Path(wt["path"])
        print(msg("removing_worktree", path.name), file=sys.stderr)
        result = run_command(
            ["git", "worktree", "remove", str(path)], cwd=base_dir, check=False
        )

        if result.returncode == 0:
            pass
        else:
            if result.stderr:
                print(result.stderr, file=sys.stderr)

def cmd_passthrough(args: list[str]):
    """Passthrough other git worktree commands"""
    base_dir = find_base_dir()
    if not base_dir:
        print(msg("error", msg("base_not_found")), file=sys.stderr)
        sys.exit(1)

    result = run_command(["git", "worktree"] + args, cwd=base_dir, check=False)
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
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
        print(f"  {'clone <repository_url>':<55} - リポジトリをクローン")
        print(f"  {'init':<55} - 既存リポジトリをメインリポジトリとして構成")
        print(
            f"  {'add (ad) <作業名> [<base_branch>]':<55} - worktree を追加（デフォルト: 新規ブランチ作成）"
        )
        print(
            f"  {'select (sl) [<作業名>|-]':<55} - 作業ディレクトリを切り替え（fzf対応）"
        )
        print(f"  {'list (ls) [--pr]':<55} - worktree 一覧を表示")
        print(f"  {'co/checkout <作業名>':<55} - worktree のパスを表示")
        print(f"  {'current (cur)':<55} - 現在の worktree 名を表示")
        print(
            f"  {'stash (st) <作業名> [<base_branch>]':<55} - 現在の変更をスタッシュして新規 worktree に移動"
        )
        print(
            f"  {'pr add <番号>':<55} - GitHub PR を取得して worktree を作成/パス表示"
        )
        print(f"  {'rm/remove <作業名> [-f|--force]':<55} - worktree を削除")
        print(
            f"  {'clean (cl) [--days N] [--merged] [--closed]':<55} - 不要な worktree を削除"
        )
        print(
            f"  {'setup (su)':<55} - 作業ディレクトリを初期化（ファイルコピー・フック実行）"
        )
        print()
        print("オプション:")
        print(f"  {'-h, --help':<55} - このヘルプメッセージを表示")
        print(f"  {'-v, --version':<55} - バージョン情報を表示")
    else:
        print("easy-worktree - Simple CLI tool for managing Git worktrees")
        print()
        print("Usage:")
        print("  wt <command> [options]")
        print()
        print("Commands:")
        print(f"  {'clone <repository_url>':<55} - Clone a repository")
        print(f"  {'init':<55} - Configure existing repository as main")
        print(
            f"  {'add (ad) <work_name> [<base_branch>]':<55} - Add a worktree (default: create new branch)"
        )
        print(
            f"  {'select (sl) [<name>|-]':<55} - Switch worktree selection (fzf support)"
        )
        print(f"  {'list (ls) [--pr]':<55} - List worktrees")
        print(f"  {'co/checkout <work_name>':<55} - Show path to a worktree")
        print(f"  {'current (cur)':<55} - Show current worktree name")
        print(
            f"  {'stash (st) <work_name> [<base_branch>]':<55} - Stash current changes and move to new worktree"
        )
        print(f"  {'pr add <number>':<55} - Manage GitHub PRs as worktrees")
        print(f"  {'rm/remove <work_name> [-f|--force]':<55} - Remove a worktree")
        print(
            f"  {'clean (cl) [--days N] [--merged] [--closed]':<55} - Remove unused/merged worktrees"
        )
        print(
            f"  {'setup (su)':<55} - Setup worktree (copy files and run hooks)"
        )
        print()
        print("Options:")
        print(f"  {'-h, --help':<55} - Show this help message")
        print(f"  {'-v, --version':<55} - Show version information")


def show_version():
    """Show version information"""
    print("easy-worktree version 0.1.6")


def main():
    """メインエントリポイント"""
    # ヘルプとバージョンのオプションは設定なしでも動作する
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
    elif command in ["add", "ad"]:
        cmd_add(args)
    elif command in ["list", "ls"]:
        cmd_list(args)
    elif command in ["rm", "remove"]:
        cmd_remove(args)
    elif command in ["clean", "cl"]:
        cmd_clean(args)
    elif command in ["setup", "su"]:
        cmd_setup(args)
    elif command in ["stash", "st"]:
        cmd_stash(args)
    elif command == "pr":
        cmd_pr(args)
    elif command == "select" or command == "sl":
        cmd_select(args)
    elif command in ["current", "cur"]:
        cmd_current(args)
    elif command in ["co", "checkout"]:
        cmd_checkout(args)
    else:
        # その他のコマンドは git worktree にパススルー
        cmd_passthrough([command] + args)


if __name__ == "__main__":
    main()
