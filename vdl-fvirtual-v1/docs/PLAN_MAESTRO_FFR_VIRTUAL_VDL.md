# Plan maestro: piloto de FFR virtual (Fundación Valle del Lili)

**Versión 1.0 (borrador para aprobación)** · 29 de octubre de 2026
**Para:** Comité Directivo, Comité Clínico y Comité de Ingeniería
**Contenido del paquete:** este documento + `vdl-fvirtual-v1.zip` (código base, pruebas y contenedores).

> **Alcance de este documento.** Reúne el plan clínico, regulatorio, social y de ingeniería, las fases del proyecto hasta el despliegue final, y el trabajo pendiente del código. Los umbrales numéricos marcados como *borrador* deben ser ratificados por el comité clínico y un bioestadístico. El marco regulatorio colombiano **no fue verificado** en detalle: debe confirmarlo Asuntos Regulatorios y Jurídico antes de iniciar.

---

## 1. Resumen ejecutivo

Piloto de 12 meses para incorporar en hemodinamia una herramienta de **FFR virtual basada en angiografía** (estimación computacional de la reserva fraccional de flujo sin guía de presión), con un módulo de **planificación de stent solo en modo investigación**. Responde tres preguntas con datos propios:

1. ¿El software concuerda con la guía de presión en nuestros pacientes?
2. ¿Reduce intervenciones innecesarias sin aumentar eventos?
3. ¿Es operable, seguro y sostenible en la Fundación?

**Principios:** apoyo a la decisión (no automática); validar antes de usar (modo sombra); guía de presión como respaldo y estándar de validación; datos, trazabilidad y auditoría desde el día 1; la responsabilidad clínica es siempre del médico tratante.

---

## 2. Aclaraciones sobre la evidencia

1. **El "0,8" es una razón de presiones, no un flujo.** FFR ≤ 0,80 indica isquemia funcional; los métodos virtuales (QFR, FFRangio, CT-FFR) la estiman.
2. **"Gemelo digital" agrupa tres cosas con evidencia distinta:** FFR virtual (la más sólida), modelo anatómico 3D (útil, sin efecto demostrado por sí solo) y stenting virtual (evidencia clínica escasa → solo investigación).
3. **La cifra de "casi 20 % menos de stents" salió de una entrevista;** no es una meta transferible. Se mide localmente.
4. **El FFR virtual no sustituye a la guía de presión cuando esta está disponible.** En FAVOR III Europa-Japón (2.000 pacientes; Lancet 2024;404:1835-1846) la estrategia guiada por QFR no fue no inferior a la guiada por FFR (eventos a 12 meses 6,7 % vs 4,2 %), con más revascularizaciones en el grupo QFR. FAVOR III China mostró ventaja de QFR frente a decidir solo con la imagen. **El comparador relevante de nuestro piloto es la decisión visual por angiografía**, con guía de presión en la zona gris.

---

## 3. Alcance de la v1

| | |
|---|---|
| **Tecnología** | FFR virtual por angiografía invasiva (sin hardware, contraste ni radiación adicionales). CT-FFR → fase posterior. |
| **Incluir** | Enfermedad coronaria crónica o ACS estabilizado con ≥ 1 lesión intermedia no culpable (40–90 % visual). |
| **Excluir** | Infarto con elevación del ST (lesión culpable), choque cardiogénico, tronco coronario no protegido, injertos, oclusiones crónicas, calcificación severa u ostial, angiografía de calidad insuficiente. |
| **Fuera de alcance** | Decisiones automáticas; stenting virtual con influencia clínica; uso fuera de hemodinamia. |

---

## 4. Gobernanza y responsables

| Rol | Responsabilidad |
|---|---|
| Patrocinador ejecutivo | Presupuesto, prioridad, desbloqueo de decisiones |
| Líder clínico (hemodinamista) | Protocolo, umbrales, criterios de pausa |
| Comité clínico (hemodinamia, cardiología, cirugía CV, imágenes) | Heart Team, revisión de casos discordantes |
| Ingeniería biomédica y TI | Arquitectura, integración, ciberseguridad, operación |
| Calidad y seguridad del paciente | Indicadores, eventos adversos |
| Regulatorio y jurídico | INVIMA, datos personales, contrato con proveedor |
| Comité de ética en investigación | Aprobación del protocolo y consentimiento |
| Investigación y bioestadística | Diseño, recolección, análisis |
| Trabajo social, comunicaciones, atención al usuario | Comunicación con pacientes y familias |
| **Comité de monitoreo de seguridad** | Revisa datos y puede **pausar** el programa |

---

## 5. Marco legal y regulatorio (validar)

