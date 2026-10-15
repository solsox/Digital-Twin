# Digital Twin Health

Prototipo educativo de un "gemelo digital" de salud: se registran los signos vitales de un paciente y
el sistema estima su riesgo cardiovascular (bajo / medio / alto), explica qué factores pesan más y
guarda el historial para ver cómo evoluciona.

> ⚠️ Los coeficientes del modelo son de ejemplo y **no** provienen de un estudio clínico.
> No uses este proyecto para tomar decisiones médicas.

## Estructura

```
backend/    FastAPI + SQLAlchemy (PostgreSQL; SQLite por defecto en desarrollo)
  ml/         modelo de riesgo (logístico y explicable)
  routes/     endpoints
  schemas.py  validación de entrada/salida (Pydantic)
  tests/      pruebas con pytest
frontend/   React + Vite + TypeScript + Recharts
```

## Puesta en marcha

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # y ajusta DATABASE_URL con tus credenciales
uvicorn main:app --reload
```
Sin `.env` usa SQLite local (`gemelo_dev.db`), útil para probar rápido.
Documentación interactiva en http://127.0.0.1:8000/docs

### Frontend
```bash
cd frontend
cp .env.example .env        # opcional: cambia VITE_API_URL
npm install
npm run dev
```

### Pruebas
```bash
cd backend && pytest
cd frontend && npm run lint && npm run build
```

## API

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/predict` | Predicción rápida sin guardar |
| POST | `/patients` | Crea un paciente |
| GET | `/patients`, `/patients/{id}` | Lista / consulta |
| PUT | `/patients/{id}` | Actualiza signos vitales |
| DELETE | `/patients/{id}` | Elimina paciente y su historial |
| POST | `/patients/{id}/predictions` | Calcula y guarda una predicción |
| GET | `/patients/{id}/predictions` | Historial de predicciones |
| POST | `/patients/{id}/simulate` | Escenario what-if (deltas de presión, colesterol, peso); compara riesgo actual vs. escenario sin guardar |

## Modelo de riesgo

`ml/model.py` calcula `sigmoide(intercepto + Σ aportes)`. Cada factor (edad, presión sistólica y
diastólica, colesterol, sexo e IMC) aporta en escala logit, por lo que el score siempre está entre 0 y 1
y la respuesta incluye el aporte de cada uno.

Hay dos modos, y `GET /model` indica cuál está activo:

- **Ejemplo (por defecto):** coeficientes inventados para el prototipo. No son clínicos.
- **Entrenado:** si existe `backend/ml/artifacts/risk_model.json`, se usa ese modelo. Se genera así:

```bash
cd backend
pip install -r requirements-train.txt
python -m ml.train --data ruta/a/framingham.csv   # imprime AUC, Brier y tasa base
```

El CSV es el conjunto público de Framingham (columnas `male, age, sysBP, diaBP, totChol, BMI,
TenYearCHD`). El artefacto es un JSON con coeficientes y medias: la API no necesita scikit-learn ni
carga pickles. Aun entrenado, **no está validado clínicamente**: Framingham es una cohorte antigua de
EE. UU. y sirve para aprender, no para decidir tratamientos.

## Análisis de señales e imágenes

`POST /analysis/ecg`, `/analysis/retina` y `/analysis/xray` (más `GET /analysis` con el estado de
cada modelo). Los archivos se procesan en memoria: **no se guardan ni se registran**. Se validan
tipo, tamaño (8 MB imágenes, 4 MB señales) y que realmente sean una imagen o una señal numérica.

| Análisis | Entrada | Estado |
|---|---|---|
| ECG | CSV/TXT de un canal (+ frecuencia de muestreo) | Entrenado (MIT-BIH), ~87 % en validación cruzada |
| Retina | JPG/PNG de fondo de ojo | Entrenado, **débil** (AUC 0,66) |
| Rayos X | JPG/PNG de tórax | Listo, **sin modelo** (faltan datos): ver [DATA.md](DATA.md) |

Un ECG en foto o PDF (papel) no se digitaliza: hay que subir la señal. Reentrenar:
`python -m ml.train_ecg --data ...` y `python -m ml.train_images --task retina|cxr ...`.
Fuentes, licencias y límites de cada conjunto de datos en [DATA.md](DATA.md).

## Base de datos y migraciones

Por defecto se crean las tablas al arrancar (`AUTO_CREATE_TABLES=true`). En producción:

```bash
AUTO_CREATE_TABLES=false alembic upgrade head
alembic revision --autogenerate -m "describe el cambio"   # tras modificar un modelo
```

Si ya tienes una base creada con `create_all`, márcala como migrada con `alembic stamp head`.

## Pruebas y CI

```bash
cd backend && pytest -q            # API, modelo y pipeline de entrenamiento (datos sintéticos)
cd frontend && npm test            # formulario y panel what-if
```

`.github/workflows/ci.yml` ejecuta todo esto (más lint, build y `alembic check`) en cada push y PR.
