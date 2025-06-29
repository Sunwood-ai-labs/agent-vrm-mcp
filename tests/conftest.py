import os
import pytest
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

from mcp_server_voicevox.server import VoiceVoxServer

# モックサーバーのレスポンス
MOCK_VERSION_RESPONSE = MagicMock()
MOCK_VERSION_RESPONSE.text = "0.14.5"
MOCK_VERSION_RESPONSE.raise_for_status = MagicMock()

MOCK_SPEAKERS_RESPONSE = MagicMock()
MOCK_SPEAKERS_RESPONSE.raise_for_status = MagicMock()
MOCK_SPEAKERS_RESPONSE.json = MagicMock(return_value=[
    {
        "name": "四国めたん",
        "styles": [
            {"id": 2, "name": "ノーマル"},
            {"id": 3, "name": "あまあま"}
        ]
    },
    {
        "name": "ずんだもん",
        "styles": [
            {"id": 1, "name": "ノーマル"},
            {"id": 7, "name": "あまあま"}
        ]
    }
])

MOCK_AUDIO_QUERY_RESPONSE = MagicMock()
MOCK_AUDIO_QUERY_RESPONSE.raise_for_status = MagicMock()
MOCK_AUDIO_QUERY_RESPONSE.json = MagicMock(return_value={"speedScale": 1.0})

MOCK_SYNTHESIS_RESPONSE = MagicMock()
MOCK_SYNTHESIS_RESPONSE.raise_for_status = MagicMock()
MOCK_SYNTHESIS_RESPONSE.content = b"MOCK_AUDIO_DATA"


@pytest.fixture
def mock_requests():
    """VoiceVox APIリクエストをモック化するフィクスチャ"""
    with patch("requests.get") as mock_get, patch("requests.post") as mock_post:
        # GETリクエストのモック
        mock_get.side_effect = lambda url, **kwargs: {
            "http://voicevox:50021/version": MOCK_VERSION_RESPONSE,
            "http://voicevox:50021/speakers": MOCK_SPEAKERS_RESPONSE,
        }.get(url)
        
        # POSTリクエストのモック
        mock_post.side_effect = lambda url, **kwargs: {
            "http://voicevox:50021/audio_query": MOCK_AUDIO_QUERY_RESPONSE,
            "http://voicevox:50021/synthesis": MOCK_SYNTHESIS_RESPONSE,
        }.get(url)
        
        yield mock_get, mock_post


@pytest.fixture
def mock_os_operations():
    """ファイルシステム操作をモック化するフィクスチャ"""
    with patch("os.makedirs") as mock_makedirs, \
         patch("os.path.join", return_value="/mock/path/file.wav") as mock_join, \
         patch("os.startfile") as mock_startfile:
        yield mock_makedirs, mock_join, mock_startfile


@pytest.fixture
def mock_subprocess():
    """サブプロセス操作をモック化するフィクスチャ"""
    with patch("subprocess.run") as mock_run:
        yield mock_run


@pytest.fixture
def mock_file_operations():
    """ファイル操作をモック化するフィクスチャ"""
    mock_file = MagicMock()
    with patch("builtins.open", return_value=mock_file) as mock_open:
        yield mock_open, mock_file


@pytest.fixture
def temp_output_dir():
    """一時出力ディレクトリを提供するフィクスチャ"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def voicevox_server(mock_requests, temp_output_dir):
    """テスト用のVoiceVoxServerインスタンスを提供するフィクスチャ"""
    server = VoiceVoxServer("http://voicevox:50021", output_dir=temp_output_dir)
    return server


@pytest.fixture
def mcp_server():
    """テスト用のMCP Serverモックを提供するフィクスチャ"""
    mock_server = MagicMock()
    mock_server.create_initialization_options = MagicMock(return_value={})
    return mock_server


@pytest.fixture
def mcp_streams():
    """テスト用のMCPストリームモックを提供するフィクスチャ"""
    mock_read_stream = AsyncMock()
    mock_write_stream = AsyncMock()
    return mock_read_stream, mock_write_stream