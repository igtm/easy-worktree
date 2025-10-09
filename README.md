# easy-worktree

A CLI tool for easy Git worktree management

[日本語版 README](README_ja.md)

## Overview

`easy-worktree` simplifies git worktree management by establishing conventions, reducing the cognitive load of managing multiple working trees.

### Key Features

- **Standardized directory structure**: Creates a `_base/` directory within `WT_<repository_name>/` as the main repository
- **Easy worktree management**: Create and remove worktrees from `_base/`
- **Automatic branch updates**: Runs `git fetch --all` automatically when creating worktrees

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

### Clone a new repository

```bash
wt clone https://github.com/user/repo.git
```

This creates the following structure:

```
WT_repo/
  _base/  # Main repository (typically don't modify directly)
```

### Convert an existing repository to easy-worktree structure

```bash
cd my-repo/
wt init
```

The current directory will be moved to `../WT_my-repo/_base/`.

### Add a worktree

```bash
cd WT_repo/
wt add feature-1
```

This creates the following structure:

```
WT_repo/
  _base/
  feature-1/  # Working worktree
```

You can also specify a branch name:

```bash
wt add feature-1 main
```

Create a worktree and set an alias at the same time:

```bash
wt add feature-123 --alias current    # Create feature-123 and set 'current' alias
```

### List worktrees

```bash
wt list
```

### Remove a worktree

```bash
wt rm feature-1
# or
wt remove feature-1
```

### Initialization hook (post-add)

You can set up a script to run automatically after creating a worktree.

**Hook location**: `_base/.wt/post-add`

**Automatic creation**: When you run `wt clone` or `wt init`, a template file is automatically created at `_base/.wt/post-add` (won't overwrite if it already exists). Edit this file to describe your project-specific initialization process.

```bash
# Example: editing the hook script
vim WT_repo/_base/.wt/post-add
```

```bash
#!/bin/bash
set -e

echo "Initializing worktree: $WT_WORKTREE_NAME"

# Install npm packages
if [ -f package.json ]; then
    npm install
fi

# Copy .env file
if [ -f "$WT_BASE_DIR/.env.example" ]; then
    cp "$WT_BASE_DIR/.env.example" .env
fi

echo "Setup completed!"
```

Don't forget to make it executable:

```bash
chmod +x WT_repo/_base/.wt/post-add
```

**Available environment variables**:
- `WT_WORKTREE_PATH`: Path to the created worktree
- `WT_WORKTREE_NAME`: Name of the worktree
- `WT_BASE_DIR`: Path to the `_base/` directory
- `WT_BRANCH`: Branch name
- `WT_ACTION`: Action name (`add`)

The hook runs within the newly created worktree directory.

### List worktrees with details

```bash
wt list --verbose           # Show creation time, last commit, status
wt list --sort age          # Sort by creation time
wt list --sort name         # Sort by name
```

### Clean up unused worktrees

Remove clean (no changes) worktrees in batch.

```bash
wt clean --dry-run          # Preview what will be removed
wt clean --days 30          # Remove clean worktrees older than 30 days
wt clean --all              # Remove all clean worktrees without confirmation
```

### Create worktree aliases

Create symbolic link shortcuts to frequently used worktrees.

```bash
wt alias current feature-123    # Create alias named 'current'
wt alias dev feature-xyz        # Create alias named 'dev'
wt alias current hoge3          # Automatically override existing alias
wt alias --list                 # List all aliases
wt alias --remove current       # Remove an alias
```

### Check status of all worktrees

View git status of all worktrees at once.

```bash
wt status                   # Show status of all worktrees
wt status --dirty           # Show only worktrees with changes
wt status --short           # Concise display
```

### Other git worktree commands

`wt` also supports other git worktree commands:

```bash
wt prune
wt lock <worktree>
wt unlock <worktree>
```

## Directory Structure

```
WT_<repository_name>/     # Project root directory
  _base/                   # Main git repository
  feature-1/               # Worktree 1
  bugfix-123/              # Worktree 2
  ...
```

You can run `wt` commands from `WT_<repository_name>/` or from within any worktree directory.

## Requirements

- Python >= 3.11
- Git

## License

MIT License

## Contributing

Issues and Pull Requests are welcome!
