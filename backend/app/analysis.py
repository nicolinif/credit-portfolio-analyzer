"""
analysis.py — Análisis enriquecido de cartera con Pandas.

Construye KPIs derivados sobre los datos crudos de queries.py.
Función de entrada principal para Flask (Etapa 5): construir_payload_kpis().
"""

import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from app.queries import (
    get_mora_segmentos,
    get_top_clientes,
    get_tasa_mora,
    get_distribucion_productos,
    get_situacion_bcra,
    get_resumen_cartera,
)

_BACKEND_DIR = Path(__file__).resolve().parent.parent


def _connect() -> sqlite3.Connection:
    db_url = os.environ.get("DATABASE_URL", "db/portfolio.db")
    db_path = Path(db_url)
    if not db_path.is_absolute():
        db_path = _BACKEND_DIR / db_path
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def calcular_indice_concentracion() -> dict:
    """
    Índice de concentración: qué % del saldo total representa el top 10 de clientes.

    Returns: {
        top10_pct_saldo: float,    # % del saldo total en los top 10 clientes
        top10_saldo: float,        # saldo absoluto (ARS) de los top 10
        saldo_total: float,        # saldo total de la cartera activa
        n_clientes_activos: int,   # clientes con al menos una deuda activa
    }
    """
    sql = """
        SELECT id_cliente, SUM(saldo_capital) AS saldo_cliente
        FROM deudas
        WHERE estado != 'cancelado'
        GROUP BY id_cliente
    """
    with _connect() as conn:
        df = pd.read_sql_query(sql, conn)

    if df.empty:
        return {
            "top10_pct_saldo":    0.0,
            "top10_saldo":        0.0,
            "saldo_total":        0.0,
            "n_clientes_activos": 0,
        }

    df = df.sort_values("saldo_cliente", ascending=False)
    saldo_total = float(df["saldo_cliente"].sum())
    top10_saldo = float(df.head(10)["saldo_cliente"].sum())
    top10_pct   = round(top10_saldo / saldo_total * 100, 2) if saldo_total > 0 else 0.0

    return {
        "top10_pct_saldo":    top10_pct,
        "top10_saldo":        round(top10_saldo, 2),
        "saldo_total":        round(saldo_total, 2),
        "n_clientes_activos": int(len(df)),
    }


def calcular_tendencia_mora() -> dict:
    """
    Compara la tasa de mora actual con el ritmo histórico de pagos irregulares.

    valor_actual = tasa_mora_pct del saldo activo (de get_tasa_mora).
    referencia   = % del volumen de pagos de los últimos 90 días que fue tardío/parcial.
    Ambos son porcentajes → comparación de unidades homogéneas.

    Returns: {
        valor_actual: float,   # tasa_mora_pct actual (%)
        referencia: float,     # % de pagos irregulares en últimos 90 días (%)
        tendencia: str,        # "subiendo" | "estable" | "bajando"
    }
    """
    tasa_actual = float(get_tasa_mora()["tasa_mora_pct"])

    cutoff = (datetime.today() - timedelta(days=90)).strftime("%Y-%m-%d")
    sql = """
        SELECT estado_pago, monto_pagado
        FROM pagos
        WHERE fecha_pago >= ?
    """
    with _connect() as conn:
        df = pd.read_sql_query(sql, conn, params=(cutoff,))

    if df.empty:
        return {"valor_actual": round(tasa_actual, 4), "referencia": 0.0, "tendencia": "estable"}

    total     = float(df["monto_pagado"].sum())
    irregular = float(df[df["estado_pago"].isin(["tardio", "parcial"])]["monto_pagado"].sum())
    referencia = round(irregular / total * 100, 2) if total > 0 else 0.0

    if tasa_actual > referencia * 1.10:
        tendencia = "subiendo"
    elif tasa_actual < referencia * 0.90:
        tendencia = "bajando"
    else:
        tendencia = "estable"

    return {
        "valor_actual": round(tasa_actual, 4),
        "referencia":   referencia,
        "tendencia":    tendencia,
    }


def formatear_montos_ars(valor: float) -> str:
    """
    Formatea un float como moneda argentina (separador miles=punto, decimal=coma).
    Ejemplo: 1_500_000 → "$ 1.500.000,00"
    Solo stdlib — sin dependencias externas.
    """
    negativo  = valor < 0
    formatted = f"{abs(valor):,.2f}"         # "1,500,000.00"  (convención US)
    entero, centavos = formatted.split(".")  # swap separators
    entero_ars = entero.replace(",", ".")    # "1.500.000"
    prefijo = "-$ " if negativo else "$ "
    return f"{prefijo}{entero_ars},{centavos}"


def construir_payload_kpis() -> dict:
    """
    Punto de entrada único para Flask y el agente IA.
    Integra todas las funciones de queries.py y analysis.py en un dict normalizado.
    """
    return {
        "resumen_cartera":        get_resumen_cartera(),
        "mora_segmentos":         get_mora_segmentos(),
        "top_clientes":           get_top_clientes(n=10),
        "distribucion_productos": get_distribucion_productos(),
        "situacion_bcra":         get_situacion_bcra(),
        "indice_concentracion":   calcular_indice_concentracion(),
        "tendencia_mora":         calcular_tendencia_mora(),
        "timestamp":              datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
