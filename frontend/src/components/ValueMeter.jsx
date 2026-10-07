import Icon from './Icon'
import { formatMinutes, formatMoney } from '../constants'

// Per-run value: measured generation time and AI cost against a stated manual-effort baseline.
export function RunValue({ value }) {
  if (!value) return null
  const saved = Math.max(0, value.manual_minutes - value.seconds / 60)
  return (
    <div className="value-strip" title={`Manual baseline: ${value.baseline}. Tokens: ${value.prompt_tokens} in / ${value.completion_tokens} out across ${value.llm_calls} AI calls.`}>
      <div className="value-item">
        <Icon name="bolt" size={18} />
        <div><b>{value.seconds < 60 ? `${Math.round(value.seconds)} sec` : formatMinutes(value.seconds / 60)}</b><span>to create</span></div>
      </div>
      <div className="value-item">
        <Icon name="spark" size={18} />
        <div><b>{formatMoney(value.cost_usd, value.cost_inr)}</b><span>AI cost</span></div>
      </div>
      <div className="value-item value-hero">
        <Icon name="clock" size={18} />
        <div><b>≈ {formatMinutes(saved)}</b><span>of manual work saved</span></div>
      </div>
      <span className="value-note"><Icon name="alert" size={12} /> Estimate: {value.baseline}</span>
    </div>
  )
}

// Running totals across all topics.
export function ValueTotals({ stats, compact = false }) {
  if (!stats || !stats.documents) return null
  if (compact) {
    return (
      <div className="value-compact" title={`${stats.documents} documents · AI cost ${formatMoney(stats.cost_usd, stats.cost_inr)}`}>
        <Icon name="clock" size={14} /> <b>{formatMinutes(stats.manual_minutes_saved)}</b> saved · {stats.documents} {stats.documents === 1 ? 'doc' : 'docs'}
      </div>
    )
  }
  return (
    <div className="value-totals">
      <div><b>{stats.documents}</b><span>documents created</span></div>
      <div><b>{formatMinutes(stats.manual_minutes_saved)}</b><span>manual work saved</span></div>
      <div><b>{Math.round(stats.avg_seconds)} sec</b><span>average per document</span></div>
      <div><b>{formatMoney(stats.cost_usd, stats.cost_inr)}</b><span>total AI cost</span></div>
    </div>
  )
}
