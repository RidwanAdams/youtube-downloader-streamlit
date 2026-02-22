import threading
import os
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional

from .downloader import YouTubeDownloader, StreamOption
from .cache import Cache

import logging


class YouTubeDownloaderGUI:
    def __init__(self, root: Optional[tk.Tk] = None) -> None:
        self.root = root or tk.Tk()
        self.root.title("YouTube Downloader – High Resolution")
        self.logger = logging.getLogger(__name__)
        self.cache = Cache()
        self._build_ui()

    def _build_ui(self) -> None:
        pad = 6
        # URL
        tk.Label(self.root, text="Video URL:").grid(row=0, column=0, sticky="e", pady=pad, padx=pad)
        self.url_var = tk.StringVar()
        self.url_entry = tk.Entry(self.root, textvariable=self.url_var, width=60)
        self.url_entry.grid(row=0, column=1, columnspan=3, sticky="we", pady=pad, padx=pad)

        # Resolution / Format selection
        tk.Label(self.root, text="Resolution:").grid(row=1, column=0, sticky="e", pady=pad, padx=pad)
        self.res_var = tk.StringVar(value="1080p")
        self.res_combo = ttk.Combobox(self.root, textvariable=self.res_var, values=["8K","4K","2K","1080p","720p"], state="readonly", width=6)
        self.res_combo.grid(row=1, column=1, sticky="w", pady=pad, padx=pad)

        tk.Label(self.root, text="Format:").grid(row=1, column=2, sticky="e", pady=pad, padx=pad)
        self.format_var = tk.StringVar(value="MP4 (progressive)")
        self.format_combo = ttk.Combobox(self.root, textvariable=self.format_var, values=["MP4 (progressive)", "WebM (progressive)", "MKV (progressive)", "Audio only"], state="readonly", width=20)
        self.format_combo.grid(row=1, column=3, sticky="w", pady=pad, padx=pad)

        # Buttons
        self.fetch_btn = tk.Button(self.root, text="Fetch Info", command=self.fetch_info)
        self.fetch_btn.grid(row=2, column=0, pady=pad, padx=pad)
        self.download_btn = tk.Button(self.root, text="Download", command=self.start_download)
        self.download_btn.grid(row=2, column=1, pady=pad, padx=pad)

        # Progress
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=400, mode="determinate")
        self.progress.grid(row=3, column=0, columnspan=4, sticky="we", pady=pad, padx=pad)
        self.status = tk.StringVar(value="Idle")
        self.status_label = tk.Label(self.root, textvariable=self.status)
        self.status_label.grid(row=4, column=0, columnspan=4, sticky="w", pady=pad, padx=pad)

        self.root.grid_columnconfigure(1, weight=1)

    def fetch_info(self) -> None:
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Input required", "Please enter a YouTube video URL.")
            return
        # Minimal feedback; the actual fetch will occur in a background thread during download
        self.status.set("Info cached (if any) or will fetch during download.")

    def start_download(self) -> None:
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Input required", "Please enter a YouTube video URL.")
            return
        # Run download in a worker thread to keep GUI responsive
        thread = threading.Thread(target=self._download_worker, args=(url,), daemon=True)
        thread.start()

    def _download_worker(self, url: str) -> None:
        try:
            self.status.set("Preparing download...")
            downloader = YouTubeDownloaderGUI._make_downloader(url, self.logger)
            streams = downloader.fetch_streams()
            # Pick a stream by user-selected resolution
            target_res = self.res_var.get()
            chosen = downloader.select_stream_for_resolution(streams, target_res)
            if chosen is None:
                raise RuntimeError("No suitable stream found for the selected resolution.")

            self.status.set(f"Downloading: {chosen.resolution or 'audio'}... (itag={chosen.itag})")
            self._update_progress(0)
            # Directory for downloads
            out_dir = os.path.abspath("downloads")
            os.makedirs(out_dir, exist_ok=True)
            def progress_hook(block_num: int, block_size: int, total_size: int) -> None:
                # PyTube on_progress signature: stream, chunk, bytes_remaining; adapt with a simple pct
                try:
                    if total_size:
                        percent = int((block_num * block_size) / total_size * 100)
                        self._update_progress(min(max(percent, 0), 100))
                except Exception:
                    pass

            # Download
            file_path = downloader.download(chosen.itag, output_path=out_dir, progress_cb=None)
            self.status.set("Download complete: " + file_path)
            self._update_progress(100)
        except Exception as exc:
            self.logger.exception("Download error: %s", str(exc))
            self._show_error(f"Download failed: {exc}")

    @staticmethod
    def _make_downloader(url: str, logger: logging.Logger) -> YouTubeDownloader:
        from .downloader import YouTubeDownloader
        return YouTubeDownloader(url=url, logger=logger)

    def _update_progress(self, value: int) -> None:
        try:
            self.progress['value'] = value
        except Exception:
            pass

    def _show_error(self, message: str) -> None:
        messagebox.showerror("Error", message)

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)
    gui = YouTubeDownloaderGUI()
    gui.run()
