import { useRef, useState } from 'react'
import { api } from '../api'
import Icon from './Icon'
import { formatBytes } from '../constants'

const ACCEPT = '.pptx,.docx,.pdf,.md'

export default function TemplateDropzone({ topicId, templates, onUploaded, disabled }) {
  const [drag, setDrag] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const inputRef = useRef(null)

  const upload = async (file) => {
    if (!file) return
    const ext = '.' + file.name.split('.').pop().toLowerCase()
    if (!ACCEPT.split(',').includes(ext)) {
      setError(`Unsupported file type ${ext}. Use PPTX, DOCX, PDF or MD.`)
      return
    }
    setBusy(true)
    setError(null)
    try {
      onUploaded(await api.upload(topicId, file))
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const latest = templates[templates.length - 1]
  const pal = latest?.guidance?.color_palette
  const typo = latest?.guidance?.typography

  return (
    <section className="card template" aria-labelledby="tpl-h">
      <div className="card-head">
        <h2 id="tpl-h"><Icon name="palette" /> Brand template</h2>
        <span className="mod-tag mod-C">Module C</span>
      </div>

      <div
        className={`dropzone ${drag ? 'drag' : ''} ${busy ? 'busy' : ''} ${disabled ? 'disabled' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDrag(true) }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); if (!disabled) upload(e.dataTransfer.files[0]) }}
        onClick={() => !disabled && inputRef.current?.click()}
        onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && !disabled && inputRef.current?.click()}
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-disabled={disabled}
      >
        <input ref={inputRef} type="file" accept={ACCEPT} hidden onChange={(e) => { upload(e.target.files[0]); e.target.value = '' }} />
        {busy ? (
          <><span className="spinner" /> <span>Analysing template…</span></>
        ) : (
          <>
            <span className="drop-icon"><Icon name="upload" size={20} /></span>
            <span><b>Drop a .pptx / .docx / .pdf</b> or click to browse</span>
            <small>Optional. Colours, fonts and layout are extracted and applied to the deliverable.</small>
          </>
        )}
      </div>

      {error && <div className="banner banner-error small"><Icon name="alert" size={16} /> {error}</div>}

      {latest && (
        <div className="tpl-card">
          <div className="tpl-file">
            <span className="tpl-ext">{latest.file_type}</span>
            <div>
              <div className="tpl-name">{latest.file_name}</div>
              <div className="tpl-meta">{formatBytes(latest.file_size_bytes)} · style profile extracted</div>
            </div>
          </div>
          {pal && (
            <div className="tpl-profile">
              <div className="swatches">
                {Object.entries(pal).map(([k, v]) => (
                  <span key={k} className="swatch lg" style={{ background: v }} title={`${k.replace('_hex', '')}: ${v}`} />
                ))}
              </div>
              {typo && <span className="chip chip-cyan"><Icon name="type" size={12} /> {typo.heading_font} / {typo.body_font}</span>}
            </div>
          )}
        </div>
      )}
    </section>
  )
}
