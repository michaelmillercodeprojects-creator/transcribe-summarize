

import argparse
import sys
import os
import subprocess
import tempfile
from typing import Optional
import mimetypes

import openai
from dotenv import load_dotenv
from tqdm import tqdm
import requests

import yt_dlp

from transcribe_summarize.utils import load_api_key, format_summary_prompt
from transcribe_summarize.chunked_audio import extract_audio_chunk, get_audio_chunks

load_dotenv()


def is_video_file(file_path: str) -> bool:
    video_exts = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".flv", ".wmv"}
    ext = os.path.splitext(file_path)[1].lower()
    return ext in video_exts

def is_audio_file(file_path: str) -> bool:
    audio_exts = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}
    ext = os.path.splitext(file_path)[1].lower()
    return ext in audio_exts

# Audio extraction moved to chunked_audio.py

def is_url(path: str) -> bool:
    return path.startswith("http://") or path.startswith("https://")

def is_youtube_url(url: str) -> bool:
    return "youtube.com/watch" in url or "youtu.be/" in url

def download_file(url: str) -> str:
    """Download file from URL or YouTube to a temp file, return path."""
    if is_youtube_url(url):
        # Use yt-dlp to download and extract audio to audio/ folder
        os.makedirs("audio", exist_ok=True)
        outtmpl = "audio/%(title)s.%(ext)s"
        cmd = [
            "yt-dlp", "-x", "--audio-format", "mp3", url, "-o", outtmpl
        ]
        try:
            result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # Find the downloaded file (yt-dlp prints the filename)
            # We'll look for the newest .mp3 in audio/
            import glob
            mp3_files = glob.glob("audio/*.mp3")
            if not mp3_files:
                raise RuntimeError("yt-dlp did not produce any .mp3 files in audio/")
            latest_file = max(mp3_files, key=os.path.getctime)
            return latest_file
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"yt-dlp shell command failed: {e.stderr.decode(errors='ignore')}")
    # Regular HTTP/HTTPS file
    local_ext = None
    try:
        r = requests.get(url, stream=True, timeout=30)
        r.raise_for_status()
        content_type = r.headers.get("content-type", "")
        ext = mimetypes.guess_extension(content_type.split(";")[0])
        if not ext:
            ext = os.path.splitext(url)[1]
        temp_fd, temp_path = tempfile.mkstemp(suffix=ext or "")
        os.close(temp_fd)
        with open(temp_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        return temp_path
    except Exception as e:
        raise RuntimeError(f"Failed to download file from {url}: {e}")

def transcribe_audio(input_path: str, model: str = "gpt-4o-mini-transcribe") -> str:
    """Transcribe audio/video/local/remote file. If video, extract audio first. If URL, download first."""
    temp_paths = []
    # Download if URL
    if is_url(input_path):
        print(f"Downloading file from URL: {input_path}")
        input_path = download_file(input_path)
        temp_paths.append(input_path)
    
    # Convert Windows path to Unix path
    input_path = input_path.replace('\\', '/').replace('C:', '')

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    api_key = load_api_key()
    if not api_key:
        raise EnvironmentError("OpenAI API key not found. Please set it using one of these methods:\n"
                          "1. Set OPENAI_API_KEY environment variable\n"
                          "2. Create .env file with OPENAI_API_KEY=your-key\n"
                          "3. Create ~/.openai/api_key file with just the key\n"
                          "4. Create api_key file in current directory")
    openai.api_key = api_key

    # Process audio in chunks
    chunks = get_audio_chunks(input_path)
    transcript_parts = []

    print(f"Audio will be processed in {len(chunks)} chunk(s)")
    for i, (start, chunk_duration) in enumerate(chunks):
        print(f"\nProcessing chunk {i+1}/{len(chunks)} "
              f"(from {int(start)}s to {int(start+chunk_duration)}s)...")

        # Extract audio chunk
        temp_chunk_path = extract_audio_chunk(input_path, start, chunk_duration)
        temp_paths.append(temp_chunk_path)

        try:
            with open(temp_chunk_path, "rb") as audio_file:
                print(f"Sending chunk {i+1} to OpenAI for transcription...")
                resp = openai.audio.transcriptions.create(model=model, file=audio_file)
                if isinstance(resp, dict):
                    text = resp.get("text") or resp.get("transcript") or str(resp)
                else:
                    text = getattr(resp, "text", None) or getattr(resp, "transcript", None) or str(resp)
                
                print(f"Chunk {i+1} transcription completed: {len(text)} characters")
                transcript_parts.append(text)
        finally:
            if temp_chunk_path and os.path.exists(temp_chunk_path):
                os.remove(temp_chunk_path)

    # Clean up any remaining temp files
    for p in temp_paths:
        if p and os.path.exists(p):
            os.remove(p)

    return "\n\n".join(transcript_parts)


def summarize_text(transcript: str, length: str = "short", model: str = "gpt-4o") -> str:
    api_key = load_api_key()
    if not api_key:
        raise EnvironmentError("OpenAI API key not found. Please set it using one of these methods:\n"
                          "1. Set OPENAI_API_KEY environment variable\n"
                          "2. Create .env file with OPENAI_API_KEY=your-key\n"
                          "3. Create ~/.openai/api_key file with just the key\n"
                          "4. Create api_key file in current directory")
    openai.api_key = api_key

    prompt = format_summary_prompt(transcript, length=length)

    try:
        # Use the `openai.chat.completions.create` API exposed by the installed client.
        resp = openai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0.2,
        )

        # The response usually contains `choices` -> first choice -> `message` -> `content`.
        if isinstance(resp, dict):
            choices = resp.get("choices") or []
            if choices:
                first = choices[0]
                # support both `message` or `text` fields depending on client
                msg = first.get("message") or {}
                return msg.get("content") or first.get("text") or str(first)
            return str(resp)

        # resource-like response
        choices = getattr(resp, "choices", None)
        if choices:
            first = choices[0]
            msg = getattr(first, "message", None) or {}
            return getattr(msg, "content", None) or getattr(first, "text", None) or str(first)

        return str(resp)
    except Exception as e:
        raise RuntimeError(f"Summarization failed: {e}") from e


