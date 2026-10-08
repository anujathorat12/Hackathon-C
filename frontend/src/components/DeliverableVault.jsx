import { useState } from 'react'
import { api } from '../api'
import Icon from './Icon'
import { FORMATS, formatBytes, formatTime } from '../constants'
import SlideDeckPreview from './SlideDeckPreview'
import WordDocumentPreview from './WordDocumentPreview'

export default function DeliverableVault({ deliverable: d, versions = [], topicId, refinedContent = '', title = 'Deliverable' }) {
  const [showPreview, setShowPreview] = useState(false)
  const fmt = FORMATS[d.format] || FORMATS.DOCX
  const report = d.accessibility_report || {}
  const checks = [
    { label: 'Contrast ratio', value: report.contrast_ratio ? `${Number(report.contrast_ratio).toFixed(1)}:1` : '—', ok: (report.contrast_ratio ?? 0) >= 4.5 },
    { label: 'Heading order', value: report.heading_order_valid ? 'Valid' : 'Issues', ok: !!report.heading_order_valid },
    { label: 'Table headers', value: report.table_headers_tagged ? 'Tagged' : 'Missing', ok: !!report.table_headers_tagged },
  ]
  const unitLabel = d.format === 'PPT' ? 'slides' : 'pages'

  return (
    <section className="card vault" aria-labelledby="vault-h">
      <div className="vault-glow" aria-hidden="true" />
      <div className="card-head">
        <div>
          <span className="eyebrow eyebrow-green"><Icon name="check" size={14} /> Deliverable ready</span>
          <h2 id="vault-h" className="h-lg">Deliverable vault</h2>
        </div>
        <span className="tag tag-fmt" style={{ '--fmt': fmt.color }}>Native {fmt.label} file</span>
      </div>

      <div className="vault-body">
        <div className="file-card" style={{ '--fmt': fmt.color }}>
          <div className="file-glyph">
            <Icon name="file" size={40} strokeWidth={1.4} />
            <span>{fmt.ext}</span>
          </div>
          <div className="file-info">
            <div className="file-name">{d.file_name}</div>
            <div className="file-meta">
              <span>{fmt.label}</span>
              <span>{formatBytes(d.file_size_bytes)}</span>
              <span>~{d.page_or_slide_count} {unitLabel}</span>
              <span>Compiled {formatTime(d.compiled_at)}</span>
              {d.version && <span>Version {d.version}</span>}
            </div>
            <div className="file-card-buttons">
              <a className="btn btn-primary btn-lg" href={api.fileUrl(d.download_url)} download={d.file_name}>
                <Icon name="download" /> Download {fmt.ext}
              </a>
              <button
                type="button"
                className={`btn btn-secondary btn-lg ${showPreview ? 'is-active' : ''}`}
                onClick={() => setShowPreview(!showPreview)}
              >
                <Icon name={showPreview ? 'x' : 'eye'} /> {showPreview ? 'Close preview' : `Inspect ${fmt.label}`}
              </button>
            </div>
          </div>
        </div>

        <div className="a11y">
          <div className={`a11y-badge ${d.wcag_compliant ? 'pass' : 'warn'}`}>
            <Icon name="shield" size={26} />
            <div>
              <strong>Accessibility checks</strong>
              <span>{d.wcag_compliant ? 'Passed automated WCAG 2.2 AA checks' : 'Some automated checks need attention'}</span>
            </div>
          </div>
          <ul className="a11y-checks">
            {checks.map((c) => (
              <li key={c.label} className={c.ok ? 'ok' : 'bad'}>
                <Icon name={c.ok ? 'check' : 'alert'} size={15} strokeWidth={2.4} />
                <span>{c.label}</span>
                <b>{c.value}</b>
              </li>
            ))}
          </ul>
          {report.details?.length > 0 && (
            <details className="a11y-details">
              <summary>Audit log ({report.details.length})</summary>
              <ul>{report.details.map((t, i) => <li key={i}>{t}</li>)}</ul>
            </details>
          )}
        </div>
      </div>

      {versions.length > 0 && (
        <div className="versions">
          <h3><Icon name="layers" size={15} /> Version history</h3>
          <ol>
            {[...versions].reverse().map((v) => (
              <li key={v.file_name} className={v.file_name === d.file_name ? 'current' : ''}>
                <span className="v-tag">v{v.version || '1.0'}</span>
                <span className="v-note">{v.change_note || 'Approved version'}</span>
                <span className="v-time">{formatTime(v.compiled_at)}</span>
                <a href={api.fileUrl(v.download_url)} download={v.file_name} aria-label={`Download version ${v.version}`}>
                  <Icon name="download" size={15} />
                </a>
              </li>
            ))}
          </ol>
        </div>
      )}

      {showPreview && (
        <div className="vault-preview-expanded">
          <div className="vault-preview-header">
            <h3><Icon name="eye" size={16} /> Compiled Deliverable Preview ({fmt.label})</h3>
            <span className="hint">Interactive presentation rendered from compiled deliverable</span>
          </div>
          <div className="doc-frame">
            {d.format === 'PPT' ? (
              <SlideDeckPreview
                markdown={refinedContent}
                title={title}
                topicId={topicId}
                deliverable={d}
                status="COMPLETED"
              />
            ) : d.format === 'DOCX' ? (
              <WordDocumentPreview
                markdown={refinedContent}
                title={title}
                deliverable={d}
              />
            ) : (
              <div className="doc" style={{ padding: 24 }}>
                <pre style={{ whiteSpace: 'pre-wrap' }}>{refinedContent}</pre>
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  )
}
