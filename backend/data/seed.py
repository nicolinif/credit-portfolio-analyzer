"""
seed.py — Generador de datos sintéticos para Credit Portfolio Analyzer.

Genera ~200 clientes con datos bancarios argentinos realistas y distribución
de mora BCRA controlada a nivel de deuda:
  50 % sin mora (0 días)
  25 % mora 1-30 días
  15 % mora 31-90 días
  10 % > 90 días  (5 % → 91-180d, 3 % → 181-365d, 2 % → >365d)

Solo usa stdlib: sqlite3, random, datetime, pathlib.

Uso:
    python3 backend/data/seed.py

TODAY fijo = 2026-05-29 para reproducibilidad garantizada.
"""

import sqlite3
import random
import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------------------------
TODAY   = datetime.date(2026, 5, 29)
SEED    = 42
random.seed(SEED)

SCRIPT_DIR  = Path(__file__).resolve().parent
DB_DIR      = SCRIPT_DIR.parent / "db"
DB_PATH     = DB_DIR / "portfolio.db"
SCHEMA_PATH = SCRIPT_DIR / "schema.sql"

# ---------------------------------------------------------------------------
# DATOS DE REFERENCIA — nombres y geografía argentina
# ---------------------------------------------------------------------------
NOMBRES_M = [
    "Alejandro", "Carlos", "Daniel", "Eduardo", "Federico",
    "Gonzalo", "Hernán", "Ignacio", "Javier", "Leonardo",
    "Marcelo", "Nicolás", "Oscar", "Pablo", "Ramiro",
    "Sebastián", "Tomás", "Walter", "Agustín", "Cristian",
    "Diego", "Emilio", "Facundo", "Gabriel", "Horacio",
]

NOMBRES_F = [
    "Adriana", "Beatriz", "Carolina", "Diana", "Elena",
    "Florencia", "Gabriela", "Hilda", "Irene", "Jimena",
    "Karina", "Laura", "Mariana", "Natalia", "Paola",
    "Romina", "Silvana", "Tamara", "Valeria", "Yanina",
    "Analía", "Brenda", "Cecilia", "Daniela", "Estela",
]

APELLIDOS = [
    "García", "Fernández", "González", "Rodríguez", "López",
    "Martínez", "Sánchez", "Pérez", "Gómez", "Díaz",
    "Torres", "Ramírez", "Flores", "Acosta", "Molina",
    "Romero", "Herrera", "Medina", "Álvarez", "Moreno",
    "Ruiz", "Suárez", "Vega", "Reyes", "Ortiz",
    "Mendoza", "Silva", "Vargas", "Rojas", "Ríos",
    "Guerrero", "Jiménez", "Cabrera", "Leiva", "Pereyra",
    "Olivares", "Blanco", "Villanueva", "Castro", "Peralta",
]

# Provincia → localidades. Pesos por población relativa.
PROVINCIAS = {
    "Buenos Aires": [
        "La Plata", "Mar del Plata", "Quilmes", "Lanús",
        "Lomas de Zamora", "Bahía Blanca", "Morón", "Tigre",
    ],
    "CABA": [
        "Palermo", "Belgrano", "Caballito", "Flores",
        "Villa Urquiza", "San Telmo", "Almagro", "Recoleta",
    ],
    "Córdoba": [
        "Córdoba Capital", "Villa María", "Río Cuarto", "San Francisco",
    ],
    "Santa Fe": [
        "Rosario", "Santa Fe Capital", "Rafaela", "Venado Tuerto",
    ],
    "Mendoza": [
        "Mendoza Capital", "San Rafael", "Godoy Cruz",
    ],
    "Tucumán": [
        "San Miguel de Tucumán", "Yerba Buena", "Concepción",
    ],
    "Entre Ríos": [
        "Paraná", "Concordia", "Gualeguaychú",
    ],
    "Salta": [
        "Salta Capital", "Orán", "Tartagal",
    ],
    "Misiones": [
        "Posadas", "Oberá",
    ],
    "Chaco": [
        "Resistencia", "Presidencia Roque Sáenz Peña",
    ],
}
PROV_LIST    = list(PROVINCIAS.keys())
PROV_WEIGHTS = [35, 20, 12, 10, 6, 4, 3, 3, 4, 3]

