"""In-process Educational Identity cache for passive Phase 1 resolution."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock

from app.modules.eui.schemas.educational_identity import EducationalIdentity


@dataclass(frozen=True)
class EducationalIdentityCacheSnapshot:
    entries: int
    hits: int
    misses: int


class EducationalIdentityCache:
    """Small thread-safe in-process cache.

    This is intentionally not persistent. Later phases may add a different
    cache/storage strategy only through explicit authorization.
    """

    def __init__(self, *, max_entries: int = 512) -> None:
        self.max_entries = max_entries
        self._lock = Lock()
        self._items: dict[str, EducationalIdentity] = {}
        self._order: list[str] = []
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> EducationalIdentity | None:
        with self._lock:
            item = self._items.get(key)
            if item is None:
                self._misses += 1
                return None
            self._hits += 1
            return item

    def set(self, key: str, identity: EducationalIdentity) -> None:
        with self._lock:
            if key not in self._items:
                self._order.append(key)
            self._items[key] = identity
            while len(self._order) > self.max_entries:
                oldest = self._order.pop(0)
                self._items.pop(oldest, None)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()
            self._order.clear()
            self._hits = 0
            self._misses = 0

    def snapshot(self) -> EducationalIdentityCacheSnapshot:
        with self._lock:
            return EducationalIdentityCacheSnapshot(
                entries=len(self._items),
                hits=self._hits,
                misses=self._misses,
            )


educational_identity_cache = EducationalIdentityCache()
