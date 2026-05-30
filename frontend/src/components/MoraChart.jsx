import { Bar } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend,
} from 'chart.js'
import { formatARS } from '../utils'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

const BUCKET_LABELS = {
  sin_mora:    'Sin mora',
  mora_1_30:   'Mora 1-30 días',
  mora_31_90:  'Mora 31-90 días',
  mora_mas_90: 'Mora +90 días',
}

const BUCKET_COLORS = {
  sin_mora:    'rgba(34, 197, 94, 0.8)',
  mora_1_30:   'rgba(250, 204, 21, 0.8)',
  mora_31_90:  'rgba(249, 115, 22, 0.8)',
  mora_mas_90: 'rgba(239, 68, 68, 0.8)',
}

export default function MoraChart({ segmentos }) {
  const data = {
    labels: segmentos.map(s => BUCKET_LABELS[s.bucket_mora] ?? s.bucket_mora),
    datasets: [{
      label: 'Saldo (ARS)',
      data: segmentos.map(s => s.saldo_total),
      backgroundColor: segmentos.map(s => BUCKET_COLORS[s.bucket_mora] ?? 'rgba(148,163,184,0.8)'),
      borderRadius: 4,
    }],
  }

  const options = {
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: { label: ctx => ` ${formatARS(ctx.raw)}` },
      },
    },
    scales: {
      x: {
        ticks: {
          callback: val => formatARS(val),
          font: { size: 11 },
          color: '#9ca3af',
        },
        grid: { color: '#374151' },
      },
      y: {
        ticks: { color: '#9ca3af' },
        grid: { color: '#374151' },
      },
    },
  }

  return (
    <div className="bg-gray-800 rounded-lg p-5">
      <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-4">
        Distribución por Mora
      </h2>
      <div style={{ height: '200px' }}>
        <Bar data={data} options={options} />
      </div>
    </div>
  )
}
