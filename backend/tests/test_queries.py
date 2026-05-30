"""
test_queries.py — Tests de las funciones de análisis de cartera.

Corren contra la base de datos real (backend/db/portfolio.db).
Prerequisito: haber ejecutado backend/data/seed.py con seed=42.

Ejecutar desde la raíz del proyecto:
    source backend/venv/bin/activate
    pip install pytest
    pytest backend/tests/test_queries.py -v
"""

from app.queries import (
    get_mora_segmentos,
    get_top_clientes,
    get_tasa_mora,
    get_distribucion_productos,
    get_situacion_bcra,
    get_resumen_cartera,
)


# ---------------------------------------------------------------------------
# get_mora_segmentos
# ---------------------------------------------------------------------------

class TestGetMoraSegmentos:
    def setup_method(self):
        self.result = get_mora_segmentos()

    def test_returns_list_of_dicts(self):
        assert isinstance(self.result, list)
        assert all(isinstance(r, dict) for r in self.result)

    def test_expected_buckets_present(self):
        buckets = {r["bucket_mora"] for r in self.result}
        assert "sin_mora"    in buckets
        assert "mora_1_30"   in buckets
        assert "mora_31_90"  in buckets
        assert "mora_mas_90" in buckets

    def test_required_keys(self):
        for r in self.result:
            assert "bucket_mora"     in r
            assert "cantidad_deudas" in r
            assert "saldo_total"     in r
            assert "pct_saldo"       in r

    def test_saldo_positivo(self):
        for r in self.result:
            assert r["saldo_total"] >= 0

    def test_pct_suma_100(self):
        total_pct = sum(r["pct_saldo"] for r in self.result)
        assert abs(total_pct - 100.0) < 0.1

    def test_sin_mora_presente(self):
        sin_mora = next(r for r in self.result if r["bucket_mora"] == "sin_mora")
        assert sin_mora["pct_saldo"] > 0


# ---------------------------------------------------------------------------
# get_top_clientes
# ---------------------------------------------------------------------------

class TestGetTopClientes:
    def test_default_retorna_10(self):
        assert len(get_top_clientes()) == 10

    def test_n_personalizable(self):
        assert len(get_top_clientes(n=5))  == 5
        assert len(get_top_clientes(n=20)) == 20

    def test_required_keys(self):
        for r in get_top_clientes(n=3):
            assert "id_cliente"       in r
            assert "nombre_completo"  in r
            assert "segmento"         in r
            assert "situacion_deudor" in r
            assert "cantidad_deudas"  in r
            assert "saldo_total"      in r

    def test_situacion_deudor_valida(self):
        for r in get_top_clientes(n=10):
            assert r["situacion_deudor"] in {1, 2, 3, 4, 5}

    def test_ordenado_descendente(self):
        saldos = [r["saldo_total"] for r in get_top_clientes(n=10)]
        assert saldos == sorted(saldos, reverse=True)

    def test_saldo_positivo(self):
        for r in get_top_clientes(n=10):
            assert r["saldo_total"] > 0

    def test_segmento_valido(self):
        segmentos_validos = {"retail", "pyme", "corporativo"}
        for r in get_top_clientes(n=10):
            assert r["segmento"] in segmentos_validos


# ---------------------------------------------------------------------------
# get_tasa_mora
# ---------------------------------------------------------------------------

class TestGetTasaMora:
    def setup_method(self):
        self.result = get_tasa_mora()

    def test_returns_dict(self):
        assert isinstance(self.result, dict)

    def test_required_keys(self):
        assert "saldo_mora"    in self.result
        assert "saldo_total"   in self.result
        assert "tasa_mora_pct" in self.result

    def test_tasa_entre_0_y_100(self):
        assert 0 <= self.result["tasa_mora_pct"] <= 100

    def test_saldo_mora_menor_o_igual_a_total(self):
        assert self.result["saldo_mora"] <= self.result["saldo_total"]

    def test_saldo_total_positivo(self):
        assert self.result["saldo_total"] > 0

    def test_tasa_mayor_a_cero(self):
        assert self.result["tasa_mora_pct"] > 0