# ---------------------------------------------------------------------------
# CATÁLOGO DE PRODUCTOS
# ---------------------------------------------------------------------------
PRODUCTOS_CATALOG = [
    {
        "nombre_producto": "Préstamo Personal Nación",
        "tipo_producto": "personal",
        "tasa_nominal_anual": 65.0,
        "plazo_maximo_meses": 60,
    },
    {
        "nombre_producto": "Tarjeta de Crédito Nación",
        "tipo_producto": "tarjeta",
        "tasa_nominal_anual": 79.0,
        "plazo_maximo_meses": 12,
    },
    {
        "nombre_producto": "Crédito Hipotecario UVA",
        "tipo_producto": "hipotecario",
        "tasa_nominal_anual": 6.0,
        "plazo_maximo_meses": 240,
    },
    {
        "nombre_producto": "Crédito Prendario Nación",
        "tipo_producto": "prendario",
        "tasa_nominal_anual": 52.0,
        "plazo_maximo_meses": 60,
    },
    {
        "nombre_producto": "Capital de Trabajo PyME",
        "tipo_producto": "capital_trabajo",
        "tasa_nominal_anual": 60.0,
        "plazo_maximo_meses": 36,
    },
    {
        "nombre_producto": "Descuento de Cheques",
        "tipo_producto": "descuento_cheques",
        "tasa_nominal_anual": 58.0,
        "plazo_maximo_meses": 6,
    },
]

# Rangos de monto en ARS (contexto 2026)
MONTO_RANGES = {
    "personal":           (500_000,    10_000_000),
    "tarjeta":            (200_000,     5_000_000),
    "hipotecario":     (50_000_000,   500_000_000),
    "prendario":        (3_000_000,    30_000_000),
    "capital_trabajo":  (2_000_000,    50_000_000),
    "descuento_cheques":(1_000_000,    20_000_000),
}

# TNA por producto con variación individual (%)
TNA_RANGES = {
    "personal":           (55.0, 75.0),
    "tarjeta":            (65.0, 90.0),
    "hipotecario":         (6.0,  6.0),  # UVA + tasa fija
    "prendario":          (45.0, 60.0),
    "capital_trabajo":    (50.0, 70.0),
    "descuento_cheques":  (50.0, 68.0),
}

# Plazos disponibles por producto (meses)
PLAZOS = {
    "personal":           [12, 18, 24, 36, 48, 60],
    "tarjeta":            [0],                        # revolving
    "hipotecario":        [60, 120, 180, 240],
    "prendario":          [12, 24, 36, 48, 60],
    "capital_trabajo":    [6, 12, 18, 24, 36],
    "descuento_cheques":  [1, 2, 3, 6],
}

# Productos habilitados por segmento (evita combinaciones imposibles)
PROD_POR_SEGMENTO = {
    "retail":      ["personal", "tarjeta", "hipotecario", "prendario"],
    "pyme":        ["personal", "capital_trabajo", "descuento_cheques", "prendario"],
    "corporativo": ["capital_trabajo", "descuento_cheques", "hipotecario", "prendario"],
}

# ---------------------------------------------------------------------------
# DISTRIBUCIÓN DE MORA (pesos acumulativos sobre [0, 1])
# ---------------------------------------------------------------------------
MORA_BUCKETS = [
    # (label,           min_dias, max_dias, peso_acumulado)
    ("sin_mora",               0,       0, 0.50),
    ("mora_1_30",              1,      30, 0.75),
    ("mora_31_90",            31,      90, 0.90),
    ("mora_91_180",           91,     180, 0.95),
    ("mora_181_365",         181,     365, 0.98),
    ("mora_mas_365",         366,     700, 1.00),
]


def _pick_mora() -> tuple[int, str]:
    """Devuelve (dias_mora, label) según distribución target."""
    r = random.random()
    for label, lo, hi, cum in MORA_BUCKETS:
        if r <= cum:
            return (lo if lo == hi else random.randint(lo, hi)), label
    return 0, "sin_mora"


def _dias_to_bcra(dias: int) -> int:
    """Mapeo días de mora → Situación BCRA (Com. A 2216/6938)."""
    if dias <=  30: return 1
    if dias <=  90: return 2
    if dias <= 180: return 3
    if dias <= 365: return 4
    return 5


