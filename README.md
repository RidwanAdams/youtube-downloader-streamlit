# YouTube Downloader

A Python-based YouTube video downloader with high-resolution support, built using pytube. This project provides:
- Highest available video resolutions (including 1080p, 2K, 4K, and 8K when available)
- Audio-only downloads
- Optional merging via FFmpeg for separate video and audio streams
- A Tkinter-based GUI for desktop use
- A **Streamlit web interface** for browser-based downloads
- Caching of video metadata to speed up repeated lookups
- Basic tests with a small unit-test suite

## Prerequisites

- Python 3.10+
- pytube
- streamlit (for web interface)
- FFmpeg (optional, for merging video+audio)

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or install in editable mode
pip install -e .
```

## Usage

### Web Interface (Recommended)

Run the Streamlit web app:

```bash
streamlit run app.py
```

Then open your browser at `http://localhost:8501`

### Desktop GUI

```bash
python -m src.gui
```

### Command Line

```bash
python -c "from src.downloader import YouTubeDownloader; d = YouTubeDownloader('VIDEO_URL'); streams = d.fetch_streams(); stream = d.select_stream_for_resolution(streams, '1080p'); d.download(stream.itag, 'downloads')"
```

## Notes

- The design emphasizes clarity, modularity, and testability. Some advanced features (like robust download resuming across YouTube's adaptive streams) require deeper integration and additional tooling beyond this initial scaffold.
