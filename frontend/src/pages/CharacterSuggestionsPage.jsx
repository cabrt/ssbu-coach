import { useState, useMemo } from 'react'
import { getSuggestionsByCharacter, removeSuggestion } from '../lib/suggestionsStore'

const API_URL = 'http://localhost:8000/api'

function formatTime(seconds) {
  if (seconds == null || seconds === 0) return ''
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function getSeverityClass(severity) {
  switch (severity) {
    case 'high': return 'severity-high'
    case 'positive': return 'severity-positive'
    case 'info': return 'severity-info'
    default: return ''
  }
}

export default function CharacterSuggestionsPage({ onBack, onWatchVideo }) {
  const [byCharacter, setByCharacter] = useState(() => getSuggestionsByCharacter())
  const characters = useMemo(() => Object.keys(byCharacter).sort(), [byCharacter])
  const [selectedCharacter, setSelectedCharacter] = useState(() => {
    const keys = Object.keys(getSuggestionsByCharacter()).sort()
    return keys[0] || null
  })

  const suggestions = selectedCharacter ? (byCharacter[selectedCharacter] || []) : []

  const handleRemove = (id, e) => {
    e?.stopPropagation()
    removeSuggestion(id)
    const next = getSuggestionsByCharacter()
    setByCharacter(next)
    const nextChars = Object.keys(next).sort()
    if (nextChars.length === 0) {
      setSelectedCharacter(null)
    } else if (!next[selectedCharacter] || next[selectedCharacter].length === 0) {
      setSelectedCharacter(nextChars[0])
    }
  }

  const handleWatchVideo = (suggestion) => {
    if (!suggestion.videoId || !onWatchVideo) return
    
    // Calculate start time (5 seconds before the timestamp, minimum 0)
    const startTime = Math.max(0, (suggestion.timestamp || 0) - 5)
    const videoUrl = `${API_URL}/video/${suggestion.videoId}`
    
    onWatchVideo({
      videoUrl,
      videoId: suggestion.videoId,
      startTime,
      suggestion,
    })
  }

  const totalCount = characters.reduce((acc, c) => acc + (byCharacter[c]?.length || 0), 0)

  return (
    <div className="suggestions-page">
      <header className="suggestions-header">
        <h1>Character suggestions</h1>
        <p>Improvement notes you saved, grouped by character</p>
        <button type="button" className="nav-link-btn" onClick={onBack}>
          ← Back to Coach
        </button>
      </header>

      {totalCount === 0 ? (
        <div className="suggestions-empty">
          <p>No suggestions saved yet.</p>
          <p>Analyze a replay and use “Save to my list” on any key moment to add it here.</p>
        </div>
      ) : (
        <>
          <div className="suggestions-char-tabs">
            {characters.map((char) => (
              <button
                key={char}
                type="button"
                className={`char-tab ${selectedCharacter === char ? 'active' : ''}`}
                onClick={() => setSelectedCharacter(char)}
              >
                <span className="char-tab-name">{char}</span>
                <span className="char-tab-count">{byCharacter[char].length}</span>
              </button>
            ))}
          </div>

          {selectedCharacter && (
            <section className="suggestions-list-section">
              <h2>{selectedCharacter} suggestions</h2>
              <ul className="suggestions-list">
                {suggestions.map((s) => (
                  <li 
                    key={s.id} 
                    className={`suggestion-card ${getSeverityClass(s.severity)} ${s.videoId ? 'clickable' : ''}`}
                    onClick={() => s.videoId && handleWatchVideo(s)}
                    title={s.videoId ? 'Click to watch video at this moment' : ''}
                  >
                    <div className="suggestion-body">
                      <p className="suggestion-message">{s.message}</p>
                      <div className="suggestion-meta-row">
                        {s.timestamp != null && s.timestamp > 0 && (
                          <span className="suggestion-time">@{formatTime(s.timestamp)}</span>
                        )}
                        <span className="suggestion-type">{s.type.replace('_', ' ')}</span>
                        {s.videoId && (
                          <span className="suggestion-video-name" title={s.videoName || s.videoId}>
                            📹 {s.videoName || s.videoId}
                          </span>
                        )}
                      </div>
                      {s.videoId && (
                        <span className="suggestion-watch-hint">Click to watch</span>
                      )}
                    </div>
                    <button
                      type="button"
                      className="remove-suggestion-btn"
                      onClick={(e) => handleRemove(s.id, e)}
                      title="Remove from list"
                    >
                      Remove
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </>
      )}
    </div>
  )
}
