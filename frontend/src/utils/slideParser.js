/**
 * Parses markdown content into structured slide data matching the python-pptx builder.
 * Produces:
 *  - Slide 1: Dark luxury navy cover slide with pill badge, title, subtitle, and metadata.
 *  - Slides 2+: Clean off-white content slides with title, underline accent, cards, stat metrics, tables, and running footer.
 */

export function parseMarkdownToSlides(markdown = '', workspaceTitle = 'Autonomous Presentation') {
  if (!markdown || !markdown.trim()) {
    return [
      {
        slideNumber: 1,
        isCover: true,
        title: workspaceTitle,
        subtitle: 'Autonomous Multi-Agent AI Content Generation & Synthesis System\nStrict Topic Isolation • Native Binary Architecture • WCAG 2.2 Level AA',
        pillBadge: 'SYSTEM DELIVERABLE • ContentGenie',
        metadata: `VERSION 1.0 (Final System Specification)   |   DATE: ${new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'long', year: 'numeric' })}   |   AUTHOR: ContentGenie`,
        cards: [],
        statCards: [],
        table: null,
        fact: null,
      },
    ]
  }

  // 1. Split into slide chunks
  let chunks = []
  if (markdown.includes('<!-- slide -->')) {
    chunks = markdown.split('<!-- slide -->').map((c) => c.trim()).filter(Boolean)
  } else {
    const lines = markdown.split(/\r?\n/)
    let currentChunk = []
    for (const line of lines) {
      const trimmed = line.trim()
      if (trimmed === '---' || trimmed === '***') {
        if (currentChunk.length > 0) {
          chunks.push(currentChunk.join('\n').trim())
          currentChunk = []
        }
        continue
      }
      if (trimmed.startsWith('# ') || trimmed.startsWith('## ')) {
        if (currentChunk.length > 0) {
          chunks.push(currentChunk.join('\n').trim())
          currentChunk = []
        }
      }
      currentChunk.push(line)
    }
    if (currentChunk.length > 0) {
      chunks.push(currentChunk.join('\n').trim())
    }
  }

  chunks = chunks.filter((c) => c.trim().length > 0)
  if (chunks.length === 0) {
    chunks = [markdown.trim()]
  }

  const slides = []

  // Extract cover title and optional subtitle from chunk 0
  const firstChunkLines = chunks[0].split(/\r?\n/).map((l) => l.trim()).filter(Boolean)
  const nonMetaLines = firstChunkLines.filter(
    (l) => !/(?:\*|_)?(?:add|use|apply|insert)\s+(?:logo|branding|template|background|color\s+palette)/i.test(l)
  )

  let coverTitle = workspaceTitle
  if (nonMetaLines.length > 0 && nonMetaLines[0].startsWith('#')) {
    coverTitle = nonMetaLines[0].replace(/^#+\s*/, '').trim()
  }

  let coverSubtitle = 'Autonomous Multi-Agent AI Content Generation & Synthesis System\nStrict Topic Isolation • Native Binary Architecture • WCAG 2.2 Level AA'
  const explicitSub = nonMetaLines.slice(1).find((l) => !l.startsWith('#') && !l.startsWith('|'))
  if (explicitSub) {
    coverSubtitle = explicitSub.replace(/^[-*]\s*/, '').trim()
  }

  // Cover Slide (Slide 1)
  slides.push({
    slideNumber: 1,
    isCover: true,
    title: coverTitle,
    subtitle: coverSubtitle,
    pillBadge: 'SYSTEM DELIVERABLE • ContentGenie',
    metadata: `VERSION 1.0 (Final System Specification)   |   DATE: ${new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'long', year: 'numeric' })}   |   AUTHOR: ContentGenie`,
    cards: [],
    statCards: [],
    table: null,
    fact: null,
  })

  // Body chunks: if chunk 0 had only the H1 title/subtitle, slides 2+ come from chunks 1..N
  const bodyChunks = chunks.length > 1 ? chunks.slice(1) : (
    nonMetaLines.length > 2 ? [nonMetaLines.slice(2).join('\n')] : []
  )

  bodyChunks.forEach((chunk) => {
    const rawLines = chunk.split(/\r?\n/)
    let slideTitle = `Slide ${slides.length + 1}`
    const contentLines = []
    let table = null
    let fact = null
    const statCards = []

    // Detect markdown tables
    const tableLines = rawLines.filter((l) => l.trim().startsWith('|') && l.trim().endsWith('|'))
    if (tableLines.length >= 2) {
      const headers = tableLines[0].split('|').map((c) => c.trim()).filter(Boolean)
      const dataRows = tableLines.slice(2).map((r) => r.split('|').map((c) => c.trim()).filter(Boolean)).filter((r) => r.length > 0)
      if (headers.length > 0 && dataRows.length > 0) {
        table = { headers, rows: dataRows }
      }
    }

    for (const rawLine of rawLines) {
      const line = rawLine.trim()
      if (!line || line === '---' || line === '***' || line === '___') continue

      // Skip meta prompt echoes or instructions
      if (/(?:\*|_)?(?:add|use|apply|insert)\s+(?:logo|branding|template|background|color\s+palette)/i.test(line)) {
        continue
      }

      if (line.startsWith('# ') || line.startsWith('## ') || line.startsWith('### ')) {
        slideTitle = line.replace(/^#+\s*/, '').trim()
        continue
      }

      // Skip table rows as parsed separately
      if (line.startsWith('|') && line.endsWith('|')) continue

      // Fact / citation callout
      if (
        line.toLowerCase().startsWith('*fact:') ||
        line.toLowerCase().startsWith('fact:') ||
        line.startsWith('>')
      ) {
        fact = line.replace(/^\*+/, '').replace(/\*+$/, '').replace(/^>\s*/, '').trim()
        continue
      }

      // Check for KPI / Stat Metric: "**Title:** 142 seconds (sub-detail)"
      const statMatch = line.match(/^\*\*(.*?)\:\*\*\s*(.*)$/)
      if (statMatch) {
        const title = statMatch[1].trim()
        const rest = statMatch[2].trim()
        const numMatch = rest.match(/(\d+(?:\.\d+)?(?:%|s|x|:1)?(?:\s*(?:seconds|min|ms|hrs|GB|MB))?)/i)
        if (numMatch && (rest.length < 50 || numMatch[1].length > 1)) {
          const highlight = numMatch[1].trim()
          const detail = rest.replace(highlight, '').trim().replace(/^[,\-\s(]+/, '').replace(/\)$/, '')
          statCards.push({ title, number: highlight, desc: detail })
          continue
        }
      }

      // Bullet items or regular text
      let cleaned = line
      if (cleaned.startsWith('- ') || cleaned.startsWith('* ')) {
        cleaned = cleaned.substring(2).trim()
      }
      if (cleaned) {
        contentLines.push(cleaned)
      }
    }

    if (slideTitle || contentLines.length > 0 || table || statCards.length > 0) {
      slides.push({
        slideNumber: slides.length + 1,
        isCover: false,
        title: slideTitle,
        cards: contentLines,
        statCards: statCards.length >= 2 ? statCards : [],
        table,
        fact,
        footerLeft: 'ContentGenie • Multi-Agent Autonomous Content Synthesis System',
        footerRight: `SLIDE ${slides.length + 1}`,
      })
    }
  })

  return slides
}
