import { useState, useMemo } from 'react'

// Single source of truth: event type -> label + color (used for both dots and legend)
const EVENT_TYPE_CONFIG = {
  damage_taken:    { label: 'Damage taken',    color: '#ec4899' },  // Pink (distinct from Stock lost)
  stock_lost:      { label: 'Stock lost',      color: '#dc2626' },  // Dark red
  stock_taken:     { label: 'Stock taken',     color: '#3b82f6' },  // Blue
  combo:           { label: 'Combo',           color: '#22c55e' },  // Green
  neutral:         { label: 'Neutral',         color: '#eab308' },  // Yellow
  edgeguard:       { label: 'Edgeguard',       color: '#06b6d4' },  // Cyan
  got_edgeguarded: { label: 'Got edgeguarded', color: '#8b5cf6' },  // Purple
  momentum_advantage:    { label: 'Momentum +', color: '#22c55e' },
  momentum_disadvantage: { label: 'Momentum −', color: '#f97316' },  // Orange
  habit:           { label: 'Habit',           color: '#f59e0b' },  // Amber
}

function toSeconds(value) {
  if (value == null || typeof value !== 'number') return 0
  return value > 10000 ? value / 1000 : value
}

function formatTime(seconds) {
  const s = Math.max(0, Math.floor(seconds))
  const mins = Math.floor(s / 60)
  const secs = s % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

export default function Timeline({ tips, duration, onSeek, seekTime }) {
  const [activeTypes, setActiveTypes] = useState(null)

  const timelineTips = useMemo(() => {
    if (!tips || !Array.isArray(tips)) return []
    return tips.filter(
      (t) => t.type !== 'character_tip' && t.timestamp != null
    )
  }, [tips])

  const allTypesInData = useMemo(() => {
    const set = new Set()
    timelineTips.forEach((t) => set.add(t.type))
    return set
  }, [timelineTips])

  const effectiveActiveTypes = useMemo(() => {
    if (activeTypes === null) return allTypesInData
    return activeTypes
  }, [activeTypes, allTypesInData])

  const visibleTips = useMemo(() => {
    return timelineTips.filter((t) => effectiveActiveTypes.has(t.type))
  }, [timelineTips, effectiveActiveTypes])

  const toggleLegendType = (type) => {
    setActiveTypes((prev) => {
      const next = new Set(prev === null ? allTypesInData : prev)
      if (prev === null) {
        return new Set([type])
      }
      if (next.has(type)) {
        next.delete(type)
      } else {
        next.add(type)
      }
      return next
    })
  }

  if (!timelineTips.length || !duration || duration <= 0) return null

  const seekSeconds = toSeconds(seekTime)

  return (
    <div className="timeline">
      <div className="timeline-bar">
        {visibleTips.map((tip, i) => {
          const ts = toSeconds(tip.timestamp)
          const position = Math.min(100, Math.max(0, (ts / duration) * 100))
          const color = EVENT_TYPE_CONFIG[tip.type]?.color ?? '#888'
          const isSelected = seekTime != null && Math.abs(ts - seekSeconds) < 0.5
          return (
            <div
              key={`${i}-${tip.timestamp}-${tip.type}`}
              className={`timeline-marker ${isSelected ? 'timeline-marker-selected' : ''}`}
              style={{
                left: `${position}%`,
                backgroundColor: color,
                zIndex: 2,
                pointerEvents: 'auto',
              }}
              title={`${formatTime(ts)} - ${(EVENT_TYPE_CONFIG[tip.type]?.label ?? tip.type).replace('_', ' ')}`}
              onClick={(e) => {
                e.stopPropagation()
                onSeek?.(ts)
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  onSeek?.(ts)
                }
              }}
              role="button"
              tabIndex={0}
              aria-label={`Seek to ${formatTime(ts)}`}
            />
          )
        })}
      </div>
      <div className="timeline-labels">
        <span>0:00</span>
        <span>{formatTime(duration)}</span>
      </div>
      <div className="timeline-legend">
        {Array.from(allTypesInData)
          .filter((type) => EVENT_TYPE_CONFIG[type])
          .map((type) => {
            const config = EVENT_TYPE_CONFIG[type]
            const isActive = effectiveActiveTypes.has(type)
            return (
              <button
                key={type}
                type="button"
                className={`legend-item legend-item-toggle ${isActive ? 'legend-item-active' : 'legend-item-inactive'}`}
                onClick={() => toggleLegendType(type)}
                aria-pressed={isActive}
              >
                <span
                  className="legend-dot"
                  style={{ background: config.color }}
                />
                {config.label}
              </button>
            )
          })}
      </div>
    </div>
  )
}
