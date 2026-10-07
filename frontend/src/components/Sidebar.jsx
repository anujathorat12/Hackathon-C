import Icon from './Icon'
import { FORMATS, STATUS_LABELS } from '../constants'
import { ValueTotals } from './ValueMeter'

export default function Sidebar({ workspaces, activeId, onSelect, onNew, onDelete, stats }) {
  return (
    <aside className="sidebar" aria-label="Topic workspaces">
      <button className="btn btn-primary btn-block" onClick={onNew}>
        <Icon name="plus" /> New topic
      </button>

      <div className="sidebar-label">
        <Icon name="folder" size={14} /> Workspaces <span className="count">{workspaces.length}</span>
      </div>

      <nav className="ws-list">
        {workspaces.length === 0 && <p className="ws-empty">No topics yet. Each topic gets an isolated context.</p>}
        {[...workspaces].reverse().map((ws) => {
          const fmt = FORMATS[ws.target_format] || FORMATS.DOCX
          const status = ws.status || 'CREATED'
          return (
            <div key={ws.id} className={`ws-item ${ws.id === activeId ? 'active' : ''}`}>
              <button className="ws-select" onClick={() => onSelect(ws.id)} aria-current={ws.id === activeId}>
                <span className="fmt-badge" style={{ '--fmt': fmt.color }}>{ws.target_format}</span>
                <span className="ws-text">
                  <span className="ws-title">{ws.title}</span>
                  <span className={`ws-status st-${status}`}><i />{STATUS_LABELS[status] || status}</span>
                </span>
              </button>
              <button
                className="icon-btn ws-delete"
                aria-label={`Delete ${ws.title}`}
                onClick={() => window.confirm(`Delete "${ws.title}"?`) && onDelete(ws.id)}
              >
                <Icon name="trash" size={15} />
              </button>
            </div>
          )
        })}
      </nav>

      <ValueTotals stats={stats} compact />
      <div className="sidebar-foot">
        <Icon name="shield" size={14} /> Topic-scoped memory · zero cross-topic leakage
      </div>
    </aside>
  )
}
