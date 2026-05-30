"""
test_routes.py — Tests de los endpoints Flask de la API REST.

Los endpoints de datos llaman a la DB real (seed=42).
El endpoint /api/reporte mockea generar_reporte para no consumir Groq.

Ejecutar desde la raíz del proyecto:
    source backend/venv/bin/activate
    pytest backend/tests/test_routes.py -v
"""

from unittest.mock import patch

import pytest

from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


class TestHealth:
    def test_status_200(self, client):
        assert client.get("/api/health").status_code == 200

    def test_status_ok(self, client):
        assert client.get("/api/health").get_json()["status"] == "ok"

    def test_timestamp_present(self, client):
        assert "timestamp" in client.get("/api/health").get_json()


class TestKpis:
    def test_status_200(self, client):
        assert client.get("/api/kpis").status_code == 200

    def test_envelope_ok(self, client):
        data = client.get("/api/kpis").get_json()
        assert data["status"] == "ok"
        assert "data" in data

    def test_payload_keys(self, client):
        data = client.get("/api/kpis").get_json()["data"]
        for key in ("resumen_cartera", "mora_segmentos", "top_clientes",
                    "distribucion_productos", "situacion_bcra",
                    "indice_concentracion", "tendencia_mora", "timestamp"):
            assert key in data


class TestMoraSegmentos:
    def test_status_200(self, client):
        assert client.get("/api/mora-segmentos").status_code == 200

    def test_returns_list(self, client):
        data = client.get("/api/mora-segmentos").get_json()
        assert data["status"] == "ok"
        assert isinstance(data["data"], list)

    def test_buckets_presentes(self, client):
        buckets = {r["bucket_mora"] for r in client.get("/api/mora-segmentos").get_json()["data"]}
        assert "sin_mora" in buckets


class TestTopClientes:
    def test_default_10(self, client):
        data = client.get("/api/top-clientes").get_json()
        assert len(data["data"]) <= 10

    def test_custom_n(self, client):
        data = client.get("/api/top-clientes?n=5").get_json()
        assert len(data["data"]) <= 5

    def test_n_capped_at_50(self, client):
        data = client.get("/api/top-clientes?n=200").get_json()
        assert len(data["data"]) <= 50

    def test_campos_cliente(self, client):
        row = client.get("/api/top-clientes?n=1").get_json()["data"][0]
        assert "nombre_completo" in row
        assert "saldo_total" in row


class TestDistribucionProductos:
    def test_status_200(self, client):
        assert client.get("/api/distribucion-productos").status_code == 200

    def test_returns_list(self, client):
        data = client.get("/api/distribucion-productos").get_json()
        assert isinstance(data["data"], list)


class TestSituacionBcra:
    def test_status_200(self, client):
        assert client.get("/api/situacion-bcra").status_code == 200

    def test_situaciones_1_a_5(self, client):
        data = client.get("/api/situacion-bcra").get_json()["data"]
        for r in data:
            assert r["situacion_bcra"] in {1, 2, 3, 4, 5}

    def test_descripcion_presente(self, client):
        data = client.get("/api/situacion-bcra").get_json()["data"]
        assert all("descripcion" in r for r in data)


class TestReporte:
    MOCK_REPORTE = "## Resumen Ejecutivo de Cartera\nContenido de prueba."

    def test_status_200(self, client):
        with patch("app.routes.generar_reporte", return_value=self.MOCK_REPORTE):
            assert client.get("/api/reporte").status_code == 200

    def test_envelope_structure(self, client):
        with patch("app.routes.generar_reporte", return_value=self.MOCK_REPORTE):
            data = client.get("/api/reporte").get_json()
        assert data["status"] == "ok"
        assert "reporte" in data
        assert "timestamp" in data

    def test_reporte_content(self, client):
        with patch("app.routes.generar_reporte", return_value=self.MOCK_REPORTE):
            data = client.get("/api/reporte").get_json()
        assert data["reporte"] == self.MOCK_REPORTE
