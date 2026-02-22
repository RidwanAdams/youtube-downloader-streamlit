import unittest
from unittest.mock import MagicMock

from src.downloader import YouTubeDownloader, StreamOption


class TestYouTubeDownloader(unittest.TestCase):
    def test_parse_resolution_digits(self):
        dl = YouTubeDownloader(url="http://example")
        # access private helper for test
        self.assertEqual(dl._resolution_index("1080p"), 1080)
        self.assertEqual(dl._resolution_index("2160p"), 2160)
        self.assertEqual(dl._resolution_index(None), 0)

    def test_select_stream_for_resolution_exact(self):
        streams = [
            StreamOption(itag=1, mime_type="video/mp4", resolution="1080p", fps=30, abr=None),
            StreamOption(itag=2, mime_type="video/mp4", resolution="2160p", fps=60, abr=None),
            StreamOption(itag=3, mime_type="video/mp4", resolution="4320p", fps=60, abr=None),
        ]
        dl = YouTubeDownloader(url="http://example")
        chosen = dl.select_stream_for_resolution(streams, "2160p")
        self.assertIsNotNone(chosen)
        self.assertEqual(chosen.resolution, "2160p")

    def test_select_stream_for_resolution_fallback(self):
        streams = [
            StreamOption(itag=1, mime_type="video/mp4", resolution="1080p", fps=30, abr=None),
            StreamOption(itag=2, mime_type="video/mp4", resolution="720p", fps=30, abr=None),
        ]
        dl = YouTubeDownloader(url="http://example")
        chosen = dl.select_stream_for_resolution(streams, "1800p")
        self.assertIsNotNone(chosen)
        self.assertEqual(chosen.resolution, "1080p")


if __name__ == '__main__':
    unittest.main()
