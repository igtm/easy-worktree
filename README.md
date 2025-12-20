![hero](hero.png)

# easy-worktree

A CLI tool for easy Git worktree management.

[日本語版 README](README_ja.md)

## Overview

`easy-worktree` simplifies git worktree management.
It keeps the root of your git repository as your primary working area (main), while managing other worktrees in a subdirectory (default: `.worktrees/`).

### Key Features

- **Standardized directory structure**: Worktrees are created in a `.worktrees/` subdirectory (configurable). Keeps your root directory clean.
- **Auto Sync**: Automatically sync files ignored by git (like `.env`) from the root to each worktree.
- **Clear Status**: `wt list` shows worktree branches, their status (clean/dirty), and associated GitHub PRs in a beautiful table.
- **Smart Cleanup**: Easily batch remove merged branches or old unused worktrees.
- **Two-letter shortcuts**: Fast execution with shortcuts like `ad`, `ls`, `st`, `sy`, `cl`.

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

#### Sync configuration files (shortcut: `sy`)

Sync files like `.env` that are not in git from the root to your worktrees.

```bash
wt sync .env
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
sync_files = [".env"]          # Files to auto-sync
auto_copy_on_add = true         # Enable auto-sync on add
```

## Hooks

You can define scripts to run automatically after `wt add`.
Templates are created in `.wt/post-add` upon initialization.

## License

MIT License
