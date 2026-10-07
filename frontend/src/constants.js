export const AGENTS = [
  { name: 'Requirement Analysis Agent', short: 'Requirement Analysis', accent: 'violet', icon: 'target', blurb: 'Decodes the brief into objectives, audience and tone.' },
  { name: 'Planning Agent', short: 'Content Planning', accent: 'violet', icon: 'layers', blurb: 'Architects a section-by-section content plan.' },
  { name: 'Reference Analysis Agent', short: 'Reference Analysis', accent: 'cyan', icon: 'palette', blurb: 'Extracts palette, typography and layout from your template.' },
  { name: 'Research & Enrichment Agent', short: 'Research & Enrichment', accent: 'violet', icon: 'search', blurb: 'Grounds every section in topic-scoped, cited facts.' },
  { name: 'Content Generation Agent', short: 'Content Generation', accent: 'violet', icon: 'pen', blurb: 'Writes the full draft, section by section.' },
  { name: 'Content Review Agent', short: 'Content Review', accent: 'violet', icon: 'shield', blurb: 'Measures readability, trims fluff and checks citations are kept.' },
  { name: 'Format Generation Agent', short: 'Format Generation', accent: 'cyan', icon: 'file', blurb: 'Compiles the native file and runs automated accessibility checks.' },
]

export const FORMATS = {
  PPT: { label: 'PowerPoint', ext: '.pptx', color: '#fb923c', hint: 'Slide deck' },
  DOCX: { label: 'Word', ext: '.docx', color: '#60a5fa', hint: 'Report with document control' },
  PDF: { label: 'PDF', ext: '.pdf', color: '#f87171', hint: 'Print-ready brief' },
  MD: { label: 'Markdown', ext: '.md', color: '#a3e635', hint: 'Docs-as-code' },
}

// complex: scripts the PDF engine can't shape correctly, so PDF output is disabled for them.
export const LANGUAGES = [
  { value: 'English', label: 'English' },
  { value: 'Hindi', label: 'हिन्दी · Hindi', complex: true },
  { value: 'Marathi', label: 'मराठी · Marathi', complex: true },
  { value: 'Tamil', label: 'தமிழ் · Tamil', complex: true },
  { value: 'Telugu', label: 'తెలుగు · Telugu', complex: true },
  { value: 'Bengali', label: 'বাংলা · Bengali', complex: true },
  { value: 'Gujarati', label: 'ગુજરાતી · Gujarati', complex: true },
  { value: 'Kannada', label: 'ಕನ್ನಡ · Kannada', complex: true },
  { value: 'Spanish', label: 'Español · Spanish' },
  { value: 'French', label: 'Français · French' },
  { value: 'German', label: 'Deutsch · German' },
]

export const PRESETS = [
  {
    title: 'Clinical Multi-Agent Architecture',
    description: 'Executive deck explaining how a multi-agent AI system coordinates triage, diagnostics support and clinical documentation while keeping patient data isolated.',
    target_format: 'PPT',
    user_instructions: 'Audience is hospital leadership. Keep slides crisp, max 5 bullets each.',
  },
  {
    title: 'Zero-Trust Security Policy',
    description: 'Enterprise policy document defining zero-trust principles, identity controls, network segmentation and incident response responsibilities.',
    target_format: 'DOCX',
    user_instructions: 'Formal tone with a document control table and a RACI matrix.',
  },
  {
    title: 'GenAI Adoption Research Brief',
    description: 'Research brief on generative AI adoption across industries: drivers, risks, ROI evidence and a 12-month roadmap.',
    target_format: 'PDF',
    user_instructions: 'Cite sources and include a comparison table.',
  },
  {
    title: 'Developer Onboarding Guide',
    description: 'Onboarding guide for engineers joining the platform team: architecture tour, local setup, coding standards and first-week checklist.',
    target_format: 'MD',
    user_instructions: '',
  },
]

export const STATUS_LABELS = {
  CREATED: 'Ready',
  IDLE: 'Ready',
  PROCESSING: 'Agents running',
  WAITING_FOR_REVIEW: 'Awaiting review',
  COMPILING: 'Compiling',
  COMPLETED: 'Delivered',
  FAILED: 'Failed',
  UNKNOWN: 'Ready',
}

export const formatBytes = (n = 0) =>
  n < 1024 ? `${n} B` : n < 1048576 ? `${(n / 1024).toFixed(1)} KB` : `${(n / 1048576).toFixed(2)} MB`

export const formatMinutes = (m = 0) => {
  const h = Math.floor(m / 60)
  const min = Math.round(m % 60)
  return h ? `${h} h${min ? ` ${min} min` : ''}` : `${min} min`
}

export const formatMoney = (usd = 0, inr = 0) =>
  `$${usd < 0.01 ? usd.toFixed(4) : usd.toFixed(2)} (≈ ₹${inr < 1 ? inr.toFixed(2) : inr.toFixed(0)})`

export const formatTime = (iso) => {
  const d = iso ? new Date(iso) : new Date()
  return Number.isNaN(d.getTime()) ? '--:--:--' : d.toLocaleTimeString([], { hour12: false })
}
