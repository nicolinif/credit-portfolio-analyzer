"""
test_ai_report.py — Tests del módulo de generación de reportes con Groq.

No llama a la API real; usa mocks para no consumir créditos.

Ejecutar desde la raíz del proyecto:
    source backend/venv/bin/activate
    pytest backend/tests/test_ai_report.py -v
"""

import os
from unittest.mock import MagicMock, patch

from app.ai_report import _construir_prompt, generar_reporte

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

KPI_FIXTURE = {
    "resumen_cartera": {
        "total_clientes":           200,
        "clientes_con_deuda_activa": 180,
        "total_deudas_activas":     300,
        "saldo_total_activo":       500_000_000.0,
        "saldo_en_mora":             75_000_000.0,
        "tasa_mora_pct":                     15.0,
    },
    "indice_concentracion": {
        "top10_pct_saldo":   28.5,
        "top10_saldo":  142_500_000.0,
        "saldo_total":  500_000_000.0,
        "n_clientes_activos": 180,
    },
    "tendencia_mora": {
        "valor_actual": 15.0,
        "referencia":   12.0,
        "tendencia":    "subiendo",
    },
    "mora_segmentos":         [],
    "top_clientes":           [],
    "distribucion_productos": [],
    "situacion_bcra":         [],
    "timestamp":              "2026-05-29T12:00:00Z",
}

REPORTE_MOCK = """\
## Resumen Ejecutivo de Cartera
La cartera presenta un saldo activo de ARS 500.000.000 con tasa de mora del 15 %.

## Alertas y Riesgos Detectados
La mora supera el umbral moderado (10 %) y muestra tendencia ascendente.

## Recomendaciones Accionables
1. Reforzar gestión de cobranza en los segmentos con mayor mora.
2. Revisar políticas de otorgamiento para los productos con mayor irregularidad.
3. Constituir previsiones adicionales dado el nivel de mora severa.
"""


def _mock_response(content: str) -> MagicMock:
    """Construye un MagicMock que imita la estructura de respuesta del SDK de Groq."""
    msg           = MagicMock()
    msg.content   = content
    choice        = MagicMock()
    choice.message = msg
    response          = MagicMock()
    response.choices  = [choice]
    return response


# ---------------------------------------------------------------------------
# TestSinApiKey
# ---------------------------------------------------------------------------

class TestSinApiKey:
    def test_retorna_string_sin_crash(self):
        with patch.dict(os.environ, {"GROQ_API_KEY": ""}, clear=False):
            result = generar_reporte(KPI_FIXTURE)
        assert isinstance(result, str)

    def test_mensaje_de_error_claro(self):
        with patch.dict(os.environ, {"GROQ_API_KEY": ""}, clear=False):
            result = generar_reporte(KPI_FIXTURE)
        assert "ERROR" in result
        assert "GROQ_API_KEY" in result


# ---------------------------------------------------------------------------
# TestReporteExitoso
# ---------------------------------------------------------------------------

class TestReporteExitoso:
    def test_retorna_string(self):
        with patch("app.ai_report.Groq") as mock_groq, \
             patch.dict(os.environ, {"GROQ_API_KEY": "fake-key"}):
            mock_groq.return_value.chat.completions.create.return_value = \
                _mock_response(REPORTE_MOCK)
            result = generar_reporte(KPI_FIXTURE)
        assert isinstance(result, str)

    def test_reporte_no_esta_vacio(self):
        with patch("app.ai_report.Groq") as mock_groq, \
             patch.dict(os.environ, {"GROQ_API_KEY": "fake-key"}):
            mock_groq.return_value.chat.completions.create.return_value = \
                _mock_response(REPORTE_MOCK)
            result = generar_reporte(KPI_FIXTURE)
        assert len(result.strip()) > 0

    def test_estructura_secciones(self):
        with patch("app.ai_report.Groq") as mock_groq, \
             patch.dict(os.environ, {"GROQ_API_KEY": "fake-key"}):
            mock_groq.return_value.chat.completions.create.return_value = \
                _mock_response(REPORTE_MOCK)
            result = generar_reporte(KPI_FIXTURE)
        assert "Resumen Ejecutivo" in result
        assert "Alertas"           in result
        assert "Recomendaciones"   in result

    def test_usa_modelo_de_env(self):
        modelo_custom = "llama-3.1-8b-instant"
        with patch("app.ai_report.Groq") as mock_groq, \
             patch.dict(os.environ, {"GROQ_API_KEY": "fake-key",
                                     "GROQ_MODEL": modelo_custom}):
            mock_groq.return_value.chat.completions.create.return_value = \
                _mock_response(REPORTE_MOCK)
            generar_reporte(KPI_FIXTURE)
            kwargs = mock_groq.return_value.chat.completions.create.call_args.kwargs
        assert kwargs["model"] == modelo_custom


# ---------------------------------------------------------------------------
# TestErroresApi
# ---------------------------------------------------------------------------

class TestErroresApi:
    def _llamar_con_excepcion(self, exc: Exception) -> str:
        with patch("app.ai_report.Groq") as mock_groq, \
             patch.dict(os.environ, {"GROQ_API_KEY": "fake-key"}):
            mock_groq.return_value.chat.completions.create.side_effect = exc
            return generar_reporte(KPI_FIXTURE)

    def test_respuesta_vacia_retorna_error(self):
        with patch("app.ai_report.Groq") as mock_groq, \
             patch.dict(os.environ, {"GROQ_API_KEY": "fake-key"}):
            mock_groq.return_value.chat.completions.create.return_value = \
                _mock_response("")
            result = generar_reporte(KPI_FIXTURE)
        assert "ERROR" in result

    def test_excepcion_generica_retorna_error(self):
        result = self._llamar_con_excepcion(Exception("fallo inesperado"))
        assert isinstance(result, str)
        assert "ERROR" in result

    def test_nunca_lanza_excepcion(self):
        try:
            result = self._llamar_con_excepcion(RuntimeError("algo raro"))
            assert isinstance(result, str)
        except Exception:
            assert False, "generar_reporte lanzó una excepción en lugar de capturarla"

    def test_error_contiene_descripcion(self):
        result = self._llamar_con_excepcion(Exception("conexión rechazada"))
        assert len(result) > 10


# ---------------------------------------------------------------------------
# TestConstruirPrompt
# ---------------------------------------------------------------------------

class TestConstruirPrompt:
    def test_retorna_string(self):
        assert isinstance(_construir_prompt(KPI_FIXTURE), str)

    def test_contiene_datos_principales(self):
        prompt = _construir_prompt(KPI_FIXTURE)
        assert "15"          in prompt   # tasa de mora
        assert "2026-05-29"  in prompt   # timestamp

    def test_contiene_json_completo(self):
        prompt = _construir_prompt(KPI_FIXTURE)
        assert "resumen_cartera"      in prompt
        assert "indice_concentracion" in prompt
        assert "tendencia_mora"       in prompt
