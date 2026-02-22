#!/usr/bin/env python3
"""
Git worktree を簡単に管理するための CLI ツール
"""

import os
import subprocess
import shutil
import sys
import hashlib
import difflib
from pathlib import Path
import re
from datetime import datetime, timezone
import toml

GLOBAL_GIT_DIR: Path | None = None
WORKTREE_METADATA_FILE = "worktree_metadata.toml"


# 言語判定
def is_japanese() -> bool:
    """LANG環境変数から日本語かどうかを判定"""
    lang = os.environ.get("LANG", "")
    return "ja" in lang.lower()


# メッセージ辞書
MESSAGES = {
    "error": {"en": "Error: {}", "ja": "エラー: {}"},
    "usage": {
        "en": "Usage: wt clone [--bare] <repository_url> [dest_dir]",
        "ja": "使用方法: wt clone [--bare] <repository_url> [dest_dir]",
    },
    "usage_add": {
        "en": "Usage: wt add (ad) <work_name> [<base_branch>] [--skip-setup|--no-setup] [--select [<command>...]]",
        "ja": "使用方法: wt add (ad) <作業名> [<base_branch>] [--skip-setup|--no-setup] [--select [<コマンド>...]]",
    },
    "usage_select": {
        "en": "Usage: wt select (sl) [<name>|-] [<command>...]",
        "ja": "使用方法: wt select (sl) [<名前>|-] [<コマンド>...]",
    },
    "usage_diff": {
        "en": "Usage: wt diff (df) [<name>] [args...]",
        "ja": "使用方法: wt diff (df) [<名前>] [引数...]",
    },
    "usage_config": {
        "en": "Usage: wt config [--global|--local] [<key> [<value>]]",
        "ja": "使用方法: wt config [--global|--local] [<キー> [<値>]]",
    },
    "usage_list": {
        "en": "Usage: wt list (ls) [--pr] [--quiet|-q] [--days N] [--merged] [--closed] [--all] [--sort created|last-commit|name|branch] [--asc|--desc]",
        "ja": "使用方法: wt list (ls) [--pr] [--quiet|-q] [--days N] [--merged] [--closed] [--all] [--sort created|last-commit|name|branch] [--asc|--desc]",
    },
    "usage_run": {
        "en": "Usage: wt run <name> <command>...",
        "ja": "使用方法: wt run <名前> <コマンド>...",
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
    "wt_home_not_found": {
        "en": "No non-bare worktree found for this bare repository. Create a base-branch worktree first.",
        "ja": "この bare リポジトリで利用可能な non-bare worktree が見つかりません。先にベースブランチの worktree を作成してください。",
    },
    "suggest_init": {
        "en": "Initialize wt config with: {}",
        "ja": "wt 設定を初期化: {}",
    },
    "did_you_mean": {
        "en": "Did you mean: {}",
        "ja": "もしかして: {}",
    },
    "available_worktrees": {
        "en": "Available worktrees: {}",
        "ja": "利用可能な worktree: {}",
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
    "usage_completion": {
        "en": "Usage: wt completion <bash|zsh>",
        "ja": "使用方法: wt completion <bash|zsh>",
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
    "using_setup_source": {
        "en": "Using setup source: {}",
        "ja": "セットアップコピー元: {}",
    },
    "setup_source_not_found": {
        "en": "Setup source directory not found. Skipping file copy.",
        "ja": "セットアップコピー元が見つからないため、ファイルコピーをスキップします。",
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
    cmd: list[str],
    cwd: Path = None,
    check: bool = True,
    apply_global_git_dir: bool = True,
) -> subprocess.CompletedProcess:
    """コマンドを実行"""
    try:
        final_cmd = cmd
        if (
            apply_global_git_dir
            and GLOBAL_GIT_DIR
            and cmd
            and cmd[0] == "git"
            and not any(arg == "--git-dir" or arg.startswith("--git-dir=") for arg in cmd)
        ):
            final_cmd = ["git", f"--git-dir={GLOBAL_GIT_DIR}"] + cmd[1:]

        # print(f"DEBUG: Running command: {cmd} cwd={cwd}", file=sys.stderr)
        result = subprocess.run(
            final_cmd, cwd=cwd, capture_output=True, text=True, check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        print(msg("error", e.stderr), file=sys.stderr)
        sys.exit(1)


def print_init_suggestion():
    """wt init の実行例を表示"""
    if GLOBAL_GIT_DIR:
        cmd = f"wt --git-dir={GLOBAL_GIT_DIR} init"
    else:
        cmd = "wt init"
    print(msg("suggest_init", cmd), file=sys.stderr)


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


def get_default_branch_for_bare_git_dir(git_dir: Path) -> str | None:
    """bare git-dir からデフォルトブランチ名を検出"""
    result = run_command(
        ["git", f"--git-dir={git_dir}", "symbolic-ref", "refs/remotes/origin/HEAD"],
        check=False,
        apply_global_git_dir=False,
    )
    if result.returncode == 0 and result.stdout.strip():
        ref = result.stdout.strip()
        return ref.split("/")[-1]

    for b in ["main", "master"]:
        check = run_command(
            ["git", f"--git-dir={git_dir}", "show-ref", "--verify", f"refs/heads/{b}"],
            check=False,
            apply_global_git_dir=False,
        )
        if check.returncode == 0:
            return b

    head_ref = run_command(
        ["git", f"--git-dir={git_dir}", "symbolic-ref", "HEAD"],
        check=False,
        apply_global_git_dir=False,
    )
    if head_ref.returncode == 0 and head_ref.stdout.strip():
        ref = head_ref.stdout.strip()
        if ref.startswith("refs/heads/"):
            return ref.replace("refs/heads/", "", 1)

    return None


def ensure_base_worktree_for_bare(base_dir: Path) -> Path:
    """bare リポジトリに non-bare worktree が無ければ作成して返す"""
    existing = get_preferred_non_bare_worktree(base_dir)
    if existing:
        return existing

    default_branch = get_default_branch_for_bare_git_dir(base_dir)
    if not default_branch:
        print(msg("error", msg("default_branch_not_found")), file=sys.stderr)
        sys.exit(1)

    base_worktree_root = base_dir.parent / base_dir.stem
    base_worktree_path = base_worktree_root / default_branch
    if base_worktree_path.exists():
        print(msg("error", msg("already_exists", base_worktree_path)), file=sys.stderr)
        sys.exit(1)

    print(msg("creating_worktree", base_worktree_path), file=sys.stderr)
    run_command(
        [
            "git",
            f"--git-dir={base_dir}",
            "worktree",
            "add",
            str(base_worktree_path),
            default_branch,
        ],
        apply_global_git_dir=False,
    )
    print(msg("completed_worktree", base_worktree_path), file=sys.stderr)
    return base_worktree_path


def get_preferred_non_bare_worktree(base_dir: Path) -> Path | None:
    """bare リポジトリ時に基準として使う non-bare worktree を返す"""
    default_branch = get_default_branch(base_dir)
    entries = get_worktree_entries(base_dir)

    if default_branch:
        for entry in entries:
            if entry.get("is_bare"):
                continue
            if entry.get("branch") == default_branch:
                candidate = Path(entry.get("path", "")).resolve()
                if candidate.exists():
                    return candidate

    for entry in entries:
        if entry.get("is_bare"):
            continue
        candidate = Path(entry.get("path", "")).resolve()
        if candidate.exists():
            return candidate

    return None


def get_wt_home_dir(base_dir: Path) -> Path | None:
    """`.wt` を置くホームディレクトリを返す"""
    if not is_bare_repository(base_dir):
        return base_dir
    return get_preferred_non_bare_worktree(base_dir)


def require_wt_home_dir(base_dir: Path) -> Path:
    """`.wt` 用ホームディレクトリを必須で取得"""
    wt_home = get_wt_home_dir(base_dir)
    if not wt_home:
        print(msg("error", msg("wt_home_not_found")), file=sys.stderr)
        print_init_suggestion()
        sys.exit(1)
    return wt_home


def get_wt_dir(base_dir: Path) -> Path:
    """`.wt` ディレクトリの実体パスを返す"""
    return require_wt_home_dir(base_dir) / ".wt"


def load_config(base_dir: Path) -> dict:
    """設定ファイルを読み込む (Global -> Project -> Local)"""
    default_config = {
        "worktrees_dir": ".worktrees",
        "setup_files": [".env"],
        "setup_source_dir": None,
        "diff": {"tool": "git"},
    }

    # 1. Global (XDG)
    xdg_config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    global_config_file = xdg_config_home / "easy-worktree" / "config.toml"
    
    # 2. Project
    wt_dir = get_wt_dir(base_dir)
    project_config_file = wt_dir / "config.toml"
    
    # 3. Local
    local_config_file = wt_dir / "config.local.toml"

    def merge_config(base, overlay):
        for k, v in overlay.items():
            if isinstance(v, dict) and k in base and isinstance(base[k], dict):
                merge_config(base[k], v)
            else:
                base[k] = v

    # Load order
    for cfg_file in [global_config_file, project_config_file, local_config_file]:
        if cfg_file.exists():
            try:
                with open(cfg_file, "r", encoding="utf-8") as f:
                    user_config = toml.load(f)
                    merge_config(default_config, user_config)
            except Exception as e:
                print(msg("error", f"Failed to load config {cfg_file}: {e}"), file=sys.stderr)

    return default_config


def save_config(base_dir: Path, config: dict):
    """(Deprecated) Use save_config_to_file instead."""
    wt_dir = get_wt_dir(base_dir)
    wt_dir.mkdir(exist_ok=True)
    config_file = wt_dir / "config.toml"
    save_config_to_file(config_file, config)


def save_config_to_file(file_path: Path, config_updates: dict):
    """既存の設定を維持しつつ、DEEPマージして保存する"""
    config = {}
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config = toml.load(f)
        except Exception:
            pass

    def deep_merge(target, source):
        for k, v in source.items():
            if isinstance(v, dict) and k in target and isinstance(target[k], dict):
                deep_merge(target[k], v)
            else:
                target[k] = v

    deep_merge(config, config_updates)
    
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        toml.dump(config, f)


def get_metadata_file(base_dir: Path) -> Path:
    """XDG 配下のメタデータファイルパスを返す"""
    xdg_home = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    app_dir = xdg_home / "easy-worktree"
    try:
        app_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        app_dir = Path("/tmp") / "easy-worktree"
        app_dir.mkdir(parents=True, exist_ok=True)

    result = run_command(["git", "rev-parse", "--git-common-dir"], cwd=base_dir, check=False)
    if result.returncode == 0:
        git_common_dir = Path(result.stdout.strip())
        if not git_common_dir.is_absolute():
            git_common_dir = (base_dir / git_common_dir).resolve()
    else:
        git_common_dir = base_dir.resolve()

    repo_key = hashlib.sha1(str(git_common_dir).encode("utf-8")).hexdigest()[:16]
    return app_dir / f"worktree_metadata_{repo_key}.toml"


def load_worktree_metadata(base_dir: Path) -> dict:
    """worktree のメタデータを読み込む"""
    metadata_file = get_metadata_file(base_dir)
    default_data = {"worktrees": []}

    if metadata_file.exists():
        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                data = toml.load(f)
            if isinstance(data, dict) and isinstance(data.get("worktrees"), list):
                return data
        except Exception:
            pass

    return default_data


def save_worktree_metadata(base_dir: Path, metadata: dict):
    """worktree のメタデータを保存する"""
    metadata_file = get_metadata_file(base_dir)
    with open(metadata_file, "w", encoding="utf-8") as f:
        toml.dump(metadata, f)


def record_worktree_created(
    base_dir: Path, worktree_path: Path, created_at: datetime | None = None
):
    """worktree の作成時刻を記録（未登録時のみ）"""
    create_hook_template(base_dir)
    metadata = load_worktree_metadata(base_dir)
    target = str(worktree_path.resolve())

    for item in metadata.get("worktrees", []):
        if item.get("path") == target:
            if not item.get("created_at"):
                item["created_at"] = (created_at or datetime.now()).isoformat()
                save_worktree_metadata(base_dir, metadata)
            return

    metadata.setdefault("worktrees", []).append(
        {
            "path": target,
            "created_at": (created_at or datetime.now()).isoformat(),
        }
    )
    save_worktree_metadata(base_dir, metadata)


def get_recorded_worktree_created(base_dir: Path, worktree_path: Path) -> datetime | None:
    """記録済みの作成時刻を取得"""
    metadata = load_worktree_metadata(base_dir)
    target = str(worktree_path.resolve())

    for item in metadata.get("worktrees", []):
        if item.get("path") == target:
            created_at = item.get("created_at")
            if not created_at:
                return None
            try:
                return datetime.fromisoformat(created_at)
            except Exception:
                return None
    return None


def remove_worktree_metadata(base_dir: Path, worktree_path: Path):
    """worktree のメタデータを削除"""
    metadata = load_worktree_metadata(base_dir)
    target = str(worktree_path.resolve())
    before = len(metadata.get("worktrees", []))
    metadata["worktrees"] = [
        item for item in metadata.get("worktrees", []) if item.get("path") != target
    ]
    if len(metadata["worktrees"]) != before:
        save_worktree_metadata(base_dir, metadata)


def create_hook_template(base_dir: Path):
    """post-add hook のテンプレートと .wt/ 内のファイルを作成"""
    wt_home = require_wt_home_dir(base_dir)
    wt_dir = wt_home / ".wt"

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
                "setup_source_dir": None,
            },
        )

    # .gitignore (repository root) に worktrees_dir を追加
    config = load_config(base_dir)
    worktrees_dir_name = config.get("worktrees_dir", ".worktrees")
    root_gitignore = wt_home / ".gitignore"

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
setup_source_dir = ""           # 空なら自動判定。指定時はこのディレクトリからコピー
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
setup_source_dir = ""           # Empty means auto-detect; otherwise copy from this directory
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
    if GLOBAL_GIT_DIR:
        if GLOBAL_GIT_DIR.name == ".git":
            return GLOBAL_GIT_DIR.parent
        return GLOBAL_GIT_DIR

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


def is_bare_repository(base_dir: Path) -> bool:
    """リポジトリが bare かどうか判定"""
    result = run_command(
        ["git", "rev-parse", "--is-bare-repository"], cwd=base_dir, check=False
    )
    return result.returncode == 0 and result.stdout.strip().lower() == "true"


def get_worktree_entries(base_dir: Path) -> list[dict]:
    """git worktree list --porcelain を最小情報でパース"""
    result = run_command(["git", "worktree", "list", "--porcelain"], cwd=base_dir)

    entries = []
    current = {}
    for line in result.stdout.strip().split("\n"):
        if not line:
            if current:
                entries.append(current)
                current = {}
            continue

        if line.startswith("worktree "):
            current["path"] = line.split(" ", 1)[1]
        elif line.startswith("branch "):
            current["branch"] = line.split(" ", 1)[1].replace("refs/heads/", "")
        elif line.strip() == "bare":
            current["is_bare"] = True

    if current:
        entries.append(current)

    for entry in entries:
        entry["is_bare"] = entry.get("is_bare", False)

    return entries


def resolve_setup_source_dir(base_dir: Path, target_path: Path, config: dict) -> Path | None:
    """setup file のコピー元ディレクトリを決定"""
    configured_source = config.get("setup_source_dir")
    if configured_source:
        source_dir = Path(configured_source)
        if not source_dir.is_absolute():
            source_dir = (base_dir / source_dir).resolve()
        return source_dir

    if not is_bare_repository(base_dir):
        return base_dir

    resolved_target = target_path.resolve()
    preferred = get_preferred_non_bare_worktree(base_dir)
    if preferred and preferred != resolved_target:
        return preferred

    entries = get_worktree_entries(base_dir)

    for entry in entries:
        if entry.get("is_bare"):
            continue
        candidate = Path(entry.get("path", "")).resolve()
        if candidate.exists() and candidate != resolved_target:
            return candidate

    return None


def copy_setup_files(base_dir: Path, target_path: Path, setup_files: list[str], config: dict) -> int:
    """setup_files をコピーする。コピー元が見つからない場合は警告してスキップ"""
    source_dir = resolve_setup_source_dir(base_dir, target_path, config)
    if not source_dir or not source_dir.exists():
        print(msg("setup_source_not_found"), file=sys.stderr)
        return 0

    print(msg("using_setup_source", source_dir), file=sys.stderr)

    count = 0
    for file_name in setup_files:
        src = source_dir / file_name
        dst = target_path / file_name
        if src.exists() and src != dst:
            print(msg("setting_up", src, dst), file=sys.stderr)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            count += 1
    return count


def cmd_clone(args: list[str]):
    """wt clone [--bare] <repository_url> [dest_dir] - Clone a repository"""
    if len(args) < 1:
        print(msg("usage"), file=sys.stderr)
        sys.exit(1)

    bare_mode = False
    clean_args = []
    for arg in args:
        if arg == "--bare":
            bare_mode = True
        else:
            clean_args.append(arg)

    if len(clean_args) < 1:
        print(msg("usage"), file=sys.stderr)
        sys.exit(1)

    repo_url = clean_args[0]
    repo_name = get_repository_name(repo_url)

    if len(clean_args) > 1:
        dest_dir = Path(clean_args[1])
    else:
        dest_dir = Path(f"{repo_name}.git" if bare_mode else repo_name)

    if dest_dir.exists():
        print(msg("error", msg("already_exists", dest_dir)), file=sys.stderr)
        sys.exit(1)

    print(msg("cloning", repo_url, dest_dir), file=sys.stderr)
    clone_cmd = ["git", "clone"]
    if bare_mode:
        clone_cmd.append("--bare")
    clone_cmd.extend([repo_url, str(dest_dir)])
    run_command(clone_cmd, apply_global_git_dir=False)
    print(msg("completed_clone", dest_dir), file=sys.stderr)

    if bare_mode:
        ensure_base_worktree_for_bare(dest_dir)
        # bare の場合は base branch worktree 側に .wt を作成
        create_hook_template(dest_dir)
    else:
        # post-add hook と設定ファイルを作成
        create_hook_template(dest_dir)


def cmd_init(args: list[str]):
    """wt init - Initialize easy-worktree in current git repository"""
    base_dir = find_base_dir()
    if not base_dir:
        print(msg("error", msg("not_git_repo")), file=sys.stderr)
        sys.exit(1)

    if is_bare_repository(base_dir):
        ensure_base_worktree_for_bare(base_dir)

    # post-add hook と設定ファイルを作成
    create_hook_template(base_dir)


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
    hook_path = get_wt_dir(base_dir) / "post-add"

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
        record_worktree_created(base_dir, worktree_path)
        if not skip_setup:
            setup_files = config.get("setup_files", [])
            copy_setup_files(base_dir, worktree_path, setup_files, config)

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
    select_command = None
    
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ["--skip-setup", "--no-setup"]:
            skip_setup = True
        elif arg == "--select":
            select = True
            if i + 1 < len(args):
                select_command = args[i+1:]
            break # Consume everything after --select as command
        else:
            clean_args.append(arg)
        i += 1

    # Heuristic: if clean_args is empty but we have select_command,
    # it likely means the user put --select before the work_name.
    if not clean_args and select_command:
        # Take the first one as work_name
        clean_args.append(select_command.pop(0))
        if not select_command:
            select_command = None

    if not clean_args:
        print(msg("usage_add"), file=sys.stderr)
        sys.exit(1)

    work_name = clean_args[0]
    branch_to_use = clean_args[1] if len(clean_args) >= 2 else None

    base_dir = find_base_dir()
    wt_path = add_worktree(work_name, branch_to_use=branch_to_use, skip_setup=skip_setup, base_dir=base_dir)

    if select and wt_path:
        wt_dir = get_wt_dir(base_dir)
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
        
        switch_selection(work_name, base_dir, current_sel, last_sel_file, command=select_command)


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
        run_command(["git", "stash", "pop"], cwd=wt_path, apply_global_git_dir=False)


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

        created = get_recorded_worktree_created(base_dir, path)
        if not created and path.exists():
            # 初回のみ fallback で拾って記録し、以降は固定値を使う
            stat_info = path.stat()
            created = datetime.fromtimestamp(stat_info.st_ctime)
            record_worktree_created(base_dir, path, created_at=created)
        if created:
            wt["created"] = created

        # 最終コミット日時
        result = run_command(
            ["git", "log", "-1", "--format=%ct", wt.get("head", "HEAD")],
            cwd=base_dir,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            wt["last_commit"] = datetime.fromtimestamp(int(result.stdout.strip()))

        # git status（変更があるか）
        result = run_command(
            ["git", "status", "--porcelain"],
            cwd=path,
            check=False,
            apply_global_git_dir=False,
        )
        wt["is_clean"] = result.returncode == 0 and not result.stdout.strip()
        wt["has_untracked"] = "??" in result.stdout

        # Diff stats取得
        result_diff = run_command(
            ["git", "diff", "HEAD", "--shortstat"],
            cwd=path,
            check=False,
            apply_global_git_dir=False,
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


def parse_clean_filter_options(args: list[str]) -> tuple[bool, bool, bool, int | None]:
    """clean/list 共通のフィルタオプションを解析"""
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

    return clean_all, clean_merged, clean_closed, days


def resolve_clean_targets(base_dir: Path, worktrees: list[dict], args: list[str]) -> list[dict]:
    """cmd_clean と同じ判定で対象 worktree を返す（削除はしない）"""
    clean_all, clean_merged, clean_closed, days = parse_clean_filter_options(args)

    aliased_worktrees = set()
    for item in base_dir.iterdir():
        if item.is_symlink():
            try:
                target = item.resolve()
                aliased_worktrees.add(target)
            except Exception:
                pass

    merged_branches = set()
    merged_pr_branches = set()

    default_branch = get_default_branch(base_dir)
    default_branch_sha = None
    if default_branch:
        res_sha = run_command(
            ["git", "rev-parse", default_branch], cwd=base_dir, check=False
        )
        if res_sha.returncode == 0:
            default_branch_sha = res_sha.stdout.strip()

    if clean_merged and default_branch:
        result = run_command(
            ["git", "branch", "--merged", default_branch], cwd=base_dir, check=False
        )
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                line = line.strip()
                if line.startswith("* ") or line.startswith("+ "):
                    line = line[2:].strip()
                if line:
                    merged_branches.add(line)

        if shutil.which("gh"):
            import json

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
                except Exception:
                    pass

    closed_pr_branches = set()
    if clean_closed and shutil.which("gh"):
        import json

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
            except Exception:
                pass

    targets = []
    now = datetime.now()

    for wt in worktrees:
        path = Path(wt["path"])

        if path == base_dir:
            continue
        if path in aliased_worktrees:
            continue

        reason = None
        is_merged = (
            wt.get("branch") in merged_branches
            or wt.get("branch") in merged_pr_branches
        )
        if clean_merged and is_merged:
            if default_branch_sha and wt.get("branch") not in merged_pr_branches:
                wt_sha = run_command(
                    ["git", "rev-parse", wt.get("branch")], cwd=base_dir, check=False
                ).stdout.strip()
                if wt_sha == default_branch_sha:
                    continue
            if wt.get("is_clean"):
                reason = "merged"

        is_closed = wt.get("branch") in closed_pr_branches
        if not reason and clean_closed and is_closed and wt.get("is_clean"):
            reason = "closed"

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
            new_item = dict(wt)
            new_item["reason"] = reason
            targets.append(new_item)

    return targets


def sort_worktrees(worktrees: list[dict], sort_key: str, descending: bool):
    """worktree 一覧を指定キーでソート"""
    if sort_key == "last-commit":
        worktrees.sort(
            key=lambda x: x.get("last_commit", datetime.min), reverse=descending
        )
    elif sort_key == "name":
        worktrees.sort(
            key=lambda x: Path(x.get("path", "")).name.lower(), reverse=descending
        )
    elif sort_key == "branch":
        worktrees.sort(key=lambda x: x.get("branch", "").lower(), reverse=descending)
    else:
        worktrees.sort(key=lambda x: x.get("created", datetime.min), reverse=descending)


def get_worktree_names(base_dir: Path) -> list[str]:
    """利用可能な worktree 名一覧を返す"""
    names = []
    for wt in get_worktree_info(base_dir):
        p = Path(wt["path"])
        name = "main" if p == base_dir else p.name
        names.append(name)
    return names


def suggest_worktree_name(base_dir: Path, typed_name: str):
    """入力された worktree 名の候補を表示"""
    names = get_worktree_names(base_dir)
    if not names:
        return
    matches = difflib.get_close_matches(typed_name, names, n=3, cutoff=0.4)
    if matches:
        print(msg("did_you_mean", ", ".join(matches)), file=sys.stderr)
    else:
        print(msg("available_worktrees", ", ".join(names)), file=sys.stderr)


def cmd_list(args: list[str]):
    """wt list - List worktrees"""
    base_dir = find_base_dir()
    if not base_dir:
        print(msg("error", msg("base_not_found")), file=sys.stderr)
        sys.exit(1)

    if "--help" in args or "-h" in args:
        print(msg("usage_list"), file=sys.stderr)
        return

    quiet = "--quiet" in args or "-q" in args
    show_pr = "--pr" in args

    sort_key = "created"
    descending = True
    if "--sort" in args:
        i = args.index("--sort")
        if i + 1 >= len(args):
            print(msg("usage_list"), file=sys.stderr)
            sys.exit(1)
        sort_key = args[i + 1]
        if sort_key not in ["created", "last-commit", "name", "branch"]:
            print(msg("error", f"Invalid sort key: {sort_key}"), file=sys.stderr)
            print(msg("usage_list"), file=sys.stderr)
            sys.exit(1)
    if "--asc" in args:
        descending = False
    if "--desc" in args:
        descending = True

    worktrees = get_worktree_info(base_dir)
    clean_all, clean_merged, clean_closed, days = parse_clean_filter_options(args)
    if clean_all or clean_merged or clean_closed or days is not None:
        worktrees = resolve_clean_targets(base_dir, worktrees, args)

    sort_worktrees(worktrees, sort_key, descending)

    # PR infoの取得
    if show_pr:
        for wt in worktrees:
            branch = wt.get("branch", "")
            if branch:
                wt["pr_info"] = get_pr_info(branch, cwd=base_dir)

    for wt in worktrees:
        wt["relative_created"] = get_relative_time(wt.get("created"))
        wt["relative_last_commit"] = get_relative_time(wt.get("last_commit"))

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
    created_w = (
        max(
            len(msg("created_at")),
            max((len(wt.get("relative_created", "")) for wt in worktrees), default=0),
        )
        + 2
    )
    last_commit_w = (
        max(
            len(msg("last_commit")),
            max(
                (len(wt.get("relative_last_commit", "")) for wt in worktrees),
                default=0,
            ),
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

    base_header = (
        f"{msg('worktree_name'):<{name_w}} {msg('branch_name'):<{branch_w}} "
        f"{msg('created_at'):<{created_w}} {msg('last_commit'):<{last_commit_w}} "
        f"{msg('changes_label'):<{status_w}}"
    )
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
        rel_created = wt.get("relative_created", "N/A")
        rel_last_commit = wt.get("relative_last_commit", "N/A")
        changes_display = wt.get("changes_display", "no changes")
        changes_clean_len = wt.get("changes_clean_len", 1)

        # ANSI コード分を補正して表示
        changes_padding = " " * (status_w - changes_clean_len)

        print(
            f"{name_display}{name_padding} {branch:<{branch_w}} "
            f"{rel_created:<{created_w}} {rel_last_commit:<{last_commit_w}} "
            f"{changes_display}{changes_padding}",
            end="",
        )
        if show_pr:
            print(f"   {wt.get('pr_info', '')}", end="")
        print()


def cmd_diff(args: list[str]):
    """wt diff (df) [<name>] [args...] - Show changes"""
    base_dir = find_base_dir()
    if not base_dir:
        print(msg("error", msg("base_not_found")), file=sys.stderr)
        sys.exit(1)

    config = load_config(base_dir)
    worktrees = get_worktree_info(base_dir)
    names = []
    for wt in worktrees:
        p = Path(wt["path"])
        name = "main" if p == base_dir else p.name
        names.append(name)

    target_wt = None
    remaining_args = []

    i = 0
    while i < len(args):
        arg = args[i]
        if target_wt is None and arg in names:
            target_wt = arg
        else:
            remaining_args.append(arg)
        i += 1

    # Determine target path
    if target_wt:
        target_path = base_dir
        if target_wt != "main":
            worktrees_dir_name = config.get("worktrees_dir", ".worktrees")
            target_path = base_dir / worktrees_dir_name / target_wt
    else:
        target_path = Path.cwd()

    diff_tool = config.get("diff", {}).get("tool", "git")

    if diff_tool == "lumen":
        # Use lumen
        if shutil.which("lumen"):
            # Include --watch by default
            cmd = ["lumen", "diff", "--watch"] + remaining_args
            try:
                subprocess.run(cmd, cwd=target_path)
            except KeyboardInterrupt:
                pass
            return
        else:
            print(
                msg("error", "lumen not found. Please install it first."),
                file=sys.stderr,
            )
            sys.exit(1)

    # git diff
    if not remaining_args:
        # Default behavior: diff against base branch
        base_branch = get_default_branch(base_dir)
        if base_branch:
            # Check if we are on a different branch
            res_curr = run_command(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=target_path,
                check=False,
                apply_global_git_dir=False,
            )
            curr_branch = res_curr.stdout.strip() if res_curr.returncode == 0 else ""

            if curr_branch and curr_branch != base_branch:
                remaining_args = [base_branch]

    cmd = ["git", "diff"] + remaining_args
    try:
        # Use sys.stdout/stderr to ensure capture in tests and environments
        subprocess.run(cmd, cwd=target_path, stdout=sys.stdout, stderr=sys.stderr)
    except KeyboardInterrupt:
        pass


def cmd_config(args: list[str]):
    """wt config [--global|--local] [<key> [<value>]]"""
    base_dir = find_base_dir()
    # base_dir is optional for --global
    
    is_global = "--global" in args
    is_local = "--local" in args
    remaining_args = [a for a in args if a not in ["--global", "--local"]]

    if is_global:
        xdg_config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        target_file = xdg_config_home / "easy-worktree" / "config.toml"
    elif is_local:
        if not base_dir:
            print(msg("error", msg("base_not_found")), file=sys.stderr)
            sys.exit(1)
        target_file = get_wt_dir(base_dir) / "config.local.toml"
    else:
        # Default is project config
        if not base_dir:
            if not is_global:
                print(msg("error", msg("base_not_found")), file=sys.stderr)
                sys.exit(1)
        target_file = get_wt_dir(base_dir) / "config.toml"

    if not remaining_args:
        # Show all (merged)
        config = load_config(base_dir) if base_dir else load_config(Path("/")) # Dummy for global-only
        print(toml.dumps(config).strip())
        return

    key = remaining_args[0]
    if len(remaining_args) == 1:
        # Get value
        if is_global or is_local:
            # Load specific file
            config = {}
            if target_file.exists():
                try:
                    with open(target_file, "r", encoding="utf-8") as f:
                        config = toml.load(f)
                except Exception:
                    pass
        else:
            # Merged config
            config = load_config(base_dir) if base_dir else load_config(Path("/"))
            
        parts = key.split(".")
        val = config
        for p in parts:
            if isinstance(val, dict) and p in val:
                val = val[p]
            else:
                val = None
                break
        if val is not None:
            if isinstance(val, (dict, list)):
                print(toml.dumps({key: val}).strip())
            else:
                print(val)
        return

    # Set value
    value = remaining_args[1]
    
    # Simple type conversion
    if value.lower() == "true":
        value = True
    elif value.lower() == "false":
        value = False
    elif value.isdigit():
        value = int(value)

    # Convert dot key to nested dict
    parts = key.split(".")
    update = {}
    curr = update
    for p in parts[:-1]:
        curr[p] = {}
        curr = curr[p]
    curr[parts[-1]] = value

    try:
        save_config_to_file(target_file, update)
        # print(f"Updated {target_file}")
    except Exception as e:
        print(msg("error", f"Failed to save config: {e}"), file=sys.stderr)
        sys.exit(1)


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

    target_for_metadata = None
    for wt in get_worktree_info(base_dir):
        p = Path(wt["path"])
        if p.name == work_name or str(p) == work_name:
            target_for_metadata = p
            break
    if not target_for_metadata:
        print(msg("error", msg("select_not_found", work_name)), file=sys.stderr)
        suggest_worktree_name(base_dir, work_name)
        sys.exit(1)

    # worktree を削除
    print(msg("removing_worktree", work_name), file=sys.stderr)
    result = run_command(
        ["git", "worktree", "remove"] + flags + [work_name], cwd=base_dir, check=False
    )

    if result.returncode == 0:
        if target_for_metadata:
            remove_worktree_metadata(base_dir, target_for_metadata)
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
    suggest_worktree_name(base_dir, work_name)
    sys.exit(1)


def cmd_select(args: list[str]):
    """wt sl/select [<name>|-] - Manage/Switch worktree selection"""
    base_dir = find_base_dir()
    if not base_dir:
        print(msg("error", msg("base_not_found")), file=sys.stderr)
        sys.exit(1)

    wt_dir = get_wt_dir(base_dir)
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
    command = args[1:] if len(args) > 1 else None

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
        suggest_worktree_name(base_dir, target)
        sys.exit(1)

    switch_selection(target, base_dir, current_sel, last_sel_file, command=command)


def cmd_run(args: list[str]):
    """wt run <work_name> <command>... - Run command in worktree and exit"""
    if len(args) < 2:
        print(msg("usage_run"), file=sys.stderr)
        sys.exit(1)

    work_name = args[0]
    command = args[1:]

    base_dir = find_base_dir()
    if not base_dir:
        print(msg("error", msg("base_not_found")), file=sys.stderr)
        sys.exit(1)

    # find target path
    target_path = base_dir
    if work_name != "main":
        config = load_config(base_dir)
        worktrees_dir_name = config.get("worktrees_dir", ".worktrees")
        target_path = base_dir / worktrees_dir_name / work_name

    if not target_path.exists():
        print(msg("error", msg("select_not_found", work_name)), file=sys.stderr)
        suggest_worktree_name(base_dir, work_name)
        sys.exit(1)

    # set environment variables
    env = os.environ.copy()
    env["WT_SESSION_NAME"] = work_name

    # run command
    try:
        subprocess.run(command, cwd=target_path, env=env, check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
    except Exception as e:
        print(msg("error", str(e)), file=sys.stderr)
        sys.exit(1)


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


def switch_selection(target, base_dir, current_sel, last_sel_file, command: list[str] = None):
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

        if command:
            cmd_str = " ".join(command)
            # コマンド実行後にシェルを維持するために "cmd; exec shell" を実行
            os.execl(shell, shell, "-c", f"{cmd_str}; exec {shell}")
        else:
            os.execl(shell, shell)
    else:
        # Output path for script/backtick use
        print(str(target_path.absolute()))
        if command:
            # 非 TTY の場合でもコマンドがあれば実行しておく (パイプなどでの利用を想定)
            import subprocess
            subprocess.run(command, cwd=target_path, check=True)


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

    count = copy_setup_files(base_dir, target_path, setup_files, config)

    if count > 0:
        print(msg("completed_setup", count), file=sys.stderr)

    # Run post-add hook
    work_name = target_path.name
    if target_path == base_dir:
        work_name = "main"

    # Get branch name for the current worktree
    branch = None
    result = run_command(
        ["git", "branch", "--show-current"],
        cwd=target_path,
        check=False,
        apply_global_git_dir=False,
    )
    if result.returncode == 0:
        branch = result.stdout.strip()

    run_post_add_hook(target_path, work_name, base_dir, branch)


def cmd_clean(args: list[str]):
    """wt clean - Remove old/unused/merged worktrees"""
    base_dir = find_base_dir()
    if not base_dir:
        print(msg("error", msg("base_not_found")), file=sys.stderr)
        sys.exit(1)

    clean_all, _, _, _ = parse_clean_filter_options(args)
    worktrees = get_worktree_info(base_dir)
    targets = resolve_clean_targets(base_dir, worktrees, args)

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
            remove_worktree_metadata(base_dir, path)
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


def _bash_completion_script() -> str:
    return r"""_wt_completions() {
    local cur prev words cword
    _init_completion || return

    local wt_bin="${words[0]}"
    local commands="clone init add ad select sl list ls co checkout current cur stash st pr rm remove clean cl setup su run completion"

    if [[ ${cword} -eq 1 ]]; then
        COMPREPLY=( $(compgen -W "${commands} --git-dir --help --version" -- "${cur}") )
        return 0
    fi

    if [[ "${prev}" == "--git-dir" ]]; then
        COMPREPLY=( $(compgen -d -- "${cur}") )
        return 0
    fi

    local subcmd=""
    for w in "${words[@]:1}"; do
        if [[ "${w}" != --* ]]; then
            subcmd="${w}"
            break
        fi
    done

    local wt_names="$(${wt_bin} list --quiet 2>/dev/null)"

    case "${subcmd}" in
        add|ad)
            COMPREPLY=( $(compgen -W "--skip-setup --no-setup --select ${wt_names}" -- "${cur}") )
            ;;
        select|sl|co|checkout|run|rm|remove)
            COMPREPLY=( $(compgen -W "${wt_names}" -- "${cur}") )
            ;;
        clean|cl)
            COMPREPLY=( $(compgen -W "--days --merged --closed --all" -- "${cur}") )
            ;;
        list|ls)
            COMPREPLY=( $(compgen -W "--pr --quiet -q --days --merged --closed --all --sort --asc --desc created last-commit name branch" -- "${cur}") )
            ;;
        stash|st)
            COMPREPLY=( $(compgen -W "${wt_names}" -- "${cur}") )
            ;;
        pr)
            COMPREPLY=( $(compgen -W "add co" -- "${cur}") )
            ;;
        completion)
            COMPREPLY=( $(compgen -W "bash zsh" -- "${cur}") )
            ;;
        *)
            COMPREPLY=( $(compgen -W "${commands}" -- "${cur}") )
            ;;
    esac
}
complete -F _wt_completions wt
"""


def _zsh_completion_script() -> str:
    bash_script = _bash_completion_script()
    return (
        "autoload -U +X bashcompinit && bashcompinit\n"
        + bash_script
        + "compdef _wt_completions wt\n"
    )


def cmd_completion(args: list[str]):
    """wt completion <bash|zsh> - Print shell completion script"""
    if len(args) != 1 or args[0] not in ["bash", "zsh"]:
        print(msg("usage_completion"), file=sys.stderr)
        sys.exit(1)

    shell = args[0]
    if shell == "bash":
        print(_bash_completion_script())
    else:
        print(_zsh_completion_script())


def show_help():
    """Show help message"""
    if is_japanese():
        print("easy-worktree - Git worktree を簡単に管理するための CLI ツール")
        print()
        print("使用方法:")
        print("  wt <command> [options]")
        print()
        print("コマンド:")
        print(f"  {'clone [--bare] <repository_url> [dest_dir]':<55} - リポジトリをクローン")
        print(f"  {'init':<55} - 既存リポジトリをメインリポジトリとして構成")
        print(
            f"  {'add (ad) <作業名> [<base_branch>] [--skip-setup|--no-setup] [--select [<コマンド>...]]':<55} - worktree を追加"
        )
        print(
            f"  {'select (sl) [<作業名>|-] [<コマンド>...]':<55} - 作業ディレクトリを切り替え（fzf対応）"
        )
        print(
            f"  {'list (ls) [--pr] [--quiet|-q] [--days N] [--merged] [--closed] [--all] [--sort ...] [--asc|--desc]':<55} - worktree 一覧を表示"
        )
        print(f"  {'diff (df) [<作業名>] [引数...]':<55} - 変更を表示 (git diff)")
        print(f"  {'config [<キー> [<値>]] [--global|--local]':<55} - 設定の取得/設定")
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
            f"  {'clean (cl) [--days N] [--merged] [--closed] [--all]':<55} - 不要な worktree を削除"
        )
        print(
            f"  {'setup (su)':<55} - 作業ディレクトリを初期化（ファイルコピー・フック実行）"
        )
        print(f"  {'completion <bash|zsh>':<55} - シェル補完スクリプトを出力")
        print()
        print("オプション:")
        print(f"  {'-h, --help':<55} - このヘルプメッセージを表示")
        print(f"  {'-v, --version':<55} - バージョン情報を表示")
        print(f"  {'--git-dir <path>':<55} - Git ディレクトリを明示指定")
    else:
        print("easy-worktree - Simple CLI tool for managing Git worktrees")
        print()
        print("Usage:")
        print("  wt <command> [options]")
        print()
        print("Commands:")
        print(f"  {'clone [--bare] <repository_url> [dest_dir]':<55} - Clone a repository")
        print(f"  {'init':<55} - Configure existing repository as main")
        print(
            f"  {'add (ad) <work_name> [<base_branch>] [--skip-setup|--no-setup] [--select [<command>...]]':<55} - Add a worktree"
        )
        print(
            f"  {'select (sl) [<name>|-] [<command>...]':<55} - Switch worktree selection (fzf support)"
        )
        print(
            f"  {'list (ls) [--pr] [--quiet|-q] [--days N] [--merged] [--closed] [--all] [--sort ...] [--asc|--desc]':<55} - List worktrees"
        )
        print(f"  {'diff (df) [<name>] [args...]':<55} - Show changes (git diff)")
        print(f"  {'config [<key> [<value>]] [--global|--local]':<55} - Get/Set configuration")
        print(f"  {'co/checkout <work_name>':<55} - Show path to a worktree")
        print(f"  {'current (cur)':<55} - Show current worktree name")
        print(
            f"  {'stash (st) <work_name> [<base_branch>]':<55} - Stash current changes and move to new worktree"
        )
        print(f"  {'pr add <number>':<55} - Manage GitHub PRs as worktrees")
        print(f"  {'rm/remove <work_name> [-f|--force]':<55} - Remove a worktree")
        print(
            f"  {'clean (cl) [--days N] [--merged] [--closed] [--all]':<55} - Remove unused/merged worktrees"
        )
        print(
            f"  {'setup (su)':<55} - Setup worktree (copy files and run hooks)"
        )
        print(f"  {'completion <bash|zsh>':<55} - Print shell completion script")
        print()
        print("Options:")
        print(f"  {'-h, --help':<55} - Show this help message")
        print(f"  {'-v, --version':<55} - Show version information")
        print(f"  {'--git-dir <path>':<55} - Explicitly set git directory")


def show_version():
    """Show version information"""
    print("easy-worktree version 0.2.4")


def parse_global_args(argv: list[str]) -> list[str]:
    """グローバル引数を抽出して argv を返す"""
    global GLOBAL_GIT_DIR

    cleaned = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg.startswith("--git-dir="):
            git_dir = arg.split("=", 1)[1]
            if not git_dir:
                print(msg("error", "Missing value for --git-dir"), file=sys.stderr)
                sys.exit(1)
            GLOBAL_GIT_DIR = Path(git_dir).expanduser().resolve()
        elif arg == "--git-dir":
            if i + 1 >= len(argv):
                print(msg("error", "Missing value for --git-dir"), file=sys.stderr)
                sys.exit(1)
            GLOBAL_GIT_DIR = Path(argv[i + 1]).expanduser().resolve()
            i += 1
        else:
            cleaned.append(arg)
        i += 1

    return cleaned


def main():
    """メインエントリポイント"""
    # ヘルプとバージョンのオプションは設定なしでも動作する
    raw_args = parse_global_args(sys.argv[1:])
    if len(raw_args) < 1:
        show_help()
        sys.exit(1)

    command = raw_args[0]
    args = raw_args[1:]

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
    elif command in ["diff", "df"]:
        cmd_diff(args)
    elif command == "config":
        cmd_config(args)
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
    elif command == "run":
        cmd_run(args)
    elif command == "completion":
        cmd_completion(args)
    else:
        # その他のコマンドは git worktree にパススルー
        cmd_passthrough([command] + args)


if __name__ == "__main__":
    main()