- **INVIMA:** dispositivos médicos con registro sanitario (Decreto 4725 de 2005). Pedir al proveedor su registro o permiso vigente; si no lo tiene, encuadrar como investigación clínica con las autorizaciones aplicables.
- **Datos personales:** Ley 1581 de 2012 y reglamentación; los datos de salud son sensibles (autorización expresa e informada).
- **Transferencia internacional:** confirmar dónde se procesan las imágenes; preferir procesamiento local o imágenes desidentificadas.
- **Historia clínica y habilitación:** Resolución 1995 de 1999, interoperabilidad (Ley 2015 de 2020) y estándares de habilitación vigentes.
- **Responsabilidad:** software de apoyo; debe constar en protocolo, consentimiento y contrato.

---

## 6. Protocolo clínico

**Flujo en sala**
1. Angiografía con calidad mínima: ≥ 2 proyecciones separadas ≥ 25°, nitroglicerina intracoronaria, sin superposición (parámetros finales según fabricante).
2. Técnico entrenado carga el estudio y obtiene el valor virtual (meta *borrador*: < 10 min).
3. El hemodinamista interpreta el valor junto con anatomía y cuadro clínico.

**Reglas de decisión (borrador para el comité)**

| Valor virtual | Conducta sugerida |
|---|---|
| > 0,85 | Diferir ICP, tratamiento médico óptimo |
| 0,75 – 0,85 (zona gris) | Confirmar con guía de presión (FFR/iFR) o imagen intravascular |
| < 0,75 | Favorece ICP; decide el operador |

**Siempre:** tratamiento médico óptimo y rehabilitación cardiaca si se difiere el stent; Heart Team en casos complejos o discordantes; IVUS/OCT como estándar de confirmación; stenting virtual solo comparado a posteriori con lo implantado.
**Seguimiento:** 30 días y 12 meses (muerte, infarto, revascularización no planificada, angina, calidad de vida).

---

## 7. Fases del proyecto (de la preparación al despliegue final)

### Visión general

| Fase | Periodo | Objetivo | Puerta de salida |
|---|---|---|---|
| **0. Preparación** | Meses 0–2 | Habilitar legal, ético, clínico y técnico | Gate A |
| **1. Despliegue técnico en modo sombra** | Mes 3 | Poner la plataforma en operación sin influir en conductas | Gate B |
| **2. Modo sombra (validación)** | Meses 3–5 | Medir concordancia con guía de presión | Gate C |
| **3. Uso guiado supervisado** | Meses 6–12 | Usar el resultado para decidir con respaldo de presión | Gate D |
| **4. Evaluación y escala** | Mes 12+ | Decidir institucionalización y expansión | Decisión final |

### Fase 0 — Preparación (meses 0–2)

| Frente | Entregables |
|---|---|
| Clínico | Comité conformado; protocolo v1; umbrales borrador; hoja de recolección; plan de entrenamiento |
| Regulatorio/jurídico | Concepto sobre INVIMA; contrato con proveedor (datos, lugar de procesamiento, auditoría, incidentes, salida); evaluación de transferencia de datos |
| Ético | Protocolo y consentimiento aprobados por el comité de ética |
| Investigación | Línea base (lesiones intermedias evaluadas en el último año y tasa histórica de ICP); plan estadístico; tamaño muestral |
| Ingeniería | Repositorio, CI, entornos dev/staging; mapa de integración con sala de hemodinamia y PACS; sprints 1–4 (sección 8) |
| Social | Material para pacientes; plan de comunicación; estrategia de campeones |

**Gate A (para pasar a despliegue):** contrato firmado · concepto regulatorio y aprobación ética obtenidos · protocolo y umbrales aprobados · línea base medida · plan de entrenamiento listo · presupuesto aprobado.

### Fase 1 — Despliegue técnico en modo sombra (mes 3)

- Ambiente de producción on-premise con `MODE=shadow`.
- Integración real: Orthanc ↔ servicio de ingesta ↔ API ↔ motor del proveedor.
- Pruebas de seguridad (configuración y penetración) y ensayo de recuperación de desastres.
- Entrenamiento de técnicos y hemodinamistas; simulacros en sala.
- Procedimiento de caída: ante cualquier falla se vuelve a la práctica habitual sin impacto asistencial.

**Gate B (puesta en marcha):** lista de verificación de la sección 9 completa · ensayo en staging con estudios reales desidentificados · autenticación institucional operando · auditoría verificada · responsable de guardia técnica nombrado.

### Fase 2 — Modo sombra (meses 3–5)

