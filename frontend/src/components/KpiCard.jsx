const COLORS = {
  verde:    { border: 'border-l-green-500',  text: 'text-green-400'  },
  amarillo: { border: 'border-l-yellow-400', text: 'text-yellow-400' },
  rojo:     { border: 'border-l-red-500',    text: 'text-red-400'    },
  azul:     { border: 'border-l-blue-500',   text: 'text-blue-400'   },
  gris:     { border: 'border-l-gray-500',   text: 'text-gray-400'   },
}

export default function KpiCard({ titulo, valor, subtitulo, color = 'azul' }) {
  const { border, text } = COLORS[color] ?? COLORS.azul
  return (
    <div className={`bg-gray-800 rounded-lg p-5 border-l-4 ${border}`}>
      <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide">{titulo}</p>
      <p className={`mt-1 text-3xl font-bold ${text}`}>{valor}</p>
      {subtitulo && <p className="mt-1 text-sm text-gray-500">{subtitulo}</p>}
    </div>
  )
}
