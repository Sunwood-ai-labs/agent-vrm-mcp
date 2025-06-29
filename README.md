<div align="center">

![Image](https://github.com/user-attachments/assets/a88c69ce-c034-47c3-8d05-26c348aa063e)

# 🤖 Agent VRM MCP サーバー

</div>


<div align="center">

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Pytest](https://img.shields.io/badge/tested%20with-pytest-00AEEF?logo=pytest)](https://pytest.org)

[![GitHub Repo stars](https://img.shields.io/github/stars/Sunwood-ai-labs/agent-vrm-mcp?style=social)](https://github.com/Sunwood-ai-labs/agent-vrm-mcp/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/Sunwood-ai-labs/agent-vrm-mcp?style=social)](https://github.com/Sunwood-ai-labs/agent-vrm-mcp/network/members)
[![GitHub release](https://img.shields.io/github/v/release/Sunwood-ai-labs/agent-vrm-mcp)](https://github.com/Sunwood-ai-labs/agent-vrm-mcp/releases)
[![GitHub tag](https://img.shields.io/github/v/tag/Sunwood-ai-labs/agent-vrm-mcp)](https://github.com/Sunwood-ai-labs/agent-vrm-mcp/tags)

</div>

AgentVRM を介してVRMアバター機能を提供する Model Context Protocol サーバーです。このサーバーにより、Claude は AgentVRM エンジンが提供するVRMアバターを使用してテキストから音声を生成し、3Dアバターとして表現することができます。

---


## 🎥 デモ動画

https://github.com/user-attachments/assets/ea4b736d-a326-45b0-be88-b01fff6dc3f3

## ✨ 機能

- **テキスト読み上げ**: 指定したテキストを AgentVRM のVRMアバターで読み上げます。
- **VRMアバター表示**: 3DのVRMアバターがテキストを読み上げ、表情やアニメーションも表現します。
- **音声の自動再生**: 生成した音声をその場で自動的に再生します。
- **音声ファイル保存**: 生成した音声は `assets` フォルダに `.wav` ファイルとして保存されます。

## 🚀 前提条件

- AgentVRM エンジンが動作していること（ローカルまたはリモートで）
- Python 3.10 以上

## 📦 インストール

### uv の使用（推奨）

[`uv`](https://docs.astral.sh/uv/) を使用する場合は特別なインストールは必要ありません。直接 [`uvx`](https://docs.astral.sh/uv/guides/tools/) を使用して *agent-vrm-mcp* を実行します。

## ⚙️ 設定

### AgentVRM エンジン

このサーバーは動作するために AgentVRM エンジンが必要です。エンジンの起動は手動で行う必要があります。
デフォルトでは `http://localhost:3001/api/speak_text` への接続を試みます。`--api-url` 引数で別の URL を指定することができます。

AgentVRM エンジンは [公式 AgentVRM リポジトリ](https://github.com/pixiv/AgentVRM) からダウンロードしてインストールできます。

### Claude Desktop 用の設定

Claude Desktop の設定に追加：

<details>
<summary>uvx を使用する場合</summary>

```json
{
  "mcpServers": {
    "vrm": {
      "command": "uvx",
      "args": ["agent-vrm-mcp", "--api-url=http://localhost:3001/api/speak_text"]
    }
  }
}

```
</details>

## 🛠️ 利用可能なツール

- `speak_text` - AgentVRM を使用してテキストを音声に変換し、VRMアバターで表現
  - 必須引数：
    - `text` (文字列): 音声に変換するテキスト
  - オプション引数：
    - `speaker_id` (整数、デフォルト: 1): 使用する話者の ID
    - `speed_scale` (数値、デフォルト: 1.0): 再生速度の倍率
    - `auto_play` (真偽値、デフォルト: True): 生成後に自動再生するか

## 🎵 特別な機能

- 生成後の音声は、プラットフォーム固有の方法で自動的に再生されます：
  - **Windows**: デフォルトのシステムプレーヤーを使用
  - **macOS**: 内蔵の `afplay` ユーティリティを使用
  - **Linux**: まず `aplay` を試し、失敗した場合は `xdg-open` にフォールバック

## 📁 プロジェクト構造

- `src/agent_vrm_mcp`: [ソースコード](./src/agent_vrm_mcp/README.md)
- `tests`: [テストコード](./tests/README.md)

## 🧑‍💻 開発モードでのセットアップ・実行手順

開発者向けに、`uv` を用いた開発モードでのインストールおよびMCP Inspectorによる実行手順をまとめます。

```bash
# プロジェクトディレクトリで開発モードでインストール
cd C:\Prj\agent-vrm-mcp
uv sync

# 開発モードでパッケージをインストール
uv pip install -e .

# MCP Inspector で実行
npx @modelcontextprotocol/inspector python -m agent_vrm_mcp --api-url=http://localhost:3001/api/speak_text
```

- `uv sync` で依存パッケージを同期します。
- `uv pip install -e .` で開発モード（編集可能インストール）を行います。
- MCP Inspectorを使うことで、`agent_vrm_mcp`サーバーをAPIエンドポイント指定で起動できます。

## 📄 ライセンス

agent-vrm-mcp は MIT ライセンスの下で提供されています。これは、MIT ライセンスの条件に従い、自由に使用、修正、配布することができることを意味します。


## 🔗 リンク

- GitHub: [https://github.com/Sunwood-ai-labs/agent-vrm-mcp](https://github.com/Sunwood-ai-labs/agent-vrm-mcp)
  - [タグ一覧](https://github.com/Sunwood-ai-labs/agent-vrm-mcp/tags)
- PyPI: [https://pypi.org/project/agent-vrm-mcp/](https://pypi.org/project/agent-vrm-mcp/)
