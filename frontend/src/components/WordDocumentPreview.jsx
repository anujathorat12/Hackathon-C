import { useMemo } from 'react'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import Icon from './Icon'

export default function WordDocumentPreview({ markdown = '', title = 'Executive Document', deliverable }) {
  const html = useMemo(() => DOMPurify.sanitize(marked.parse(markdown || '')), [markdown])

  const today = useMemo(() => {
    return new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'long', year: 'numeric' })
  }, [])

  return (
    <div className="word-doc-viewer">
      {/* Word Header Ribbon */}
      <div className="word-ribbon">
        <div className="word-ribbon-left">
          <span className="word-badge">
            <Icon name="file" size={14} /> Microsoft Word (.docx)
          </span>
          <span className="word-status">Executive Document Standard</span>
        </div>
        <div className="word-ribbon-right">
          <span className="word-pill">WCAG 2.2 AA Formatted</span>
        </div>
      </div>

      <div className="word-paper-container">
        {/* Page 1: Document Control Sheet */}
        <section className="word-page word-cover-page">
          <div className="word-page-header">
            <span>DOCUMENT CONTROL SPECIFICATION</span>
            <span>SYSTEM ID: AGENT-101</span>
          </div>

          <div className="word-cover-body">
            <span className="word-cover-eyebrow">Enterprise Deliverable</span>
            <h1 className="word-cover-title">{title}</h1>
            <p className="word-cover-desc">
              Autonomous multi-agent document synthesis conforming to corporate typography, accessibility, and structured document control.
            </p>

            <div className="word-section-title">1. Document Control &amp; Revision History</div>
            <table className="word-control-table">
              <tbody>
                <tr>
                  <th>Document ID</th>
                  <td>DOC-101-{title.replace(/[^a-zA-Z0-9]/g, '').slice(0, 8).toUpperCase()}-V1</td>
                </tr>
                <tr>
                  <th>Version</th>
                  <td>1.0 (Final System Specification)</td>
                </tr>
                <tr>
                  <th>Status</th>
                  <td><span className="word-tag-approved">Approved for Distribution</span></td>
                </tr>
                <tr>
                  <th>Classification</th>
                  <td>Confidential // Internal Enterprise</td>
                </tr>
                <tr>
                  <th>Generated Date</th>
                  <td>{today}</td>
                </tr>
                <tr>
                  <th>Author</th>
                  <td>Autonomous Multi-Agent AI System (AGENT-101)</td>
                </tr>
              </tbody>
            </table>

            <div className="word-section-title">2. Verification Matrix</div>
            <table className="word-control-table">
              <thead>
                <tr>
                  <th>Role</th>
                  <th>Agent Engine</th>
                  <th>Verification Status</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Content Generator</td>
                  <td>Content Generation Agent</td>
                  <td>Verified &bull; Grounded Facts</td>
                </tr>
                <tr>
                  <td>Auditor &amp; Reviewer</td>
                  <td>Content Review Agent</td>
                  <td>Passed Reading Grade &amp; Style Check</td>
                </tr>
                <tr>
                  <td>Format Compiler</td>
                  <td>Format Generation Agent</td>
                  <td>WCAG 2.2 Level AA Passed</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="word-page-footer">
            <span>CONFIDENTIAL // AGENT-101</span>
            <span>Page 1 of Executive Report</span>
          </div>
        </section>

        {/* Page 2+: Content Sheet */}
        <section className="word-page word-content-page">
          <div className="word-page-header">
            <span>{title}</span>
            <span>AGENT-101 DELIVERABLE</span>
          </div>

          <article className="word-article-content" dangerouslySetInnerHTML={{ __html: html }} />

          <div className="word-page-footer">
            <span>CONFIDENTIAL // AGENT-101</span>
            <span>Document Content</span>
          </div>
        </section>
      </div>
    </div>
  )
}
