import { useEffect, useMemo, useRef, useState } from 'react'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { api, getToken } from '../api'
import Icon from './Icon'
import { FORMATS } from '../constants'

// Renders the compiled preview file in its real format: slides, Word pages, the PDF itself, or markdown.
export default function FormatPreview({ preview, loading, error, format, onRetry, onFallback }) {
  const fmt = FORMATS[format] || FORMATS.DOCX

  if (loading) {
    return (
      <div className="fp-state">
        <span className="spinner" />
        <b>Building your {fmt.label} preview…</b>
        <small>Compiling the real {fmt.ext} file so you can review exactly what you'll receive.</small>
      </div>
    )
  }
  if (error) {
    return (
      <div className="fp-state fp-error">
        <Icon name="alert" size={22} />
        <b>Couldn't build the preview</b>
        <small>{error}</small>
        <button className="btn btn-ghost" onClick={onRetry}><Icon name="refresh" size={15} /> Try again</button>
      </div>
    )
  }
  if (!preview) return null

  const count = preview.page_or_slide_count
  const caption = (
    <div className="fp-caption">
      <span><b>{preview.file_name}</b></span>
      <span>
        {format === 'PPT' ? `${count} slides${preview.notes_count ? ` · speaker notes on ${preview.notes_count}` : ''} · scroll to see all` : format === 'MD' ? 'Markdown file' : `~${count} pages · scroll to see all`}
        {preview.renderer === 'pdf' && (
          <> · <a href={api.fileUrl(preview.pdf_url || preview.file_url)} target="_blank" rel="noreferrer">Open in new tab</a></>
        )}
      </span>
    </div>
  )

  switch (preview.renderer) {
    case 'pdf':
      return <>{caption}<iframe className="fp-pdf" title={`${fmt.label} preview`} src={api.fileUrl(preview.pdf_url || preview.file_url)} /></>
    case 'pptx':
      return <div className="fp-scroll">{caption}<PptxView url={api.fileUrl(preview.file_url)} onFallback={onFallback} /></div>
    case 'docx':
      return <div className="fp-scroll">{caption}<DocxView url={api.fileUrl(preview.file_url)} onFallback={onFallback} /></div>
    default:
      return <>{caption}<MarkdownView markdown={preview.content_markdown} /></>
  }
}

function useFileBuffer(url) {
  const [state, setState] = useState({ buffer: null, error: null })
  useEffect(() => {
    let cancelled = false
    setState({ buffer: null, error: null })
    const headers = {}
    const token = getToken?.()
    if (token) headers['Authorization'] = `Bearer ${token}`
    fetch(url, { cache: 'no-store', headers })
      .then((r) => (r.ok ? r.arrayBuffer() : Promise.reject(new Error(`${r.status} ${r.statusText}`))))
      .then((buffer) => !cancelled && setState({ buffer, error: null }))
      .catch((e) => !cancelled && setState({ buffer: null, error: e.message }))
    return () => { cancelled = true }
  }, [url])
  return state
}

function PptxView({ url, onFallback }) {
  const hostRef = useRef(null)
  const { buffer, error } = useFileBuffer(url)
  const [renderError, setRenderError] = useState(null)

  useEffect(() => {
    const host = hostRef.current
    if (!buffer || !host) return
    let previewer
    let cancelled = false
    host.innerHTML = ''
    import('pptx-preview')
      .then(({ init }) => {
        if (cancelled) return
        const hostWidth = host.clientWidth || 960
        const width = Math.max(480, Math.min(hostWidth - 32, 1100))
        previewer = init(host, { width, height: Math.round(width * 9 / 16), mode: 'list' })
        return previewer.preview(buffer)
      })
      .catch((e) => !cancelled && setRenderError(e.message || 'Could not render the slides.'))
    return () => {
      cancelled = true
      try { previewer?.destroy() } catch { /* already torn down */ }
    }
  }, [buffer])

  if (error || renderError) {
    return (
      <div className="fp-state fp-error">
        <Icon name="alert" size={22} />
        <b>Couldn't render PowerPoint binary</b>
        <small>{error || renderError}</small>
        {onFallback && (
          <button className="btn btn-secondary btn-sm" onClick={onFallback} style={{ marginTop: 8 }}>
            <Icon name="layers" size={14} /> Switch to interactive slide view
          </button>
        )}
      </div>
    )
  }
  return <div className="fp-pptx" ref={hostRef}>{!buffer && <div className="fp-state"><span className="spinner" /></div>}</div>
}

function DocxView({ url, onFallback }) {
  const hostRef = useRef(null)
  const { buffer, error } = useFileBuffer(url)
  const [renderError, setRenderError] = useState(null)

  useEffect(() => {
    const host = hostRef.current
    if (!buffer || !host) return
    let cancelled = false
    host.innerHTML = ''
    import('docx-preview')
      .then(({ renderAsync }) => !cancelled && renderAsync(buffer, host, undefined, {
        className: 'fp-docx-page', inWrapper: true, ignoreLastRenderedPageBreak: false, breakPages: true,
      }))
      .catch((e) => !cancelled && setRenderError(e.message || 'Could not render the document.'))
    return () => { cancelled = true }
  }, [buffer])

  if (error || renderError) {
    return (
      <div className="fp-state fp-error">
        <Icon name="alert" size={22} />
        <b>Couldn't render Word document binary</b>
        <small>{error || renderError}</small>
        {onFallback && (
          <button className="btn btn-secondary btn-sm" onClick={onFallback} style={{ marginTop: 8 }}>
            <Icon name="eye" size={14} /> Switch to reading view
          </button>
        )}
      </div>
    )
  }
  return <div className="fp-docx" ref={hostRef}>{!buffer && <div className="fp-state"><span className="spinner" /></div>}</div>
}

function MarkdownView({ markdown }) {
  const html = useMemo(() => DOMPurify.sanitize(marked.parse(markdown || '')), [markdown])
  return <article className="doc" dangerouslySetInnerHTML={{ __html: html }} />
}
