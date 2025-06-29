import asyncio
import base64
import datetime
import json
import os
import re
import requests
import time
import wave
from typing import Any, Dict, List, Optional, Sequence, Union

from loguru import logger
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import EmbeddedResource, ImageContent, TextContent, Tool

class AgentVRMServer:
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

        # AgentVRMサーバー側で再生されるため、音声の長さ分待機
        logger.info(f"AgentVRM再生のため{duration:.2f}秒待機中...")
        time.sleep(duration)
        logger.info("待機完了")

        return output_path


async def serve(api_url: str = "http://localhost:3001/api/speak_text", output_dir: Optional[str] = None) -> None:
    server = Server("mcp-vrm")
    vrm_server = AgentVRMServer(api_url, output_dir)

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="speak_text",
                description="AgentVRM APIでテキストを音声合成しファイル保存する",
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
                filepath = vrm_server.speak_text(
                    text, speaker_id, speed_scale
                )
                return [
                    TextContent(
                        type="text",
                        text=f"音声を生成し保存しました。\n保存先: {filepath}"
                    )
                ]
            else:
                raise ValueError(f"Unknown tool: {name}")
        except Exception as e:
            logger.error(f"Error processing AgentVRM request: {e}")
            raise ValueError(f"Error processing AgentVRM request: {str(e)}")

    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options)
