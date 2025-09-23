import os
from typing import Optional


def is_valid_api_key(key: str) -> bool:
    """Check if string looks like a valid OpenAI API key format."""
    if not key or not isinstance(key, str):
        return False
    # Most OpenAI keys start with 'sk-' and are 51 characters long
    return key.startswith('sk-') and len(key) >= 40

def load_api_key() -> Optional[str]:
    """Load OpenAI API key from multiple locations in priority order:
    1. Environment variable OPENAI_API_KEY
    2. .env file in current directory
    3. ~/.openai/api_key file
    4. ./api_key file in current directory
    """
    # Try environment variable first
    key = os.environ.get("OPENAI_API_KEY")
    if is_valid_api_key(key):
        return key

    # Look for .env file in current directory
    if os.path.exists(".env"):
        try:
            with open(".env") as f:
                for line in f:
                    if line.startswith("OPENAI_API_KEY="):
                        key = line.split("=", 1)[1].strip().strip("'\"")
                        if is_valid_api_key(key):
                            return key
        except:
            pass

    # Check ~/.openai/api_key
    home = os.path.expanduser("~")
    openai_config = os.path.join(home, ".openai", "api_key")
    if os.path.exists(openai_config):
        try:
            with open(openai_config) as f:
                key = f.read().strip()
                if is_valid_api_key(key):
                    return key
        except:
            pass

    # Finally check ./api_key in current directory
    if os.path.exists("api_key"):
        try:
            with open("api_key") as f:
                key = f.read().strip()
                if is_valid_api_key(key):
                    return key
        except:
            pass

    return None


def format_summary_prompt(transcript: str, length: str = "short") -> str:
    """Return a prompt instructing the model to summarize the transcript.

    length: 'short'|'medium'|'detailed'
    """
    if length not in ("short", "medium", "detailed"):
        raise ValueError("length must be 'short', 'medium', or 'detailed'")
    return (
        f"Summarize the following transcript into a {length} concise summary. "
        "Keep key points, speakers if clear, and action items when present:\n\n"
        f"{transcript}"
    )
