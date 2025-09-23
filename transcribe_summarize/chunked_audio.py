import subprocess
import tempfile
import os
from typing import List, Tuple

def get_audio_duration(audio_path: str) -> float:
    """Get audio duration in seconds using ffmpeg."""
    cmd = ["ffmpeg", "-i", audio_path]
    try:
        result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        output = result.stderr.decode()
        # Find Duration: HH:MM:SS.ms line
        for line in output.split('\n'):
            if 'Duration:' in line:
                time_str = line.split('Duration:')[1].split(',')[0].strip()
                h, m, s = time_str.split(':')
                return float(h) * 3600 + float(m) * 60 + float(s)
        raise ValueError(f"Could not find duration in ffmpeg output:\n{output}")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ffmpeg failed: {e.stderr.decode()}")

def extract_audio_chunk(video_path: str, start_time: float, duration: float) -> str:
    """Extract a chunk of audio from video using ffmpeg."""
    temp_fd, temp_audio_path = tempfile.mkstemp(suffix=".mp3")
    os.close(temp_fd)
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_time),  # start time in seconds
        "-t", str(duration),     # duration in seconds
        "-i", video_path,        # input
        "-vn",                   # disable video
        "-acodec", "libmp3lame", # use mp3 codec
        "-ar", "16000",          # 16kHz sampling rate
        "-ac", "1",              # mono
        "-b:a", "32k",           # 32kbps bitrate
        temp_audio_path
    ]
    print(f"Extracting audio chunk using ffmpeg command: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Audio chunk extraction complete. Saved to: {temp_audio_path}")
        if not os.path.exists(temp_audio_path):
            raise RuntimeError("ffmpeg did not produce output file")
        return temp_audio_path
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode(errors='ignore')
        raise RuntimeError(f"ffmpeg audio extraction failed:\nCommand: {' '.join(cmd)}\nError: {error_msg}")

def get_audio_chunks(audio_path: str, max_duration: float = 1380, overlap: float = 10) -> List[Tuple[float, float]]:
    """Split audio into chunks of max_duration with overlap seconds of overlap."""
    duration = get_audio_duration(audio_path)
    if duration <= max_duration:
        return [(0, duration)]
    
    chunks = []
    start = 0
    while start < duration:
        chunk_duration = min(max_duration, duration - start)
        chunks.append((start, chunk_duration))
        start += max_duration - overlap
    return chunks