"""API del piloto de FFR virtual. Apoyo a la decisión: no reemplaza el juicio médico.

Ejecutar:  uvicorn app.main:create_app --factory
"""
from __future__ import annotations

import hmac
import json
from dataclasses import dataclass
from typing import Callable

from fastapi import Depends, FastAPI, Header, HTTPException
from sqlalchemy import select

from app.audit import verify_chain
from app.config import Settings
from app.decision import Thresholds, check_eligibility, recommend, result_visible
from app.engines import build_engine
from app.engines.base import EngineInput
from app.metrics import concordance
from app.privacy import pseudonymize
from app.quality import Projection, assess_quality
from app.schemas import AnalysisOut, AnalysisRequest, CaseCreate, OutcomeIn, Recommendation
from app.store import (
    AnalysisRow, AuditRow, CaseRow, OutcomeRow, append_audit, make_session_factory, now_iso,
)

ROLES = ("technician", "operator", "researcher")


@dataclass(frozen=True)
class Actor:
    name: str
    role: str


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    settings.validate()
    thresholds = Thresholds(settings.defer_above, settings.favor_below)
    engine = build_engine(settings)
    sessions = make_session_factory(settings.database_url)

    app = FastAPI(title="VDL FFR virtual v1", version="0.1.0")
    app.state.sessions = sessions
    app.state.settings = settings

    # ---- Autenticación PLACEHOLDER: reemplazar por OIDC/SSO institucional con roles reales (sprint S2). ----
    def actor_dep(
        x_api_key: str = Header(...),
        x_actor: str = Header(...),
        x_role: str = Header(...),
    ) -> Actor:
        if not hmac.compare_digest(x_api_key, settings.api_key):
            raise HTTPException(401, "Credenciales inválidas")
        if x_role not in ROLES:
            raise HTTPException(403, "Rol no válido")
        return Actor(x_actor, x_role)

    def require(*roles: str) -> Callable[[Actor], Actor]:
        def dep(actor: Actor = Depends(actor_dep)) -> Actor:
            if actor.role not in roles:
                raise HTTPException(403, "Rol sin permiso para esta acción")
            return actor
        return dep

    def analysis_view(case_id: int, a: AnalysisRow, role: str) -> AnalysisOut:
        reasons = json.loads(a.quality_reasons)
        base = dict(case_id=case_id, mode=a.mode, analyzable=a.analyzable,
                    quality_ok=a.quality_ok, quality_reasons=reasons)
        if not result_visible(a.mode, role):
            return AnalysisOut(**base, visible=False,
                               message="Modo sombra: resultado almacenado, no disponible para uso clínico")
        return AnalysisOut(
            **base, visible=True, value=a.virtual_value,
            recommendation=Recommendation(a.recommendation) if a.recommendation else None,
            engine_name=a.engine_name, engine_version=a.engine_version,
        )

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "mode": settings.mode, "engine": engine.name}

    @app.post("/cases", status_code=201)
    def create_case(body: CaseCreate, actor: Actor = Depends(require("technician", "operator"))) -> dict:
        reasons = check_eligibility(body)
        if reasons:
            with sessions.begin() as s:
                append_audit(s, actor.name, actor.role, "case_rejected", {"reasons": reasons})
            raise HTTPException(422, {"eligible": False, "reasons": reasons})
        with sessions.begin() as s:
            row = CaseRow(
                patient_pseudonym=pseudonymize(body.patient_ref, settings.pseudonym_key),
                study_uid=body.study_uid, lesion_label=body.lesion_label,
                visual_stenosis_pct=body.visual_stenosis_pct,
                clinical_context=body.clinical_context.value, consent_id=body.consent_id,
                created_at=now_iso(), created_by=actor.name,
            )
            s.add(row)
            s.flush()
            append_audit(s, actor.name, actor.role, "case_created",
                         {"case_id": row.id, "pseudonym": row.patient_pseudonym, "consent_id": body.consent_id})
            return {"case_id": row.id, "pseudonym": row.patient_pseudonym}

    @app.post("/cases/{case_id}/analysis")
    def run_analysis(case_id: int, body: AnalysisRequest, actor: Actor = Depends(require(*ROLES))) -> AnalysisOut:
        with sessions.begin() as s:
            case = s.get(CaseRow, case_id)
            if not case:
                raise HTTPException(404, "Caso no encontrado")
            projections = [Projection(p.primary_angle, p.secondary_angle, p.frame_rate) for p in body.projections]
            q = assess_quality(
                projections,
                nitroglycerin_given=body.intracoronary_nitroglycerin,
                no_vessel_overlap=body.no_vessel_overlap,
                min_angle_deg=settings.min_angle_deg, min_fps=settings.min_fps,
            )
            value = None
            analyzable = False
            name = ver = None
            rec = Recommendation.not_analyzable
            if q.ok:
                res = engine.compute(EngineInput(case.study_uid, case.lesion_label, case.visual_stenosis_pct))
                analyzable, value, name, ver = res.analyzable, res.value, res.engine_name, res.engine_version
                if analyzable and value is not None:
                    rec = recommend(value, thresholds)
            row = AnalysisRow(
                case_id=case_id, created_at=now_iso(), created_by=actor.name, mode=settings.mode,
                quality_ok=q.ok, quality_reasons=json.dumps(q.reasons, ensure_ascii=False),
                analyzable=analyzable, virtual_value=value, recommendation=rec.value,
                engine_name=name, engine_version=ver,
                thresholds=json.dumps({"defer_above": thresholds.defer_above, "favor_below": thresholds.favor_below}),
            )
            s.add(row)
            s.flush()
            append_audit(s, actor.name, actor.role, "analysis_run", {
                "case_id": case_id, "analysis_id": row.id, "mode": settings.mode,
                "quality_ok": q.ok, "analyzable": analyzable, "engine": name, "engine_version": ver,
            })
            return analysis_view(case_id, row, actor.role)

    @app.get("/cases/{case_id}/analysis/latest")
    def latest_analysis(case_id: int, actor: Actor = Depends(require(*ROLES))) -> AnalysisOut:
        with sessions() as s:
            a = s.execute(select(AnalysisRow).where(AnalysisRow.case_id == case_id)
                          .order_by(AnalysisRow.id.desc()).limit(1)).scalar_one_or_none()
            if not a:
                raise HTTPException(404, "Sin análisis")
            return analysis_view(case_id, a, actor.role)

    @app.post("/cases/{case_id}/outcome", status_code=201)
    def record_outcome(case_id: int, body: OutcomeIn, actor: Actor = Depends(require("operator"))) -> dict:
        if (body.wire_value is None) != (body.wire_type is None):
            raise HTTPException(422, "wire_value y wire_type deben enviarse juntos")
        with sessions.begin() as s:
            if not s.get(CaseRow, case_id):
                raise HTTPException(404, "Caso no encontrado")
            row = OutcomeRow(
                case_id=case_id, created_at=now_iso(), recorded_by=actor.name,
                operator_decision=body.operator_decision.value,
                wire_value=body.wire_value, wire_type=body.wire_type.value if body.wire_type else None,
            )
            s.add(row)
            s.flush()
            append_audit(s, actor.name, actor.role, "outcome_recorded", {
                "case_id": case_id, "decision": row.operator_decision, "has_wire": body.wire_value is not None})
            return {"outcome_id": row.id}

    @app.get("/metrics/concordance")
    def metrics(actor: Actor = Depends(require("researcher"))) -> dict:
        with sessions() as s:
            pairs: list[tuple[float, float]] = []
            total = analyzable = 0
            for case in s.execute(select(CaseRow)).scalars():
                a = s.execute(select(AnalysisRow).where(AnalysisRow.case_id == case.id)
                              .order_by(AnalysisRow.id.desc()).limit(1)).scalar_one_or_none()
                if not a:
                    continue
                total += 1
                analyzable += int(a.analyzable)
                o = s.execute(select(OutcomeRow).where(OutcomeRow.case_id == case.id, OutcomeRow.wire_value.is_not(None))
                              .order_by(OutcomeRow.id.desc()).limit(1)).scalar_one_or_none()
                if a.analyzable and a.virtual_value is not None and o:
                    pairs.append((a.virtual_value, o.wire_value))
            return {"cases_analyzed": total,
                    "analyzable_rate": (analyzable / total) if total else None,
                    "concordance": concordance(pairs).as_dict()}

    @app.get("/audit/verify")
    def audit_verify(actor: Actor = Depends(require("researcher"))) -> dict:
        with sessions() as s:
            rows = list(s.execute(select(AuditRow).order_by(AuditRow.id)).scalars())
            ok, bad = verify_chain(rows)
            return {"events": len(rows), "chain_ok": ok, "first_bad_index": bad}

    return app
