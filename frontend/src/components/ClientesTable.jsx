import { formatARS } from '../utils'

const BADGE = {
  1: { cls: 'bg-green-900 text-green-300',  label: 'Normal'                      },
  2: { cls: 'bg-blue-900 text-blue-300',    label: 'Seg. especial'               },
  3: { cls: 'bg-yellow-900 text-yellow-300',label: 'Con problemas'               },
  4: { cls: 'bg-orange-900 text-orange-300',label: 'Alto riesgo'                 },
  5: { cls: 'bg-red-900 text-red-300',      label: 'Irrecuperable'               },
}

export default function ClientesTable({ clientes }) {
  return (
    <div className="bg-gray-800 rounded-lg p-5">
      <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-4">
        Top 10 Deudores
      </h2>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-gray-500 border-b border-gray-700">
              <th className="pb-2 font-semibold">Nombre</th>
              <th className="pb-2 font-semibold">Segmento</th>
              <th className="pb-2 font-semibold">Sit. BCRA</th>
              <th className="pb-2 font-semibold text-right">Deudas</th>
              <th className="pb-2 font-semibold text-right">Saldo Total</th>
            </tr>
          </thead>
          <tbody>
            {clientes.map(c => {
              const sit = BADGE[c.situacion_deudor]
              return (
                <tr key={c.id_cliente} className="border-b border-gray-700/50 hover:bg-gray-700/40 transition-colors">
                  <td className="py-2 font-medium text-gray-100">{c.nombre_completo}</td>
                  <td className="py-2 capitalize text-gray-400">{c.segmento}</td>
                  <td className="py-2">
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-bold ${sit?.cls ?? 'bg-gray-700 text-gray-400'}`}
                      title={sit?.label}
                    >
                      {c.situacion_deudor}
                      <span className="font-normal opacity-75">— {sit?.label}</span>
                    </span>
                  </td>
                  <td className="py-2 text-right text-gray-400">{c.cantidad_deudas}</td>
                  <td className="py-2 text-right font-medium text-gray-100">{formatARS(c.saldo_total)}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
