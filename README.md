# Credit Portfolio Analyzer

Herramienta de análisis de cartera crediticia bancaria con datos sintéticos argentinos,
reportes analíticos y narrativa ejecutiva generada con IA (Groq API).

Desarrollado como portfolio técnico por un ex-Oficial de Negocios del Banco Nación,
para demostrar dominio de negocio bancario combinado con habilidades full-stack.

## Stack

| Capa       | Tecnología                           |
|------------|--------------------------------------|
| Backend    | Python 3.11 · Flask · SQLite         |
| Analytics  | Pandas                               |
| IA         | Groq API (llama-3.3-70b-versatile)   |
| Frontend   | React 18 · Vite · Tailwind (Etapa 6) |

## Estructura del monorepo

```
credit-portfolio-analyzer/
├── backend/     # API Flask + base de datos SQLite + análisis Pandas
└── frontend/    # React (Etapa 6+)
```

## Etapas del proyecto

| Etapa | Descripción                              | Estado      |
|-------|------------------------------------------|-------------|
| 1     | Monorepo + base de datos + seed          | En progreso |
| 2     | API Flask + análisis Pandas              | Pendiente   |
| 3–5   | Frontend React + Chart.js                | Pendiente   |
| 6     | Groq AI: reportes ejecutivos             | Pendiente   |

## Quick Start (Etapa 1)

```bash
cd credit-portfolio-analyzer

# Crear y activar virtualenv
python3 -m venv backend/venv
source backend/venv/bin/activate

# Instalar dependencias
pip install -r backend/requirements.txt

# Crear base de datos con datos sintéticos
python3 backend/data/seed.py

# Verificar
sqlite3 backend/db/portfolio.db "SELECT COUNT(*) FROM clientes;"
```

## Notas de dominio bancario

- **Situación BCRA** según Comunicación A 2216 / 6938:
  - 1 → Normal (0-30 días de atraso)
  - 2 → Con seguimiento especial (31-90 días)
  - 3 → Con problemas (91-180 días)
  - 4 → Con alto riesgo de insolvencia (181-365 días)
  - 5 → Irrecuperable (> 365 días)
- **Segmentos**: retail, pyme, corporativo
- **Calificación interna** A-E: worst-case de todas las deudas del cliente

## Licencia

MIT
