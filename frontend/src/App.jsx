import { useEffect, useState } from 'react'
import axios from 'axios'
import KpiCard from './components/KpiCard'
import MoraChart from './components/MoraChart'
import ClientesTable from './components/ClientesTable'
import AiReport from './components/AiReport'
import { formatARS } from './utils'

function moraColor(pct) {
  if (pct < 15) return 'verde'
  if (pct < 30) return 'amarillo'
  return 'rojo'
}

function concentracionColor(pct) {
  if (pct < 30) return 'verde'
  if (pct < 50) return 'amarillo'
  return 'rojo'
}

function tendenciaColor(t) {
  if (t === 'bajando') return 'verde'
  if (t === 'estable') return 'amarillo'
  return 'rojo'
}

const TENDENCIA_SYMBOL = { subiendo: '↑', estable: '→', bajando: '↓' }

export default function App() {
  const [kpis, setKpis]       = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)

  useEffect(() => {
    axios.get('/api/kpis')
      .then(({ data }) => setKpis(data.data))
      .catch(() => setError('No se pudo conectar con el backend. ¿Está corriendo en :5000?'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center">
      <p className="text-gray-400 text-lg">Cargando dashboard…</p>
    </div>
  )

  if (error) return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center">
      <p className="text-red-400 text-lg">{error}</p>
    </div>
  )

  const rc = kpis.resumen_cartera
  const ic = kpis.indice_concentracion
  const tm = kpis.tendencia_mora

  return (
    <div className="min-h-screen bg-gray-900">
      <header className="bg-gray-950 text-white px-8 py-5 border-b border-gray-800">
        <h1 className="text-xl font-bold tracking-wide">Credit Portfolio Analyzer</h1>
        <p className="text-sm text-gray-400 mt-0.5">Dashboard de Gestión de Cartera Crediticia</p>
      </header>

      <main className="max-w-[1400px] mx-auto px-8 py-6 space-y-6">
        <div className="grid grid-cols-3 gap-4">
          <KpiCard
            titulo="Tasa de Mora"
            valor={`${rc.tasa_mora_pct} %`}
            subtitulo="Saldo en mora / saldo total activo"
            color={moraColor(rc.tasa_mora_pct)}
          />
          <KpiCard
            titulo="Saldo Total Activo"
            valor={formatARS(rc.saldo_total_activo)}
            subtitulo={`${rc.total_deudas_activas} deudas activas`}
            color="azul"
          />
          <KpiCard
            titulo="Concentración Top 10"
            valor={`${ic.top10_pct_saldo} %`}
            subtitulo="Del saldo total en los 10 principales deudores"
            color={concentracionColor(ic.top10_pct_saldo)}
          />
          <KpiCard
            titulo="Tendencia de Mora"
            valor={`${TENDENCIA_SYMBOL[tm.tendencia] ?? '—'} ${tm.tendencia}`}
            subtitulo={`Actual ${tm.valor_actual} % vs. referencia ${tm.referencia} %`}
            color={tendenciaColor(tm.tendencia)}
          />
          <KpiCard
            titulo="Clientes Activos"
            valor={ic.n_clientes_activos}
            subtitulo={`de ${rc.total_clientes} clientes totales`}
            color="azul"
          />
          <KpiCard
            titulo="Deudas Activas"
            valor={rc.total_deudas_activas}
            subtitulo={`${rc.clientes_con_deuda_activa} clientes con deuda`}
            color="gris"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <MoraChart segmentos={kpis.mora_segmentos} />
          <ClientesTable clientes={kpis.top_clientes} />
        </div>

        <AiReport />
      </main>
    </div>
  )
}
