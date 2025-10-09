# PyPI へのデプロイ手順

このドキュメントでは、`easy-worktree` を PyPI（本番）と TestPyPI（テスト環境）にアップロードする手順を説明します。

## 準備

### 1. 必要なパッケージのインストール

```bash
pip install build twine
```

### 2. PyPI と TestPyPI のアカウント作成

- **TestPyPI**: https://test.pypi.org/account/register/
- **PyPI**: https://pypi.org/account/register/

### 3. API トークンの作成

各サービスでアカウント設定から API トークンを作成してください。

- TestPyPI: https://test.pypi.org/manage/account/token/
- PyPI: https://pypi.org/manage/account/token/

## ビルド

パッケージをビルドします：

```bash
# クリーンビルド（古いビルドファイルを削除）
rm -rf dist/ build/ *.egg-info

# ビルド実行
python -m build
```

これにより `dist/` ディレクトリに以下が生成されます：
- `easy-worktree-0.0.1.tar.gz` (ソース配布物)
- `easy-worktree-0.0.1-py3-none-any.whl` (ホイール)

## TestPyPI へのアップロード（テスト環境）

まずはテスト環境にアップロードして動作確認します：

```bash
python -m twine upload --repository testpypi dist/*
```

認証情報を求められたら：
- Username: `__token__`
- Password: TestPyPI の API トークン（`pypi-` で始まる文字列）

### TestPyPI からのインストールテスト

```bash
pip install --index-url https://test.pypi.org/simple/ easy-worktree
```

動作確認：

```bash
wt --help
```

## PyPI へのアップロード（本番環境）

TestPyPI で動作確認ができたら、本番環境にアップロードします：

```bash
python -m twine upload dist/*
```

認証情報を求められたら：
- Username: `__token__`
- Password: PyPI の API トークン

### PyPI からのインストール確認

```bash
pip install easy-worktree
```

## ~/.pypirc の設定（オプション）

毎回認証情報を入力したくない場合は、`~/.pypirc` に設定を保存できます：

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_PYPI_API_TOKEN_HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TESTPYPI_API_TOKEN_HERE
```

**セキュリティ注意**: このファイルには API トークンが平文で保存されるため、権限を適切に設定してください：

```bash
chmod 600 ~/.pypirc
```

## バージョンアップ時の手順

1. `pyproject.toml` のバージョン番号を更新
2. 変更内容を git にコミット
3. ビルドとアップロード：

```bash
# クリーンビルド
rm -rf dist/ build/ *.egg-info

# ビルド
python -m build

# TestPyPI でテスト
python -m twine upload --repository testpypi dist/*

# 動作確認後、本番へアップロード
python -m twine upload dist/*
```

## トラブルシューティング

### "File already exists" エラー

同じバージョン番号のファイルは再アップロードできません。バージョン番号を上げてください。

### 依存関係のエラー

`pyproject.toml` の `dependencies` セクションを確認してください。

### ビルドエラー

```bash
# キャッシュをクリア
rm -rf dist/ build/ *.egg-info __pycache__

# 再ビルド
python -m build
```

## 参考リンク

- [Python Packaging User Guide](https://packaging.python.org/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [TestPyPI](https://test.pypi.org/)
- [PyPI](https://pypi.org/)
