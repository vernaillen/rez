#!/usr/bin/env python3
import argparse
import os
import re
import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path

def clean_vtt(content: str) -> str:
    """
    Clean WebVTT content to plain text.
    Removes headers, timestamps, and duplicate lines.
    """
    lines = content.splitlines()
    text_lines = []
    seen = set()
    
    timestamp_pattern = re.compile(r'\d{2}:\d{2}:\d{2}\.\d{3}\s-->\s\d{2}:\d{2}:\d{2}\.\d{3}')
    
    for line in lines:
        line = line.strip()
        if not line or line == 'WEBVTT' or line.isdigit():
            continue
        if timestamp_pattern.match(line):
            continue
        if line.startswith('NOTE') or line.startswith('STYLE'):
            continue
            
        if text_lines and text_lines[-1] == line:
            continue
            
        line = re.sub(r'<[^>]+>', '', line)
        
        text_lines.append(line)
        
    return '\n'.join(text_lines)

def extract_video_id(url: str) -> str:
    """Extract video ID from various YouTube URL formats."""
    patterns = [
        r'(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$',
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None

def get_transcript_supadata(url: str) -> str:
    """Fallback: fetch transcript via Supadata API."""
    import json
    
    api_key = os.environ.get("SUPADATA_API_KEY")
    if not api_key:
        return None
    
    api_url = f"https://api.supadata.ai/v1/transcript?url={url}"
    
    try:
        result = subprocess.run(
            ["curl", "-s", "--max-time", "30", api_url, "-H", f"x-api-key: {api_key}"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
        content = data.get("content", [])
        if isinstance(content, list):
            return "\n".join(s.get("text", "") for s in content)
        return str(content) if content else None
    except Exception as e:
        print(f"Supadata API error: {e}", file=sys.stderr)
        return None

def get_transcript(url: str):
    with tempfile.TemporaryDirectory() as temp_dir:
        cmd = [
            "yt-dlp",
            "--write-subs",
            "--write-auto-subs",
            "--skip-download",
            "--sub-lang", "en",
            "--output", "subs",
        ]
        
        # Add proxy if configured (YOUTUBE_PROXY or SOCKS_PROXY env var)
        proxy = os.environ.get("YOUTUBE_PROXY") or os.environ.get("SOCKS_PROXY")
        if proxy:
            cmd.extend(["--proxy", proxy])
        
        cmd.append(url)
        
        try:
            subprocess.run(cmd, cwd=temp_dir, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"yt-dlp failed: {e.stderr.decode()[:200]}. Trying Supadata fallback...", file=sys.stderr)
            result = get_transcript_supadata(url)
            if result:
                print(result)
                return
            print("Both yt-dlp and Supadata fallback failed.", file=sys.stderr)
            sys.exit(1)
        except FileNotFoundError:
            print("Error: yt-dlp not found. Trying Supadata fallback...", file=sys.stderr)
            result = get_transcript_supadata(url)
            if result:
                print(result)
                return
            print("Error: yt-dlp not found and Supadata fallback failed.", file=sys.stderr)
            sys.exit(1)

        temp_path = Path(temp_dir)
        vtt_files = list(temp_path.glob("*.vtt"))
        
        if not vtt_files:
            print("No subtitles via yt-dlp. Trying Supadata fallback...", file=sys.stderr)
            result = get_transcript_supadata(url)
            if result:
                print(result)
                return
            print("No subtitles found and Supadata fallback failed.", file=sys.stderr)
            sys.exit(1)
            
        vtt_file = vtt_files[0]
        
        content = vtt_file.read_text(encoding='utf-8')
        clean_text = clean_vtt(content)
        print(clean_text)

def main():
    parser = argparse.ArgumentParser(description="Fetch YouTube transcript.")
    parser.add_argument("url", help="YouTube video URL")
    args = parser.parse_args()
    
    get_transcript(args.url)

if __name__ == "__main__":
    main()
