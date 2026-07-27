"""In-process Educational Context cache for passive Phase 1 resolution."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock

from app.modules.eui.schemas.educational_context import EducationalContext


@dataclass(frozen=True)
class EducationalContextCacheSnapshot:
    entries: int
    hits: int
    misses: int


class EducationalContextCache:
    """Small thread-safe in-process cache.

    This is intentionally process-local and non-persistent. Later phases may add
    a different cache/storage strategy only through explicit authorization.
    """

    def __init__(self, *, max_entries: int = 512) -> None:
        self.max_entries = max_entries
        self._lock = Lock()
        self._items: dict[str, EducationalContext] = {}
        self._order: list[str] = []
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> EducationalContext | None:
        with self._lock:
            item = self._items.get(key)
            if item is None:
                self._misses += 1
                return None
            self._hits += 1
            return item

    def set(self, key: str, context: EducationalContext) -> None:
        with self._lock:
            if key not in self._items:
                self._order.append(key)
            self._items[key] = context
            while len(self._order) > self.max_entries:
                oldest = self._order.pop(0)
                self._items.pop(oldest, None)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()
            self._order.clear()
            self._hits = 0
            self._misses = 0

    def snapshot(self) -> EducationalContextCacheSnapshot:
        with self._lock:
            return EducationalContextCacheSnapshot(
                entries=len(self._items),
                hits=self._hits,
                misses=self._misses,
            )


educational_context_cache = EducationalContextCache()
