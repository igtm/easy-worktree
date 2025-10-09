#!/usr/bin/env python3
"""
Git worktree を簡単に管理するための CLI ツール
"""
import subprocess
import sys
from pathlib import Path
import re


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
        print(f"エラー: {e.stderr}", file=sys.stderr)
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
    """wt clone <repository_url> - リポジトリをクローン"""
    if len(args) < 1:
        print("使用方法: wt clone <repository_url>", file=sys.stderr)
        sys.exit(1)

    repo_url = args[0]
    repo_name = get_repository_name(repo_url)

    # WT_<repository_name>/_base にクローン
    parent_dir = Path(f"WT_{repo_name}")
    base_dir = parent_dir / "_base"

    if base_dir.exists():
        print(f"エラー: {base_dir} はすでに存在します", file=sys.stderr)
        sys.exit(1)

    parent_dir.mkdir(exist_ok=True)

    print(f"クローン中: {repo_url} -> {base_dir}")
    run_command(["git", "clone", repo_url, str(base_dir)])
    print(f"完了: {base_dir} にクローンしました")


def cmd_init(args: list[str]):
    """wt init - 既存の git リポジトリを WT_<repo>/_base/ に移動"""
    current_dir = Path.cwd()

    # 現在のディレクトリが git リポジトリか確認
    result = run_command(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=current_dir,
        check=False
    )

    if result.returncode != 0:
        print("エラー: 現在のディレクトリは git リポジトリではありません", file=sys.stderr)
        sys.exit(1)

    git_root = Path(result.stdout.strip())

    # カレントディレクトリがリポジトリのルートでない場合はエラー
    if git_root != current_dir:
        print(f"エラー: リポジトリのルートディレクトリ {git_root} で実行してください", file=sys.stderr)
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
        print(f"エラー: {wt_parent_dir} はすでに存在します", file=sys.stderr)
        sys.exit(1)

    # WT_<repo>/ ディレクトリを作成
    print(f"{wt_parent_dir} を作成中...")
    wt_parent_dir.mkdir(exist_ok=True)

    # 現在のディレクトリを WT_<repo>/_base/ に移動
    print(f"{current_dir} -> {new_base_dir} に移動中...")
    current_dir.rename(new_base_dir)

    print(f"完了: {new_base_dir} に移動しました")
    print(f"次回から {wt_parent_dir} で wt コマンドを使用してください")


def cmd_add(args: list[str]):
    """wt add <作業名> - worktree を追加"""
    if len(args) < 1:
        print("使用方法: wt add <作業名> [<branch>]", file=sys.stderr)
        sys.exit(1)

    base_dir = find_base_dir()
    if not base_dir:
        print("エラー: _base/ ディレクトリが見つかりません", file=sys.stderr)
        print("WT_<repository_name>/ ディレクトリ内で実行してください", file=sys.stderr)
        sys.exit(1)

    work_name = args[0]
    branch = args[1] if len(args) > 1 else work_name

    # worktree のパスを決定（_base の親ディレクトリに作成）
    worktree_path = base_dir.parent / work_name

    if worktree_path.exists():
        print(f"エラー: {worktree_path} はすでに存在します", file=sys.stderr)
        sys.exit(1)

    # ブランチを最新に更新
    print("リモートから最新情報を取得中...")
    run_command(["git", "fetch", "--all"], cwd=base_dir)

    # worktree を追加
    print(f"worktree を作成中: {worktree_path}")
    result = run_command(
        ["git", "worktree", "add", str(worktree_path), branch],
        cwd=base_dir,
        check=False
    )

    if result.returncode == 0:
        print(f"完了: {worktree_path} に worktree を作成しました")
    else:
        # エラーメッセージを表示
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        sys.exit(1)


def cmd_list(args: list[str]):
    """wt list - worktree 一覧を表示"""
    base_dir = find_base_dir()
    if not base_dir:
        print("エラー: _base/ ディレクトリが見つかりません", file=sys.stderr)
        sys.exit(1)

    result = run_command(["git", "worktree", "list"] + args, cwd=base_dir)
    print(result.stdout, end='')


def cmd_remove(args: list[str]):
    """wt rm/remove <作業名> - worktree を削除"""
    if len(args) < 1:
        print("使用方法: wt rm <作業名>", file=sys.stderr)
        sys.exit(1)

    base_dir = find_base_dir()
    if not base_dir:
        print("エラー: _base/ ディレクトリが見つかりません", file=sys.stderr)
        sys.exit(1)

    work_name = args[0]

    # worktree を削除
    print(f"worktree を削除中: {work_name}")
    result = run_command(
        ["git", "worktree", "remove", work_name],
        cwd=base_dir,
        check=False
    )

    if result.returncode == 0:
        print(f"完了: {work_name} を削除しました")
    else:
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        sys.exit(1)


def cmd_passthrough(args: list[str]):
    """その他の git worktree コマンドをパススルー"""
    base_dir = find_base_dir()
    if not base_dir:
        print("エラー: _base/ ディレクトリが見つかりません", file=sys.stderr)
        sys.exit(1)

    result = run_command(["git", "worktree"] + args, cwd=base_dir, check=False)
    print(result.stdout, end='')
    if result.stderr:
        print(result.stderr, end='', file=sys.stderr)
    sys.exit(result.returncode)


def show_help():
    """ヘルプメッセージを表示"""
    print("easy-worktree - Git worktree を簡単に管理するための CLI ツール")
    print()
    print("使用方法:")
    print("  wt <command> [options]")
    print()
    print("コマンド:")
    print("  clone <repository_url>  - リポジトリをクローン")
    print("  init                     - 既存リポジトリを WT_<repo>/_base/ に移動")
    print("  add <作業名> [<branch>] - worktree を追加")
    print("  list                     - worktree 一覧を表示")
    print("  rm <作業名>              - worktree を削除")
    print("  remove <作業名>          - worktree を削除")
    print("  <git-worktree-command>   - その他の git worktree コマンド")
    print()
    print("オプション:")
    print("  -h, --help     - このヘルプメッセージを表示")
    print("  -v, --version  - バージョン情報を表示")


def show_version():
    """バージョン情報を表示"""
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
