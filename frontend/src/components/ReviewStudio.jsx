import { useMemo, useState } from 'react'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import Icon from './Icon'

export default function ReviewStudio({ content, metrics = {}, status, onApprove }) {
  const [tab, setTab] = useState('preview')
  const [draft, setDraft] = useState(content)
  const compiling = status === 'COMPILING'
  const delivered = status === 'COMPLETED'
  const edited = draft !== content

  const html = useMemo(() => DOMPurify.sanitize(marked.parse(draft || '')), [draft])
  const words = useMemo(() => (draft.trim() ? draft.trim().split(/\s+/).length : 0), [draft])
  const sections = useMemo(() => (draft.match(/^#{1,2}\s/gm) || []).length, [draft])

  const stats = [
    { label: 'Reading grade', value: metrics.reading_grade_level ?? '—', note: 'target 8–10' },
    { label: 'Words', value: words, note: `${sections} sections` },
    { label: 'Sentences shortened', value: metrics.sentences_shortened ?? '—', note: 'by Review Agent' },
    { label: 'Citations verified', value: metrics.verified_citations_count ?? '—', note: 'grounded facts' },
  ]

  return (
    <section className="card review" aria-labelledby="review-h">
      <div className="card-head">
        <div>
          <span className="eyebrow"><Icon name="user" size={14} /> Human-in-the-loop checkpoint</span>
          <h2 id="review-h" className="h-lg">Review the refined draft</h2>
        </div>
        <div className="tabs" role="tablist">
          <button role="tab" aria-selected={tab === 'preview'} className={tab === 'preview' ? 'on' : ''} onClick={() => setTab('preview')}>
            <Icon name="eye" size={15} /> Preview
          </button>
          <button role="tab" aria-selected={tab === 'edit'} className={tab === 'edit' ? 'on' : ''} onClick={() => setTab('edit')}>
            <Icon name="pen" size={15} /> Edit markdown
          </button>
        </div>
      </div>

      {metrics.llm_mode === 'fallback' && (
        <div className="banner banner-warn review-warn" role="alert">
          <Icon name="alert" /> This draft is offline <b>sample content</b>, not written for your topic. Add a valid{' '}
          <code>GROQ_API_KEY</code> to <code>backend/.env</code>, restart the server, then click Regenerate.
        </div>
      )}

      <div className="stats">
        {stats.map((s) => (
          <div key={s.label} className="stat">
            <span className="stat-value">{s.value}</span>
            <span className="stat-label">{s.label}</span>
            <span className="stat-note">{s.note}</span>
          </div>
        ))}
      </div>

      <div className="doc-frame">
        {tab === 'preview' ? (
          <article className="doc" dangerouslySetInnerHTML={{ __html: html }} />
        ) : (
          <textarea className="doc-editor" value={draft} onChange={(e) => setDraft(e.target.value)}
            spellCheck="true" aria-label="Refined markdown content" />
        )}
      </div>

      <div className="review-actions">
        <span className="hint">
          {edited ? <><Icon name="pen" size={14} /> Your edits will be compiled.</>
            : delivered ? 'Delivered. Edit the markdown to recompile.' : 'Nothing is compiled until you approve.'}
        </span>
        <div className="review-buttons">
          {edited && <button className="btn btn-ghost" onClick={() => setDraft(content)} disabled={compiling}>Discard edits</button>}
          <button className={`btn btn-success btn-lg ${compiling ? 'is-busy' : ''}`} onClick={() => onApprove(draft)}
            disabled={compiling || (delivered && !edited)}>
            {compiling ? <><span className="spinner" /> Compiling…</>
              : delivered ? <><Icon name="refresh" /> Recompile with edits</>
                : <><Icon name="check" /> Approve &amp; compile</>}
          </button>
        </div>
      </div>
    </section>
  )
}
