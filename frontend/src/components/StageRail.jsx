import Icon from './Icon'

const STAGES = [
  { key: 'brief', label: 'Brief captured', icon: 'folder' },
  { key: 'agents', label: 'Autonomous agents', icon: 'spark' },
  { key: 'review', label: 'Human review', icon: 'user' },
  { key: 'compile', label: 'Native compile', icon: 'file' },
  { key: 'deliver', label: 'Delivered', icon: 'download' },
]

function stageIndex(status, hasRun) {
  switch (status) {
    case 'PROCESSING': return 1
    case 'WAITING_FOR_REVIEW': return 2
    case 'COMPILING': return 3
    case 'COMPLETED': return 5
    case 'FAILED': return hasRun ? 1 : 0
    default: return 0
  }
}

export default function StageRail({ status, hasRun }) {
  const current = stageIndex(status, hasRun)
  return (
    <ol className="stage-rail" aria-label="Workflow stages">
      {STAGES.map((s, i) => {
        const state = i < current || (i === 0) ? 'done' : i === current ? 'active' : 'todo'
        return (
          <li key={s.key} className={`stage ${state}`} aria-current={state === 'active' ? 'step' : undefined}>
            <span className="stage-dot">{state === 'done' ? <Icon name="check" size={14} strokeWidth={2.6} /> : <Icon name={s.icon} size={14} />}</span>
            <span className="stage-label">{s.label}</span>
          </li>
        )
      })}
    </ol>
  )
}
