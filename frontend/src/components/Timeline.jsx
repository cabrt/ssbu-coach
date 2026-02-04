export default function Timeline({ tips, duration, onSeek }) {
  if (!tips || tips.length === 0 || !duration) return null

  const getMarkerColor = (type) => {
    switch (type) {
      case 'damage_taken': return '#ef4444'
      case 'stock_lost': return '#dc2626'
      case 'combo': return '#22c55e'
      case 'neutral': return '#eab308'
      default: return '#888'
    }
  }

  return (
    <div className="timeline">
      <div className="timeline-bar">
        {tips.map((tip, i) => {
          const position = (tip.timestamp / duration) * 100
          return (
            <div
              key={i}
              className="timeline-marker"
              style={{
                left: `${position}%`,
                backgroundColor: getMarkerColor(tip.type)
              }}
              title={`${formatTime(tip.timestamp)} - ${tip.type}`}
              onClick={() => onSeek?.(tip.timestamp)}
            />
          )
        })}
      </div>
      <div className="timeline-labels">
        <span>0:00</span>
        <span>{formatTime(duration)}</span>
      </div>
      <div className="timeline-legend">
        <span className="legend-item">
          <span className="legend-dot" style={{ background: '#ef4444' }} />
          Damage taken
        </span>
        <span className="legend-item">
          <span className="legend-dot" style={{ background: '#22c55e' }} />
          Combo
        </span>
        <span className="legend-item">
          <span className="legend-dot" style={{ background: '#eab308' }} />
          Neutral
        </span>
      </div>
    </div>
  )
}

function formatTime(seconds) {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