def sanitize_filename(s: str) -> str:
    import re
    s = s.strip().replace(' ', '_')
    s = re.sub(r'[^A-Za-z0-9_.-]', '', s)
    return s[:64]  # limit length

def main(argv: Optional[list] = None):
    parser = argparse.ArgumentParser(description="Transcribe audio/video/local/remote file and summarize")
    parser.add_argument("--input", required=True, help="Path or URL to audio or video file (any format supported by ffmpeg)")
    parser.add_argument("--summary-length", choices=["short", "medium", "detailed"], default="short")
    parser.add_argument("--transcribe-model", default="gpt-4o-mini-transcribe")
    parser.add_argument("--summary-model", default="gpt-4o")
    args = parser.parse_args(argv)

    print(f"Starting transcription for: {args.input}")
    transcript = transcribe_audio(args.input, model=args.transcribe_model)
    print("Transcription complete.\n")
    print("Starting summarization...")
    summary = summarize_text(transcript, length=args.summary_length, model=args.summary_model)
    print("Summarization complete.\n")

    # Output directory and filenames
    os.makedirs("output", exist_ok=True)
    base = args.input
    if is_url(base):
        base = base.split('/')[-1].split('?')[0]
    base = sanitize_filename(base)
    transcript_path = f"output/{base}_transcript.txt"
    summary_path = f"output/{base}_summary.txt"

    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(transcript)
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary)

    print("--- Transcript ---")
    print(transcript)
    print("\n--- Summary ---")
    print(summary)

    print(f"\nTranscript saved to: {transcript_path}")
    print(f"Summary saved to: {summary_path}")

if __name__ == "__main__":
    main()
