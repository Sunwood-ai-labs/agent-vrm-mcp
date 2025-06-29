import asyncio
import base64
import datetime
import json
import logging
import os
import platform
import re
import requests
import subprocess
import wave
from typing import Any, Dict, List, Optional, Sequence, Union

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import EmbeddedResource, ImageContent, TextContent, Tool

logger = logging.getLogger(__name__)

class ChatVRMServer:
    def __init__(self, api_url: str, output_dir: Optional[str] = None):
        self.api_url = api_url.rstrip("/")
        # 出力ディレクトリ
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(os.path.dirname(script_dir))
        self.output_dir = output_dir or os.path.join(base_dir, "assets")
        os.makedirs(self.output_dir, exist_ok=True)

    def speak_text(
        self,
        text: str,
        speaker_id: int = 1,
        speed_scale: float = 1.0,
        auto_play: bool = True,
    ) -> str:
        payload = {
            "text": text,
            "speakerId": speaker_id,
            "speedScale": speed_scale,
        }
        logger.info(f"APIリクエスト送信: {payload}")
        response = requests.post(self.api_url, json=payload)
        response.raise_for_status()
        data = response.json()
        logger.info(f"サーバーレスポンスのキー: {list(data.keys())}")

        if "audio" not in data:
            logger.warning("audioフィールドがレスポンスにありません。")
            raise ValueError("audioフィールドがレスポンスにありません。")

        audio_data_uri = data["audio"]
        m = re.match(r"data:audio/wav;base64,(.*)", audio_data_uri)
        if not m:
            logger.error("audioフィールドが想定外の形式です")
            raise ValueError("audioフィールドが想定外の形式です")
        audio_base64 = m.group(1)
        audio_bytes = base64.b64decode(audio_base64)
        now = datetime.datetime.now()
        filename = f"output_speak_text_{now.strftime('%Y%m%d_%H%M%S')}.wav"
        output_path = os.path.join(self.output_dir, filename)
        with open(output_path, "wb") as f:
            f.write(audio_bytes)
        logger.info(f"音声ファイルを{output_path}として保存しました。")

        # wavファイルの長さ（秒）を計算
        with wave.open(output_path, "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            duration = frames / float(rate)
        logger.info(f"音声の長さ: {duration:.2f}秒")

        if auto_play:
            self.play_audio(output_path)

        return output_path

    def play_audio(self, filepath: str) -> None:
        try:
            system = platform.system().lower()
            if system == "windows":
                try:
                    subprocess.run([
                        "powershell", "-c",
                        f"(New-Object Media.SoundPlayer '{filepath}').PlaySync()"
                    ], check=True, capture_output=True)
                    logger.info(f"Audio played using PowerShell: {filepath}")
                    return
                except Exception:
                    pass
                try:
                    subprocess.run([
                        "start", "/min", "wmplayer", "/close", filepath
                    ], shell=True, check=True)
                    logger.info(f"Audio played using Windows Media Player: {filepath}")
                    return
                except Exception:
                    pass
                os.startfile(filepath)
                logger.info(f"Audio opened with default application: {filepath}")
            elif system == "darwin":
                subprocess.run(["afplay", filepath], check=True)
                logger.info(f"Audio played using afplay: {filepath}")
            else:
                try:
                    subprocess.run(["aplay", "-q", filepath], check=True)
                    logger.info(f"Audio played using aplay: {filepath}")
                except Exception:
                    try:
                        subprocess.run(["paplay", filepath], check=True)
                        logger.info(f"Audio played using paplay: {filepath}")
                    except Exception:
                        subprocess.run(["xdg-open", filepath], check=True)
                        logger.info(f"Audio opened with default application: {filepath}")
        except Exception as e:
            logger.error(f"Failed to play audio: {e}")
            logger.info(f"Audio file saved to: {filepath}")

async def serve(api_url: str = "http://localhost:3001/api/speak_text", output_dir: Optional[str] = None) -> None:
    server = Server("mcp-vrm")
    vrm_server = ChatVRMServer(api_url, output_dir)

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="speak_text",
                description="ChatVRM APIでテキストを音声合成しファイル保存・再生する",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "喋らせたいテキスト"
                        },
                        "speaker_id": {
                            "type": "integer",
                            "description": "話者ID (デフォルト: 1)",
                            "default": 1
                        },
                        "speed_scale": {
                            "type": "number",
                            "description": "再生速度 (デフォルト: 1.0)",
                            "default": 1.0
                        },
                        "auto_play": {
                            "type": "boolean",
                            "description": "自動再生するか (デフォルト: True)",
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
        try:
            if name == "speak_text":
                text = arguments.get("text")
                if not text:
                    raise ValueError("textは必須です")
                speaker_id = arguments.get("speaker_id", 1)
                speed_scale = arguments.get("speed_scale", 1.0)
                auto_play = arguments.get("auto_play", True)
                filepath = vrm_server.speak_text(
                    text, speaker_id, speed_scale, auto_play
                )
                return [
                    TextContent(
                        type="text",
                        text=f"音声を生成し{'再生しました' if auto_play else '保存しました'}。\n保存先: {filepath}"
                    )
                ]
            else:
                raise ValueError(f"Unknown tool: {name}")
        except Exception as e:
            logger.error(f"Error processing ChatVRM request: {e}")
            raise ValueError(f"Error processing ChatVRM request: {str(e)}")

    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options)
