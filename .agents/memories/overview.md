# easy-worktree 開発オーバービュー

## 開発フロー
1. **実装**: 変更要件に沿ってコードを更新します。
2. **検証**: 変更に応じたテストや動作確認を行います。
3. **rulesync 同期**: `.rulesync/rules/` を更新したあとは、必ず `npx rulesync generate` を実行して生成物を同期してから commit します。

## PR と release label
- プロダクトの挙動や配布パッケージに影響する変更で PR を作るときは、必ず release label を 1 つだけ付けます。
- 付ける label は次の 3 つのどれか 1 つです。
  - `release:major`: 破壊的変更、既存ユーザーの移行が必要な変更、互換性を壊す CLI/設定変更
  - `release:minor`: 新機能、ユーザー向けコマンド追加、既存互換を保った機能拡張
  - `release:patch`: バグ修正、小さな UX 改善、互換性を壊さない既存機能の修正
- `release:major` / `release:minor` / `release:patch` を複数同時に付けてはいけません。
- 今回のような GitHub Actions 整備、CI/開発環境の調整、rulesync 整備、内部リファクタ、プロダクト挙動に影響しない docs 更新は release label なしで PR を作成します。
