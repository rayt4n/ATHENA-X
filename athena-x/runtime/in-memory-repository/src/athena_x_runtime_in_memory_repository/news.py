"""In-memory NewsRepository."""
from __future__ import annotations
from datetime import datetime
from threading import RLock
from typing import Any

from athena_x_runtime_repository_interface import WriteResult, QueryResult
from athena_x_runtime_repository_interface.base import BaseRepository
from athena_x_runtime_db_events import DBEventEmitter, DBEventType
from athena_x_runtime_db_monitoring import DBMonitor


class InMemoryNewsRepository(BaseRepository):
    schema_name = "canonical_news"

    def __init__(self, event_emitter=None, monitor=None):
        self._articles: dict[str, dict] = {}  # id → article
        self._lock = RLock()
        self._emitter = event_emitter or DBEventEmitter()
        self._monitor = monitor or DBMonitor()

    async def write_article(self, record: Any) -> WriteResult:
        with self._monitor.track("write_article"):
            with self._lock:
                record_id = record.get("id", self._generate_record_id())
                stored = {"record_id": record_id, "data": record, "written_at": self._now().isoformat()}
                self._articles[record_id] = stored

            result = self._make_write_result(record_id, "headlines", event_published=True)
            await self._emitter.emit_write(
                event_type=DBEventType.NEWS_WRITTEN,
                schema=self.schema_name, table="headlines",
                record_id=record_id, symbol=None, payload=record,
            )
            return result

    async def read_article(self, article_id: str) -> Any | None:
        with self._monitor.track("read_article"):
            with self._lock:
                stored = self._articles.get(article_id)
                return stored["data"] if stored else None

    async def query_articles(
        self, symbols=None, categories=None,
        start=None, end=None, limit=50,
    ) -> QueryResult:
        with self._monitor.track("query_articles"):
            with self._lock:
                results = []
                for stored in self._articles.values():
                    article = stored["data"]
                    # Filter by symbols
                    if symbols and not any(s in article.get("symbols", []) for s in symbols):
                        continue
                    # Filter by categories
                    if categories and not any(c in article.get("categories", []) for c in categories):
                        continue
                    results.append(article)
                    if len(results) >= limit:
                        break
                return QueryResult(records=results, count=len(results))
