"""
Couche base de données partagée pipeline <-> backend.

SQLite par défaut (zéro config, fichier unique) ; bascule PostgreSQL en posant
LEARNSCROLL_DATABASE_URL=postgresql+psycopg://user:pass@host/db.

Le feed ne lit QUE cette base : aucune génération IA au runtime. L'IA n'écrit
ici que via le pipeline batch.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime, Float, ForeignKey, Integer, String, Text, create_engine, func,
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker,
)

_DEFAULT_SQLITE = "sqlite:///" + os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "learnscroll.db")
)
DATABASE_URL = os.getenv("LEARNSCROLL_DATABASE_URL", _DEFAULT_SQLITE)

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Series(Base):
    __tablename__ = "series"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    category: Mapped[str] = mapped_column(String(40), default="")
    total: Mapped[int] = mapped_column(Integer, default=0)
    cards: Mapped[list["Card"]] = relationship(back_populates="series")


class Card(Base):
    __tablename__ = "cards"
    id: Mapped[int] = mapped_column(primary_key=True)
    # custom_id du batch : idempotence (on ne réinsère pas deux fois le même sujet).
    external_id: Mapped[str] = mapped_column(String(120), unique=True, index=True)

    hook: Mapped[str] = mapped_column(String(300))
    category: Mapped[str] = mapped_column(String(40), index=True)
    mode: Mapped[str] = mapped_column(String(20), index=True)  # actualite | info
    reading_time: Mapped[str] = mapped_column(String(10))
    teaser: Mapped[str] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text)

    _why: Mapped[str] = mapped_column("why_layers", Text, default="[]")
    _sources: Mapped[str] = mapped_column("sources", Text, default="[]")
    _tags: Mapped[str] = mapped_column("tags", Text, default="[]")
    image_prompt: Mapped[str] = mapped_column(Text, default="")
    image_url: Mapped[str] = mapped_column(Text, default="")

    model_used: Mapped[str] = mapped_column(String(60), default="")
    series_id: Mapped[int | None] = mapped_column(ForeignKey("series.id"), nullable=True)
    series_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    series: Mapped["Series | None"] = relationship(back_populates="cards")

    # -- JSON helpers (colonnes texte) ------------------------------------- #
    @property
    def why_layers(self) -> list[dict]:
        return json.loads(self._why or "[]")

    @why_layers.setter
    def why_layers(self, v: list[dict]) -> None:
        self._why = json.dumps(v, ensure_ascii=False)

    @property
    def sources(self) -> list[dict]:
        return json.loads(self._sources or "[]")

    @sources.setter
    def sources(self, v: list[dict]) -> None:
        self._sources = json.dumps(v, ensure_ascii=False)

    @property
    def tags(self) -> list[str]:
        return json.loads(self._tags or "[]")

    @tags.setter
    def tags(self, v: list[str]) -> None:
        self._tags = json.dumps(v, ensure_ascii=False)

    def to_feed(self) -> dict:
        """Vue légère pour le feed (sans le body complet)."""
        return {
            "id": self.id,
            "hook": self.hook,
            "category": self.category,
            "mode": self.mode,
            "reading_time": self.reading_time,
            "teaser": self.teaser,
            "image_url": self.image_url,
            "tags": self.tags,
        }

    def to_detail(self) -> dict:
        return {
            **self.to_feed(),
            "body": self.body,
            "why_layers": self.why_layers,
            "sources": self.sources,
            "series": self.series.name if self.series else None,
            "series_index": self.series_index,
        }


class WhyDeepCache(Base):
    """Cache des approfondissements « pourquoi » générés à la demande.

    Au-delà des couches pré-générées, on génère à la volée — mais UNE seule fois
    par (carte, question) : la réponse est ensuite servie depuis ce cache, jamais
    régénérée. Coût borné.
    """
    __tablename__ = "why_deep_cache"
    id: Mapped[int] = mapped_column(primary_key=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("cards.id"), index=True)
    question_hash: Mapped[str] = mapped_column(String(64), index=True)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Interaction(Base):
    """Signaux comportementaux : personnalisation + gamification."""
    __tablename__ = "interactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(80), index=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("cards.id"), index=True)
    kind: Mapped[str] = mapped_column(String(20), index=True)  # view | like | favorite | share | expand
    dwell_ms: Mapped[int] = mapped_column(Integer, default=0)   # temps passé sur la carte
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


def init_db() -> None:
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "data"), exist_ok=True)
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    init_db()
    print(f"Base initialisée : {DATABASE_URL}")
