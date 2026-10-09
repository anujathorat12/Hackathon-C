import { useState } from 'react'
import Icon from './Icon'
import ShareButton from './ShareButton'

export default function LandingPage({ onOpenAuth }) {
  const [activeStep, setActiveStep] = useState(0)

  const scrollTo = (id) => {
    const el = document.getElementById(id)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  const steps = [
    {
      num: '01',
      title: 'Audience & Brief Analysis',
      desc: 'Parses your initial topic brief to identify target audiences, core business objectives, and desired executive tone.',
      badge: 'Strategy'
    },
    {
      num: '02',
      title: 'Intelligent Structuring',
      desc: 'Generates format-adaptive architectures — structured slide outlines for presentations or hierarchical sections for reports.',
      badge: 'Planning'
    },
    {
      num: '03',
      title: 'Brand & Template Ingestion',
      desc: 'Learns from your uploaded PowerPoint or Word templates to match your corporate color palette, fonts, and styling rules.',
      badge: 'Brand Styling'
    },
    {
      num: '04',
      title: 'Fact Grounding & Research',
      desc: 'Gathers verified domain facts and citations to ensure every deliverable is accurate, authoritative, and hallucination-free.',
      badge: 'Research'
    },
    {
      num: '05',
      title: 'Active-Voice Synthesis',
      desc: 'Drafts publication-ready content with strong action verbs, executive summaries, data tables, and structured takeaways.',
      badge: 'Synthesis'
    },
    {
      num: '06',
      title: 'Quality & Readability Polish',
      desc: 'Evaluates reading ease, sentence variety, and clarity, refining text to professional business standards.',
      badge: 'Editorial'
    },
    {
      num: '07',
      title: 'Native Binary Compilation',
      desc: 'Assembles approved content into genuine, fully-editable PowerPoint slides, Word documents, and high-resolution PDFs.',
      badge: 'Deliverable'
    }
  ]

  const formats = [
    {
      ext: 'PPTX',
      title: 'PowerPoint Presentations',
      badge: '16:9 Widescreen',
      features: [
        'Branded cover and divider slides',
        'Key metric highlight cards & stat pills',
        'Clean tabular comparison slides',
        'Custom corporate color schemes'
      ],
      color: '#f97316'
    },
    {
      ext: 'DOCX',
      title: 'Executive Word Reports',
      badge: 'Corporate Layout',
      features: [
        'Formatted title page & table of contents',
        'Structured headings & callout boxes',
        'Styled tables with clear headers',
        'Optimized executive reading flow'
      ],
      color: '#3b82f6'
    },
    {
      ext: 'PDF',
      title: 'Print-Ready Documents',
      badge: 'Paged Media',
      features: [
        'Crisp modern vector typography',
        'High-contrast accessible styling',
        'Automated page numbering & footers',
        'Instant client-ready distribution'
      ],
      color: '#ef4444'
    },
    {
      ext: 'MD',
      title: 'Clean Markdown',
      badge: 'Source Code',
      features: [
        'Semantic hierarchy & clean syntax',
        'Ready for CMS & documentation portals',
        'Inline verified citations',
        'Zero meta fluff or boilerplate'
      ],
      color: '#10b981'
    }
  ]

  const enterpriseFeatures = [
    {
      icon: 'bolt',
      title: 'Autonomous Multi-Agent Workflow',
      desc: 'Seven specialized AI agents collaborate sequentially — from brief analysis to editorial polish — delivering deep, structured work.'
    },
    {
      icon: 'sparkle',
      title: 'Brand Template Matching',
      desc: 'Upload reference slides or documents. The engine automatically adopts your fonts, margins, and hex color palettes.'
    },
    {
      icon: 'shield',
      title: 'Human-in-the-Loop Review',
      desc: 'Review and refine generated drafts in the integrated editor before triggering binary compilation and final export.'
    },
    {
      icon: 'check',
      title: 'Always-On Multi-Model Redundancy',
      desc: 'Enterprise reliability with automated failover cascading across leading AI models, preserving 100% of your session context.'
    }
  ]

  return (
    <div className="landing-page">
      {/* ── Floating Island Header ───────────────────────────────────── */}
      <header className="landing-nav-wrapper">
        <nav className="landing-nav-island">
          {/* Brand */}
          <button className="landing-brand" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} aria-label="AGENT-101 Home">
            <div className="brand-logo-icon">
              <svg viewBox="0 0 32 32" width="22" height="22">
                <defs>
                  <linearGradient id="lndg" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0" stopColor="#a78bfa" />
                    <stop offset="1" stopColor="#22d3ee" />
                  </linearGradient>
                </defs>
                <path d="M16 2 28.1 9v14L16 30 3.9 23V9z" fill="url(#lndg)" />
                <path d="M11 21.5 16 10l5 11.5M12.8 17.5h6.4" fill="none" stroke="#fff" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <div className="brand-wordmark">
              <span className="brand-primary">AGENT</span>
              <span className="brand-accent">101</span>
            </div>
          </button>

          {/* Navigation Links in Frosted Glass Pill */}
          <div className="landing-nav-links">
            <a
              href="#how-it-works"
              className="nav-link"
              onClick={(e) => { e.preventDefault(); scrollTo('how-it-works') }}
            >
              How It Works
            </a>
            <a
              href="#deliverables"
              className="nav-link"
              onClick={(e) => { e.preventDefault(); scrollTo('deliverables') }}
            >
              Deliverables
            </a>
            <a
              href="#features"
              className="nav-link"
              onClick={(e) => { e.preventDefault(); scrollTo('features') }}
            >
              Features
            </a>
          </div>

          {/* Actions */}
          <div className="landing-nav-actions">
            <ShareButton />
            <button className="nav-login-link" onClick={() => onOpenAuth('login')}>
              Sign In
            </button>
            <button className="nav-signup-btn" onClick={() => onOpenAuth('register')}>
              <span>Get Started</span>
              <svg viewBox="0 0 16 16" width="13" height="13" fill="none">
                <path d="M6 3.5L10.5 8L6 12.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          </div>
        </nav>
      </header>

      {/* ── Hero Section ─────────────────────────────────────────────── */}
      <header className="landing-hero">
        <div className="hero-badge">
          <span className="hero-badge-dot" />
          <span>Autonomous Enterprise Content Studio</span>
        </div>

        <h1 className="hero-title">
          From a One-Line Brief to <span className="gradient-text">Publication-Ready</span> Deliverables
        </h1>

        <p className="hero-subtitle">
          Transform any topic into polished presentations, executive reports, and documents in seconds. Powered by autonomous multi-agent orchestration, custom brand style matching, and native document compilers.
        </p>

        <div className="hero-cta-group">
          <button className="btn btn-primary hero-btn" onClick={() => onOpenAuth('register')}>
            <Icon name="bolt" size={18} /> Get Started Free
          </button>
          <button className="btn btn-ghost hero-btn" onClick={() => onOpenAuth('login')}>
            Sign In to Studio
          </button>
        </div>

        <div className="hero-trust-row">
          <button type="button" className="trust-pill" onClick={() => scrollTo('deliverables')}>
            <span>📊</span> PowerPoint (.pptx)
          </button>
          <button type="button" className="trust-pill" onClick={() => scrollTo('deliverables')}>
            <span>📄</span> Word (.docx)
          </button>
          <button type="button" className="trust-pill" onClick={() => scrollTo('deliverables')}>
            <span>📑</span> Print PDF (.pdf)
          </button>
          <button type="button" className="trust-pill" onClick={() => scrollTo('deliverables')}>
            <span>📝</span> Clean Markdown (.md)
          </button>
        </div>

        {/* ── Interactive Process Flow ─────────────────────────────────── */}
        <div className="hero-pipeline-preview" id="how-it-works">
          <div className="pipeline-preview-header">
            <span className="preview-label">How It Works • 7-Stage Agent Pipeline</span>
            <span className="preview-status">Interactive Overview</span>
          </div>

          <div className="pipeline-nodes-row">
            {steps.map((s, idx) => (
              <button
                key={s.num}
                type="button"
                className={`pipeline-node-btn ${activeStep === idx ? 'active' : ''}`}
                onClick={() => setActiveStep(idx)}
              >
                <div className="node-num">{s.num}</div>
                <div className="node-agent">{s.title.split(' ')[0]}</div>
              </button>
            ))}
          </div>

          <div className="active-step-card">
            <div className="active-step-top">
              <span className="active-step-badge">{steps[activeStep].badge}</span>
              <span className="active-step-num">Stage {steps[activeStep].num} of 07</span>
            </div>
            <h3 className="active-step-title">{steps[activeStep].title}</h3>
            <p className="active-step-desc">{steps[activeStep].desc}</p>
          </div>
        </div>
      </header>

      {/* ── Key Features Grid ─────────────────────────────────────────── */}
      <section className="landing-section" id="features">
        <div className="section-head">
          <span className="section-tag">Platform Features</span>
          <h2>Designed for Executive Excellence</h2>
          <p>Everything you need to produce professional content at scale, without compromising on quality or brand integrity.</p>
        </div>

        <div className="features-grid">
          {enterpriseFeatures.map((f, i) => (
            <div key={i} className="feature-card">
              <div className="feature-icon-box">
                <Icon name={f.icon} size={22} />
              </div>
              <h3 className="feature-title">{f.title}</h3>
              <p className="feature-desc">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Deliverables Showcase ────────────────────────────────────── */}
      <section className="landing-section" id="deliverables">
        <div className="section-head">
          <span className="section-tag">Deliverables</span>
          <h2>Native File Outputs Ready to Share</h2>
          <p>Export real, fully-formatted binary files — ready for immediate board presentations, client reviews, or publishing.</p>
        </div>

        <div className="formats-grid">
          {formats.map((f) => (
            <div key={f.ext} className="format-card">
              <div className="format-top">
                <span className="format-ext" style={{ color: f.color }}>.{f.ext.toLowerCase()}</span>
                <span className="format-badge">{f.badge}</span>
              </div>
              <h3 className="format-title">{f.title}</h3>
              <ul className="format-features">
                {f.features.map((feat, i) => (
                  <li key={i}>
                    <Icon name="check" size={14} />
                    <span>{feat}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      {/* ── Final Call to Action ──────────────────────────────────────── */}
      <section className="landing-cta-banner">
        <h2>Ready to Transform Your Content Workflow?</h2>
        <p>Create an account in seconds, define your topic brief, and experience autonomous multi-agent content generation.</p>
        <div className="landing-cta-actions">
          <button className="btn btn-primary hero-btn" onClick={() => onOpenAuth('register')}>
            <Icon name="bolt" size={18} /> Get Started Free
          </button>
          <button className="btn btn-ghost hero-btn" onClick={() => onOpenAuth('login')}>
            Sign In to Existing Account
          </button>
        </div>
      </section>

      {/* ── Professional SaaS Footer ─────────────────────────────────── */}
      <footer className="landing-footer">
        <div className="footer-top">
          <div className="landing-brand">
            <div className="brand-name">AGENT<span>-101</span></div>
            <div className="brand-sub">Agentic Content Studio</div>
          </div>
          <div className="footer-links">
            <a href="#how-it-works" onClick={(e) => { e.preventDefault(); scrollTo('how-it-works') }}>How It Works</a>
            <a href="#features" onClick={(e) => { e.preventDefault(); scrollTo('features') }}>Features</a>
            <a href="#deliverables" onClick={(e) => { e.preventDefault(); scrollTo('deliverables') }}>Deliverables</a>
            <button className="footer-link-btn" onClick={() => onOpenAuth('login')}>Sign In</button>
          </div>
        </div>
        <div className="footer-bottom">
          <span>© 2025 AGENT-101 Studio. All rights reserved. Enterprise Autonomous Content Platform.</span>
        </div>
      </footer>
    </div>
  )
}
