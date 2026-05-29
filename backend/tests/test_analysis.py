"""
test_analysis.py — Tests de las funciones de análisis con Pandas.

Corren contra la base de datos real (backend/db/portfolio.db).
Prerequisito: haber ejecutado backend/data/seed.py con seed=42.

Ejecutar desde la raíz del proyecto:
    source backend/venv/bin/activate
    pytest backend/tests/test_analysis.py -v
"""

from app.analysis import (
    calcular_indice_concentracion,
    calcular_tendencia_mora,
    formatear_montos_ars,
    construir_payload_kpis,
)


# ---------------------------------------------------------------------------
# formatear_montos_ars  (función pura — sin DB)
# ---------------------------------------------------------------------------

class TestFormatearMontosArs:
    def test_millon_y_medio(self):
        assert formatear_montos_ars(1_500_000) == "$ 1.500.000,00"

    def test_cero(self):
        assert formatear_montos_ars(0) == "$ 0,00"

    def test_con_centavos(self):
        assert formatear_montos_ars(1_234.56) == "$ 1.234,56"

    def test_monto_pequeno(self):
        assert formatear_montos_ars(100) == "$ 100,00"

    def test_negativo(self):
        assert formatear_montos_ars(-500) == "-$ 500,00"

    def test_prefijo_signo_pesos(self):
        assert formatear_montos_ars(1_000).startswith("$ ")

    def test_separador_miles_es_punto(self):
        assert "1.000.000" in formatear_montos_ars(1_000_000)

    def test_separador_decimal_es_coma(self):
        assert "1,50" in formatear_montos_ars(1.5)


# ---------------------------------------------------------------------------
# calcular_indice_concentracion
# ---------------------------------------------------------------------------

class TestCalcularIndiceConcentracion:
    def setup_method(self):
        self.result = calcular_indice_concentracion()

    def test_retorna_dict(self):
        assert isinstance(self.result, dict)

    def test_keys_requeridas(self):
        assert "top10_pct_saldo"    in self.result
        assert "top10_saldo"        in self.result
        assert "saldo_total"        in self.result
        assert "n_clientes_activos" in self.result

    def test_top10_pct_entre_0_y_100(self):
        assert 0 <= self.result["top10_pct_saldo"] <= 100

    def test_top10_saldo_menor_o_igual_a_total(self):
        assert self.result["top10_saldo"] <= self.result["saldo_total"]

    def test_n_clientes_activos_positivo(self):
        assert self.result["n_clientes_activos"] > 0

    def test_concentracion_significativa(self):
        assert self.result["top10_pct_saldo"] > 0

    def test_saldo_total_positivo(self):
        assert self.result["saldo_total"] > 0


# ---------------------------------------------------------------------------
# calcular_tendencia_mora
# ---------------------------------------------------------------------------

class TestCalcularTendenciaMora:
    def setup_method(self):
        self.result = calcular_tendencia_mora()

    def test_retorna_dict(self):
        assert isinstance(self.result, dict)

    def test_keys_requeridas(self):
        assert "valor_actual" in self.result
        assert "referencia"   in self.result
        assert "tendencia"    in self.result

    def test_valor_actual_positivo(self):
        assert self.result["valor_actual"] > 0

    def test_referencia_no_negativa(self):
        assert self.result["referencia"] >= 0

    def test_tendencia_valor_valido(self):
        assert self.result["tendencia"] in {"subiendo", "estable", "bajando"}

    def test_valor_actual_es_porcentaje(self):
        assert 0 <= self.result["valor_actual"] <= 100


# ---------------------------------------------------------------------------
# construir_payload_kpis
# ---------------------------------------------------------------------------

class TestConstruirPayloadKpis:
    def setup_method(self):
        self.payload = construir_payload_kpis()

    def test_retorna_dict(self):
        assert isinstance(self.payload, dict)

    def test_claves_principales(self):
        esperadas = {
            "resumen_cartera", "mora_segmentos", "top_clientes",
            "distribucion_productos", "situacion_bcra",
            "indice_concentracion", "tendencia_mora", "timestamp",
        }
        assert esperadas.issubset(self.payload.keys())

    def test_timestamp_formato_iso(self):
        ts = self.payload["timestamp"]
        assert isinstance(ts, str)
        assert ts.endswith("Z")
        assert "T" in ts

    def test_top_clientes_es_lista_de_10(self):
        assert isinstance(self.payload["top_clientes"], list)
        assert len(self.payload["top_clientes"]) == 10

    def test_mora_segmentos_es_lista(self):
        assert isinstance(self.payload["mora_segmentos"], list)
        assert len(self.payload["mora_segmentos"]) > 0

    def test_indice_concentracion_tiene_pct(self):
        ic = self.payload["indice_concentracion"]
        assert isinstance(ic, dict)
        assert "top10_pct_saldo" in ic

    def test_tendencia_mora_tiene_tendencia(self):
        tm = self.payload["tendencia_mora"]
        assert isinstance(tm, dict)
        assert tm["tendencia"] in {"subiendo", "estable", "bajando"}

    def test_resumen_cartera_tiene_saldo(self):
        rc = self.payload["resumen_cartera"]
        assert "saldo_total_activo" in rc
        assert rc["saldo_total_activo"] > 0
