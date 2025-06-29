from .server import serve

def main():
    """MCP VoiceVox Server - Text-to-speech functionality through VoiceVox for MCP"""
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(
        description="give a model the ability to synthesize speech with VoiceVox"
    )
    parser.add_argument("--voicevox-url", type=str, default="http://localhost:50021", 
                        help="URL of the VoiceVox API")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="Directory to save audio files (default: system temp directory)")
    
    args = parser.parse_args()
    asyncio.run(serve(args.voicevox_url, args.output_dir))


if __name__ == "__main__":
    main()