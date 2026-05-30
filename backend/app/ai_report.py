"""
ai_report.py — Generación de reportes ejecutivos con Groq API.

Recibe el payload de construir_payload_kpis() y produce un reporte
en lenguaje natural usando un LLM vía Groq.
"""

import json
import os

import groq as _groq_exc
from groq import Groq

_DEFAULT_MODEL = "llama-3.3-70b-versatile"
_TIMEOUT_SECS  = 30.0

_SYSTEM_PROMPT = """\
Sos un analista senior de riesgo crediticio de un banco argentino con amplia \
experiencia en análisis de cartera y regulación BCRA.

Tu tarea es generar reportes ejecutivos de cartera crediticia para la gerencia.

Reglas:
- Usá únicamente los datos proporcionados; nunca inventés cifras ni porcentajes.
- Aplicá terminología bancaria argentina: cartera activa, mora, irregularidad, \
situación BCRA, incobrabilidad, constitución de previsiones, exposición, etc.
- Expresá los montos en pesos argentinos (ARS), con separador de miles en punto.
- Umbrales de alerta: mora leve > 5 %, moderada > 10 %, severa > 20 %; \
concentración top-10 > 30 % del saldo total se considera riesgo sistémico.
- Redactá en español formal; el reporte será leído por gerentes de banco.

Estructura OBLIGATORIA — respetá estos encabezados exactos sin añadir otros:

## Resumen Ejecutivo de Cartera
[síntesis de los indicadores clave: saldo total, tasa de mora, cantidad de clientes \
y deudas activas, nivel de concentración e índice de tendencia]

## Alertas y Riesgos Detectados
[identificá explícitamente qué indicadores superan umbrales preocupantes; \
mencioná la situación BCRA si hay proporción significativa en categorías 3-5]

## Recomendaciones Accionables
[entre 3 y 5 acciones concretas y priorizadas que la gerencia puede ejecutar \
basándose en los datos; evitá recomendaciones genéricas]
"""


def _construir_prompt(kpis: dict) -> str:
    """Serializa el payload de KPIs en un mensaje estructurado para el LLM."""
    rc = kpis.get("resumen_cartera", {})
    ic = kpis.get("indice_concentracion", {})
    tm = kpis.get("tendencia_mora", {})
    ts = kpis.get("timestamp", "sin fecha")

    lineas = [
        f"Generá un reporte ejecutivo de la siguiente cartera crediticia (datos al {ts}).\n",
        "### INDICADORES GENERALES",
        f"- Clientes totales: {rc.get('total_clientes', 'N/D')}",
        f"- Clientes con deuda activa: {rc.get('clientes_con_deuda_activa', 'N/D')}",
        f"- Deudas activas: {rc.get('total_deudas_activas', 'N/D')}",
        f"- Saldo capital activo: ARS {rc.get('saldo_total_activo', 0):,.2f}",
        f"- Saldo en mora (en_mora + incobrable): ARS {rc.get('saldo_en_mora', 0):,.2f}",
        f"- Tasa de mora: {rc.get('tasa_mora_pct', 0)} %",
        "",
        "### ÍNDICE DE CONCENTRACIÓN",
        f"- Top 10 clientes concentran el {ic.get('top10_pct_saldo', 0)} % del saldo total",
        f"- Saldo top 10: ARS {ic.get('top10_saldo', 0):,.2f}",
        f"- Clientes activos totales: {ic.get('n_clientes_activos', 'N/D')}",
        "",
        "### TENDENCIA DE MORA",
        f"- Tasa de mora actual: {tm.get('valor_actual', 0)} %",
        f"- Referencia histórica (% pagos irregulares últimos 90 días): {tm.get('referencia', 0)} %",
        f"- Tendencia: {tm.get('tendencia', 'N/D')}",
        "",
        "### DATOS COMPLETOS (JSON)",
        json.dumps(kpis, ensure_ascii=False, indent=2),
    ]
    return "\n".join(lineas)


def generar_reporte(kpis: dict) -> str:
    """
    Genera un reporte ejecutivo de cartera a partir del payload de KPIs.
    Nunca lanza excepciones: ante cualquier error retorna un mensaje descriptivo.
    """
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        return (
            "[ERROR] GROQ_API_KEY no configurada. "
            "Definí la variable de entorno antes de generar el reporte."
        )

    model = os.environ.get("GROQ_MODEL", _DEFAULT_MODEL)

    try:
        client   = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user",   "content": _construir_prompt(kpis)},
            ],
            timeout=_TIMEOUT_SECS,
        )
        texto = response.choices[0].message.content or ""
        if not texto.strip():
            return "[ERROR] La API respondió correctamente pero el reporte vino vacío."
        return texto

    except _groq_exc.AuthenticationError:
        return "[ERROR] API key de Groq inválida o sin permisos."
    except _groq_exc.RateLimitError:
        return "[ERROR] Rate limit de Groq superado. Intentá en unos minutos."
    except _groq_exc.APITimeoutError:
        return f"[ERROR] La API de Groq no respondió en {int(_TIMEOUT_SECS)} segundos."
    except _groq_exc.APIConnectionError:
        return "[ERROR] No se pudo conectar con la API de Groq. Verificá la conexión."
    except _groq_exc.APIError as e:
        return f"[ERROR] Error de API de Groq: {e}"
    except Exception as e:
        return f"[ERROR] Error inesperado al generar el reporte: {e}"