# ---------------------------------------------------------------------------
# get_distribucion_productos
# ---------------------------------------------------------------------------

class TestGetDistribucionProductos:
    def setup_method(self):
        self.result = get_distribucion_productos()

    def test_returns_list_of_dicts(self):
        assert isinstance(self.result, list)
        assert len(self.result) > 0

    def test_required_keys(self):
        for r in self.result:
            assert "tipo_producto"   in r
            assert "nombre_producto" in r
            assert "cantidad_deudas" in r
            assert "saldo_total"     in r
            assert "tasa_promedio"   in r

    def test_tipos_validos(self):
        tipos_validos = {
            "personal", "tarjeta", "hipotecario",
            "prendario", "capital_trabajo", "descuento_cheques",
        }
        for r in self.result:
            assert r["tipo_producto"] in tipos_validos

    def test_saldo_positivo(self):
        for r in self.result:
            assert r["saldo_total"] >= 0

    def test_tasa_promedio_positiva(self):
        for r in self.result:
            assert r["tasa_promedio"] > 0

    def test_ordenado_por_saldo_descendente(self):
        saldos = [r["saldo_total"] for r in self.result]
        assert saldos == sorted(saldos, reverse=True)


# ---------------------------------------------------------------------------
# get_situacion_bcra
# ---------------------------------------------------------------------------

class TestGetSituacionBcra:
    def setup_method(self):
        self.result = get_situacion_bcra()

    def test_returns_list_of_dicts(self):
        assert isinstance(self.result, list)
        assert len(self.result) > 0

    def test_required_keys(self):
        for r in self.result:
            assert "situacion_bcra"  in r
            assert "cantidad_deudas" in r
            assert "saldo_total"     in r
            assert "pct_cantidad"    in r
            assert "descripcion"     in r

    def test_situaciones_validas(self):
        for r in self.result:
            assert 1 <= r["situacion_bcra"] <= 5

    def test_descripcion_no_vacia(self):
        for r in self.result:
            assert len(r["descripcion"]) > 0

    def test_situacion_1_es_mayoritaria(self):
        sit1 = next((r for r in self.result if r["situacion_bcra"] == 1), None)
        assert sit1 is not None
        assert sit1["pct_cantidad"] > 50

    def test_pct_suma_100(self):
        total = sum(r["pct_cantidad"] for r in self.result)
        assert abs(total - 100.0) < 0.1


# ---------------------------------------------------------------------------
# get_resumen_cartera
# ---------------------------------------------------------------------------

class TestGetResumenCartera:
    def setup_method(self):
        self.result = get_resumen_cartera()

    def test_returns_dict(self):
        assert isinstance(self.result, dict)

    def test_required_keys(self):
        required = {
            "total_clientes",
            "total_deudas_activas",
            "clientes_con_deuda_activa",
            "saldo_total_activo",
            "saldo_en_mora",
            "tasa_mora_pct",
        }
        assert required.issubset(self.result.keys())

    def test_total_clientes_es_200(self):
        assert self.result["total_clientes"] == 200

    def test_total_deudas_activas_positivo(self):
        assert self.result["total_deudas_activas"] > 0

    def test_clientes_activos_menor_o_igual_a_total(self):
        assert self.result["clientes_con_deuda_activa"] <= self.result["total_clientes"]

    def test_saldo_mora_menor_o_igual_a_total(self):
        assert self.result["saldo_en_mora"] <= self.result["saldo_total_activo"]

    def test_tasa_mora_entre_0_y_100(self):
        assert 0 <= self.result["tasa_mora_pct"] <= 100

    def test_consistencia_saldo_mora_y_tasa(self):
        esperado = (self.result["saldo_en_mora"] / self.result["saldo_total_activo"]) * 100
        assert abs(self.result["tasa_mora_pct"] - esperado) < 0.01
