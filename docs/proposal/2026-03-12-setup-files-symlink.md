# セットアップファイル (setup_files) の Symlink サポート

## Summary
`wt add` 実行時の自動セットアップにおいて、ファイルを「コピー」するだけでなく、「シンボリックリンク」として配置できるようにする設定（例: `setup_links`）の追加提案です。

## Problem
現在の `easy-worktree` では、`setup_files = [".env"]` のように設定すると、base ブランチ（またはルート）から対象ファイルが「コピー」されます。
しかし、ローカルでの開発中に「新しい API キーを `.env` に追加した」「ローカル DB のパスワードを変更した」という場合、既に作成済みの複数の worktree の `.env` ファイルを手動で全て更新して回る必要があり、非常に手間がかかります。コピーされたファイルは同期されないため、複数 worktree を横断して開発していると、特定の worktree だけ環境変数の不整合でエラーになるという事故（摩擦）が頻繁に発生します。

## Proposal
`config.toml` に新しい設定項目を追加し、コピーではなくシンボリックリンク（symlink）を作成できるようにします。

**設定例 (専用の配列を用意):**
```toml
setup_files = []       # コピーしたいファイル（既存動作）
setup_links = [".env"] # symlink したいファイル（新機能）
```

`wt add`（および `wt setup`）の実行時、`setup_links` に指定されたファイルは、`setup_source_dir` にある実体を指す symlink として対象 worktree 内に作成されます。

## Inspiration
- **pnpm / uv**: パッケージや依存環境の実体を1箇所に持ち、symlink 等で各プロジェクトから参照させることで、同期の手間とディスク容量を省くアプローチ。
- **dotfiles 管理ツール (stow, chezmoi 等)**: 実体を一元管理し、必要な場所に symlink を張る構成。

## Expected Daily Benefit
ベースとなる `.env` を1箇所（ルートやベース worktree）で更新するだけで、すべての worktree に即座にその変更が反映されます。「この worktree ではなぜか起動しないと思ったら `.env` が古かった」という無駄なデバッグ時間を完全にゼロにでき、日々の並行作業の安定性が大きく向上します。

## Scope and Non-Goals
- **Scope**: 設定ファイルでの `setup_links` 指定のサポートと、`wt add` / `wt setup` 時の symlink 作成処理（絶対パスまたは相対パスでの安全なリンク作成）。
- **Non-Goals**: Windows 環境における symlink 作成の権限問題などに対する過剰なフォールバック（基本は Unix 系の標準的な `ln -s` の挙動に合わせ、Windows は OS 側の設定に委ねるなど、実装を極力シンプルに保つ）。

## Risks or Open Questions
- **編集・削除の影響**: worktree 側で `.env` をエディタで編集した場合、実体も書き換わるため便利ですが、それを意図しないユーザーには既存の「コピー」を使い続けてもらうようドキュメントで案内する必要があります。
- **ベースディレクトリの解決**: bare リポジトリ構成の場合、リンク先（実体）のパスをどう解決するかが課題になります。現在でも `setup_source_dir` を自動解決する仕組みがあるため、そこへの絶対パスリンクにするのが最も安全と考えられます。

## Suggested Rollout
1. `config.toml` に `setup_links` を追加し、CLI で読み込めるようにする。
2. `wt setup` のロジック内で、対象が `setup_links` の場合はファイルのコピーではなく `os.symlink` によるリンク作成を行う分岐を追加する。
3. bare および non-bare リポジトリでのパス解決が正しく行われるかのテストを追加する。