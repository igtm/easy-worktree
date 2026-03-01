import sys
import shutil
import subprocess
from pathlib import Path

def run_command(cmd):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return result.stdout.strip(), result.returncode
    except Exception as e:
        return str(e), 1

def doctor():
    print("🩺 easy-worktree doctor")
    print("=======================")

    print("\n[System]")
    print(f"Python: {sys.version.split(' ')[0]}")
    
    # Check Git
    git_path = shutil.which("git")
    if git_path:
        out, code = run_command(["git", "--version"])
        print(f"Git: {out} ({git_path})")
    else:
        print("Git: Not found ❌")
        
    # Check gh
    gh_path = shutil.which("gh")
    if gh_path:
        out, code = run_command(["gh", "--version"])
        print(f"GitHub CLI (gh): {out.splitlines()[0]} ({gh_path})")
    else:
        print("GitHub CLI (gh): Not found (Optional)")

    # Check fzf
    fzf_path = shutil.which("fzf")
    if fzf_path:
        out, code = run_command(["fzf", "--version"])
        print(f"fzf: {out.splitlines()[0]} ({fzf_path})")
    else:
        print("fzf: Not found (Optional, used for interactive selection)")

doctor()
