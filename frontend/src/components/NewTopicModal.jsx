import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import Icon from './Icon'
import { FORMATS, formatBytes } from '../constants'

const TEMPLATE_TYPES = ['.pptx', '.docx', '.pdf', '.md']

export default function NewTopicModal({ initial, onClose, onCreate, onCreated }) {
  const [form, setForm] = useState({
    title: initial.title || '',
    description: initial.description || '',
    target_format: initial.target_format || 'DOCX',
    user_instructions: initial.user_instructions || '',
  })
  const [template, setTemplate] = useState(null)
  const [drag, setDrag] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  // Set once the workspace exists, so a failed template upload can be retried without creating a duplicate.
  const [createdId, setCreatedId] = useState(null)
  const titleRef = useRef(null)
  const fileRef = useRef(null)

  useEffect(() => {
    titleRef.current?.focus()
    const onKey = (e) => e.key === 'Escape' && !busy && close()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  })

  const close = () => (createdId ? onCreated(createdId) : onClose())

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value })

  const pickTemplate = (file) => {
    if (!file) return
    const ext = '.' + file.name.split('.').pop().toLowerCase()
    if (!TEMPLATE_TYPES.includes(ext)) {
      setError(`Unsupported template type ${ext}. Use PPTX, DOCX, PDF or MD.`)
      return
    }
    setError(null)
    setTemplate(file)
  }

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    let id = createdId
    try {
      if (!id) {
        id = await onCreate(form)
        setCreatedId(id)
      }
      if (template) await api.upload(id, template)
      onCreated(id)
    } catch (err) {
      setError(id
        ? `Topic created, but the template upload failed: ${err.message}. Choose another file or continue without one.`
        : err.message || 'Could not create the workspace.')
      setBusy(false)
    }
  }

  const submitLabel = busy
    ? (createdId || !template ? 'Creating…' : 'Creating & analysing template…')
    : createdId ? 'Retry template upload' : 'Create workspace'

  return (
    <div className="modal-scrim" onMouseDown={(e) => e.target === e.currentTarget && !busy && close()}>
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
        <div className="modal-head">
          <div>
            <span className="eyebrow"><Icon name="spark" size={14} /> New topic workspace</span>
            <h2 id="modal-title">What should the agents create?</h2>
          </div>
          <button className="icon-btn" onClick={close} aria-label="Close" disabled={busy}><Icon name="x" /></button>
        </div>

        <form onSubmit={submit} className="form">
          <label className="field">
            <span>Title</span>
            <input ref={titleRef} required value={form.title} onChange={set('title')} disabled={!!createdId}
              placeholder="e.g. Zero-Trust Security Policy" />
          </label>

          <label className="field">
            <span>Brief</span>
            <textarea required rows={3} value={form.description} onChange={set('description')} disabled={!!createdId}
              placeholder="Describe the topic, purpose and scope of the document." />
          </label>

          <fieldset className="field" disabled={!!createdId}>
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

          <div className="field">
            <span>Brand template <em>optional</em></span>
            {template ? (
              <div className="tpl-picked">
                <span className="tpl-ext">{template.name.split('.').pop().toUpperCase()}</span>
                <div className="tpl-picked-text">
                  <div className="tpl-name">{template.name}</div>
                  <div className="tpl-meta">{formatBytes(template.size)} · colours, fonts and layout will be applied</div>
                </div>
                <button type="button" className="icon-btn" onClick={() => setTemplate(null)} disabled={busy}
                  aria-label="Remove template"><Icon name="x" size={16} /></button>
              </div>
            ) : (
              <div
                className={`dropzone dropzone-compact ${drag ? 'drag' : ''}`}
                onDragOver={(e) => { e.preventDefault(); setDrag(true) }}
                onDragLeave={() => setDrag(false)}
                onDrop={(e) => { e.preventDefault(); setDrag(false); pickTemplate(e.dataTransfer.files[0]) }}
                onClick={() => fileRef.current?.click()}
                onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && fileRef.current?.click()}
                role="button"
                tabIndex={0}
              >
                <span className="drop-icon"><Icon name="upload" size={18} /></span>
                <span className="drop-text">
                  <span><b>Drop a .pptx / .docx / .pdf / .md</b> or click to browse</span>
                  <small>Without a template, a clean corporate theme is used.</small>
                </span>
              </div>
            )}
            <input ref={fileRef} type="file" accept={TEMPLATE_TYPES.join(',')} hidden
              onChange={(e) => { pickTemplate(e.target.files[0]); e.target.value = '' }} />
          </div>

          <label className="field">
            <span>Instructions <em>optional</em></span>
            <textarea rows={2} value={form.user_instructions} onChange={set('user_instructions')} disabled={!!createdId}
              placeholder="Audience, tone, must-have sections…" />
          </label>

          {error && <div className="banner banner-error"><Icon name="alert" /> {error}</div>}

          <div className="modal-actions">
            <button type="button" className="btn btn-ghost" onClick={close} disabled={busy}>
              {createdId ? 'Continue without template' : 'Cancel'}
            </button>
            <button type="submit" className="btn btn-primary" disabled={busy || (createdId && !template)}>
              {busy && <span className="spinner" />}
              {submitLabel} {!busy && <Icon name="arrow" size={16} />}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
