import { useState } from 'react'
import axios from 'axios'

export default function AiReport() {
  const [reporte, setReporte] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState(null)

  async function generarReporte() {
    setLoading(true)
    setError(null)
    setReporte(null)
    try {
      const { data } = await axios.get('/api/reporte')
      setReporte(data.reporte)
    } catch (e) {
      setError(e.response?.data?.message ?? 'Error al conectar con el servidor.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-gray-800 rounded-lg p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
          Reporte Ejecutivo IA
        </h2>
        <button
          onClick={generarReporte}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white text-sm font-semibold rounded hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              Generando…
            </span>
          ) : 'Generar Reporte IA'}
        </button>
      </div>

      {error && (
        <div className="p-3 bg-red-900/30 border border-red-700 text-red-400 rounded text-sm">
          {error}
        </div>
      )}

      {reporte && (
        <div className="mt-2 text-sm text-gray-200 whitespace-pre-wrap leading-relaxed">
          {reporte}
        </div>
      )}

      {!loading && !reporte && !error && (
        <p className="text-sm text-gray-500 italic">
          Hacé clic en el botón para generar un reporte ejecutivo con IA.
        </p>
      )}
    </div>
  )
}
