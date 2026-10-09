import Icon from './Icon'
import { AGENTS, FORMATS, PRESETS } from '../constants'
import { ValueTotals } from './ValueMeter'

export default function EmptyState({ onPreset, onNew, offline, stats }) {
  return (
    <section className="hero">
      <div className="hero-copy">
        <span className="eyebrow"><Icon name="spark" size={14} /> 7 autonomous agents · human-approved · accessibility-checked</span>
        <h1>
          From a one-line brief to a <span className="grad-text">boardroom-ready</span> document.
        </h1>
        <p className="lede">
          ContentGenie plans, researches, writes, reviews and compiles native PowerPoint, Word, PDF and Markdown
          deliverables that match your brand template, with automated accessibility checks. You review and approve before anything is compiled.
        </p>
        <div className="hero-actions">
          <button className="btn btn-primary btn-lg" onClick={onNew}>
            <Icon name="plus" /> Start a new topic
          </button>
          <span className="hero-note">or launch a ready-made demo brief ↓</span>
        </div>
        <ValueTotals stats={stats} />
        {offline && (
          <div className="banner banner-warn" role="alert">
            <Icon name="alert" /> Can’t reach the API. Start the backend with <code>uvicorn app.main:app --port 8000</code> from <code>backend/</code>.
          </div>
        )}
      </div>

      <div className="orbit" aria-hidden="true">
        <div className="orbit-core">
          <Icon name="spark" size={34} />
        </div>
        <div className="orbit-ring">
          {AGENTS.map((a, i) => (
            <div key={a.name} className={`orbit-node accent-${a.accent}`} style={{ '--i': i, '--n': AGENTS.length }}>
              <span><Icon name={a.icon} size={18} /></span>
            </div>
          ))}
        </div>
      </div>

      <div className="presets">
        {PRESETS.map((p) => {
          const fmt = FORMATS[p.target_format]
          return (
            <button key={p.title} className="preset" onClick={() => onPreset(p)} style={{ '--fmt': fmt.color }}>
              <span className="preset-top">
                <span className="fmt-badge" style={{ '--fmt': fmt.color }}>{p.target_format}</span>
                <span className="preset-kind">{fmt.hint}</span>
              </span>
              <span className="preset-title">{p.title}</span>
              <span className="preset-desc">{p.description}</span>
              <span className="preset-cta">Use this brief <Icon name="arrow" size={15} /></span>
            </button>
          )
        })}
      </div>
    </section>
  )
}
