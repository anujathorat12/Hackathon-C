import { useEffect, useRef, useState } from 'react'
import Icon from './Icon'
import { FORMATS } from '../constants'

export default function NewTopicModal({ initial, onClose, onCreate }) {
  const [form, setForm] = useState({
    title: initial.title || '',
    description: initial.description || '',
    target_format: initial.target_format || 'DOCX',
    user_instructions: initial.user_instructions || '',
  })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const titleRef = useRef(null)

  useEffect(() => {
    titleRef.current?.focus()
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await onCreate(form)
      onClose()
    } catch (err) {
      setError(err.message || 'Could not create the workspace.')
      setBusy(false)
    }
  }

  return (
    <div className="modal-scrim" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
        <div className="modal-head">
          <div>
            <span className="eyebrow"><Icon name="spark" size={14} /> New topic workspace</span>
            <h2 id="modal-title">What should the agents create?</h2>
          </div>
          <button className="icon-btn" onClick={onClose} aria-label="Close"><Icon name="x" /></button>
        </div>

        <form onSubmit={submit} className="form">
          <label className="field">
            <span>Title</span>
            <input ref={titleRef} required value={form.title} onChange={set('title')} placeholder="e.g. Zero-Trust Security Policy" />
          </label>

          <label className="field">
            <span>Brief</span>
            <textarea required rows={3} value={form.description} onChange={set('description')}
              placeholder="Describe the topic, purpose and scope of the document." />
          </label>

          <fieldset className="field">
            <legend>Output format</legend>
            <div className="format-grid">
              {Object.entries(FORMATS).map(([key, f]) => (
                <label key={key} className={`format-opt ${form.target_format === key ? 'on' : ''}`} style={{ '--fmt': f.color }}>
                  <input type="radio" name="fmt" value={key} checked={form.target_format === key} onChange={set('target_format')} />
                  <span className="format-ext">{f.ext}</span>
                  <span className="format-name">{f.label}</span>
                  <span className="format-hint">{f.hint}</span>
                </label>
              ))}
            </div>
          </fieldset>

          <label className="field">
            <span>Instructions <em>optional</em></span>
            <textarea rows={2} value={form.user_instructions} onChange={set('user_instructions')}
              placeholder="Audience, tone, must-have sections…" />
          </label>

          {error && <div className="banner banner-error"><Icon name="alert" /> {error}</div>}

          <div className="modal-actions">
            <button type="button" className="btn btn-ghost" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={busy}>
              {busy ? 'Creating…' : <>Create workspace <Icon name="arrow" size={16} /></>}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
