import os
import sys
import subprocess
from unittest.mock import MagicMock, patch

import pytest
import requests

from mcp_server_voicevox.server import VoiceVoxServer

def test_init_success(mock_requests, mock_os_operations):
    """VoiceVoxServerの初期化が正常に行われるかテスト"""
    mock_makedirs, _, _ = mock_os_operations
    server = VoiceVoxServer("http://voicevox:50021")
    
    # os.makedirsが呼ばれたかを確認
    mock_makedirs.assert_called_once()
    
    # VoiceVox APIに接続確認リクエストが送信されたかを確認
    mock_get, _ = mock_requests
    mock_get.assert_called_with("http://voicevox:50021/version")


def test_init_connection_error(mock_os_operations):
    """VoiceVox APIに接続できない場合のエラーハンドリングをテスト"""
    # リクエストでエラーが発生するようにモック化
    with patch("requests.get", side_effect=Exception("Connection error")):
        # エラーが捕捉され、サーバーが正常に初期化されることを確認
        server = VoiceVoxServer("http://nonexistent:50021")
        assert server.voicevox_url == "http://nonexistent:50021"


def test_get_speakers(voicevox_server, mock_requests):
    """get_speakersメソッドが正常に動作するかテスト"""
    speakers = voicevox_server.get_speakers()
    
    # 正しい数のスピーカーが返されるか確認
    assert len(speakers) == 2
    assert speakers[0]["name"] == "四国めたん"
    assert len(speakers[0]["styles"]) == 2
    
    # APIリクエストが正しく行われたか確認
    mock_get, _ = mock_requests
    mock_get.assert_any_call("http://voicevox:50021/speakers")


def test_text_to_speech(voicevox_server, mock_requests, mock_file_operations, mock_os_operations):
    """text_to_speechメソッドが正常に動作するかテスト"""
    # play_audioメソッドをモック化
    with patch.object(voicevox_server, 'play_audio') as mock_play_audio:
        filepath = voicevox_server.text_to_speech("こんにちは", speaker_id=1, speed=1.2)
        
        # APIリクエストが正しいパラメータで呼ばれたか確認
        _, mock_post = mock_requests
        mock_post.assert_any_call(
            "http://voicevox:50021/audio_query",
            params={"text": "こんにちは", "speaker": 1}
        )
        
        # 速度パラメータが正しく設定されたか確認 (audio_queryの結果を修正しているか)
        assert mock_post.call_args_list[1][1]['data'] == '{"speedScale": 1.2}'
        
        # ファイルが正しく保存されたか確認
        mock_open, mock_file = mock_file_operations
        mock_file.__enter__.return_value.write.assert_called_once_with(b"MOCK_AUDIO_DATA")
        
        # 音声が再生されたか確認
        mock_play_audio.assert_called_once()


@pytest.mark.parametrize("platform_name, mock_method, expected_calls", [
    (
        "Windows",
        "os.startfile",
        [
            ("powershell", ['powershell', '-c', "(New-Object Media.SoundPlayer '/path/to/audio.wav').PlaySync()"]),
            ("wmplayer", ['start', '/min', 'wmplayer', '/close', '/path/to/audio.wav']),
            ("startfile", '/path/to/audio.wav'),
        ]
    ),
    ("Darwin", "subprocess.run", [("afplay", ["afplay", "/path/to/audio.wav"])]),
    (
        "Linux",
        "subprocess.run",
        [
            ("aplay", ["aplay", "-q", "/path/to/audio.wav"]),
            ("paplay", ["paplay", "/path/to/audio.wav"]),
            ("xdg-open", ["xdg-open", "/path/to/audio.wav"]),
        ]
    ),
])
def test_play_audio(voicevox_server, mock_subprocess, platform_name, mock_method, expected_calls):
    """play_audioメソッドが各プラットフォームで正しく動作するかテスト"""
    with patch("platform.system", return_value=platform_name):
        # Windowsの場合の特殊なモック処理
        if platform_name == "Windows":
            with patch("os.startfile") as mock_startfile:
                # 最初の2つの試みが失敗するように設定
                mock_subprocess.side_effect = [
                    subprocess.SubprocessError,
                    subprocess.SubprocessError,
                    None  # 3番目のos.startfileは成功
                ]
                voicevox_server.play_audio("/path/to/audio.wav")
                
                # PowerShell と wmplayer の呼び出しを確認
                assert mock_subprocess.call_count == 2
                mock_subprocess.assert_any_call(
                    ['powershell', '-c', "(New-Object Media.SoundPlayer '/path/to/audio.wav').PlaySync()"],
                    check=True, capture_output=True
                )
                mock_subprocess.assert_any_call(
                    ['start', '/min', 'wmplayer', '/close', '/path/to/audio.wav'],
                    shell=True, check=True
                )
                
                # os.startfileが最終的に呼ばれることを確認
                mock_startfile.assert_called_once_with('/path/to/audio.wav')

        # macOS と Linux の場合のテスト
        else:
            for i, (name, call_args) in enumerate(expected_calls):
                mock_subprocess.reset_mock()
                # 最後の試み以外は失敗するように設定
                side_effects = [subprocess.SubprocessError] * i + [None]
                mock_subprocess.side_effect = side_effects
                
                voicevox_server.play_audio("/path/to/audio.wav")
                
                # 正しいコマンドが呼ばれたか確認
                mock_subprocess.assert_called_with(call_args, check=True)
                assert mock_subprocess.call_count == i + 1
