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

#### Initialize an existing repository

```bash
cd my-repo/
wt init
```

Initializes `easy-worktree` in the current repository. Your main repository stays at the project root.

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

#### List worktrees

```bash
wt list
wt list --pr  # Show PR information
```


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
```



### Configuration

Customize behavior in `.wt/config.toml`:

```toml
worktrees_dir = ".worktrees"   # Directory where worktrees are created
setup_files = [".env"]          # Files to auto-copy during setup
auto_copy_on_add = true         # Enable auto-copy on worktree creation
```

## Hooks

You can define scripts to run automatically after `wt add`.
Templates are created in `.wt/post-add` upon initialization.

## License

MIT License
