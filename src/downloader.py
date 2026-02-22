import json
import logging
import os
import re
import subprocess
from dataclasses import dataclass
from typing import Any, Callable, List, Optional

from pytubefix import YouTube


@dataclass
class StreamOption:
    itag: int
    mime_type: str
    resolution: Optional[str]
    fps: Optional[int]
    abr: Optional[str]


class YouTubeDownloader:
    """High-level YouTube downloader with best-effort high-res support."""

    def __init__(self, url: str, logger: Optional[logging.Logger] = None, cache: Optional[Any] = None, client: str = 'MWEB') -> None:
        self.url = url
        self.logger = logger or logging.getLogger(__name__)
        self.cache = cache
        self.client = client

    def _validate_url(self) -> None:
        if not isinstance(self.url, str) or not self.url:
            raise ValueError("Invalid YouTube URL provided.")

    def fetch_streams(self) -> List[StreamOption]:
        """Fetch available streams for the URL and return a sorted list."""
        self._validate_url()
        try:
            yt = YouTube(
                self.url, 
                on_progress_callback=None, 
                on_complete_callback=None,
                client=self.client
            )  # type: ignore[arg-type]
        except Exception as exc:
            self.logger.exception("Failed to initialize YouTube object for URL: %s", self.url)
            raise

        options: List[StreamOption] = []
        for s in yt.streams:
            options.append(
                StreamOption(
                    itag=s.itag,
                    mime_type=s.mime_type,
                    resolution=getattr(s, 'resolution', None),
                    fps=getattr(s, 'fps', None),
                    abr=getattr(s, 'abr', None),
                )
            )
        # Prefer progressive streams (video+audio) if available; otherwise, fall back to the best video+audio split
        options.sort(key=lambda o: self._resolution_index(o.resolution), reverse=True)
        return options

    @staticmethod
    def _resolution_index(res: Optional[str]) -> int:
        if not res:
            return 0
        m = re.search(r"(\d+)", res)
        if m:
            try:
                return int(m.group(1))
            except ValueError:
                return 0
        return 0

    def select_stream_for_resolution(self, streams: List[StreamOption], target: str) -> Optional[StreamOption]:
        # exact match first
        t = target.lower()
        for s in streams:
            if s.resolution and s.resolution.lower() == t:
                return s
        # fallback to highest resolution not smaller than target
        target_num = self._parse_resolution(target)
        candidates = [s for s in streams if s.resolution]
        candidates.sort(key=lambda s: self._parse_resolution(s.resolution or ""), reverse=True)
        for s in candidates:
            if self._parse_resolution(s.resolution or "") >= target_num:
                return s
        return streams[0] if streams else None

    @staticmethod
    def _parse_resolution(res: str) -> int:
        m = re.search(r"(\d+)", res)
        return int(m.group(1)) if m else 0

    def download(self, itag: int, output_path: str, filename: Optional[str] = None,
                 progress_cb: Optional[Callable[[int, int], None]] = None) -> str:
        """Download a single stream by its itag."""
        yt = YouTube(self.url, on_progress_callback=progress_cb, client=self.client)
        stream = yt.streams.get_by_itag(itag)
        if stream is None:
            raise ValueError(f"Stream with itag {itag} not found.")
        return stream.download(output_path=output_path, filename=filename)  # type: ignore[arg-type]

    def download_audio_only(self, output_path: str, filename: Optional[str] = None,
                          progress_cb: Optional[Callable[[int, int], None]] = None) -> str:
        yt = YouTube(self.url, on_progress_callback=progress_cb, client=self.client)
        audio_streams = list(yt.streams.filter(only_audio=True))
        if not audio_streams:
            raise ValueError("No audio-only streams available.")
        # Choose highest bitrate if available
        audio_stream = max(audio_streams, key=lambda s: s.abr or "0kbps")
        return audio_stream.download(output_path=output_path, filename=filename)  # type: ignore[arg-type]

    @staticmethod
    def merge_video_audio(video_path: str, audio_path: str, output_path: str) -> None:
        """Merge separate video and audio streams using ffmpeg. Requires ffmpeg in PATH."""
        try:
            cmd = ["ffmpeg", "-y", "-i", video_path, "-i", audio_path, "-c", "copy", output_path]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception:
            raise
