import Icon from './Icon'
import { MODULES } from '../constants'

export default function Header({ health, onHome }) {
  const online = !!health
  const pending = health === undefined
  return (
    <header className="header">
      <button className="brand" onClick={onHome} aria-label="AGENT-101 home">
        <div className="brand-mark" aria-hidden="true">
          <svg viewBox="0 0 32 32" width="34" height="34">
            <defs>
              <linearGradient id="brandg" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0" stopColor="#8b5cf6" />
                <stop offset="1" stopColor="#22d3ee" />
              </linearGradient>
            </defs>
            <path d="M16 2 28.1 9v14L16 30 3.9 23V9z" fill="url(#brandg)" />
            <path d="M11 21.5 16 10l5 11.5M12.8 17.5h6.4" fill="none" stroke="#fff" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <div>
          <div className="brand-name">AGENT<span>-101</span></div>
          <div className="brand-sub">Agentic Content Studio</div>
        </div>
      </button>

      <div className="header-right">
        <div className="module-legend" aria-label="System modules">
          {Object.entries(MODULES).map(([key, m]) => (
            <span key={key} className={`module-chip mod-${key}`} title={`${m.label}: ${m.name}`}>
              <b>{key}</b><span className="module-chip-name">{m.name}</span>
            </span>
          ))}
        </div>
        <div className={`health ${online ? 'ok' : pending ? 'wait' : 'down'}`} role="status">
          <span className="health-dot" />
          {pending && 'Connecting…'}
          {!pending && !online && 'API offline'}
          {online && (
            <>
              <span>API live</span>
              <span className="health-meta">
                <Icon name="bolt" size={12} /> {health.llm === 'offline-fallback' ? 'Offline LLM' : health.llm}
              </span>
              <span className="health-meta">{health.storage === 'mongodb' ? 'MongoDB' : 'In-memory'}</span>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
