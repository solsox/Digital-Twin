"""Persistencia (SQLAlchemy 2). SQLite en desarrollo/pruebas, PostgreSQL en el entorno real."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import ForeignKey, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool

from app.audit import GENESIS, canonical, compute_hash


class Base(DeclarativeBase):
    pass


class CaseRow(Base):
    __tablename__ = "cases"
    id: Mapped[int] = mapped_column(primary_key=True)
    patient_pseudonym: Mapped[str] = mapped_column(String(64), index=True)
    study_uid: Mapped[str] = mapped_column(String(128))
    lesion_label: Mapped[str] = mapped_column(String(128))
    visual_stenosis_pct: Mapped[int]
    clinical_context: Mapped[str] = mapped_column(String(64))
    consent_id: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[str] = mapped_column(String(40))
    created_by: Mapped[str] = mapped_column(String(64))


class AnalysisRow(Base):
    __tablename__ = "analyses"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), index=True)
    created_at: Mapped[str] = mapped_column(String(40))
    created_by: Mapped[str] = mapped_column(String(64))
    mode: Mapped[str] = mapped_column(String(16))
    quality_ok: Mapped[bool]
    quality_reasons: Mapped[str] = mapped_column(Text, default="[]")
    analyzable: Mapped[bool]
    virtual_value: Mapped[Optional[float]]
    recommendation: Mapped[Optional[str]] = mapped_column(String(32))
    engine_name: Mapped[Optional[str]] = mapped_column(String(64))
    engine_version: Mapped[Optional[str]] = mapped_column(String(32))
    thresholds: Mapped[str] = mapped_column(Text, default="{}")


class OutcomeRow(Base):
    __tablename__ = "outcomes"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), index=True)
    created_at: Mapped[str] = mapped_column(String(40))
    recorded_by: Mapped[str] = mapped_column(String(64))
    operator_decision: Mapped[str] = mapped_column(String(32))
    wire_value: Mapped[Optional[float]]
    wire_type: Mapped[Optional[str]] = mapped_column(String(8))


class AuditRow(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    ts: Mapped[str] = mapped_column(String(40))
    actor: Mapped[str] = mapped_column(String(64))
    role: Mapped[str] = mapped_column(String(32))
    event_type: Mapped[str] = mapped_column(String(64))
    payload: Mapped[str] = mapped_column(Text)
    prev_hash: Mapped[str] = mapped_column(String(64))
    hash: Mapped[str] = mapped_column(String(64))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def make_session_factory(database_url: str) -> sessionmaker[Session]:
    kwargs: dict[str, Any] = {}
    if database_url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        if ":memory:" in database_url:
            kwargs["poolclass"] = StaticPool
    engine = create_engine(database_url, **kwargs)
    Base.metadata.create_all(engine)
    return sessionmaker(engine, expire_on_commit=False)


def append_audit(session: Session, actor: str, role: str, event_type: str, payload: dict[str, Any]) -> AuditRow:
    """Agrega un evento a la cadena. En PostgreSQL con varias réplicas usar un bloqueo
    consultivo (pg_advisory_xact_lock) para serializar la escritura de la cadena."""
    last = session.execute(select(AuditRow).order_by(AuditRow.id.desc()).limit(1)).scalar_one_or_none()
    prev = last.hash if last else GENESIS
    ts = now_iso()
    body = canonical(payload)
    row = AuditRow(
        ts=ts, actor=actor, role=role, event_type=event_type, payload=body,
        prev_hash=prev, hash=compute_hash(prev, ts, actor, role, event_type, body),
    )
    session.add(row)
    session.flush()
    return row
