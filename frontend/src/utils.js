export function formatARS(valor) {
  if (valor == null) return '—'
  const abs = Math.abs(valor)
  const [entero, centavos] = abs.toFixed(2).split('.')
  const enteroARS = entero.replace(/\B(?=(\d{3})+(?!\d))/g, '.')
  return `${valor < 0 ? '-' : ''}$ ${enteroARS},${centavos}`
}
