# 🤖 src/agent_vrm_mcp

このディレクトリには、AgentVRM APIを利用したMCPサーバー「agent-vrm-mcp」の主要なソースコードが含まれています。

---

## 📝 概要

AgentVRMの `/api/speak_text` エンドポイントを叩き、テキストから音声合成を行うMCPサーバーです。  
MCPツールとして `speak_text` を提供し、テキストを音声ファイル（WAV）として保存・自動再生できます。

---

## 📦 ファイル構成

- `__init__.py`: パッケージ初期化・CLIエントリーポイント（`main`関数）を定義
- `__main__.py`: `python -m agent_vrm_mcp` で直接実行可能にするエントリーポイント
- `server.py`: MCPサーバー本体・AgentVRM API連携・ツール定義

---

## 🚀 使い方

### 1. AgentVRMサーバーの起動

事前にAgentVRMサーバー（例: `http://localhost:3001`）を起動しておく必要があります。

### 2. MCPサーバーの起動

```bash
uvx agent-vrm-mcp --api-url=http://localhost:3001/api/speak_text
```

- `--api-url`: AgentVRMのAPIエンドポイントURL（省略時は `http://localhost:3001/api/speak_text`）
- `--output-dir`: 音声ファイルの保存先ディレクトリ（省略時は `assets/`）

---

## 🛠️ 利用可能なツール

### `speak_text`

AgentVRM APIでテキストを音声合成し、ファイル保存・自動再生します。

#### 入力スキーマ

| パラメータ    | 型      | 必須 | デフォルト | 説明                   |
|--------------|---------|------|------------|------------------------|
| text         | string  | ○    | -          | 喋らせたいテキスト     |
| speaker_id   | integer |      | 1          | 話者ID                 |
| speed_scale  | number  |      | 1.0        | 再生速度               |
| auto_play    | boolean |      | True       | 生成後に自動再生するか |

#### 出力

- 音声ファイルの保存先パス
- 自動再生した場合はその旨を返します

---

## 📁 プロジェクト構造

- `src/agent_vrm_mcp`: 本サーバーのソースコード
- `assets/`: 音声ファイルの出力先（自動生成）

---

## 📝 備考

- AgentVRM APIのレスポンス仕様に依存します
- 音声ファイルはWAV形式で保存されます
- Windows/macOS/Linuxで自動再生に対応

---

[🔼 上位のREADMEへ](../../README.md)
