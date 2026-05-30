from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from app.ai_report import generar_reporte
from app.analysis import construir_payload_kpis
from app.queries import (
    get_distribucion_productos,
    get_mora_segmentos,
    get_situacion_bcra,
    get_top_clientes,
)

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    })


@api_bp.route("/kpis")
def kpis():
    try:
        return jsonify({"status": "ok", "data": construir_payload_kpis()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route("/mora-segmentos")
def mora_segmentos():
    try:
        return jsonify({"status": "ok", "data": get_mora_segmentos()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route("/top-clientes")
def top_clientes():
    try:
        n = request.args.get("n", 10, type=int)
        n = min(max(n, 1), 50)
        return jsonify({"status": "ok", "data": get_top_clientes(n=n)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route("/distribucion-productos")
def distribucion_productos():
    try:
        return jsonify({"status": "ok", "data": get_distribucion_productos()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route("/situacion-bcra")
def situacion_bcra():
    try:
        return jsonify({"status": "ok", "data": get_situacion_bcra()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route("/reporte")
def reporte():
    try:
        kpis = construir_payload_kpis()
        texto = generar_reporte(kpis)
        return jsonify({
            "status": "ok",
            "reporte": texto,
            "timestamp": kpis.get(
                "timestamp",
                datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            ),
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
