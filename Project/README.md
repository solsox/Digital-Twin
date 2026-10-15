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
y la respuesta incluye el aporte de cada uno. Para usar un modelo real, reemplaza `predict_risk`
manteniendo su interfaz (devuelve `RiskResult`).
