from .server import serve

def main():
    """MCP VRM Server - AgentVRM APIを叩いて音声合成するMCPサーバー"""
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(
        description="AgentVRM APIを使ってテキストを音声合成するMCPサーバー"
    )
    parser.add_argument("--api-url", type=str, default="http://localhost:3001/api/speak_text",
                        help="AgentVRM APIのエンドポイントURL")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="音声ファイルの保存先ディレクトリ（デフォルト: ./assets）")

    args = parser.parse_args()
    asyncio.run(serve(args.api_url, args.output_dir))

if __name__ == "__main__":
    main()
