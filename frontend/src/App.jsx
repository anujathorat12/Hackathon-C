import { useCallback, useEffect, useState } from 'react'
import { api } from './api'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import EmptyState from './components/EmptyState'
import NewTopicModal from './components/NewTopicModal'
import Workspace from './components/Workspace'

export default function App() {
  const [workspaces, setWorkspaces] = useState([])
  const [activeId, setActiveId] = useState(null)
  const [health, setHealth] = useState(undefined)
  const [loaded, setLoaded] = useState(false)
  const [draft, setDraft] = useState(null) // modal initial values; null = closed
  const [stats, setStats] = useState(null)

  const refreshStats = useCallback(() => { api.stats().then(setStats).catch(() => {}) }, [])

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth(null))
    refreshStats()
    api.list()
      .then((list) => {
        setWorkspaces(list)
        if (list.length) setActiveId(list[list.length - 1].id)
      })
      .catch(() => {})
      .finally(() => setLoaded(true))
  }, [])

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
    refreshStats()
    setWorkspaces((list) => {
      const next = list.filter((w) => w.id !== id)
      if (id === activeId) setActiveId(next.length ? next[next.length - 1].id : null)
      return next
    })
  }

  const setStatus = useCallback((id, status) => {
    setWorkspaces((list) => list.map((w) => (w.id === id ? { ...w, status } : w)))
    if (status === 'WAITING_FOR_REVIEW') refreshStats()
  }, [refreshStats])

  const active = workspaces.find((w) => w.id === activeId)

  return (
    <div className="app">
      <div className="backdrop" aria-hidden="true">
        <div className="orb orb-a" />
        <div className="orb orb-b" />
        <div className="orb orb-c" />
        <div className="grid" />
      </div>

      <Header health={health} onHome={() => setActiveId(null)} />

      <div className="shell">
        <Sidebar
          workspaces={workspaces}
          activeId={activeId}
          onSelect={setActiveId}
          onNew={() => setDraft({})}
          onDelete={deleteWorkspace}
          stats={stats}
        />
        <main className="main" id="main">
          {active ? (
            <Workspace key={active.id} ws={active} onStatus={setStatus} />
          ) : (
            loaded && <EmptyState stats={stats} offline={health === null} onPreset={(p) => setDraft(p)} onNew={() => setDraft({})} />
          )}
        </main>
      </div>

      {draft && (
        <NewTopicModal initial={draft} onClose={() => setDraft(null)} onCreate={createWorkspace} onCreated={openCreated} />
      )}
    </div>
  )
}
