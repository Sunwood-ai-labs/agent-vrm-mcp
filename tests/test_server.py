import os
import sys
import subprocess
from unittest.mock import MagicMock, patch

import pytest
import requests

from agent_vrm_mcp.server import ChatVRMServer

def test_init_success(mock_os_operations):
    """ChatVRMServerの初期化が正常に行われるかテスト"""
    mock_makedirs, _, _ = mock_os_operations
    server = ChatVRMServer("http://localhost:3001/api/speak_text")
    
    # os.makedirsが呼ばれたかを確認
    mock_makedirs.assert_called_once()
    
    # APIのURLが正しく設定されているか確認
    assert server.api_url == "http://localhost:3001/api/speak_text"


def test_init_connection_error(mock_os_operations):
    """ChatVRM APIに接続できない場合のエラーハンドリングをテスト"""
    # サーバーが正常に初期化されることを確認
    server = ChatVRMServer("http://nonexistent:3001/api/speak_text")
    assert server.api_url == "http://nonexistent:3001/api/speak_text"


def test_speak_text_basic(chatvrm_server, mock_requests, mock_file_operations, mock_os_operations):
    """speak_textメソッドの基本機能をテスト"""
    # play_audioメソッドをモック化
    with patch.object(chatvrm_server, 'play_audio') as mock_play_audio:
        filepath = chatvrm_server.speak_text("こんにちは")
        
        # APIリクエストが正しいパラメータで呼ばれたか確認
        _, mock_post = mock_requests
        mock_post.assert_called_once()
        
        # ファイルが正しく保存されたか確認
        mock_open, mock_file = mock_file_operations
        mock_file.__enter__.return_value.write.assert_called_once()
        
        # 音声が再生されたか確認
        mock_play_audio.assert_called_once()


def test_speak_text_with_params(chatvrm_server, mock_requests, mock_file_operations):
    """speak_textメソッドのパラメータ指定をテスト"""
    # play_audioメソッドをモック化
    with patch.object(chatvrm_server, 'play_audio') as mock_play_audio:
        filepath = chatvrm_server.speak_text(
            "こんにちは", 
            speaker_id=2, 
            speed_scale=1.2, 
            auto_play=False
        )
        
        # APIリクエストが正しいパラメータで呼ばれたか確認
        _, mock_post = mock_requests
        call_args = mock_post.call_args[1]['json']
        assert call_args['text'] == "こんにちは"
        assert call_args['speakerId'] == 2
        assert call_args['speedScale'] == 1.2
        
        # auto_play=Falseなので再生されないことを確認
        mock_play_audio.assert_not_called()


@pytest.mark.parametrize("platform_name, expected_command", [
    ("Windows", "powershell"),
    ("Darwin", "afplay"),
    ("Linux", "aplay"),
])
def test_play_audio(chatvrm_server, mock_subprocess, platform_name, expected_command):
    """play_audioメソッドが各プラットフォームで正しく動作するかテスト"""
    with patch("platform.system", return_value=platform_name.lower()):
        if platform_name == "Windows":
            with patch("os.startfile") as mock_startfile:
                # 最初の試みが失敗するように設定
                mock_subprocess.side_effect = [subprocess.SubprocessError, None]
                chatvrm_server.play_audio("/path/to/audio.wav")
                # 最終的にos.startfileが呼ばれることを確認
                mock_startfile.assert_called_once_with('/path/to/audio.wav')
        else:
            chatvrm_server.play_audio("/path/to/audio.wav")
            # 正しいコマンドが呼ばれたか確認
            mock_subprocess.assert_called_once()
            call_args = mock_subprocess.call_args[0][0]
            assert call_args[0] == expected_command.lower()


def test_speak_text_error_handling(chatvrm_server, mock_requests):
    """speak_textメソッドのエラーハンドリングをテスト"""
    # APIリクエストが失敗する場合
    _, mock_post = mock_requests
    mock_post.side_effect = requests.RequestException("API Error")
    
    with pytest.raises(requests.RequestException):
        chatvrm_server.speak_text("テストテキスト")