# `wt select` の Tmux ネイティブ統合（サブシェル回避とウィンドウ自動作成）

## Summary
`wt select` でワークツリーを切り替える際、現在の「サブシェルを起動してネストする」方式に加え、Tmux ユーザー向けに「Tmux の新規ウィンドウ（またはセッション）を作成してそこへ切り替える」バックエンドを選択できるようにする提案。

## Problem
現在、`wt select <name>` は `bash` や `zsh` のサブシェルを起動することでディレクトリ移動を実現しています。
しかし、Tmux を常用している開発者の場合、以下の課題があります：
1. **ネストの発生と `exit` の手間**: 作業を終えて別のワークツリーに移る際、不要になったサブシェルがスタックとして溜まるか、都度 `exit` を叩く必要があります。
2. **Tmux のペイン/ウィンドウ管理との不整合**: 理想的には「1ワークツリー = 1 Tmux ウィンドウ（またはセッション）」として管理したいですが、現状は1つのウィンドウ内でシェルが深くネストしてしまいます。
3. すでに Tmux 上で `wt select` を実行した際、既存のペインが別のワークツリーのコンテキストに上書きされてしまい、並行作業がしづらいことがあります。

## Proposal
`wt config select.backend tmux` のように設定可能にし、Tmux 環境下ではサブシェル起動をバイパスしてネイティブに Tmux コマンドを発行するようにします。

- **動作イメージ**:
  1. `wt select feature-A` を実行。
  2. `easy-worktree` が `tmux new-window -c <feature-A-path> -n "wt:feature-A"` 相当のコマンドを実行。
  3. 即座に新しく作成されたウィンドウ（すでに存在する場合はそのウィンドウ）へフォーカスが移る。
- **設定オプション**:
  - `select.backend = "subshell"` (デフォルト)
  - `select.backend = "tmux-window"` (Tmux ウィンドウを作成)
  - `select.backend = "tmux-session"` (Tmux セッションを作成)

## Inspiration
- **tmux-sessionizer (ThePrimeagen)**: fzf でプロジェクトを選び、Tmux セッションを自動作成・アタッチするワークフロー。
- 既存の `wt select` のディレクトリ移動の手軽さを、Tmux のライフサイクル管理に拡張する発想です。

## Expected Daily Benefit
- Tmux ヘビーユーザーにとって、シェルのネストを気にすることなく、複数のワークツリーを独立したウィンドウとしてシームレスに行き来できるようになります。
- 終了時は単に `exit` (ウィンドウ破棄) だけでよく、元の作業コンテキストが汚染されません。
- 「この機能の調査はウィンドウ1、あのバグ修正はウィンドウ2」という並行作業が、`wt select` だけで完結します。

## Scope and Non-Goals
- **Non-Goal**: Tmux 以外のターミナルマルチプレクサ (Zellij, screen 等) の全サポートを最初から実装すること。まずは利用者の多い Tmux に絞る。
- **Non-Goal**: ターミナルエミュレータ自体のタブ操作（例: iTerm2 のタブを AppleScript で開くなど）。環境依存が強すぎるため対象外。

## Risks or Open Questions
- すでに Tmux の外（アタッチ前）で `wt select` を叩いた場合、どうフォールバックするか？ (`subshell` にフォールバックするか、`tmux new-session` を起動するか)
- ウィンドウ名が重複した場合のハンドリング（すでに `wt:feature-A` が開かれている場合はそこにフォーカスを移すだけにするのが理想的）。

## Suggested Rollout
1. まず実験的機能として環境変数 `WT_EXPERIMENTAL_TMUX=1` で有効化できるように実装。
2. 動作確認後、`wt config select.backend` として正式な設定項目に追加。
3. `README.md` の「Tmux 連携」セクションに、この推奨設定を追記する。
