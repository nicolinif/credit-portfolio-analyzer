-- =============================================================================
-- Credit Portfolio Analyzer — Database Schema
-- Dominio bancario argentino · Clasificación BCRA Comunicación A 2216/6938
-- =============================================================================

PRAGMA foreign_keys = ON;
PRAGMA journal_mode  = WAL;

-- ---------------------------------------------------------------------------
-- 1. CLIENTES
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS clientes (
    id_cliente           INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre               TEXT    NOT NULL,
    apellido             TEXT    NOT NULL,
    dni                  TEXT    NOT NULL UNIQUE,
    cuil                 TEXT    NOT NULL UNIQUE,
    genero               TEXT    NOT NULL CHECK (genero IN ('M', 'F')),
    fecha_nacimiento     TEXT    NOT NULL,   -- ISO 8601: YYYY-MM-DD
    email                TEXT,
    telefono             TEXT,
    domicilio            TEXT,
    localidad            TEXT,
    provincia            TEXT,
    fecha_alta           TEXT    NOT NULL,   -- ISO 8601: YYYY-MM-DD
    segmento             TEXT    NOT NULL CHECK (segmento IN ('retail', 'pyme', 'corporativo')),
    calificacion_interna TEXT    NOT NULL CHECK (calificacion_interna IN ('A', 'B', 'C', 'D', 'E'))
    -- A=excelente, B=bueno, C=normal, D=seguimiento, E=irrecuperable
);

CREATE INDEX IF NOT EXISTS idx_clientes_segmento      ON clientes (segmento);
CREATE INDEX IF NOT EXISTS idx_clientes_calificacion  ON clientes (calificacion_interna);

-- ---------------------------------------------------------------------------
-- 2. PRODUCTOS
-- Catálogo de productos de crédito. Tabla de referencia estática.
-- tipo_producto='tarjeta' implica modalidad revolving (cuotas_totales = 0).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS productos (
    id_producto         INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_producto     TEXT    NOT NULL,
    tipo_producto       TEXT    NOT NULL CHECK (tipo_producto IN (
                            'personal', 'tarjeta', 'hipotecario',
                            'prendario', 'capital_trabajo', 'descuento_cheques'
                        )),
    tasa_nominal_anual  REAL    NOT NULL,   -- TNA expresada en porcentaje (ej: 65.5)
    plazo_maximo_meses  INTEGER NOT NULL CHECK (plazo_maximo_meses > 0)
);

CREATE INDEX IF NOT EXISTS idx_productos_tipo ON productos (tipo_producto);

-- ---------------------------------------------------------------------------
-- 3. DEUDAS
-- Tabla de hechos principal. Una fila = una facilidad crediticia.
-- dias_mora y situacion_bcra son desnormalizados para performance analítica.
-- BCRA (Com. A 2216/6938):
--   0-30d   → Situación 1 (normal)
--   31-90d  → Situación 2 (con seguimiento especial)
--   91-180d → Situación 3 (con problemas)
--   181-365d→ Situación 4 (con alto riesgo de insolvencia)
--   >365d   → Situación 5 (irrecuperable)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS deudas (
    id_deuda            INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente          INTEGER NOT NULL REFERENCES clientes  (id_cliente),
    id_producto         INTEGER NOT NULL REFERENCES productos (id_producto),
    monto_original      REAL    NOT NULL CHECK (monto_original  > 0),
    saldo_capital       REAL    NOT NULL CHECK (saldo_capital  >= 0),   -- ARS vigente
    tasa_interes        REAL    NOT NULL,                                -- TNA % aplicada
    fecha_otorgamiento  TEXT    NOT NULL,   -- YYYY-MM-DD
    fecha_vencimiento   TEXT    NOT NULL,   -- YYYY-MM-DD
    cuotas_totales      INTEGER NOT NULL CHECK (cuotas_totales  >= 0),  -- 0 = revolving
    cuotas_pagadas      INTEGER NOT NULL CHECK (cuotas_pagadas  >= 0),
    estado              TEXT    NOT NULL CHECK (estado IN (
                            'vigente', 'en_mora', 'incobrable', 'cancelado'
                        )),
    dias_mora           INTEGER NOT NULL DEFAULT 0 CHECK (dias_mora    >= 0),
    situacion_bcra      INTEGER NOT NULL DEFAULT 1 CHECK (situacion_bcra BETWEEN 1 AND 6)
);

