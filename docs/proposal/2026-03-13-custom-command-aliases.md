# Custom Command Aliases (カスタムエイリアス機能)

## Summary
`easy-worktree` の設定ファイル (`config.toml`) において、`wt` コマンドに対するカスタムエイリアスを定義できるようにする提案です。

## Problem
ユーザーは日々の開発の中で、特定のオプションを組み合わせた `wt` コマンドを頻繁に実行します（例: `wt clean --merged --days 14 --yes` や `wt list --sort last-commit --desc`、あるいは `wt run lazygit` など）。
現在これらを短縮するには、ユーザー自身がシェルのエイリアス（`.zshrc` など）を定義する必要があります。しかし、シェルエイリアスはプロジェクトローカルな設定としてチームで共有することが難しく、また `wt <alias>` のような統一感のある直感的な呼び出しができません。

## Proposal
グローバル、またはプロジェクトローカルの `.wt/config.toml` に `[aliases]` セクションを追加し、任意のサブコマンドと引数の組み合わせを定義できるようにします。

設定例 (`config.toml`):
```toml
[aliases]
clm = "clean --merged"
recent = "list --sort last-commit --desc"
lg = "run lazygit"
```

これにより、ユーザーは以下のように直感的にエイリアスを呼び出せるようになります。
```bash
$ wt clm
# `wt clean --merged` として実行される

$ wt recent --pr
# `wt list --sort last-commit --desc --pr` のように、後続の引数も渡される
```

## Inspiration
- `git alias` (`~/.gitconfig` の `[alias]` セクションによる短縮コマンドの定義)
- `gh alias` (`gh` CLI 組み込みのエイリアス機能)
- `npm run-script` / `cargo` のエイリアス機能

## Expected Daily Benefit
- よく使う長いコマンドや複雑なオプション指定を短縮でき、日々のタイピングコストと認知負荷を下げることができる。
- `wt run` などの外部コマンド呼び出しを短縮（`wt lg` -> `wt run lazygit` など）することで、`wt` を起点とした操作フローがよりスムーズになる。
- `.wt/config.toml` にエイリアスを定義してリポジトリにコミットすることで、「このプロジェクトで推奨されるワークツリーの一括操作」をチーム全員で簡単に共有できる。

## Scope and Non-Goals
- **Scope**: `wt` のエントリーポイントでの引数展開処理の追加。コマンドラインの第1引数が `aliases` に存在する場合、その定義内容に展開してから後続の引数を結合して実行する。
- **Non-Goals**: パイプ（`|`）やリダイレクト（`>`）など、シェル固有の複雑な構文のサポート。あくまで `easy-worktree` 自身のコマンドおよび引数の展開にスコープを留めます。

## Risks or Open Questions
- **名前の衝突**: 将来的に `easy-worktree` に新しい組み込みコマンド（例: `recent` など）が追加された場合、ユーザー定義のエイリアスと名前が衝突する可能性があります。組み込みコマンドを常に優先し、衝突時には warning を出すなどの安全策が必要です。
- **自己参照ループ**: エイリアスが別のエイリアスを呼び出す（再帰的な定義）場合の無限ループを防ぐため、展開は1回のみにするか、深さ制限を設ける必要があります。

## Suggested Rollout
1. `config.toml` パーサーに `[aliases]` テーブルの読み込み機能を追加する。
2. CLI の実行エントリポイントで、受け取ったサブコマンドが組み込みコマンドに存在しない場合、エイリアス設定から展開を試みるロジックを実装する。
3. エイリアス展開時の引数結合ロジックと、組み込みコマンドとの衝突検知ロジックを追加する。
4. ドキュメントに `[aliases]` の使い方と設定例を追記する。