def _dias_to_estado(dias: int, vencimiento: datetime.date) -> str:
    if dias == 0:
        return "cancelado" if vencimiento < TODAY else "vigente"
    if dias > 365:
        return "incobrable"
    return "en_mora"


# ---------------------------------------------------------------------------
# HELPERS — generación de datos personales
# ---------------------------------------------------------------------------

def _gen_dni() -> str:
    return str(random.randint(10_000_000, 45_000_000))


def _gen_cuil(dni: str, genero: str) -> str:
    """CUIL sintético con dígito verificador mod-11 (algoritmo AFIP)."""
    prefix = "20" if genero == "M" else "27"
    base   = prefix + dni.zfill(8)
    pesos  = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    total  = sum(int(base[i]) * pesos[i] for i in range(10))
    rem    = 11 - (total % 11)
    vd     = 0 if rem == 11 else (9 if rem == 10 else rem)
    return f"{base}{vd}"


def _gen_email(nombre: str, apellido: str) -> str:
    tr = str.maketrans("áéíóúÁÉÍÓÚ", "aeiouAEIOU")
    n  = nombre.translate(tr).lower()
    a  = apellido.translate(tr).lower()
    domain = random.choice(["gmail.com", "hotmail.com", "yahoo.com.ar", "outlook.com"])
    return f"{n}.{a}{random.randint(1, 999)}@{domain}"


def _gen_telefono() -> str:
    area = random.choice(["011", "0221", "0351", "0341", "0261", "0381"])
    return f"{area}-{random.randint(4_000_000, 9_999_999)}"


def _gen_domicilio() -> str:
    calles = [
        "Av. Corrientes", "San Martín", "Mitre", "Rivadavia", "Belgrano",
        "Sarmiento", "Independencia", "9 de Julio", "25 de Mayo", "Córdoba",
        "Las Heras", "Tucumán", "Entre Ríos", "Chacabuco", "Mendoza",
    ]
    return f"{random.choice(calles)} {random.randint(100, 9999)}"


def _gen_segmento() -> str:
    return random.choices(["retail", "pyme", "corporativo"], weights=[75, 20, 5])[0]


def _situacion_deudor(dias_mora_list: list[int]) -> int:
    """Situación BCRA del deudor: MAX(situacion_bcra) de todas sus deudas.
    Un cliente se clasifica por su peor deuda (Com. A 2216/6938)."""
    return max(_dias_to_bcra(d) for d in dias_mora_list)


# ---------------------------------------------------------------------------
# GENERADOR DE PAGOS
# Sistema francés simplificado para cuotas fijas; mínimo mensual para tarjeta.
# ---------------------------------------------------------------------------