- El valor se calcula y se guarda, **no se muestra** a roles clínicos.
- Se registra, por lesión, la guía de presión cuando el operador la realiza o cuando el protocolo de investigación la exige (~150–200 lesiones; confirmar con bioestadístico: con 150 lesiones y 90 % de exactitud el IC 95 % es ≈ ±5 puntos).
- Reportes quincenales de concordancia, tasa de casos analizables y tiempos.

**Gate C (pasar a uso guiado), metas *borrador* a ratificar:**
- Exactitud frente a guía de presión ≥ 90 % y sensibilidad ≥ 85 % (con IC 95 % reportado).
- Casos analizables ≥ 85 %; tiempo añadido < 10 min.
- Sin eventos de seguridad atribuibles al piloto.
- Desempeño aceptable en subgrupos (sexo, edad, diabetes).
- Aprobación del comité de monitoreo de seguridad y del comité clínico.

### Fase 3 — Uso guiado supervisado (meses 6–12)

- Cambio a `MODE=guided` (con aviso formal, entrenamiento previo y comunicado a pacientes).
- Zona gris siempre confirmada con presión o imagen intravascular.
- Revisión mensual de casos discordantes en Heart Team.
- Seguimiento de desenlaces a 30 días y 12 meses.

**Gate D (continuidad):** sin señales de daño (eventos no superiores a la línea base); concordancia sostenida; ICP evitadas medidas frente a línea base; operación estable.
**Reglas de pausa automáticas (borrador):** concordancia por debajo de la meta en dos cortes consecutivos; exceso de eventos frente a la línea base; falla de seguridad de datos; cambio de versión del motor sin revalidación.

### Fase 4 — Evaluación y escala (mes 12+)

- Informe final (desempeño, ICP evitadas, eventos, costos, experiencia de usuarios y pacientes).
- Decisión: institucionalizar, ajustar o detener.
- Si se escala: más operadores, CT-FFR, conector FHIR completo, interfaz de revisión, planificación de stent con evidencia propia, acuerdos con aseguradoras.

---

## 8. Ingeniería: estado del código y trabajo pendiente

### 8.1 Qué trae el zip (`vdl-fvirtual-v1`)

Plataforma base **no clínica**, con 28 pruebas automáticas que pasan:

| Módulo | Función |
|---|---|
| `app/decision.py` | Elegibilidad, reglas de zona gris, visibilidad por modo y rol |
| `app/quality.py` | Puerta de calidad angiográfica y lectura de metadatos DICOM |
| `app/engines/` | Interfaz `Engine`; `mock.py` (**simulado, no clínico**) y `vendor.py` (vacío) |
| `app/privacy.py` | Seudónimo HMAC; desidentificación DICOM básica |
| `app/audit.py` + `app/store.py` | Cadena de auditoría por hash y persistencia SQLAlchemy |
| `app/metrics.py` | Exactitud + IC Wilson, sensibilidad, especificidad, AUC, diferencia media |
| `app/main.py` | API FastAPI con roles y modo sombra/guiado |
| `Dockerfile`, `docker-compose.yml` | API + PostgreSQL + Orthanc (desarrollo) |

### 8.2 Stack

Python 3.12 · FastAPI · Pydantic v2 · SQLAlchemy 2 · PostgreSQL 16 · Orthanc (DICOM) · Docker/Compose (Kubernetes si TI lo exige) · React + TypeScript (visor, fase posterior) · HL7 FHIR R4 (integración, fase posterior) · Prometheus/Grafana (observabilidad).

### 8.3 Backlog por sprints (2 semanas)

