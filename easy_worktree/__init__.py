#!/usr/bin/env python3
"""
Git worktree を簡単に管理するための CLI ツール
"""
import os
import subprocess
import sys
from pathlib import Path
import re


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
        'en': 'Usage: wt add <work_name> [<branch>]',
        'ja': '使用方法: wt add <作業名> [<branch>]'
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


def cmd_add(args: list[str]):
    """wt add <work_name> - Add a worktree"""
    if len(args) < 1:
        print(msg('usage_add'), file=sys.stderr)
        sys.exit(1)

    base_dir = find_base_dir()
    if not base_dir:
        print(msg('error', msg('base_not_found')), file=sys.stderr)
        print(msg('run_in_wt_dir'), file=sys.stderr)
        sys.exit(1)

    work_name = args[0]
    branch = args[1] if len(args) > 1 else work_name

    # worktree のパスを決定（_base の親ディレクトリに作成）
    worktree_path = base_dir.parent / work_name

    if worktree_path.exists():
        print(msg('error', msg('already_exists', worktree_path)), file=sys.stderr)
        sys.exit(1)

    # ブランチを最新に更新
    print(msg('fetching'))
    run_command(["git", "fetch", "--all"], cwd=base_dir)

    # worktree を追加
    print(msg('creating_worktree', worktree_path))
    result = run_command(
        ["git", "worktree", "add", str(worktree_path), branch],
        cwd=base_dir,
        check=False
    )

    if result.returncode == 0:
        print(msg('completed_worktree', worktree_path))
    else:
        # エラーメッセージを表示
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        sys.exit(1)


def cmd_list(args: list[str]):
    """wt list - List worktrees"""
    base_dir = find_base_dir()
    if not base_dir:
        print(msg('error', msg('base_not_found')), file=sys.stderr)
        sys.exit(1)

    result = run_command(["git", "worktree", "list"] + args, cwd=base_dir)
    print(result.stdout, end='')


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
        print("  clone <repository_url>   - リポジトリをクローン")
        print("  init                      - 既存リポジトリを WT_<repo>/_base/ に移動")
        print("  add <作業名> [<branch>]  - worktree を追加")
        print("  list                      - worktree 一覧を表示")
        print("  rm <作業名>               - worktree を削除")
        print("  remove <作業名>           - worktree を削除")
        print("  <git-worktree-command>    - その他の git worktree コマンド")
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
        print("  clone <repository_url>   - Clone a repository")
        print("  init                      - Move existing repo to WT_<repo>/_base/")
        print("  add <work_name> [<branch>] - Add a worktree")
        print("  list                      - List worktrees")
        print("  rm <work_name>            - Remove a worktree")
        print("  remove <work_name>        - Remove a worktree")
        print("  <git-worktree-command>    - Other git worktree commands")
        print()
        print("Options:")
        print("  -h, --help     - Show this help message")
        print("  -v, --version  - Show version information")


def show_version():
    """Show version information"""
    print("easy-worktree version 0.0.1")


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
    else:
        # その他のコマンドは git worktree にパススルー
        cmd_passthrough([command] + args)


if __name__ == "__main__":
    main()
