import { useCallback, useEffect, useState } from 'react'
import { api, getToken, setToken } from './api'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import EmptyState from './components/EmptyState'
import NewTopicModal from './components/NewTopicModal'
import Workspace from './components/Workspace'
import LandingPage from './components/LandingPage'
import AuthModal from './components/AuthModal'
import AdminModal from './components/AdminModal'

export default function App() {
  const [currentUser, setCurrentUser] = useState(null)
  const [authChecking, setAuthChecking] = useState(true)
  const [authModal, setAuthModal] = useState(null) // 'login' | 'register' | null
  const [adminModal, setAdminModal] = useState(false)

  const [workspaces, setWorkspaces] = useState([])
  const [activeId, setActiveId] = useState(null)
  const [health, setHealth] = useState(undefined)
  const [loaded, setLoaded] = useState(false)
  const [draft, setDraft] = useState(null) // modal initial values; null = closed

  // Check existing session token on mount
  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth(null))

    const token = getToken()
    if (token) {
      api.me()
        .then((user) => {
          setCurrentUser(user)
          loadWorkspaces()
        })
        .catch(() => {
          setToken(null)
          setCurrentUser(null)
        })
        .finally(() => setAuthChecking(false))
    } else {
      setAuthChecking(false)
    }
  }, [])

  const loadWorkspaces = useCallback(() => {
    setLoaded(false)
    api.list()
      .then((list) => {
        setWorkspaces(list)
        if (list.length) setActiveId(list[list.length - 1].id)
      })
      .catch(() => {})
      .finally(() => setLoaded(true))
  }, [])

  const handleLogout = async () => {
    try { await api.logout() } catch {}
    setToken(null)
    setCurrentUser(null)
    setWorkspaces([])
    setActiveId(null)
    setAdminModal(false)
  }

  const handleAuthSuccess = (user) => {
    setCurrentUser(user)
    setAuthModal(null)
    loadWorkspaces()
  }

  // The modal uploads the optional template after this, then calls openCreated.
  const createWorkspace = async (data) => {
    const res = await api.create(data)
    const ws = { id: res.workspace_id, ...data, status: res.status, created_at: new Date().toISOString() }
    setWorkspaces((list) => [...list, ws])
    return ws.id
  }

  const openCreated = (id) => {
    setDraft(null)
    setActiveId(id)
  }

  const deleteWorkspace = async (id) => {
    await api.remove(id)
    setWorkspaces((list) => {
      const next = list.filter((w) => w.id !== id)
      if (id === activeId) setActiveId(next.length ? next[next.length - 1].id : null)
      return next
    })
  }

  const setStatus = useCallback((id, status) => {
    setWorkspaces((list) => list.map((w) => (w.id === id ? { ...w, status } : w)))
  }, [])

  const active = workspaces.find((w) => w.id === activeId)

  // Initial session verification loader
  if (authChecking) {
    return (
      <div className="app app-loading-screen">
        <div className="loading-spinner" />
        <p>Initializing AGENT-101 Studio…</p>
      </div>
    )
  }

  return (
    <div className="app">
      <div className="backdrop" aria-hidden="true">
        <div className="orb orb-a" />
        <div className="orb orb-b" />
        <div className="orb orb-c" />
        <div className="grid" />
      </div>

      {currentUser ? (
        /* Authenticated Studio Environment */
        <>
          <Header
            health={health}
            user={currentUser}
            onHome={() => setActiveId(null)}
            onOpenAuth={(mode) => setAuthModal(mode)}
            onOpenAdmin={() => setAdminModal(true)}
            onLogout={handleLogout}
          />
          <div className="shell">
            <Sidebar
              workspaces={workspaces}
              activeId={activeId}
              onSelect={setActiveId}
              onNew={() => setDraft({})}
              onDelete={deleteWorkspace}
            />
            <main className="main" id="main">
              {active ? (
                <Workspace key={active.id} ws={active} onStatus={setStatus} />
              ) : (
                loaded && <EmptyState offline={health === null} onPreset={(p) => setDraft(p)} onNew={() => setDraft({})} />
              )}
            </main>
          </div>
        </>
      ) : (
        /* Public Landing Page */
        <LandingPage
          onOpenAuth={(mode) => setAuthModal(mode)}
          health={health}
        />
      )}

      {/* Auth Modal (Login / Register) */}
      {authModal && (
        <AuthModal
          initialMode={authModal}
          onClose={() => setAuthModal(null)}
          onAuthSuccess={handleAuthSuccess}
        />
      )}

      {/* Admin Oversight Modal */}
      {adminModal && currentUser?.role === 'admin' && (
        <AdminModal
          onClose={() => setAdminModal(false)}
          health={health}
          currentUser={currentUser}
        />
      )}

      {/* New Topic Creation Modal */}
      {draft && currentUser && (
        <NewTopicModal
          initial={draft}
          onClose={() => setDraft(null)}
          onCreate={createWorkspace}
          onCreated={openCreated}
        />
      )}
    </div>
  )
}
