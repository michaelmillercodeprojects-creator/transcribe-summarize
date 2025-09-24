#!/bin/bash
# Usage: ./summarize.sh <input_path_or_url> [summary-length]
# Example: ./summarize.sh audio/myfile.mp3 short
#          ./summarize.sh https://www.youtube.com/watch?v=xxxx medium
set -e

if [ -z "$OPENAI_API_KEY" ]; then
  echo "Error: OPENAI_API_KEY is not set. Export it or add to .env."
  exit 1
fi

INPUT="$1"
SUMMARY_LENGTH="${2:-short}"

if [ -z "$INPUT" ]; then
  echo "Usage: $0 <input_path_or_url> [summary-length]"
  exit 1
fi

python -m transcribe_summarize.transcribe_summarize --input "$INPUT" --summary-length "$SUMMARY_LENGTH"