def _gen_pagos(
    id_deuda: int,
    tipo: str,
    monto: float,
    tna: float,
    fecha_otorg: datetime.date,
    cuotas_pagadas: int,
    dias_mora: int,
) -> list[dict]:
    """Genera historial de pagos coherente con el estado de mora de la deuda."""
    if cuotas_pagadas == 0:
        return []

    pagos = []
    tasa_m = tna / 100 / 12

    if tipo == "tarjeta":
        for i in range(cuotas_pagadas):
            fecha = fecha_otorg + datetime.timedelta(days=30 * (i + 1))
            if fecha > TODAY:
                break
            is_last = (i == cuotas_pagadas - 1)
            if is_last and dias_mora > 0:
                ep = random.choice(["tardio", "parcial"])
                mp = round(monto * random.uniform(0.05, 0.15), 2)
            else:
                ep = "puntual" if random.random() > 0.08 else "tardio"
                mp = round(monto * random.uniform(0.05, 0.20), 2)
            pagos.append({
                "id_deuda":    id_deuda,
                "fecha_pago":  fecha.isoformat(),
                "monto_pagado": mp,
                "tipo_pago":   "cuota",
                "estado_pago": ep,
            })
    else:
        # Sistema francés: cuota fija mensual
        if tasa_m > 0 and cuotas_pagadas > 0:
            n     = cuotas_pagadas
            cuota = round(monto * tasa_m * (1 + tasa_m) ** n / ((1 + tasa_m) ** n - 1), 2)
        else:
            cuota = round(monto / max(cuotas_pagadas, 1), 2)

        for i in range(cuotas_pagadas):
            fecha = fecha_otorg + datetime.timedelta(days=30 * (i + 1))
            if fecha > TODAY:
                break
            is_last = (i == cuotas_pagadas - 1)
            if is_last and dias_mora > 0:
                ep = random.choice(["tardio", "parcial"])
                mp = round(cuota * random.uniform(0.50, 0.95), 2)
                tp = "regularizacion" if ep == "parcial" else "cuota"
            else:
                ep = "puntual" if random.random() > 0.08 else "tardio"
                mp = cuota
                tp = "cuota"
            pagos.append({
                "id_deuda":    id_deuda,
                "fecha_pago":  fecha.isoformat(),
                "monto_pagado": mp,
                "tipo_pago":   tp,
                "estado_pago": ep,
            })

    return pagos


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def seed():
    print(f"[seed] TODAY = {TODAY}  |  DB = {DB_PATH}")
    DB_DIR.mkdir(parents=True, exist_ok=True)

    if DB_PATH.exists():
        DB_PATH.unlink()
        print("[seed] Base de datos anterior eliminada.")

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode  = WAL")
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    print("[seed] Schema aplicado.")

    cur = conn.cursor()

    # --- Productos ---
    cur.executemany(
        "INSERT INTO productos (nombre_producto, tipo_producto, tasa_nominal_anual, plazo_maximo_meses) "
        "VALUES (:nombre_producto, :tipo_producto, :tasa_nominal_anual, :plazo_maximo_meses)",
        PRODUCTOS_CATALOG,
    )
    conn.commit()

    # Índice en memoria: tipo_producto → lista de id_producto
    tipo_a_ids: dict[str, list[int]] = {}
    for row in cur.execute("SELECT id_producto, tipo_producto FROM productos"):
        tipo_a_ids.setdefault(row[1], []).append(row[0])

    print(f"[seed] {len(PRODUCTOS_CATALOG)} productos insertados.")

    # --- Clientes, deudas y pagos ---
    stats: dict = {
        "clientes": 0,
        "deudas":   0,
        "pagos":    0,
        "mora_dist": {b[0]: 0 for b in MORA_BUCKETS},
    }

    for _ in range(200):
        # ---- Cliente --------------------------------------------------------
        genero   = random.choice(["M", "F"])
        nombre   = random.choice(NOMBRES_M if genero == "M" else NOMBRES_F)
        apellido = random.choice(APELLIDOS)
        dni      = _gen_dni()
        cuil     = _gen_cuil(dni, genero)
        prov     = random.choices(PROV_LIST, weights=PROV_WEIGHTS)[0]
        localidad = random.choice(PROVINCIAS[prov])
        segmento = _gen_segmento()
        n_deudas = random.choices([1, 2, 3], weights=[50, 35, 15])[0]

        moras            = [_pick_mora() for _ in range(n_deudas)]
        situacion_deudor = _situacion_deudor([d for d, _ in moras])

        cur.execute(
            "INSERT INTO clientes "
            "(nombre, apellido, dni, cuil, genero, fecha_nacimiento, "
            " email, telefono, domicilio, localidad, provincia, fecha_alta, "
            " segmento, situacion_deudor) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                nombre, apellido, dni, cuil, genero,
                (TODAY - datetime.timedelta(days=random.randint(22 * 365, 70 * 365))).isoformat(),
                _gen_email(nombre, apellido),
                _gen_telefono(),
                _gen_domicilio(),
                localidad, prov,
                (TODAY - datetime.timedelta(days=random.randint(365, 8 * 365))).isoformat(),
                segmento, situacion_deudor,
            ),
        )
        id_cliente = cur.lastrowid
        stats["clientes"] += 1

        # ---- Deudas ---------------------------------------------------------
        tipos_disponibles = PROD_POR_SEGMENTO[segmento]

        for j in range(n_deudas):
            dias_mora, mora_label = moras[j]
            tipo    = random.choice(tipos_disponibles)
            id_prod = random.choice(tipo_a_ids[tipo])

            monto_orig = round(random.uniform(*MONTO_RANGES[tipo]), -3)
            tna        = round(random.uniform(*TNA_RANGES[tipo]), 2)

            meses_atras = random.randint(1, 48)
            fecha_otorg = TODAY - datetime.timedelta(days=30 * meses_atras)

            if tipo == "tarjeta":
                cuotas_tot = 0
                plazo_m    = 12
            else:
                plazo_m    = random.choice(PLAZOS[tipo])
                cuotas_tot = plazo_m

            fecha_venc = fecha_otorg + datetime.timedelta(days=30 * plazo_m)

            if tipo == "tarjeta":
                cuotas_pag = meses_atras
            else:
                cuotas_pag = min(meses_atras, cuotas_tot)
                if dias_mora > 0:
                    missed     = max(1, dias_mora // 30)
                    cuotas_pag = max(0, cuotas_pag - missed)

            if tipo == "tarjeta":
                saldo = round(monto_orig * random.uniform(0.30, 1.00), 2)
            elif cuotas_tot > 0:
                saldo = round(monto_orig * (1.0 - (cuotas_pag / cuotas_tot) * 0.85), 2)
            else:
                saldo = monto_orig

            saldo  = max(0.0, saldo)
            estado = _dias_to_estado(dias_mora, fecha_venc)

            cur.execute(
                "INSERT INTO deudas "
                "(id_cliente, id_producto, monto_original, saldo_capital, tasa_interes, "
                " fecha_otorgamiento, fecha_vencimiento, cuotas_totales, cuotas_pagadas, "
                " estado, dias_mora, situacion_bcra) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    id_cliente, id_prod, monto_orig, saldo, tna,
                    fecha_otorg.isoformat(), fecha_venc.isoformat(),
                    cuotas_tot, cuotas_pag, estado, dias_mora, _dias_to_bcra(dias_mora),
                ),
            )
            id_deuda = cur.lastrowid
            stats["deudas"] += 1
            stats["mora_dist"][mora_label] += 1

            # ---- Pagos ------------------------------------------------------
            pagos = _gen_pagos(
                id_deuda, tipo, monto_orig, tna, fecha_otorg, cuotas_pag, dias_mora
            )
            if pagos:
                cur.executemany(
                    "INSERT INTO pagos (id_deuda, fecha_pago, monto_pagado, tipo_pago, estado_pago) "
                    "VALUES (:id_deuda, :fecha_pago, :monto_pagado, :tipo_pago, :estado_pago)",
                    pagos,
                )
                stats["pagos"] += len(pagos)

        conn.commit()

    # --- Resumen ------------------------------------------------------------
    print("\n" + "=" * 62)
    print("SEED COMPLETADO")
    print("=" * 62)
    print(f"  Clientes : {stats['clientes']}")
    print(f"  Deudas   : {stats['deudas']}")
    print(f"  Pagos    : {stats['pagos']}")

    print("\n  Distribución de mora (a nivel deuda):")
    for label, lo, hi, _ in MORA_BUCKETS:
        n   = stats["mora_dist"].get(label, 0)
        pct = n / stats["deudas"] * 100 if stats["deudas"] else 0
        bar = "#" * int(pct / 2)
        print(f"    {label:<16} {n:>4}  ({pct:5.1f}%)  {bar}")

    print("\n  Situación BCRA:")
    for sit, cnt in conn.execute(
        "SELECT situacion_bcra, COUNT(*) FROM deudas GROUP BY 1 ORDER BY 1"
    ).fetchall():
        pct = cnt / stats["deudas"] * 100
        print(f"    Situación {sit}: {cnt:>4}  ({pct:5.1f}%)")

    print("\n  Estado de deudas:")
    for est, cnt in conn.execute(
        "SELECT estado, COUNT(*) FROM deudas GROUP BY 1 ORDER BY 1"
    ).fetchall():
        pct = cnt / stats["deudas"] * 100
        print(f"    {est:<12} {cnt:>4}  ({pct:5.1f}%)")

    total_saldo = conn.execute(
        "SELECT SUM(saldo_capital) FROM deudas WHERE estado != 'cancelado'"
    ).fetchone()[0] or 0.0
    print(f"\n  Saldo capital activo: ARS {total_saldo:>20,.2f}")
    print(f"\n  DB guardada en: {DB_PATH}")
    print("=" * 62)

    conn.close()


if __name__ == "__main__":
    seed()
