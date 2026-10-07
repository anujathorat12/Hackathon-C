import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import Icon from './Icon'
import { FORMATS, LANGUAGES, formatBytes } from '../constants'

const TEMPLATE_TYPES = ['.pptx', '.docx', '.pdf', '.md']
const SOURCE_TYPES = ['.pdf', '.docx', '.txt', '.md']

export default function NewTopicModal({ initial, onClose, onCreate, onCreated }) {
  const [form, setForm] = useState({
    title: initial.title || '',
    description: initial.description || '',
    target_format: initial.target_format || 'DOCX',
    user_instructions: initial.user_instructions || '',
    language: initial.language || 'English',
  })
  const [template, setTemplate] = useState(null)
  const [sources, setSources] = useState([])
  const [srcDrag, setSrcDrag] = useState(false)
  const [drag, setDrag] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  // Set once the workspace exists, so a failed template upload can be retried without creating a duplicate.
  const [createdId, setCreatedId] = useState(null)
  const titleRef = useRef(null)
  const fileRef = useRef(null)
  const srcRef = useRef(null)

  // Focus the title once when the dialog opens (not on every re-render, which would steal focus while typing).
  useEffect(() => {
    titleRef.current?.focus()
  }, [])

  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && !busy && close()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  })

  const close = () => (createdId ? onCreated(createdId) : onClose())

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value })
  const complexScript = LANGUAGES.find((l) => l.value === form.language)?.complex

  const setLanguage = (e) => {
    const language = e.target.value
    const complex = LANGUAGES.find((l) => l.value === language)?.complex
    setForm({ ...form, language, target_format: complex && form.target_format === 'PDF' ? 'DOCX' : form.target_format })
  }

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

  const addSources = (fileList) => {
    const files = [...(fileList || [])]
    const bad = files.filter((f) => !SOURCE_TYPES.includes('.' + f.name.split('.').pop().toLowerCase()))
    if (bad.length) setError(`Skipped ${bad.map((f) => f.name).join(', ')} — sources must be PDF, DOCX, TXT or MD.`)
    const good = files.filter((f) => !bad.includes(f))
    setSources((list) => [...list, ...good.filter((f) => !list.some((x) => x.name === f.name))].slice(0, 10))
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
      if (template) {
        await api.upload(id, template)
        setTemplate(null)
      }
      // Upload sources one by one; keep any that fail in the list so they can be retried.
      const failed = []
      for (const file of sources) {
        try {
          await api.uploadSource(id, file)
        } catch (err) {
          failed.push({ file, message: err.message })
        }
      }
      setSources(failed.map((f) => f.file))
      if (failed.length) {
        setError(`Topic created, but some sources couldn't be read: ${failed.map((f) => `${f.file.name} (${f.message})`).join('; ')}`)
        setBusy(false)
        return
      }
      onCreated(id)
    } catch (err) {
      setError(id
        ? `Topic created, but the template upload failed: ${err.message}. Choose another file or continue without one.`
        : err.message || 'Could not create the workspace.')
      setBusy(false)
    }
  }

  const submitLabel = busy
    ? (sources.length ? 'Creating & reading sources…' : template ? 'Creating & analysing template…' : 'Creating…')
    : createdId ? 'Retry uploads' : 'Create workspace'

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
                <label key={key} className={`format-opt ${form.target_format === key ? 'on' : ''} ${complexScript && key === 'PDF' ? 'off' : ''}`}
                  style={{ '--fmt': f.color }} title={complexScript && key === 'PDF' ? 'PDF is available for Latin-script languages; use Word or PowerPoint' : undefined}>
                  <input type="radio" name="fmt" value={key} checked={form.target_format === key} onChange={set('target_format')}
                    disabled={complexScript && key === 'PDF'} />
                  <span className="format-ext">{f.ext}</span>
                  <span className="format-name">{f.label}</span>
                  <span className="format-hint">{f.hint}</span>
                </label>
              ))}
            </div>
          </fieldset>

          <label className="field">
            <span>Language</span>
            <select value={form.language} onChange={setLanguage} disabled={!!createdId}>
              {LANGUAGES.map((l) => <option key={l.value} value={l.value}>{l.label}</option>)}
            </select>
            {complexScript && <small className="field-hint">Word, PowerPoint and Markdown support {form.language} fully. PDF is limited to Latin-script languages.</small>}
          </label>

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

          <div className="field">
            <span>Source documents <em>optional · the AI writes only from these and cites them</em></span>
            <div
              className={`dropzone dropzone-compact ${srcDrag ? 'drag' : ''}`}
              onDragOver={(e) => { e.preventDefault(); setSrcDrag(true) }}
              onDragLeave={() => setSrcDrag(false)}
              onDrop={(e) => { e.preventDefault(); setSrcDrag(false); addSources(e.dataTransfer.files) }}
              onClick={() => srcRef.current?.click()}
              onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && srcRef.current?.click()}
              role="button"
              tabIndex={0}
            >
              <span className="drop-icon"><Icon name="folder" size={18} /></span>
              <span className="drop-text">
                <span><b>Drop reports, policies or notes</b> (.pdf / .docx / .txt / .md)</span>
                <small>Each fact will cite the file and page, e.g. [report.pdf, p.3]. Up to 10 files.</small>
              </span>
            </div>
            <input ref={srcRef} type="file" multiple accept={SOURCE_TYPES.join(',')} hidden
              onChange={(e) => { addSources(e.target.files); e.target.value = '' }} />
            {sources.length > 0 && (
              <div className="src-list">
                {sources.map((f) => (
                  <span key={f.name} className="chip chip-cyan">
                    <Icon name="file" size={12} /> {f.name} · {formatBytes(f.size)}
                    <button type="button" className="chip-x" onClick={() => setSources((l) => l.filter((x) => x !== f))}
                      disabled={busy} aria-label={`Remove ${f.name}`}><Icon name="x" size={12} /></button>
                  </span>
                ))}
              </div>
            )}
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
            <button type="submit" className="btn btn-primary" disabled={busy || (createdId && !template && !sources.length)}>
              {busy && <span className="spinner" />}
              {submitLabel} {!busy && <Icon name="arrow" size={16} />}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
