import { useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../api'
import Icon from './Icon'
import ProgressRing from './ProgressRing'
import StageRail from './StageRail'
import PipelineFlow from './PipelineFlow'
import Telemetry from './Telemetry'
import ReviewStudio from './ReviewStudio'
import DeliverableVault from './DeliverableVault'
import { FORMATS, STATUS_LABELS } from '../constants'

const localEvent = (agent_name, status, message, payload = {}) => ({
  agent_name, status, message, payload, progress_percent: status === 'COMPLETED' ? 100 : 88,
  timestamp: new Date().toISOString(),
})

export default function Workspace({ ws, onStatus }) {
  const [status, setStatusState] = useState(ws.status || 'CREATED')
  const [events, setEvents] = useState([])
  const [content, setContent] = useState('')
  const [deliverable, setDeliverable] = useState(null)
  const [versions, setVersions] = useState([])
  const [templates, setTemplates] = useState([])
  const [sources, setSources] = useState([])
  const [streaming, setStreaming] = useState(false)
  const [error, setError] = useState(null)
  const socketRef = useRef(null)
  const reviewRef = useRef(null)
  const vaultRef = useRef(null)

  const setStatus = (s) => {
    setStatusState(s)
    onStatus(ws.id, s)
  }

  const applySnapshot = (snap) => {
    setEvents(snap.events || [])
    setContent(snap.refined_content || '')
    setDeliverable(snap.deliverables?.length ? snap.deliverables[snap.deliverables.length - 1] : null)
    setVersions(snap.deliverables || [])
    // A PROCESSING status with no events means the server restarted mid-run.
    const s = snap.status === 'PROCESSING' && !snap.events?.length ? 'CREATED' : snap.status
    setStatusState(s)
    onStatus(ws.id, s)
    return s
  }

  // Restore this workspace's run; keep polling if a run is still going server-side.
  useEffect(() => {
    let timer
    let cancelled = false
    const load = () =>
      api.run(ws.id).then((snap) => {
        if (cancelled || socketRef.current) return
        const s = applySnapshot(snap)
        if (s === 'PROCESSING' || s === 'COMPILING') timer = setTimeout(load, 900)
      }).catch(() => {})
    load()
    api.templates(ws.id).then((t) => !cancelled && setTemplates(t)).catch(() => {})
    api.sources(ws.id).then((s) => !cancelled && setSources(s)).catch(() => {})
    return () => { cancelled = true; clearTimeout(timer) }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ws.id])

  // Guide the presenter to the next step, but only on live transitions (not when restoring a tab).
  const prevStatus = useRef(status)
  useEffect(() => {
    const prev = prevStatus.current
    prevStatus.current = status
    if (prev === 'PROCESSING' && status === 'WAITING_FOR_REVIEW') reviewRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    if (prev === 'COMPILING' && status === 'COMPLETED') vaultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [status])

  const launch = async () => {
    setError(null)
    setEvents([])
    setContent('')
    setDeliverable(null)
    setVersions([])
    setStreaming(true)
    setStatus('PROCESSING')
    try {
      await api.generate(ws.id)
    } catch (e) {
      setError(e.message)
      setStreaming(false)
      setStatus('FAILED')
      return
    }
    const sock = new WebSocket(api.streamUrl(ws.id))
    socketRef.current = sock
    let sawReview = false
    sock.onmessage = (msg) => {
      const ev = JSON.parse(msg.data)
      setEvents((prev) => [...prev, ev])
      if (ev.status === 'WAITING_FOR_REVIEW') {
        sawReview = true
        setContent(ev.payload?.refined_content || '')
        setStatus('WAITING_FOR_REVIEW')
      }
      if (ev.status === 'FAILED') {
        setError(ev.message)
        setStatus('FAILED')
      }
    }
    sock.onclose = () => {
      socketRef.current = null
      setStreaming(false)
      if (!sawReview) setStatusState((s) => (s === 'PROCESSING' ? 'FAILED' : s))
    }
    sock.onerror = () => setError('Lost connection to the agent pipeline stream.')
  }

  const approve = async (markdown) => {
    setError(null)
    setStatus('COMPILING')
    setEvents((prev) => [...prev, localEvent('Format Generation Agent', 'RUNNING', `Compiling native ${ws.target_format} deliverable…`)])
    try {
      const d = await api.approve(ws.id, markdown)
      setContent(markdown)
      setDeliverable(d)
      setVersions((list) => [...list.filter((x) => x.file_name !== d.file_name), d])
      setEvents((prev) => [...prev, localEvent('Format Generation Agent', 'COMPLETED',
        `Compiled ${d.file_name} — accessibility checks ${d.wcag_compliant ? 'passed' : 'need attention'}.`, d)])
      setStatus('COMPLETED')
    } catch (e) {
      setError(e.message)
      setEvents((prev) => [...prev, localEvent('Format Generation Agent', 'FAILED', e.message)])
      setStatus('WAITING_FOR_REVIEW')
    }
  }

  const progress = useMemo(() => {
    if (status === 'COMPLETED') return 100
    if (status === 'COMPILING') return 92
    return events.reduce((max, e) => Math.max(max, e.progress_percent || 0), 0)
  }, [events, status])

  const reviewEvent = [...events].reverse().find((e) => e.status === 'WAITING_FOR_REVIEW')
  const fmt = FORMATS[ws.target_format] || FORMATS.DOCX
  const busy = streaming || status === 'PROCESSING' || status === 'COMPILING'
  const hasRun = events.length > 0
  const template = templates[templates.length - 1]
  const palette = Object.values(template?.guidance?.color_palette || {}).slice(0, 4)

  return (
    <div className="workspace">
      <section className="card ws-hero">
        <div className="ws-hero-main">
          <div className="ws-hero-tags">
            <span className="fmt-badge lg" style={{ '--fmt': fmt.color }}>{fmt.label} {fmt.ext}</span>
            <span className={`status-pill st-${status}`}><i />{STATUS_LABELS[status] || status}</span>
            {ws.language && ws.language !== 'English' && (
              <span className="tpl-chip"><Icon name="type" size={13} /><span className="tpl-chip-name">{ws.language}</span></span>
            )}
            {sources.length > 0 && (
              <span className="tpl-chip" title={sources.map((s) => `${s.file_name} (${s.locations} sections/pages)`).join(', ')}>
                <Icon name="folder" size={13} /><span className="tpl-chip-name">{sources.length} source{sources.length > 1 ? 's' : ''}</span>
              </span>
            )}
            <span className="tpl-chip" title={template ? `Brand template: ${template.file_name}` : 'No template uploaded'}>
              {palette.length > 0 && (
                <span className="tpl-chip-swatches">
                  {palette.map((c) => <i key={c} style={{ background: c }} />)}
                </span>
              )}
              <Icon name="palette" size={13} />
              <span className="tpl-chip-name">{template ? template.file_name : 'Default theme'}</span>
            </span>
          </div>
          <h1 className="ws-title-lg">{ws.title}</h1>
          <p className="ws-desc">{ws.description}</p>
          {ws.user_instructions && (
            <p className="ws-instr"><Icon name="user" size={14} /> {ws.user_instructions}</p>
          )}
          <div className="ws-hero-actions">
            <button className={`btn btn-primary btn-lg ${busy ? 'is-busy' : ''}`} onClick={launch} disabled={busy}>
              {busy ? <><span className="spinner" /> Agents at work…</>
                : hasRun ? <><Icon name="refresh" /> Regenerate</>
                  : <><Icon name="play" /> Launch autonomous generation</>}
            </button>
            {!hasRun && !busy && <span className="hint">7 agents · about a minute · you approve before compile</span>}
          </div>
        </div>
        <ProgressRing value={progress} status={status} />
      </section>

      <StageRail status={status} hasRun={hasRun} />

      {error && (
        <div className="banner banner-error" role="alert">
          <Icon name="alert" /> {error}
          <button className="icon-btn" onClick={() => setError(null)} aria-label="Dismiss"><Icon name="x" size={16} /></button>
        </div>
      )}

      <div className="ws-grid">
        <PipelineFlow events={events} status={status} />
        <div className="ws-side">
          <Telemetry events={events} live={busy} />
        </div>
      </div>

      {content && ['WAITING_FOR_REVIEW', 'COMPILING', 'COMPLETED'].includes(status) && (
        <div ref={reviewRef}>
          <ReviewStudio
            topicId={ws.id}
            format={ws.target_format}
            content={content}
            metrics={reviewEvent?.payload}
            status={status}
            title={ws.title}
            deliverable={deliverable}
            template={template}
            onApprove={approve}
          />
        </div>
      )}

      {deliverable && status === 'COMPLETED' && (
        <div ref={vaultRef}>
          <DeliverableVault deliverable={deliverable} versions={versions} topicId={ws.id} refinedContent={content} title={ws.title} />
        </div>
      )}
    </div>
  )
}
