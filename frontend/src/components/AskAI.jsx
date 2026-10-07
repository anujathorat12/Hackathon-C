import { useMemo, useState } from 'react'
import { api } from '../api'
import Icon from './Icon'

const SUGGESTIONS = [
  'Make it shorter and punchier',
  'Use simpler language',
  'Make the tone more formal',
  'Add a real-world example from India',
  'Turn the key points into a table',
]

// Plain-language revision of the whole document or a single section/slide, with undo.
export default function AskAI({ topicId, format, draft, disabled, onRevised, onUndo, canUndo, lastSummary }) {
  const [instruction, setInstruction] = useState('')
  const [section, setSection] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const sections = useMemo(() => [...draft.matchAll(/^## (.+)$/gm)].map((m) => m[1].trim()), [draft])
  const unit = format === 'PPT' ? 'slide' : 'section'

  const submit = async (text) => {
    const value = (text ?? instruction).trim()
    if (!value || busy) return
    setBusy(true)
    setError(null)
    try {
      const res = await api.revise(topicId, draft, value, section || null)
      onRevised(res.content_markdown, res.summary)
      setInstruction('')
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="ask-ai">
      <div className="ask-ai-head">
        <span className="eyebrow"><Icon name="spark" size={14} /> Ask AI to revise</span>
        {lastSummary && (
          <span className="ask-ai-done">
            <Icon name="check" size={14} /> {lastSummary}
            {canUndo && <button className="link-btn" onClick={onUndo} disabled={busy || disabled}>Undo</button>}
          </span>
        )}
      </div>
      <form className="ask-ai-row" onSubmit={(e) => { e.preventDefault(); submit() }}>
        <select value={section} onChange={(e) => setSection(e.target.value)} disabled={busy || disabled} aria-label={`Which ${unit} to revise`}>
          <option value="">Whole document</option>
          {sections.map((h, i) => <option key={`${h}-${i}`} value={h}>{`${unit === 'slide' ? 'Slide' : 'Section'}: ${h}`}</option>)}
        </select>
        <input value={instruction} onChange={(e) => setInstruction(e.target.value)} disabled={busy || disabled}
          placeholder={`Tell the AI what to change, e.g. "add a statistic" or "make it more persuasive"`} aria-label="Revision instruction" />
        <button className={`btn btn-primary ${busy ? 'is-busy' : ''}`} disabled={busy || disabled || !instruction.trim()}>
          {busy ? <><span className="spinner" /> Revising…</> : <><Icon name="spark" size={15} /> Revise</>}
        </button>
      </form>
      <div className="ask-ai-chips">
        {SUGGESTIONS.map((s) => (
          <button key={s} type="button" className="chip chip-btn" onClick={() => submit(s)} disabled={busy || disabled}>{s}</button>
        ))}
      </div>
      {error && <div className="banner banner-error small"><Icon name="alert" size={16} /> {error}</div>}
    </div>
  )
}
