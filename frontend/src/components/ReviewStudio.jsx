import { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import Icon from './Icon'
import FormatPreview from './FormatPreview'
import { RunValue } from './ValueMeter'
import AskAI from './AskAI'
import { FORMATS } from '../constants'

function SourceCheck({ check }) {
  const issues = check.unmatched.length + check.uncited_figures.length
  return (
    <div className={`src-check ${issues ? 'warn' : ''}`}>
      <div className="src-check-head">
        <Icon name={issues ? 'alert' : 'shield'} size={16} />
        {check.total
          ? `${check.matched} of ${check.total} citations point to your uploaded sources` +
            (check.passages ? ` (${check.passages} distinct passage${check.passages > 1 ? 's' : ''})` : '')
          : 'No citations found — the draft does not reference your sources'}
      </div>
      {check.unmatched.length > 0 && (
        <ul>{check.unmatched.map((c) => <li key={c}>Not found in your sources: <b>[{c}]</b></li>)}</ul>
      )}
      {check.uncited_figures.length > 0 && (
        <>
          <ul>{check.uncited_figures.map((c) => <li key={c}>Figure without a citation: “{c}”</li>)}</ul>
          <small>Check these against your documents, or ask the AI to remove unsupported figures.</small>
        </>
      )}
    </div>
  )
}

export default function ReviewStudio({ topicId, format, content, metrics = {}, status, onApprove }) {
  const fmt = FORMATS[format] || FORMATS.DOCX
  const [tab, setTab] = useState('preview')
  const [draft, setDraft] = useState(content)
  const [preview, setPreview] = useState(null)
  const [previewing, setPreviewing] = useState(false)
  const [previewError, setPreviewError] = useState(null)
  const [history, setHistory] = useState([])
  const [lastSummary, setLastSummary] = useState(null)
  const compiling = status === 'COMPILING'
  const delivered = status === 'COMPLETED'
  const edited = draft !== content
  // The preview reflects the markdown it was built from; edits after that make it stale.
  const stale = !!preview && preview.content_markdown !== draft

  const words = useMemo(() => (draft.trim() ? draft.trim().split(/\s+/).length : 0), [draft])
  const sections = useMemo(() => (draft.match(/^#{1,2}\s/gm) || []).length, [draft])

  const buildPreview = useCallback(async (markdown) => {
    setPreviewing(true)
    setPreviewError(null)
    try {
      setPreview(await api.preview(topicId, markdown))
    } catch (e) {
      setPreviewError(e.message)
    } finally {
      setPreviewing(false)
    }
  }, [topicId])

  // Build the real-format preview as soon as the review opens (and when the approved content changes),
  // but not again for markdown the current preview already shows.
  const builtFor = preview?.content_markdown
  useEffect(() => {
    if (builtFor !== content) buildPreview(content)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [buildPreview, content])

  const refresh = () => {
    setTab('preview')
    buildPreview(draft)
  }

  const applyRevision = (markdown, summary) => {
    setHistory((h) => [...h, draft])
    setDraft(markdown)
    setLastSummary(summary)
    setTab('preview')
    buildPreview(markdown)
  }

  const undoRevision = () => {
    const previous = history[history.length - 1]
    if (previous === undefined) return
    setHistory((h) => h.slice(0, -1))
    setDraft(previous)
    setLastSummary('Last AI revision undone.')
    buildPreview(previous)
  }

  const unit = format === 'PPT' ? 'slides' : format === 'MD' ? 'file' : 'pages'
  const stats = [
    { label: 'Reading grade', value: metrics.reading_grade_level || '—', note: metrics.reading_grade_level ? (metrics.initial_reading_grade_level ? `target 8–10 · draft was ${metrics.initial_reading_grade_level}` : 'target 8–10') : 'measured for English only' },
    { label: 'Words', value: words, note: `${sections} sections` },
    { label: format === 'PPT' ? 'Slides' : 'Pages', value: preview && format !== 'MD' ? preview.page_or_slide_count : '—', note: format === 'PPT' ? 'in the deck' : 'approximate' },
    { label: 'Citations', value: metrics.citations_count ?? '—', note: 'distinct sources cited in text' },
  ]

  return (
    <section className="card review" aria-labelledby="review-h">
      <div className="card-head">
        <div>
          <span className="eyebrow"><Icon name="user" size={14} /> Human-in-the-loop checkpoint</span>
          <h2 id="review-h" className="h-lg">Review your {fmt.label} before approving</h2>
        </div>
        <div className="tabs" role="tablist">
          <button role="tab" aria-selected={tab === 'preview'} className={tab === 'preview' ? 'on' : ''} onClick={() => setTab('preview')}>
            <Icon name="eye" size={15} /> {fmt.label} preview
          </button>
          <button role="tab" aria-selected={tab === 'edit'} className={tab === 'edit' ? 'on' : ''} onClick={() => setTab('edit')}>
            <Icon name="pen" size={15} /> Edit content
          </button>
        </div>
      </div>

      {metrics.llm_mode === 'fallback' && (
        <div className="banner banner-warn review-warn" role="alert">
          <Icon name="alert" /> This draft is offline <b>sample content</b>, not written for your topic. Add a valid{' '}
          <code>GROQ_API_KEY</code> to <code>backend/.env</code>, restart the server, then click Regenerate.
        </div>
      )}

      <RunValue value={metrics.value} />

      {metrics.citation_check && <SourceCheck check={metrics.citation_check} />}

      <div className="stats">
        {stats.map((s) => (
          <div key={s.label} className="stat">
            <span className="stat-value">{s.value}</span>
            <span className="stat-label">{s.label}</span>
            <span className="stat-note">{s.note}</span>
          </div>
        ))}
      </div>

      <AskAI topicId={topicId} format={format} draft={draft} disabled={compiling || previewing}
        onRevised={applyRevision} onUndo={undoRevision} canUndo={history.length > 0} lastSummary={lastSummary} />

      {stale && !previewing && (
        <div className="banner banner-info">
          <Icon name="refresh" size={16} /> You've edited the content since this preview was built.
          <button className="btn btn-ghost btn-sm" onClick={refresh}><Icon name="refresh" size={14} /> Refresh preview</button>
        </div>
      )}

      <div className={`doc-frame ${tab === 'preview' ? `fp-frame fp-${format}` : ''}`}>
        {tab === 'preview' ? (
          <FormatPreview preview={preview} loading={previewing} error={previewError} format={format} onRetry={refresh} />
        ) : (
          <textarea className="doc-editor" value={draft} onChange={(e) => setDraft(e.target.value)}
            spellCheck="true" aria-label="Document content (markdown)" />
        )}
      </div>

      <div className="review-actions">
        <span className="hint">
          {edited ? <><Icon name="pen" size={14} /> Your edits will be included.</>
            : delivered ? `Delivered. Edit the content to produce a new version.`
              : `This is the exact ${fmt.ext} you'll download (${unit}). Nothing is final until you approve.`}
        </span>
        <div className="review-buttons">
          {edited && (
            <button className="btn btn-ghost" onClick={() => setDraft(content)} disabled={compiling || previewing}>
              Discard edits
            </button>
          )}
          {stale && (
            <button className="btn btn-ghost" onClick={refresh} disabled={previewing || compiling}>
              <Icon name="refresh" size={15} /> Refresh preview
            </button>
          )}
          <button className={`btn btn-success btn-lg ${compiling ? 'is-busy' : ''}`} onClick={() => onApprove(draft)}
            disabled={compiling || previewing || (delivered && !edited)}>
            {compiling ? <><span className="spinner" /> Finalising…</>
              : delivered ? <><Icon name="refresh" /> Approve new version</>
                : <><Icon name="check" /> Approve &amp; finalise</>}
          </button>
        </div>
      </div>
    </section>
  )
}
