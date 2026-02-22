import logging
import os
import re
from dataclasses import dataclass
from typing import Any, Callable, List, Optional
import yt_dlp


@dataclass
class StreamOption:
    itag: str  # Kept as 'itag' for compatibility, but stores yt-dlp format_id
    mime_type: str
    resolution: Optional[str]
    fps: Optional[int]
    abr: Optional[str]
    filesize: Optional[int] = None


class YouTubeDownloader:
    """High-level YouTube downloader using yt-dlp for better stability."""

    def __init__(self, url: str, logger: Optional[logging.Logger] = None, cache: Optional[Any] = None) -> None:
        self.url = url
        self.logger = logger or logging.getLogger(__name__)
        self.cache = cache
        self.info: Optional[dict] = None

    def _validate_url(self) -> None:
        if not isinstance(self.url, str) or not self.url:
            raise ValueError("Invalid YouTube URL provided.")

    def fetch_info(self) -> dict:
        """Fetch full video info using yt-dlp."""
        self._validate_url()
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android'],
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.165 Mobile Safari/537.36',
            },
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            self.info = ydl.extract_info(self.url, download=False)
        return self.info

    def fetch_streams(self) -> List[StreamOption]:
        """Fetch available streams and return a sorted list of options."""
        if not self.info:
            self.fetch_info()
        
        info = self.info
        options: List[StreamOption] = []
        
        formats = info.get('formats', [])
        for f in formats:
            # We want formats that have a resolution (video) or are audio-only
            if f.get('vcodec') != 'none' or f.get('acodec') != 'none':
                res = f.get('resolution')
                if not res and f.get('height'):
                    res = f"{f.get('height')}p"
                
                options.append(
                    StreamOption(
                        itag=f.get('format_id', ''),
                        mime_type=f.get('ext', ''),
                        resolution=res,
                        fps=f.get('fps'),
                        abr=str(f.get('abr')) if f.get('abr') else None,
                        filesize=f.get('filesize') or f.get('filesize_approx')
                    )
                )
        
        # Filter duplicates and sort
        unique_options = {}
        for opt in options:
            key = (opt.resolution, opt.mime_type)
            if key not in unique_options or (opt.filesize and (not unique_options[key].filesize or opt.filesize > unique_options[key].filesize)):
                unique_options[key] = opt
        
        result = list(unique_options.values())
        result.sort(key=lambda o: self._resolution_index(o.resolution), reverse=True)
        return result

    @staticmethod
    def _resolution_index(res: Optional[str]) -> int:
        if not res:
            return 0
        m = re.search(r"(\d+)", res)
        return int(m.group(1)) if m else 0

    def select_stream_for_resolution(self, streams: List[StreamOption], target: str) -> Optional[StreamOption]:
        t = target.lower()
        for s in streams:
            if s.resolution and s.resolution.lower() == t:
                return s
        return streams[0] if streams else None

    def download(self, itag: str, output_path: str, progress_cb: Optional[Callable] = None) -> str:
        """Download a specific format by its format_id (stored in itag)."""
        filename_collector = []

        def logger_hook(d):
            if d['status'] == 'downloading' and progress_cb:
                pass
            if d['status'] == 'finished':
                filename_collector.append(d['filename'])

        ydl_opts = {
            'format': f"{itag}+bestaudio/best",
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'progress_hooks': [logger_hook],
            'merge_output_format': 'mp4',
            'extractor_args': {
                'youtube': {
                    'player_client': ['android'],
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.165 Mobile Safari/537.36',
            },
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([self.url])
        
        return filename_collector[0] if filename_collector else ""

    def download_audio_only(self, output_path: str, progress_cb: Optional[Callable] = None) -> str:
        filename_collector = []

        def logger_hook(d):
            if d['status'] == 'finished':
                filename_collector.append(d['filename'])

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'progress_hooks': [logger_hook],
            'extractor_args': {
                'youtube': {
                    'player_client': ['android'],
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.165 Mobile Safari/537.36',
            },
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([self.url])
        
        return filename_collector[0] if filename_collector else ""
