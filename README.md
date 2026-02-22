![hero](hero.png)

# easy-worktree

A CLI tool for easy Git worktree management.

[日本語版 README](README_ja.md)

## Overview

`easy-worktree` simplifies git worktree management.
It keeps the root of your git repository as your primary working area (main), while managing other worktrees in a subdirectory (default: `.worktrees/`).

### Key Features

- **Smart Selection**: Quickly switch between worktrees with `wt select`. "Jump" into a new shell instantly without any special setup.
- **Auto Setup**: Automatically copy files (like `.env`) and run hooks to prepare each worktree.
- **Clear Status**: `wt list` shows worktree branches, their status (clean/dirty), and associated GitHub PRs in a beautiful table.
- **Smart Cleanup**: Easily batch remove merged branches or old unused worktrees.
- **Two-letter shortcuts**: Fast execution with shortcuts like `ad`, `ls`, `sl`, `su`, `st`, `cl`.

## Prerequisites

`easy-worktree` requires the following:

- **Git**: 2.34 or higher recommended.
- **GitHub CLI (gh)**: Required for PR features (`wt list --pr`, `wt pr add`, `wt clean --merged`). [Installation guide](https://cli.github.com/).

## Installation

```bash
pip install easy-worktree
```

Or install the development version:

```bash
git clone https://github.com/igtm/easy-worktree.git
cd easy-worktree
pip install -e .
```

## Usage

### Getting Started

#### Clone a new repository

```bash
wt clone https://github.com/user/repo.git
```

This clones the repository and initializes `easy-worktree` configuration.

For bare repositories, you can also use plain git:

```bash
git clone --bare https://github.com/user/repo.git sandbox.git
git --git-dir=sandbox.git worktree add sandbox/main main
```

Or let `wt` do it for you:

```bash
wt clone --bare https://github.com/user/repo.git sandbox.git
```

`wt clone --bare` automatically:
- clones as bare repository (`sandbox.git`)
- creates base-branch worktree (`sandbox/<default-branch>`)
- initializes `.wt/` in that base-branch worktree

#### Initialize an existing repository

```bash
cd my-repo/
wt init
```

Initializes `easy-worktree` in the current repository. Your main repository stays at the project root.

For bare repositories:

```bash
wt --git-dir=/path/to/sandbox.git init
```

If no non-bare worktree exists yet, `wt init` will automatically create a base-branch worktree and initialize `.wt/` there.

### Managing Worktrees

#### Add a worktree (shortcut: `ad`)

```bash
wt add feature-1
```

This creates the following structure:

```
my-repo/ (main)
  .worktrees/
    feature-1/  # Your new worktree
  .wt/
  ...
```

You can also specify a base branch:

```bash
wt add feature-1 main
```

If you are operating from a bare repository, pass `--git-dir` globally:

```bash
wt --git-dir=/path/to/sandbox.git add feature-1 main
```

#### Skip Setup

If you want to create a worktree without running the automatic setup (file copy and hooks):

```bash
wt add feature-1 --skip-setup
```

You can also use the alias flag:

```bash
wt add feature-1 --no-setup
```

Create and immediately switch to the new worktree:

```bash
wt add feature-1 --select
wt add feature-1 --select npm test
```

#### List worktrees

```bash
wt list
wt list --pr  # Show PR information
wt list --sort created --desc
wt list --sort last-commit --asc
wt list --merged
wt list --days 30
```

`wt list` shows both `Created` and `Last Commit` columns.
Default sort is `Created` descending.


#### Stash and Move (shortcut: `st`)

Quickly stash your current changes and move them to a new worktree.

```bash
wt stash feature-2
```

#### Switch Worktree (shortcut: `sl`)

```bash
wt select feature-1
```

Running `wt select` will **automatically "jump"** you into the worktree directory by starting a new subshell.

- **Prompt**: Shows a `(wt:feature-1)` indicator.
- **Terminal Title**: Updates the window title to `wt:feature-1`.
- **Tmux**: Updates the tmux window name to `wt:feature-1` if running inside tmux.

To return to your original directory, simply type `exit` or press `Ctrl-D`.

*   **Interactive Mode**: Running `wt select` without arguments opens an interactive picker using `fzf`.
*   **Nesting Control**: If you are already in a `wt` subshell, it will warn you to avoid confusing nesting.

You can execute a command after switching:

```bash
wt select feature-1 npm test
```

Switch back to your previous selection:

```bash
wt select -
```

#### PR Management

Fetch a PR and create a worktree for it. (Requires `gh` CLI)

```bash
wt pr add 123    # Fetches PR #123 and creates 'pr@123' worktree
```

#### Remove a worktree

```bash
wt rm feature-1
```

Removes the worktree and its directory.

### Useful Features

#### Setup Worktree (shortcut: `su`)

Initialize the current worktree by copying required files and running the `post-add` hook.

```bash
wt setup
```

#### Diff Tool (shortcut: `df`)

```bash
wt diff
wt diff <name>
```

By default, it runs `git diff`. You can configure it to use `lumen` (a rich diff viewer):

```bash
wt config diff.tool lumen --global
```

When configured, `wt diff` will run `lumen diff --watch` in the target worktree.

#### Configuration Management (shortcut: `config`)

Manage settings globally or locally:

```bash
wt config <key> <value> [--global|--local]
wt config <key>           # Get value
wt config                 # Show current merged configuration
```

#### TUI Companion

For a more visual experience, check out [easy-worktree-tui](https://github.com/igtm/easy-worktree-tui).

```bash
pip install easy-worktree-tui
wtt
```

It provides a side-by-side view of worktrees and their diffs, with interactive add/remove features.

#### Visualization and External Tools

When you switch to a worktree using `wt select`, the following features are automatically enabled:
- **Terminal Title**: The window or tab title is updated to `wt:worktree-name`.
- **Tmux**: If you are inside tmux, the window name is automatically renamed to `wt:worktree-name`.

You can also use the `wt current` (or `cur`) command to display the current worktree name in external tools.

##### Tmux Status Bar
Add the following to your `.tmux.conf` to show the worktree name in your status line:
```tmux
set -g status-right "#(wt current) | %Y-%m-%d %H:%M"
```

##### Zsh / Bash Prompt
You can customize your prompt using the `$WT_SESSION_NAME` environment variable.

**Zsh (.zshrc)**:
```zsh
RPROMPT='${WT_SESSION_NAME:+"(wt:$WT_SESSION_NAME)"} '"$RPROMPT"
```

**Bash (.bashrc)**:
```bash
PS1='$(if [ -n "$WT_SESSION_NAME" ]; then echo "($WT_SESSION_NAME) "; fi)'$PS1
```

##### Tab Completion
Enable completion with one line:

```bash
# zsh
eval "$(wt completion zsh)"

# bash
eval "$(wt completion bash)"
```

Persist by adding the same line to `~/.zshrc` or `~/.bashrc`.

##### Starship
Add a custom module to your `starship.toml`:
```toml
[custom.easy_worktree]
command = "wt current"
when = 'test -n "$WT_SESSION_NAME"'
format = "via [$symbol$output]($style) "
symbol = "🌳 "
style = "bold green"
```

##### Powerlevel10k
Integrate beautiful worktree indicators by adding a custom segment to `.p10k.zsh`:

1. Add `easy_worktree` to `POWERLEVEL9K_LEFT_PROMPT_ELEMENTS`.
2. Define the following function:
```zsh
function prompt_easy_worktree() {
  if [[ -n $WT_SESSION_NAME ]]; then
    p10k segment -f 255 -b 28 -i '🌳' -t "wt:$WT_SESSION_NAME"
  fi
}
```


#### Cleanup (shortcut: `cl`)

```bash
wt clean --merged
wt clean --closed  # Remove worktrees for closed (unmerged) PRs
wt clean --days 30
wt clean --all
```

Deletion conditions are:
- `wt clean --all`: removes all clean worktrees (except main/base worktree and symlink-targeted worktrees), without confirmation.
- `wt clean --days N`: removes clean worktrees whose directory creation age is `>= N` days.
- `wt clean --merged`: removes clean worktrees whose branch is merged into default branch, or is found in merged PR heads from `gh pr list --state merged`.
- `wt clean --closed`: removes clean worktrees whose branch appears in closed PR heads from `gh pr list --state closed`.

Notes:
- Worktrees with local changes are never removed by `wt clean`.
- Main/base worktree is never removed.
- For `--merged`, if branch SHA equals default branch SHA and it is not in merged PR heads, removal is skipped as a safeguard.
- Confirmation prompt appears unless `--all` is specified.
- `Created` time is pinned from metadata under `$XDG_CONFIG_HOME/easy-worktree/` (not live filesystem ctime).

#### Command Reference

```bash
wt [--git-dir <path> | --git-dir=<path>] <command> ...
wt add <work_name> [<base_branch>] [--skip-setup|--no-setup] [--select [<command>...]]
wt select [<name>|-] [<command>...]
wt run <name> <command>...
wt rm <work_name> [-f|--force]
wt list [--pr] [--quiet|-q] [--days N] [--merged] [--closed] [--all] [--sort created|last-commit|name|branch] [--asc|--desc]
wt clean [--days N] [--merged] [--closed] [--all]
wt setup
wt completion <bash|zsh>
```



### Configuration

Customize behavior in `.wt/config.toml`:

```toml
worktrees_dir = ".worktrees"   # Directory where worktrees are created
setup_files = [".env"]          # Files to auto-copy during setup
setup_source_dir = ""           # Optional. Override setup file source directory
```

`setup_source_dir` supports relative paths (resolved from repository base) or absolute paths.
When empty, `wt` auto-detects the source directory:
- normal repository: repository root
- bare repository: default-branch worktree (fallback to first non-bare worktree)

#### Local Configuration Override

You can create `.wt/config.local.toml` to override settings locally. This file is automatically added to `.gitignore` and ignores `config.toml` settings.

#### `.wt/` Directory Behavior

- `.wt/` is created under a working-tree directory (never inside bare git object directory).
- In normal repositories, `.wt/` is at repository root.
- With `--git-dir=<path>`:
  - if `<path>` points to `.git`, `.wt/` is in that repository root
  - if `<path>` points to a bare repo (e.g. `sandbox.git`), `.wt/` is created in the preferred non-bare worktree (default-branch worktree first, otherwise first available non-bare worktree)
- If no non-bare worktree exists for a bare repo, `wt` reports an error and asks you to create one first.

`wt` currently stores these files in `.wt/`:
- `config.toml`
- `config.local.toml` (optional, ignored)
- `post-add`
- `post-add.local` (optional, ignored)
- `last_selection` (ignored)

Metadata storage:
- worktree creation metadata is stored under `$XDG_CONFIG_HOME/easy-worktree/` (fallback: `~/.config/easy-worktree/`)

## Hooks

You can define scripts to run automatically after `wt add`.
Templates are created in `.wt/post-add` upon initialization.

## License

MIT License
