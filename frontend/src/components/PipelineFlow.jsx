import Icon from './Icon'
import { AGENTS, formatBytes } from '../constants'

function agentState(name, events, status) {
  let last = null
  for (const e of events) if (e.agent_name === name) last = e
  if (!last) return { state: 'pending', event: null }
  if (last.status === 'RUNNING') return { state: status === 'FAILED' ? 'failed' : 'active', event: last }
  if (last.status === 'FAILED') return { state: 'failed', event: last }
  // The completed event carries the payload; RUNNING events don't.
  return { state: 'done', event: last }
}

const Chip = ({ children, tone }) => <span className={`chip ${tone ? `chip-${tone}` : ''}`}>{children}</span>

function Insight({ name, payload = {} }) {
  switch (name) {
    case 'Requirement Analysis Agent':
      return (
        <div className="insight">
          {payload.objective && <p className="insight-quote">“{payload.objective}”</p>}
          <div className="chips">
            {payload.tone && <Chip tone="violet">Tone · {payload.tone.split(',')[0]}</Chip>}
            {(payload.key_deliverables || []).slice(0, 3).map((d) => <Chip key={d}>{d}</Chip>)}
          </div>
        </div>
      )
    case 'Planning Agent':
      return (
        <div className="insight">
          <ol className="plan-list">
            {(payload.sections || []).slice(0, 5).map((s) => (
              <li key={s.section_id || s.heading}>
                <span>{s.heading}</span>
                {s.target_word_count ? <em>~{s.target_word_count}w</em> : null}
              </li>
            ))}
          </ol>
        </div>
      )
    case 'Reference Analysis Agent': {
      const pal = payload.color_palette || {}
      const typo = payload.typography || {}
      return (
        <div className="insight insight-row">
          <div className="swatches">
            {['primary_hex', 'secondary_hex', 'accent_hex', 'text_hex'].filter((k) => pal[k]).map((k) => (
              <span key={k} className="swatch" style={{ background: pal[k] }} title={`${k.replace('_hex', '')} ${pal[k]}`} />
            ))}
          </div>
          <div className="chips">
            <Chip tone="cyan"><Icon name="type" size={12} /> {typo.heading_font} / {typo.body_font}</Chip>
            <Chip>{payload.source_file_name ? `From ${payload.source_file_name}` : 'Corporate default theme'}</Chip>
          </div>
        </div>
      )
    }
    case 'Research & Enrichment Agent':
      return (
        <div className="insight">
          {payload.from_user_sources && <div className="chips" style={{ marginBottom: 8 }}><Chip tone="green">Grounded in your uploaded sources</Chip></div>}
          <ul className="facts">
            {(payload.key_facts || []).slice(0, 2).map((f) => (
              <li key={f.fact}>{f.fact} <Chip tone="cyan">{f.citation}</Chip></li>
            ))}
          </ul>
        </div>
      )
    case 'Content Generation Agent':
      return (
        <div className="insight chips">
          <Chip tone="violet">{payload.word_count || 0} words drafted</Chip>
          <Chip>Active voice</Chip><Chip>Markdown tables</Chip>
        </div>
      )
    case 'Content Review Agent':
      return (
        <div className="insight chips">
          {payload.reading_grade_level > 0 && <Chip tone="green">Reading grade {payload.reading_grade_level}{payload.initial_reading_grade_level ? ` (draft ${payload.initial_reading_grade_level})` : ''}</Chip>}
          <Chip>{payload.words_trimmed ?? 0} words trimmed</Chip>
          <Chip>{payload.sentences_shortened ?? 0} long sentences shortened</Chip>
          <Chip>{payload.citations_count ?? 0} sources cited</Chip>
        </div>
      )
    case 'Format Generation Agent':
      return payload.file_name ? (
        <div className="insight chips">
          <Chip tone="cyan">{payload.file_name}</Chip>
          <Chip>{formatBytes(payload.file_size_bytes)}</Chip>
          <Chip tone={payload.wcag_compliant ? 'green' : 'amber'}>Accessibility checks {payload.wcag_compliant ? '✓' : '!'}</Chip>
        </div>
      ) : null
    default:
      return null
  }
}

export default function PipelineFlow({ events, status }) {
  const states = AGENTS.map((a) => {
    const s = agentState(a.name, events, status)
    // The last agent only runs after human approval.
    if (a.name === 'Format Generation Agent' && status === 'WAITING_FOR_REVIEW' && s.state === 'pending') s.state = 'gated'
    return s
  })
  const doneCount = states.filter((s) => s.state === 'done').length

  return (
    <section className="card pipeline" aria-labelledby="pipeline-h">
      <div className="card-head">
        <h2 id="pipeline-h"><Icon name="spark" /> Agent pipeline</h2>
        <span className="card-meta">{doneCount}/{AGENTS.length} agents complete</span>
      </div>

      <ol className="flow">
        {AGENTS.map((a, i) => {
          const { state, event } = states[i]
          return (
            <li key={a.name} className={`node ${state}`} style={{ '--delay': `${i * 40}ms` }}>
              <div className={`node-icon accent-${a.accent}`}>
                {state === 'done' ? <Icon name="check" size={18} strokeWidth={2.6} />
                  : state === 'failed' ? <Icon name="alert" size={18} />
                    : <Icon name={a.icon} size={18} />}
              </div>
              <div className="node-body">
                <div className="node-top">
                  <span className="node-step">0{i + 1}</span>
                  <span className="node-name">{a.short}</span>
                  {state === 'active' && <span className="node-live"><i />working</span>}
                  {state === 'gated' && <span className="node-gate"><Icon name="user" size={12} /> awaiting your approval</span>}
                </div>
                <p className="node-msg">{state === 'done' && event?.message ? event.message : a.blurb}</p>
                {state === 'done' && event?.payload && <Insight name={a.name} payload={event.payload} />}
                {state === 'active' && <div className="shimmer-bar" />}
              </div>
            </li>
          )
        })}
      </ol>
    </section>
  )
}
