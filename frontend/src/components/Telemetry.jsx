import { useEffect, useRef } from 'react'
import Icon from './Icon'
import { formatTime } from '../constants'

const TAG = { RUNNING: 'RUN ', COMPLETED: ' OK ', WAITING_FOR_REVIEW: 'HOLD', FAILED: 'FAIL' }

export default function Telemetry({ events, live }) {
  const boxRef = useRef(null)

  useEffect(() => {
    const el = boxRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [events.length])

  return (
    <section className="card telemetry" aria-labelledby="telemetry-h">
      <div className="card-head">
        <h2 id="telemetry-h"><Icon name="terminal" /> Live telemetry</h2>
        <span className={`live-pill ${live ? 'on' : ''}`}><i />{live ? 'Streaming' : 'Idle'}</span>
      </div>
      <div className="console" ref={boxRef} role="log" aria-live="polite">
        {events.length === 0 && <div className="console-line muted">$ waiting for launch — events stream here over WebSocket</div>}
        {events.map((e, i) => (
          <div key={i} className={`console-line s-${e.status}`}>
            <span className="c-time">{formatTime(e.timestamp)}</span>
            <span className="c-tag">{TAG[e.status] || e.status}</span>
            <span className="c-agent">{e.agent_name.replace(' Agent', '')}</span>
            <span className="c-msg">{e.message}</span>
          </div>
        ))}
        {live && <div className="console-line"><span className="cursor" /></div>}
      </div>
    </section>
  )
}
