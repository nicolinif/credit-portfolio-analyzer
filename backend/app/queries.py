"""
queries.py — Consultas SQL de análisis de cartera crediticia.

Cada función abre su propia conexión, ejecuta la query y retorna
list[dict] o dict. Sin ORM, sin Pandas — stdlib sqlite3 puro.

Resolución del path de la DB:
  1. Lee la variable de entorno DATABASE_URL.
  2. Si es relativa, la resuelve desde backend/ (directorio padre de app/).
  3. Fallback: backend/db/portfolio.db (calculado desde __file__).
"""

import os
import sqlite3
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent  # .../backend/

# Etiquetas oficiales por Situación BCRA (Com. A 2216/6938)
_BCRA_LABELS = {
    1: "Normal",
    2: "Con seguimiento especial",
    3: "Con problemas",
    4: "Con alto riesgo de insolvencia",
    5: "Irrecuperable",
}


def _connect() -> sqlite3.Connection:
    """Devuelve una conexión SQLite con row_factory=sqlite3.Row."""
    db_url = os.environ.get("DATABASE_URL", "db/portfolio.db")
    db_path = Path(db_url)
    if not db_path.is_absolute():
        db_path = _BACKEND_DIR / db_path
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# 1. get_mora_segmentos
# ---------------------------------------------------------------------------

def get_mora_segmentos() -> list[dict]:
    """
    Saldo total y cantidad de deudas agrupados por bucket de mora.
    Buckets: sin_mora | mora_1_30 | mora_31_90 | mora_mas_90.
    Excluye deudas canceladas.
    """
    sql = """
        SELECT
            CASE
                WHEN dias_mora  =  0              THEN 'sin_mora'
                WHEN dias_mora BETWEEN  1 AND  30 THEN 'mora_1_30'
                WHEN dias_mora BETWEEN 31 AND  90 THEN 'mora_31_90'
                ELSE                                   'mora_mas_90'
            END                            AS bucket_mora,
            COUNT(*)                       AS cantidad_deudas,
            ROUND(SUM(saldo_capital), 2)   AS saldo_total,
            ROUND(
                SUM(saldo_capital) * 100.0 /
                SUM(SUM(saldo_capital)) OVER (), 2
            )                              AS pct_saldo
        FROM deudas
        WHERE estado != 'cancelado'
        GROUP BY 1
        ORDER BY MIN(dias_mora)
    """
    with _connect() as conn:
        rows = conn.execute(sql).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# 2. get_top_clientes
# ---------------------------------------------------------------------------

def get_top_clientes(n: int = 10) -> list[dict]:
    """
    Top N clientes ordenados por saldo de capital total (deudas activas).
    Incluye segmento, calificación interna y cantidad de deudas activas.
    """
    sql = """
        SELECT
            c.id_cliente,
            c.nombre || ' ' || c.apellido  AS nombre_completo,
            c.segmento,
            c.situacion_deudor,
            COUNT(d.id_deuda)              AS cantidad_deudas,
            ROUND(SUM(d.saldo_capital), 2) AS saldo_total
        FROM clientes c
        JOIN deudas d ON d.id_cliente = c.id_cliente
        WHERE d.estado != 'cancelado'
        GROUP BY c.id_cliente
        ORDER BY saldo_total DESC
        LIMIT ?
    """
    with _connect() as conn:
        rows = conn.execute(sql, (n,)).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# 3. get_tasa_mora
# ---------------------------------------------------------------------------

def get_tasa_mora() -> dict:
    """
    Tasa de mora de la cartera activa.
    Numerador: saldo de deudas en_mora + incobrable.
    Denominador: saldo total de deudas no canceladas.
    """
    sql = """
        SELECT
            ROUND(
                SUM(CASE WHEN estado IN ('en_mora', 'incobrable')
                         THEN saldo_capital ELSE 0 END), 2
            )                              AS saldo_mora,
            ROUND(SUM(saldo_capital), 2)   AS saldo_total,
            ROUND(
                SUM(CASE WHEN estado IN ('en_mora', 'incobrable')
                         THEN saldo_capital ELSE 0 END) * 100.0 /
                NULLIF(SUM(saldo_capital), 0), 4
            )                              AS tasa_mora_pct
        FROM deudas
        WHERE estado != 'cancelado'
    """
    with _connect() as conn:
        row = conn.execute(sql).fetchone()
    return dict(row)


# ---------------------------------------------------------------------------
# 4. get_distribucion_productos
# ---------------------------------------------------------------------------

def get_distribucion_productos() -> list[dict]:
    """
    Saldo, cantidad de deudas y tasa promedio por tipo de producto.
    Ordenado por saldo descendente. Excluye deudas canceladas.
    """
    sql = """
        SELECT
            p.tipo_producto,
            p.nombre_producto,
            COUNT(d.id_deuda)              AS cantidad_deudas,
            ROUND(SUM(d.saldo_capital), 2) AS saldo_total,
            ROUND(AVG(d.tasa_interes), 2)  AS tasa_promedio
        FROM deudas d
        JOIN productos p ON p.id_producto = d.id_producto
        WHERE d.estado != 'cancelado'
        GROUP BY p.tipo_producto, p.nombre_producto
        ORDER BY saldo_total DESC
    """
    with _connect() as conn:
        rows = conn.execute(sql).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# 5. get_situacion_bcra
# ---------------------------------------------------------------------------

def get_situacion_bcra() -> list[dict]:
    """
    Distribución de deudas por Situación BCRA (1 al 5).
    Incluye etiqueta descriptiva según Com. A 2216/6938.
    Excluye deudas canceladas.
    """
    sql = """
        SELECT
            situacion_bcra,
            COUNT(*)                       AS cantidad_deudas,
            ROUND(SUM(saldo_capital), 2)   AS saldo_total,
            ROUND(
                COUNT(*) * 100.0 /
                SUM(COUNT(*)) OVER (), 2
            )                              AS pct_cantidad
        FROM deudas
        WHERE estado != 'cancelado'
        GROUP BY situacion_bcra
        ORDER BY situacion_bcra
    """
    with _connect() as conn:
        rows = conn.execute(sql).fetchall()

    result = []
    for r in rows:
        item = dict(r)
        item["descripcion"] = _BCRA_LABELS.get(item["situacion_bcra"], "Desconocida")
        result.append(item)
    return result


# ---------------------------------------------------------------------------
# 6. get_resumen_cartera
# ---------------------------------------------------------------------------

def get_resumen_cartera() -> dict:
    """
    Métricas ejecutivas de la cartera completa:
      - total_clientes, total_deudas_activas, clientes_con_deuda_activa
      - saldo_total_activo, saldo_en_mora, tasa_mora_pct
    """
    sql = """
        SELECT
            (SELECT COUNT(*) FROM clientes)    AS total_clientes,
            COUNT(*)                           AS total_deudas_activas,
            COUNT(DISTINCT id_cliente)         AS clientes_con_deuda_activa,
            ROUND(SUM(saldo_capital), 2)       AS saldo_total_activo,
            ROUND(
                SUM(CASE WHEN estado IN ('en_mora', 'incobrable')
                         THEN saldo_capital ELSE 0 END), 2
            )                                  AS saldo_en_mora,
            ROUND(
                SUM(CASE WHEN estado IN ('en_mora', 'incobrable')
                         THEN saldo_capital ELSE 0 END) * 100.0 /
                NULLIF(SUM(saldo_capital), 0), 2
            )                                  AS tasa_mora_pct
        FROM deudas
        WHERE estado != 'cancelado'
    """
    with _connect() as conn:
        row = conn.execute(sql).fetchone()
    return dict(row)
