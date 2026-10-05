export default function ProgressRing({ value, status }) {
  const r = 52
  const c = 2 * Math.PI * r
  const done = status === 'COMPLETED'
  return (
    <div className={`ring ${done ? 'ring-done' : ''} ${status === 'PROCESSING' || status === 'COMPILING' ? 'ring-live' : ''}`}
      role="progressbar" aria-valuenow={value} aria-valuemin={0} aria-valuemax={100} aria-label="Pipeline progress">
      <svg viewBox="0 0 128 128" width="148" height="148">
        <defs>
          <linearGradient id="ringg" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#8b5cf6" />
            <stop offset="1" stopColor="#22d3ee" />
          </linearGradient>
        </defs>
        <circle cx="64" cy="64" r={r} className="ring-track" />
        <circle cx="64" cy="64" r={r} className="ring-bar" stroke={done ? '#34d399' : 'url(#ringg)'}
          strokeDasharray={c} strokeDashoffset={c * (1 - value / 100)} />
      </svg>
      <div className="ring-label">
        <strong>{value}<small>%</small></strong>
        <span>{done ? 'Delivered' : 'Pipeline'}</span>
      </div>
    </div>
  )
}
