# vdl-fvirtual-v1 — Plataforma del piloto de FFR virtual (Fundación Valle del Lili)

> **ESQUELETO NO CLÍNICO.** Contiene la plataforma que la institución controla (calidad de imagen,
> reglas, trazabilidad, privacidad, métricas, API). El motor incluido (`mock-NON-CLINICAL`) es
> **simulado** y no representa fisiología real. No usar para decidir conductas. El motor real será el
> SDK/servicio de un proveedor con el marco regulatorio confirmado.

> **Plan completo (fases, backlog por sprints, despliegue, checklist):** `docs/PLAN_MAESTRO_FFR_VIRTUAL_VDL.md`

## Qué resuelve la v1
1. Elegibilidad del caso (40–90 % de estenosis visual, contexto crónico/ACS estabilizado, exclusiones).
2. Puerta de calidad angiográfica (≥2 proyecciones, separación angular, fps, nitroglicerina, sin superposición).
3. Interfaz de motor intercambiable (`app/engines/`).
4. Reglas de apoyo a la decisión con zona gris configurable (`app/decision.py`).
5. **Modo sombra / guiado** (`MODE`): en sombra el resultado se guarda pero no se muestra a roles clínicos.
6. Seudonimización HMAC (la historia clínica **no se almacena**) y desidentificación DICOM básica.
7. Auditoría encadenada por hash con verificación (`GET /audit/verify`).
8. Métricas de concordancia frente a guía de presión (`GET /metrics/concordance`).

## Stack
Python 3.12 · FastAPI · Pydantic v2 · SQLAlchemy 2 · PostgreSQL 16 · Orthanc · Docker Compose.
Fase posterior: React + TypeScript (visor), HL7 FHIR R4 (integración), Prometheus/Grafana.

## Ejecutar
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest                                   # 28 pruebas

cp .env.example .env                     # editar secretos
docker compose up --build                # API :8000, Orthanc :8042
# sin Docker:
export API_KEY=una-clave-larga-1234 PSEUDONYM_KEY=$(python -c "import secrets;print(secrets.token_hex(32))") ALLOW_MOCK_ENGINE=true MODE=shadow
uvicorn app.main:create_app --factory
```
Documentación interactiva: `http://localhost:8000/docs`

## API (cabeceras: `X-Api-Key`, `X-Actor`, `X-Role` ∈ technician | operator | researcher)
| Método y ruta | Roles | Función |
|---|---|---|
| `POST /cases` | technician, operator | Crea caso (valida elegibilidad, seudonimiza) |
| `POST /cases/{id}/analysis` | todos | Puerta de calidad → motor → regla de decisión |
| `GET /cases/{id}/analysis/latest` | todos | Último análisis (respeta modo sombra) |
| `POST /cases/{id}/outcome` | operator | Decisión real y valor de guía de presión |
| `GET /metrics/concordance` | researcher | Concordancia y tasa de casos analizables |
| `GET /audit/verify` | researcher | Verifica la cadena de auditoría |

## Pendiente antes de cualquier uso clínico
- [ ] Adaptador real en `app/engines/vendor.py` (tras contrato y marco regulatorio).
- [ ] **Autenticación real**: el esquema por cabeceras es un *placeholder*; integrar OIDC/SSO con roles.
- [ ] Servicio de ingesta DICOM (Orthanc → `quality.extract_projection`).
- [ ] Bloqueo consultivo de PostgreSQL para serializar la cadena de auditoría con varias réplicas.
- [ ] Desidentificación completa (perfil DICOM PS3.15, píxeles quemados) y política de retención.
- [ ] TLS, secretos, copias de seguridad, monitoreo y pruebas de carga.
- [ ] Pruebas de seguridad y validación según el marco regulatorio.
- [ ] Conector FHIR e interfaz de revisión.
- [ ] Umbrales **aprobados por el comité clínico** (los de `.env.example` son borrador).

## Estructura
```
app/  config.py schemas.py quality.py decision.py privacy.py audit.py metrics.py store.py main.py
      engines/ base.py mock.py vendor.py
tests/  test_core.py test_api.py conftest.py
docs/   PLAN_MAESTRO_FFR_VIRTUAL_VDL.md
```
