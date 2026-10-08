import Icon from './Icon'

export default function Header({ health, user, onHome, onOpenAuth, onOpenAdmin, onLogout }) {
  const online = !!health
  const pending = health === undefined
  const isAdmin = user?.role === 'admin'

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
        {/* Health status badge */}
        <div className={`health ${online ? 'ok' : pending ? 'wait' : 'down'}`} role="status">
          <span className="health-dot" />
          {pending && 'Connecting…'}
          {!pending && !online && 'API offline'}
          {online && (
            <>
              <span>API live</span>
              <span
                className="health-meta"
                title={health?.provider_chain ? `Failover Chain: ${health.provider_chain.map(p => `${p.display_name}: ${p.status}`).join(' ➜ ')}` : ''}
              >
                <Icon name="bolt" size={12} /> {health.llm === 'offline-fallback' ? 'Offline LLM' : health.llm}
              </span>
              <span className="health-meta">{health.storage === 'mongodb' ? 'MongoDB' : 'In-memory'}</span>
            </>
          )}
        </div>

        {/* User profile / session controls */}
        {user ? (
          <div className="user-profile-menu">
            {isAdmin && (
              <button className="btn btn-ghost btn-sm admin-nav-btn" onClick={onOpenAdmin} title="Open Admin Console">
                <Icon name="bolt" size={13} /> Admin Console
              </button>
            )}

            <div className="user-pill">
              <span className={`user-avatar ${user.role}`}>
                {user.username.slice(0, 2).toUpperCase()}
              </span>
              <div className="user-info-text">
                <span className="user-name-label">{user.full_name || user.username}</span>
                <span className={`role-badge ${user.role}`}>
                  {isAdmin ? '🛡️ Admin' : '👤 User'}
                </span>
              </div>
            </div>

            <button className="btn btn-ghost btn-sm logout-btn" onClick={onLogout} title="Sign Out">
              <Icon name="x" size={14} /> Sign Out
            </button>
          </div>
        ) : (
          <div className="auth-header-actions">
            <button className="btn btn-ghost btn-sm" onClick={() => onOpenAuth('login')}>
              Sign In
            </button>
            <button className="btn btn-primary btn-sm" onClick={() => onOpenAuth('register')}>
              Create Account
            </button>
          </div>
        )}
      </div>
    </header>
  )
}