| Sprint | Fase | Tareas | Criterio de aceptación |
|---|---|---|---|
| S1 | 0 | Repositorio, CI (pruebas, lint, escaneo de dependencias), entornos dev/staging, gestión de secretos | Pipeline verde en cada cambio |
| S2 | 0 | **Autenticación OIDC/SSO** con roles reales; reemplazo del esquema por cabeceras; permisos por rol | Pruebas de acceso por rol; sin API key estática |
| S3 | 0 | **Servicio de ingesta DICOM**: Orthanc → extracción de proyecciones (`extract_projection`) → creación de análisis; desidentificación completa (perfil PS3.15, píxeles quemados) | Estudio de prueba llega de punta a punta sin datos identificables en la base de investigación |
| S4 | 0 | **Adaptador del proveedor** en `engines/vendor.py`: tiempos de espera, reintentos, versión del algoritmo en cada resultado, fallo → `analyzable=false` | Contrato de pruebas con el proveedor; un fallo nunca bloquea la sala |
| S5 | 1 | Observabilidad (logs JSON, métricas, alertas), copias de seguridad, bloqueo consultivo de PostgreSQL para la cadena de auditoría, política de retención | Restauración probada; alertas funcionando |
| S6 | 1 | Endurecimiento: TLS, segmentación de red, pruebas de penetración, ensayo de DR, pruebas de carga | Hallazgos críticos cerrados; informe de pruebas |
| S7 | 2 | Interfaz mínima para técnico y hemodinamista (carga de caso, estado, resultado según modo); formularios de resultado y guía de presión | Flujo completo en sala simulada |
| S8 | 2 | Tablero de investigación: concordancia, analizables, tiempos, discordancias; exportación para bioestadística | Cifras coinciden con cálculo independiente |
| S9 | 2 | Módulo de seguimiento a 30 días y 12 meses; alertas de pausa por reglas | Reglas de pausa probadas con datos sintéticos |
| S10 | 2→3 | Conector FHIR (lectura de datos clínicos, escritura de informe) | Intercambio probado en staging |
| S11 | 3 | Preparación del modo guiado: textos clínicos de la recomendación, registro de aceptación del aviso, revisión de usabilidad | Aprobación del comité clínico |
| S12 | 3 | Revalidación de cambios: procedimiento ante nueva versión del motor o de reglas (control de cambios) | Procedimiento documentado y ensayado |

### 8.4 Definición de terminado (para cada entrega)

Código revisado por pares · pruebas automáticas y de integración pasando · sin secretos en el repositorio · registro de auditoría de las acciones nuevas · documentación actualizada · revisión de seguridad · aprobación del responsable clínico cuando toque a reglas o textos médicos.

### 8.5 Entornos y despliegue

| Entorno | Datos | Uso |
|---|---|---|
| Desarrollo | Sintéticos | Construcción y pruebas |
| Staging | Estudios reales **desidentificados** | Ensayo de integración, seguridad, carga |
| Producción | Reales | Piloto (primero `shadow`, luego `guided`) |

- Despliegue **on-premise**, imágenes de contenedor con versiones fijadas y escaneadas.
- Cambios a producción solo mediante pipeline, con aprobación y plan de **reversión**.
- Configuración clínica (umbrales, `MODE`) bajo control de cambios y registrada en auditoría.
- Versión del motor y de las reglas almacenada en cada resultado.

---

## 9. Lista de verificación de puesta en marcha

**Clínico:** protocolo y umbrales aprobados · entrenamiento completado · procedimiento de caída conocido · comité de monitoreo activo.
**Legal/ético:** contrato firmado · concepto regulatorio · aprobación ética · consentimiento en uso.
**Seguridad:** autenticación institucional · cifrado en tránsito y en reposo · pruebas de penetración cerradas · secretos gestionados · cuentas por rol.
**Operación:** copias de seguridad y restauración probadas · monitoreo y alertas · guardia técnica · plan de reversión.
**Datos:** desidentificación validada · retención definida · cadena de auditoría verificada (`GET /audit/verify`) · exportación para investigación probada.
**Pacientes:** material educativo entregado · canal de preguntas · aviso explícito de que decide el médico.

---

## 10. Seguridad, privacidad y gobierno del modelo

- Seudonimización con clave secreta; la historia clínica no se guarda en la base de investigación.
- Acceso por roles y trazabilidad completa; auditoría encadenada.
- Contrato con el proveedor: lugar de procesamiento, retención, incidentes, auditoría, cláusulas de salida y exportación.
- Registro de versión del algoritmo; **revalidación** ante cualquier cambio de versión.
- Exigir al proveedor información sobre poblaciones de entrenamiento y validación; verificar desempeño en subgrupos locales.

---

## 11. Indicadores

| Dimensión | Indicadores |
|---|---|
| Desempeño diagnóstico | Exactitud (IC 95 %), sensibilidad, especificidad, AUC, diferencia media frente a guía de presión |
| Utilidad clínica | % de ICP evitadas frente a línea base; guías de presión evitadas |
| Seguridad | Eventos cardiovasculares a 30 días y 12 meses |
| Operación | % de casos analizables, minutos añadidos, contraste y radiación |
| Costo | Stents y guías evitados vs costo de licencia por caso |
| Experiencia | Satisfacción de operadores, técnicos y pacientes |

---

## 12. Dimensión social y humana

