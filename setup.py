from setuptools import setup, find_packages

setup(
    name="transcribe-summarize",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "openai>=1.0.0",
        "python-dotenv>=1.0",
        "requests>=2.0",
        "tqdm>=4.0",
        "yt-dlp>=2024.3.10",
    ],
    entry_points={
        "console_scripts": [
            "transcribe-summarize=transcribe_summarize.transcribe_summarize:main",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool to transcribe and summarize audio/video content using OpenAI",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    keywords="transcription, summarization, openai, audio, video",
    url="https://github.com/yourusername/transcribe-summarize",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
)