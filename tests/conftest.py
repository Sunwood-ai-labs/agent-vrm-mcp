import os
import pytest
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

from agent_vrm_mcp.server import AgentVRMServer

# モックAgentVRMサーバーのレスポンス
MOCK_AgentVRM_RESPONSE = MagicMock()
MOCK_AgentVRM_RESPONSE.raise_for_status = MagicMock()
MOCK_AgentVRM_RESPONSE.json = MagicMock(return_value={
    "audio": "data:audio/wav;base64,UklGRjIAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQ4AAAAC"
})


@pytest.fixture
def mock_requests():
    """AgentVRM APIリクエストをモック化するフィクスチャ"""
    with patch("requests.get") as mock_get, patch("requests.post") as mock_post:
        # POSTリクエストのモック (AgentVRMはPOSTのみ)
        mock_post.return_value = MOCK_AgentVRM_RESPONSE
        
        yield mock_get, mock_post


@pytest.fixture
def mock_os_operations():
    """ファイルシステム操作をモック化するフィクスチャ"""
    with patch("os.makedirs") as mock_makedirs, \
         patch("os.path.join", return_value="/mock/path/file.wav") as mock_join:
        yield mock_makedirs, mock_join




@pytest.fixture
def mock_file_operations():
    """ファイル操作をモック化するフィクスチャ"""
    mock_file = MagicMock()
    with patch("builtins.open", return_value=mock_file) as mock_open, \
         patch("wave.open") as mock_wave_open:
        # wave.openをモック化してダミーの音声情報を返す
        mock_wave_file = MagicMock()
        mock_wave_file.getnframes.return_value = 1000
        mock_wave_file.getframerate.return_value = 44100
        mock_wave_open.return_value.__enter__.return_value = mock_wave_file
        yield mock_open, mock_file


@pytest.fixture
def temp_output_dir():
    """一時出力ディレクトリを提供するフィクスチャ"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def AgentVRM_server(mock_requests, temp_output_dir):
    """テスト用のAgentVRMServerインスタンスを提供するフィクスチャ"""
    server = AgentVRMServer("http://localhost:3001/api/speak_text", output_dir=temp_output_dir)
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
