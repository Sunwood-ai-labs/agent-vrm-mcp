import asyncio
import base64
import datetime
import io
import json
import logging
import os
import subprocess
import sys
import tempfile
from typing import Any, Dict, List, Optional, Sequence, Union
import platform

import requests
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.shared.exceptions import McpError
from mcp.types import EmbeddedResource, ImageContent, TextContent, Tool
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class VoiceVoxServer:
    def __init__(self, voicevox_url: str, output_dir: Optional[str] = None):
        self.voicevox_url = voicevox_url.rstrip('/')
        
        self.check_connection()
        
        # Set output directory to mcp-voicevox/sound folder
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(os.path.dirname(script_dir))
        output_dir = output_dir or base_dir
        self.output_dir = os.path.join(base_dir, "sound")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
    def check_connection(self) -> Optional[str]:
        """VoiceVoxサーバーへの接続を確認し、バージョン情報を返す
        
        Returns:
            Optional[str]: サーバーのバージョン。接続に失敗した場合はNone
        """
        try:
            response = requests.get(f"{self.voicevox_url}/version")
            response.raise_for_status()
            version = response.text.strip('"')  # JSONレスポンスから引用符を削除
            logger.info(f"Connected to VoiceVox API v{version}")
            return version
        except Exception as e:
            logger.error(f"Failed to connect to VoiceVox API at {self.voicevox_url}: {e}")
            logger.error("Make sure VoiceVox Engine is running")
            return None
    
    def get_speakers(self) -> List[Dict[str, Any]]:
        """Get list of available speakers"""
        response = requests.get(f"{self.voicevox_url}/speakers")
        response.raise_for_status()
        return response.json()
    
    def play_audio(self, filepath: str) -> None:
        """Play audio file using system default player"""
        try:
            system = platform.system().lower()
            
            if system == "windows":
                # Windowsの場合、より確実な再生方法を試す
                try:
                    # まずはPowerShellを使ってみる
                    subprocess.run([
                        "powershell", "-c",
                        f"(New-Object Media.SoundPlayer '{filepath}').PlaySync()"
                    ], check=True, capture_output=True)
                    logger.info(f"Audio played using PowerShell: {filepath}")
                    return
                except (subprocess.SubprocessError, FileNotFoundError):
                    pass
                
                try:
                    # 次にWindows Media Playerを試す
                    subprocess.run([
                        "start", "/min", "wmplayer", "/close", filepath
                    ], shell=True, check=True)
                    logger.info(f"Audio played using Windows Media Player: {filepath}")
                    return
                except (subprocess.SubprocessError, FileNotFoundError):
                    pass
                
                # 最後の手段としてos.startfile（ダイアログが出る可能性がある）
                os.startfile(filepath)
                logger.info(f"Audio opened with default application: {filepath}")
                
            elif system == "darwin":  # macOS
                subprocess.run(["afplay", filepath], check=True)
                logger.info(f"Audio played using afplay: {filepath}")
                
            else:  # Linux
                try:
                    subprocess.run(["aplay", "-q", filepath], check=True)
                    logger.info(f"Audio played using aplay: {filepath}")
                except (subprocess.SubprocessError, FileNotFoundError):
                    try:
                        subprocess.run(["paplay", filepath], check=True)
                        logger.info(f"Audio played using paplay: {filepath}")
                    except (subprocess.SubprocessError, FileNotFoundError):
                        subprocess.run(["xdg-open", filepath], check=True)
                        logger.info(f"Audio opened with default application: {filepath}")
                        
        except Exception as e:
            logger.error(f"Failed to play audio: {e}")
            logger.info(f"Audio file saved to: {filepath}")

    def text_to_speech(self, text: str, speaker_id: int = 1, speed: float = 1.3, auto_play: bool = True) -> str:
        """Convert text to speech using VoiceVox, save to file, and optionally play it"""
        # Get audio query
        query_response = requests.post(
            f"{self.voicevox_url}/audio_query",
            params={"text": text, "speaker": speaker_id}
        )
        query_response.raise_for_status()
        query_data = query_response.json()
        
        # Adjust speed if needed
        if speed != 1.3:
            query_data["speedScale"] = speed
        
        # Synthesize speech
        synthesis_response = requests.post(
            f"{self.voicevox_url}/synthesis",
            headers={"Content-Type": "application/json"},
            params={"speaker": speaker_id},
            data=json.dumps(query_data)
        )
        synthesis_response.raise_for_status()
        
        # Create filename with timestamp and speaker ID format: YYYYmmdd_HHMM_speakerID.wav
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M")
        filename = f"{timestamp}_{speaker_id}.wav"
        filepath = os.path.join(self.output_dir, filename)
        
        # Save to file
        with open(filepath, "wb") as f:
            f.write(synthesis_response.content)
        
        # Play the audio if auto_play is True
        if auto_play:
            self.play_audio(filepath)
        
        return filepath


async def serve(voicevox_url: str = "http://localhost:50021", output_dir: Optional[str] = None) -> None:
    server = Server("mcp-voicevox")
    voicevox_server = VoiceVoxServer(voicevox_url, output_dir)
    
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available VoiceVox tools."""
        return [
            Tool(
                name="get_voices",
                description="Get a list of available voices in VoiceVox",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            ),
            Tool(
                name="text_to_speech",
                description="Convert text to speech using VoiceVox and save to a file",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to convert to speech"
                        },
                        "speaker_id": {
                            "type": "integer",
                            "description": "Speaker ID (voice). Default is 1.",
                            "default": 1
                        },
                        "speed": {
                            "type": "number",
                            "description": "Playback speed. Default is 1.3.",
                            "default": 1.3
                        },
                        "auto_play": {
                            "type": "boolean",
                            "description": "Whether to automatically play the generated audio. Default is True.",
                            "default": True
                        }
                    },
                    "required": ["text"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> Sequence[Union[TextContent, ImageContent, EmbeddedResource]]:
        """Handle tool calls for VoiceVox."""
        try:
            if name == "get_voices":
                speakers = voicevox_server.get_speakers()
                voices = []
                
                for speaker in speakers:
                    for style in speaker.get("styles", []):
                        voices.append({
                            "id": style["id"],
                            "name": f"{speaker['name']} ({style['name']})"
                        })
                
                return [
                    TextContent(
                        type="text",
                        text=json.dumps(voices, ensure_ascii=False, indent=2)
                    )
                ]
            
            elif name == "text_to_speech":
                text = arguments.get("text")
                if not text:
                    raise ValueError("Text is required")
                
                speaker_id = arguments.get("speaker_id", 1)
                speed = arguments.get("speed", 1.3)
                auto_play = arguments.get("auto_play", True)
                
                filepath = voicevox_server.text_to_speech(text, speaker_id, speed, auto_play)
                
                play_status = "音声を生成し再生しました。" if auto_play else "音声を生成しました。"
                
                return [
                    TextContent(
                        type="text",
                        text=f"{play_status}保存先:\n{filepath}\n\n音声ファイルは sound フォルダに保存されました。"
                    )
                ]
            
            else:
                raise ValueError(f"Unknown tool: {name}")

        except Exception as e:
            logger.error(f"Error processing voicevox request: {e}")
            raise ValueError(f"Error processing voicevox request: {str(e)}")

    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options)
