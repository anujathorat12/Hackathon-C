import { api } from '../api'
import Icon from './Icon'
import { FORMATS, formatBytes, formatTime } from '../constants'

export default function DeliverableVault({ deliverable: d }) {
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
        <span className="mod-tag mod-C">Compiled by Module C</span>
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
            </div>
            <a className="btn btn-primary btn-lg" href={api.fileUrl(d.download_url)} download={d.file_name}>
              <Icon name="download" /> Download {fmt.ext}
            </a>
          </div>
        </div>

        <div className="a11y">
          <div className={`a11y-badge ${d.wcag_compliant ? 'pass' : 'warn'}`}>
            <Icon name="shield" size={26} />
            <div>
              <strong>WCAG 2.2 AA</strong>
              <span>{d.wcag_compliant ? 'Accessibility audit passed' : 'Needs attention'}</span>
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
    </section>
  )
}
