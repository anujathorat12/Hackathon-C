import { useEffect, useState } from 'react'
import { api, setToken } from '../api'
import Icon from './Icon'

export default function AuthModal({ initialMode = 'login', onClose, onAuthSuccess }) {
  const [mode, setMode] = useState(initialMode) // 'login' | 'register'
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [fullName, setFullName] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState('user') // 'user' | 'admin'
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (initialMode) {
      setMode(initialMode)
      setError(null)
    }
  }, [initialMode])

  const handleQuickLogin = async (demoRole) => {
    setError(null)
    setLoading(true)
    const creds = demoRole === 'admin'
      ? { email: 'admin@agent101.ai', password: 'admin123' }
      : { email: 'user@agent101.ai', password: 'user123' }
    setEmail(creds.email)
    setPassword(creds.password)

    try {
      const res = await api.login(creds.email, creds.password)
      if (res && res.token && res.user) {
        setToken(res.token)
        onAuthSuccess(res.user)
        onClose()
      } else {
        throw new Error('Unexpected response during sign-in.')
      }
    } catch (err) {
      setError(err.message || 'Demo sign-in failed. Please verify credentials.')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      let res
      if (mode === 'login') {
        res = await api.login(email, password)
      } else {
        if (!username || username.trim().length < 3) {
          throw new Error('Username must be at least 3 characters.')
        }
        if (!email || !email.includes('@')) {
          throw new Error('Please enter a valid email address.')
        }
        if (password.length < 6) {
          throw new Error('Password must be at least 6 characters.')
        }
        res = await api.register({
          username: username.trim(),
          email: email.trim(),
          password,
          full_name: fullName.trim() || username.trim(),
          role
        })
      }

      if (res && res.token && res.user) {
        setToken(res.token)
        onAuthSuccess(res.user)
        onClose()
      } else {
        throw new Error('Unexpected authentication response.')
      }
    } catch (err) {
      setError(err.message || 'Authentication failed. Please check credentials.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal auth-modal">
        <div className="auth-header">
          <div className="auth-brand-badge">
            <svg viewBox="0 0 32 32" width="28" height="28">
              <defs>
                <linearGradient id="authbg" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0" stopColor="#8b5cf6" />
                  <stop offset="1" stopColor="#22d3ee" />
                </linearGradient>
              </defs>
              <path d="M16 2 28.1 9v14L16 30 3.9 23V9z" fill="url(#authbg)" />
              <path d="M11 21.5 16 10l5 11.5M12.8 17.5h6.4" fill="none" stroke="#fff" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <div>
              <div className="auth-title">AGENT<span>-101</span></div>
              <div className="auth-sub">Agentic Content Studio</div>
            </div>
          </div>
          <button className="icon-btn" onClick={onClose} aria-label="Close modal">
            <Icon name="x" size={18} />
          </button>
        </div>

        {/* Tab switch */}
        <div className="auth-tabs" role="tablist">
          <button
            type="button"
            className={`auth-tab ${mode === 'login' ? 'active' : ''}`}
            onClick={() => { setMode('login'); setError(null) }}
          >
            Sign In
          </button>
          <button
            type="button"
            className={`auth-tab ${mode === 'register' ? 'active' : ''}`}
            onClick={() => { setMode('register'); setError(null) }}
          >
            Create Account
          </button>
        </div>

        {error && (
          <div className="auth-error-banner" role="alert">
            <Icon name="alert" size={16} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form">
          {mode === 'register' && (
            <>
              <div className="field">
                <label className="label">Full Name</label>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g. Sarah Connor"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                />
              </div>

              <div className="field">
                <label className="label">Username *</label>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g. sarah_c"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                />
              </div>
            </>
          )}

          <div className="field">
            <label className="label">{mode === 'login' ? 'Email or Username *' : 'Email Address *'}</label>
            <input
              type={mode === 'register' ? 'email' : 'text'}
              className="input"
              placeholder={mode === 'login' ? 'admin@agent101.ai or username' : 'name@company.com'}
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div className="field">
            <label className="label">Password *</label>
            <input
              type="password"
              className="input"
              placeholder="••••••••"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          {mode === 'register' && (
            <div className="registration-role-notice">
              <span className="role-notice-icon">👤</span>
              <div>
                <div className="role-notice-title">Standard Studio Creator Account</div>
                <div className="role-notice-sub">All new accounts receive full Workspace and Document Generation privileges. Admin accounts are restricted and managed by System Administrators.</div>
              </div>
            </div>
          )}

          <div className="auth-actions">
            <button type="submit" className="btn btn-primary auth-submit-btn" disabled={loading}>
              {loading ? (
                <span>Verifying…</span>
              ) : mode === 'login' ? (
                <>
                  <Icon name="bolt" size={15} /> Sign In to Studio
                </>
              ) : (
                <>
                  <Icon name="check" size={15} /> Create Account & Launch
                </>
              )}
            </button>
          </div>
        </form>

        {mode === 'login' && (
          <div className="auth-quick-fill">
            <div className="quick-fill-label">Instant 1-Click Demo Access:</div>
            <div className="quick-fill-btns">
              <button
                type="button"
                className="btn btn-ghost btn-sm quick-demo-btn"
                onClick={() => handleQuickLogin('admin')}
                disabled={loading}
                title="1-Click Sign In as Administrator"
              >
                🛡️ Demo Admin (admin@agent101.ai)
              </button>
              <button
                type="button"
                className="btn btn-ghost btn-sm quick-demo-btn"
                onClick={() => handleQuickLogin('user')}
                disabled={loading}
                title="1-Click Sign In as Standard User"
              >
                👤 Demo User (user@agent101.ai)
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
