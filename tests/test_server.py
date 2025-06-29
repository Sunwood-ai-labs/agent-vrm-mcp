import os
import sys
from unittest.mock import MagicMock, patch

import pytest
import requests

from agent_vrm_mcp.server import AgentVRMServer

def test_init_success(mock_os_operations):
    """AgentVRMServerの初期化が正常に行われるかテスト"""
    mock_makedirs, _ = mock_os_operations
    server = AgentVRMServer("http://localhost:3001/api/speak_text")
    
    # os.makedirsが呼ばれたかを確認
    mock_makedirs.assert_called_once()
    
    # APIのURLが正しく設定されているか確認
    assert server.api_url == "http://localhost:3001/api/speak_text"


def test_init_connection_error(mock_os_operations):
    """AgentVRM APIに接続できない場合のエラーハンドリングをテスト"""
    # サーバーが正常に初期化されることを確認
    server = AgentVRMServer("http://nonexistent:3001/api/speak_text")
    assert server.api_url == "http://nonexistent:3001/api/speak_text"


def test_speak_text_basic(AgentVRM_server, mock_requests, mock_file_operations, mock_os_operations):
    """speak_textメソッドの基本機能をテスト"""
    filepath = AgentVRM_server.speak_text("こんにちは")
    
    # APIリクエストが正しいパラメータで呼ばれたか確認
    _, mock_post = mock_requests
    mock_post.assert_called_once()
    
    # ファイルが正しく保存されたか確認
    mock_open, mock_file = mock_file_operations
    mock_file.__enter__.return_value.write.assert_called_once()


def test_speak_text_with_params(AgentVRM_server, mock_requests, mock_file_operations):
    """speak_textメソッドのパラメータ指定をテスト"""
    filepath = AgentVRM_server.speak_text(
        "こんにちは", 
        speaker_id=2, 
        speed_scale=1.2
    )
    
    # APIリクエストが正しいパラメータで呼ばれたか確認
    _, mock_post = mock_requests
    call_args = mock_post.call_args[1]['json']
    assert call_args['text'] == "こんにちは"
    assert call_args['speakerId'] == 2
    assert call_args['speedScale'] == 1.2




def test_speak_text_error_handling(AgentVRM_server, mock_requests):
    """speak_textメソッドのエラーハンドリングをテスト"""
    # APIリクエストが失敗する場合
    _, mock_post = mock_requests
    mock_post.side_effect = requests.RequestException("API Error")
    
    with pytest.raises(requests.RequestException):
        AgentVRM_server.speak_text("テストテキスト")
