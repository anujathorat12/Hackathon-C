import { useEffect, useMemo, useState, useCallback, useRef } from 'react'
import { parseMarkdownToSlides } from '../utils/slideParser'
import { api } from '../api'
import Icon from './Icon'

export default function SlideDeckPreview({
  markdown = '',
  title = 'Presentation',
  topicId,
  deliverable,
  templateGuidance,
  status,
}) {
  const [activeSlide, setActiveSlide] = useState(0)
  const [viewMode, setViewMode] = useState('deck') // 'deck' | 'grid'
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [compiledSlides, setCompiledSlides] = useState(null)
  const [deliverableGuidance, setDeliverableGuidance] = useState(null)
  const containerRef = useRef(null)

  // Fetch exact compiled slides if deliverable exists
  useEffect(() => {
    let cancelled = false
    if (topicId && deliverable?.file_name) {
      fetch(`/api/v1/workspaces/${topicId}/deliverable/preview`)
        .then((r) => (r.ok ? r.json() : null))
        .then((data) => {
          if (!cancelled && data?.success) {
            if (data.slides?.length) setCompiledSlides(data.slides)
            if (data.template_guidance) setDeliverableGuidance(data.template_guidance)
          }
        })
        .catch(() => {})
    }
    return () => {
      cancelled = true
    }
  }, [topicId, deliverable?.file_name])

  // Resolve active template guidance and brand variables
  const activeGuidance = templateGuidance || deliverableGuidance
  const palette = activeGuidance?.color_palette || {}
  const primaryColor = palette.primary_hex || '#0A192F'
  const accentColor = palette.accent_hex || '#00e5ff'
  const secondaryColor = palette.secondary_hex || '#64748b'
  const fontFamily = activeGuidance?.font_family
  const templateName = activeGuidance?.source_file_name

  const themeVars = useMemo(() => ({
    '--slide-primary': primaryColor,
    '--slide-accent': accentColor,
    '--slide-secondary': secondaryColor,
    '--slide-cover-bg': primaryColor,
    '--slide-body-bg': '#FBFDFF',
    ...(fontFamily ? { '--slide-font': `"${fontFamily}", var(--display)` } : {}),
  }), [primaryColor, accentColor, secondaryColor, fontFamily])

  // Parse markdown into slides
  const parsedSlides = useMemo(() => {
    return parseMarkdownToSlides(markdown, title)
  }, [markdown, title])

  // Normalize compiled slides into the same shape if available
  const slides = useMemo(() => {
    if (compiledSlides && compiledSlides.length > 0) {
      return compiledSlides.map((s, idx) => ({
        slideNumber: s.slide_number || idx + 1,
        isCover: s.is_cover ?? idx === 0,
        title: s.title || (idx === 0 ? title : `Slide ${idx + 1}`),
        subtitle: s.subtitle || '',
        pillBadge: s.pill_badge || 'SYSTEM DELIVERABLE • AGENT-101',
        metadata: s.metadata || '',
        cards: s.cards || [],
        statCards: s.stat_cards || [],
        table: s.table || null,
        fact: s.fact || null,
        footerLeft: s.footer_left || 'AGENT-101 • Multi-Agent Autonomous Content Synthesis System',
        footerRight: s.footer_right || `SLIDE ${idx + 1}`,
      }))
    }
    return parsedSlides
  }, [compiledSlides, parsedSlides, title])

  // Clamp active slide
  const currentIdx = Math.min(Math.max(0, activeSlide), Math.max(0, slides.length - 1))
  const currentSlide = slides[currentIdx] || slides[0]

  const prevSlide = useCallback(() => {
    setActiveSlide((prev) => Math.max(0, prev - 1))
  }, [])

  const nextSlide = useCallback(() => {
    setActiveSlide((prev) => Math.min(slides.length - 1, prev + 1))
  }, [slides.length])

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'ArrowLeft') {
        prevSlide()
      } else if (e.key === 'ArrowRight' || (e.key === ' ' && isFullscreen)) {
        nextSlide()
      } else if (e.key === 'Escape' && isFullscreen) {
        setIsFullscreen(false)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [prevSlide, nextSlide, isFullscreen])

  const renderSlideContent = (slide, idx, isThumb = false) => {
    if (!slide) return null

    if (slide.isCover) {
      return (
        <div className={`slide-canvas slide-cover ${isThumb ? 'is-thumb' : ''}`} style={themeVars}>
          <div className="slide-cover-pillar" />
          <div className="slide-cover-body">
            <div className="slide-cover-badge">
              <span className="badge-dot" />
              {slide.pillBadge || 'SYSTEM DELIVERABLE • AGENT-101'}
            </div>
            <h1 className="slide-cover-title">{slide.title || title}</h1>
            <p className="slide-cover-sub">
              {slide.subtitle ||
                'Autonomous Multi-Agent AI Content Generation & Synthesis System\nStrict Topic Isolation • Native Binary Architecture • WCAG 2.2 Level AA'}
            </p>
            <div className="slide-cover-meta">
              <span>{slide.metadata || `VERSION 1.0   |   AUTHOR: AGENT-101   |   16:9 WIDESCREEN`}</span>
            </div>
          </div>
        </div>
      )
    }

    return (
      <div className={`slide-canvas slide-content ${isThumb ? 'is-thumb' : ''}`} style={themeVars}>
        <div className="slide-header">
          <h2 className="slide-title">{slide.title}</h2>
          <div className="slide-accent-bar" />
        </div>

        <div className="slide-body">
          {/* KPI Stat Cards if detected */}
          {slide.statCards && slide.statCards.length > 0 ? (
            <div className="slide-stats-grid">
              {slide.statCards.map((sc, i) => (
                <div key={i} className="slide-stat-card">
                  <div className="stat-card-pill" />
                  <span className="stat-card-label">{sc.title}</span>
                  <strong className="stat-card-number">{sc.number}</strong>
                  {sc.desc && <span className="stat-card-desc">{sc.desc}</span>}
                </div>
              ))}
            </div>
          ) : null}

          {/* Table if present */}
          {slide.table ? (
            <div className="slide-table-wrap">
              <table className="slide-table">
                <thead>
                  <tr>
                    {slide.table.headers.map((h, i) => (
                      <th key={i}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {slide.table.rows.map((row, rIdx) => (
                    <tr key={rIdx}>
                      {row.map((cell, cIdx) => (
                        <td key={cIdx}>{cell}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}

          {/* Structured Content Cards */}
          {slide.cards && slide.cards.length > 0 ? (
            <div className="slide-cards-list">
              {slide.cards.map((cardText, i) => (
                <div key={i} className="slide-card-item">
                  <span className="card-item-dot" />
                  <span className="card-item-text">{cardText}</span>
                </div>
              ))}
            </div>
          ) : null}

          {/* Fact / Grounded Citation Callout */}
          {slide.fact ? (
            <div className="slide-fact-callout">
              <Icon name="shield" size={15} />
              <span>{slide.fact}</span>
            </div>
          ) : null}
        </div>

        <div className="slide-footer">
          <div className="slide-footer-line" />
          <div className="slide-footer-info">
            <span className="footer-left">
              {slide.footerLeft || 'AGENT-101 • Multi-Agent Autonomous Content Synthesis System'}
            </span>
            <span className="footer-right">
              {slide.footerRight || `SLIDE ${idx !== undefined ? idx + 1 : slide.slideNumber}`}
            </span>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      className={`slide-deck-viewer ${isFullscreen ? 'is-fullscreen' : ''}`}
      tabIndex={0}
      aria-label="PowerPoint presentation preview"
    >
      {/* Presentation Control Bar */}
      <div className="deck-toolbar">
        <div className="deck-toolbar-left">
          <span className="deck-badge">
            <Icon name="layers" size={14} /> 16:9 Presentation Deck
          </span>
          {templateName && (
            <span className="deck-pill-template" title={`Reference Template: ${templateName}`}>
              <Icon name="palette" size={13} /> {templateName.length > 22 ? templateName.slice(0, 19) + '…' : templateName}
            </span>
          )}
          {compiledSlides ? (
            <span className="deck-pill-live" title="Rendered from the compiled .pptx file">
              <Icon name="check" size={13} /> Native PPTX Deliverable
            </span>
          ) : (
            <span className="deck-pill-draft" title="Interactive preview rendered from refined draft">
              <Icon name="eye" size={13} /> Draft Slide Deck
            </span>
          )}
          <span className="deck-counter">
            Slide <b>{currentIdx + 1}</b> of <b>{slides.length}</b>
          </span>
        </div>

        <div className="deck-toolbar-center">
          <button
            type="button"
            className="deck-nav-btn"
            onClick={prevSlide}
            disabled={currentIdx === 0}
            title="Previous slide (Left Arrow)"
          >
            <Icon name="chevron-left" size={16} /> Prev
          </button>
          <div className="deck-dots">
            {slides.map((_, i) => (
              <button
                key={i}
                type="button"
                className={`deck-dot ${i === currentIdx ? 'active' : ''}`}
                onClick={() => setActiveSlide(i)}
                title={`Go to slide ${i + 1}`}
              />
            ))}
          </div>
          <button
            type="button"
            className="deck-nav-btn"
            onClick={nextSlide}
            disabled={currentIdx === slides.length - 1}
            title="Next slide (Right Arrow)"
          >
            Next <Icon name="chevron-right" size={16} />
          </button>
        </div>

        <div className="deck-toolbar-right">
          <div className="view-mode-toggle">
            <button
              type="button"
              className={`mode-btn ${viewMode === 'deck' ? 'active' : ''}`}
              onClick={() => setViewMode('deck')}
              title="Single slide presentation deck"
            >
              <Icon name="layers" size={14} /> Deck
            </button>
            <button
              type="button"
              className={`mode-btn ${viewMode === 'grid' ? 'active' : ''}`}
              onClick={() => setViewMode('grid')}
              title="All slides grid overview"
            >
              <Icon name="grid" size={14} /> Grid ({slides.length})
            </button>
          </div>

          <button
            type="button"
            className="deck-action-btn"
            onClick={() => setIsFullscreen(!isFullscreen)}
            title={isFullscreen ? 'Exit presentation mode (Esc)' : 'Enter full presentation mode'}
          >
            <Icon name={isFullscreen ? 'minimize' : 'maximize'} size={15} />
            <span>{isFullscreen ? 'Exit' : 'Present'}</span>
          </button>
        </div>
      </div>

      {/* Main View Area */}
      {viewMode === 'deck' ? (
        <div className="deck-stage">
          <div className="slide-frame-outer">
            {renderSlideContent(currentSlide, currentIdx, false)}
          </div>

          {/* Quick Jump Thumbnail Strip */}
          <div className="deck-thumbnails-strip">
            {slides.map((slide, i) => (
              <button
                key={i}
                type="button"
                className={`thumb-card ${i === currentIdx ? 'is-active' : ''}`}
                onClick={() => setActiveSlide(i)}
                title={`Slide ${i + 1}: ${slide.title}`}
              >
                <div className="thumb-preview">
                  {renderSlideContent(slide, i, true)}
                </div>
                <div className="thumb-label">
                  <span className="thumb-num">{i + 1}</span>
                  <span className="thumb-name">{slide.title}</span>
                </div>
              </button>
            ))}
          </div>
        </div>
      ) : (
        /* Grid Overview Mode */
        <div className="deck-grid-view">
          <div className="grid-instructions">
            <span>Click any slide to jump into presentation view</span>
          </div>
          <div className="grid-slides-container">
            {slides.map((slide, i) => (
              <div
                key={i}
                className={`grid-slide-item ${i === currentIdx ? 'is-current' : ''}`}
                onClick={() => {
                  setActiveSlide(i)
                  setViewMode('deck')
                }}
              >
                <div className="grid-slide-header">
                  <span className="grid-slide-badge">Slide {i + 1}</span>
                  <span className="grid-slide-title-preview">{slide.title}</span>
                </div>
                <div className="grid-slide-content">
                  {renderSlideContent(slide, i, true)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