- **Pacientes:** consentimiento en lenguaje claro; no vender la herramienta como "una computadora que decide"; atención a la ansiedad de quien recibe la decisión de no intervenir; plan para pacientes remitidos de otras regiones (telemedicina, coordinación con su médico local).
- **Equidad:** criterios de inclusión clínicos, no económicos; monitoreo por subgrupos.
- **Profesionales:** entrenamiento de hemodinamistas, técnicos, enfermería y fellows; campeones; mantener la competencia en guía de presión y juicio clínico; la herramienta no evalúa el desempeño individual.
- **Aseguradoras:** verificar cobertura; la v1 probablemente se financia como investigación o inversión institucional; el caso económico se construye con datos propios.
- **Comunicación pública:** evitar titulares triunfalistas; comunicar solo resultados existentes.

---

## 13. Presupuesto (categorías, sin cifras)

Licencia o contrato por caso · estación de trabajo y almacenamiento · integración TI · desarrollo de ingeniería · tiempo del técnico de análisis · investigación y bioestadística · entrenamiento · trámites regulatorios y de ética · pruebas de seguridad · póliza de responsabilidad si aplica · comunicaciones y seguimiento de pacientes. Las cifras requieren cotización del proveedor.

---

## 14. Riesgos principales

| Riesgo | Mitigación |
|---|---|
| Modelo poco validado en nuestra población | Fase de modo sombra obligatoria |
| Sobrestimar el beneficio | Comparador y métricas definidos antes de empezar |
| Más revascularizaciones por falsos positivos | Zona gris con confirmación por presión |
| Fuga o transferencia indebida de datos | Contrato, desidentificación, procesamiento local |
| Vacío regulatorio | Consulta temprana a INVIMA y al comité de ética |
| Resistencia del equipo | Participación temprana, entrenamiento, campeones |
| Dependencia de un proveedor | Interfaz de motor reemplazable; cláusulas de salida |
| Cambio de versión del motor sin revalidación | Control de cambios y revalidación obligatoria |
| Falla técnica en sala | Procedimiento de caída; la práctica habitual no depende del sistema |

---

## 15. Decisiones pendientes

1. Proveedor y tecnología concretos (QFR, FFRangio u otro).
2. Umbrales definitivos de calidad y de zona gris.
3. Metas definitivas de los Gates C y D.
4. Modelo de financiación de la v1.
5. Infraestructura de despliegue (servidores propios o centro de datos institucional).
6. Estrategia de autenticación (proveedor de identidad de la Fundación).
7. Alcance de la fase posterior (CT-FFR, FHIR completo, visor, stenting virtual).

---

## 16. Anexo técnico (cómo empezar con el zip)

```bash
unzip vdl-fvirtual-v1.zip && cd vdl-fvirtual-v1
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest                                   # 28 pruebas

cp .env.example .env                     # editar secretos
docker compose up --build                # API :8000, Orthanc :8042
# sin Docker:
export API_KEY=... PSEUDONYM_KEY=... ALLOW_MOCK_ENGINE=true MODE=shadow
uvicorn app.main:create_app --factory
```

**Variables de entorno:** `DATABASE_URL`, `MODE` (`shadow`|`guided`), `ENGINE` (`mock`|`vendor`), `ALLOW_MOCK_ENGINE` (false en todo entorno clínico), `API_KEY`, `PSEUDONYM_KEY` (≥ 32 caracteres), `DEFER_ABOVE`, `FAVOR_BELOW`, `MIN_ANGLE_DEG`, `MIN_FPS`.

**API** (cabeceras *placeholder*: `X-Api-Key`, `X-Actor`, `X-Role` ∈ technician | operator | researcher; reemplazar en S2):

| Ruta | Roles | Función |
|---|---|---|
| `POST /cases` | technician, operator | Crear caso (valida elegibilidad, seudonimiza) |
| `POST /cases/{id}/analysis` | todos | Calidad → motor → regla de decisión |
| `GET /cases/{id}/analysis/latest` | todos | Último análisis (respeta el modo) |
| `POST /cases/{id}/outcome` | operator | Decisión real y guía de presión |
| `GET /metrics/concordance` | researcher | Concordancia y tasa de analizables |
| `GET /audit/verify` | researcher | Verifica la cadena de auditoría |

**Advertencias para el equipo:**
- `mock-NON-CLINICAL` genera valores simulados; **nunca** debe llegar a un entorno clínico.
- La autenticación actual es un andamio de desarrollo.
- Las pruebas automáticas verifican el software, no la validez clínica de ningún motor.
- Las imágenes `orthancteam/orthanc` y `postgres` deben fijarse a versiones específicas antes de usar en serio.

---

## 17. Referencias clave

- FAVOR III Europe-Japan: QFR-guided vs FFR-guided PCI, *Lancet* 2024;404:1835-1846.
- FAVOR III China: QFR-guided vs angiography-guided PCI, *Lancet* 2021.
- Normativa colombiana citada en la sección 5: verificar texto y vigencia con Jurídico.
