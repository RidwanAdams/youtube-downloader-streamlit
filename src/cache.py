import json
import os
from typing import Any, Dict, Optional


class Cache:
    """Simple JSON file cache for video metadata.

    Stores data under a single JSON file. Created per-user in the home directory.
    """

    def __init__(self, path: Optional[str] = None) -> None:
        self.path = path or os.path.expanduser("~/.youtube_downloader/cache.json")
        self._data: Dict[str, Any] = {}
        self._ensure_dir()
        self._load()

    def _ensure_dir(self) -> None:
        dirpath = os.path.dirname(self.path)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)

    def _load(self) -> None:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except Exception:
                self._data = {}
        else:
            self._data = {}

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
        self._save()

    def _save(self) -> None:
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
        except Exception:
            # Best-effort save; don't crash the caller on caching issues
            pass