CREATE INDEX IF NOT EXISTS idx_deudas_cliente   ON deudas (id_cliente);
CREATE INDEX IF NOT EXISTS idx_deudas_producto  ON deudas (id_producto);
CREATE INDEX IF NOT EXISTS idx_deudas_estado    ON deudas (estado);
CREATE INDEX IF NOT EXISTS idx_deudas_situacion ON deudas (situacion_bcra);
CREATE INDEX IF NOT EXISTS idx_deudas_mora      ON deudas (dias_mora);

-- ---------------------------------------------------------------------------
-- 4. PAGOS
-- Log de eventos de pago. Una fila = un evento de cobro contra una deuda.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pagos (
    id_pago             INTEGER PRIMARY KEY AUTOINCREMENT,
    id_deuda            INTEGER NOT NULL REFERENCES deudas (id_deuda),
    fecha_pago          TEXT    NOT NULL,                               -- YYYY-MM-DD
    monto_pagado        REAL    NOT NULL CHECK (monto_pagado > 0),     -- ARS
    tipo_pago           TEXT    NOT NULL CHECK (tipo_pago IN (
                            'cuota', 'cancelacion_anticipada', 'regularizacion'
                        )),
    estado_pago         TEXT    NOT NULL CHECK (estado_pago IN (
                            'puntual', 'tardio', 'parcial'
                        ))
);

CREATE INDEX IF NOT EXISTS idx_pagos_deuda  ON pagos (id_deuda);
CREATE INDEX IF NOT EXISTS idx_pagos_fecha  ON pagos (fecha_pago);

-- ---------------------------------------------------------------------------
-- VISTA: v_cartera
-- Join de las 4 tablas listo para consumo directo por Pandas/Flask.
-- Incluye bucket_mora y ratio_avance como columnas computadas.
-- En Etapa 2: pd.read_sql("SELECT * FROM v_cartera", conn) da un DataFrame
-- listo para análisis sin joins adicionales.
-- ---------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS v_cartera AS
SELECT
    -- Cliente
    c.id_cliente,
    c.nombre || ' ' || c.apellido          AS nombre_completo,
    c.dni,
    c.cuil,
    c.genero,
    c.fecha_nacimiento,
    c.segmento,
    c.calificacion_interna,
    c.localidad,
    c.provincia,
    -- Deuda
    d.id_deuda,
    d.monto_original,
    d.saldo_capital,
    d.tasa_interes,
    d.fecha_otorgamiento,
    d.fecha_vencimiento,
    d.cuotas_totales,
    d.cuotas_pagadas,
    d.estado,
    d.dias_mora,
    d.situacion_bcra,
    -- Producto
    p.nombre_producto,
    p.tipo_producto,
    p.tasa_nominal_anual                   AS tna_producto,
    -- Bucket de mora (etiqueta BCRA-alineada para reportes)
    CASE
        WHEN d.dias_mora  =  0               THEN 'sin_mora'
        WHEN d.dias_mora BETWEEN  1 AND  30  THEN 'mora_1_30'
        WHEN d.dias_mora BETWEEN 31 AND  90  THEN 'mora_31_90'
        WHEN d.dias_mora BETWEEN 91 AND 180  THEN 'mora_91_180'
        WHEN d.dias_mora BETWEEN 181 AND 365 THEN 'mora_181_365'
        ELSE                                      'mora_mas_365'
    END                                    AS bucket_mora,
    -- Avance de pago (NULL para revolving)
    CASE
        WHEN d.cuotas_totales > 0
        THEN ROUND(CAST(d.cuotas_pagadas AS REAL) / d.cuotas_totales, 4)
        ELSE NULL
    END                                    AS ratio_avance
FROM deudas d
JOIN clientes  c ON c.id_cliente  = d.id_cliente
JOIN productos p ON p.id_producto = d.id_producto;
