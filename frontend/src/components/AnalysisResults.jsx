import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import Timeline from './Timeline'
import VideoPlayer from './VideoPlayer'
import { saveSuggestion } from '../lib/suggestionsStore'

const API_URL = 'http://localhost:8000/api'

async function saveAnalysisToServer(videoId) {
  try {
    await axios.post(`${API_URL}/save-analysis/${videoId}`)
    return true
  } catch (err) {
    console.error('Failed to save analysis:', err)
    return false
  }
}

function formatTime(seconds) {
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

export default function AnalysisResults({ analysis, videoUrl, onReset }) {
  const { coaching, game_states, video_id: videoId } = analysis
  const { summary, stats, tips, characters } = coaching || {}
  const [seekTime, setSeekTime] = useState(null)
  const [savedIds, setSavedIds] = useState(new Set())
  const [videoTime, setVideoTime] = useState(0)
  const [suggestionAtTime, setSuggestionAtTime] = useState(null)
  const [suggestionLoading, setSuggestionLoading] = useState(false)
  const [analysisSaved, setAnalysisSaved] = useState(false)
  const [savingAnalysis, setSavingAnalysis] = useState(false)
  const debounceRef = useRef(null)

  const handleSaveAnalysis = async () => {
    if (!videoId || analysisSaved) return
    setSavingAnalysis(true)
    const success = await saveAnalysisToServer(videoId)
    if (success) {
      setAnalysisSaved(true)
    }
    setSavingAnalysis(false)
  }

  const handleTipClick = (timestamp) => {
    setSeekTime(timestamp)
  }

  const formatCharName = (name) => {
    if (!name) return 'Unknown'
    return name.charAt(0).toUpperCase() + name.slice(1)
  }

  const yourMaxPercent = stats?.your_max_percent ?? stats?.p1_max_percent ?? 0
  const opponentMaxPercent = stats?.opponent_max_percent ?? stats?.p2_max_percent ?? 0
  const youWon = stats?.you_won ?? (stats?.winner === 'p1')

  useEffect(() => {
    if (!videoId || videoTime == null) return
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      setSuggestionLoading(true)
      setSuggestionAtTime(null)
      axios.get(`${API_URL}/suggestion-at-time/${videoId}`, { params: { time: Math.floor(videoTime) } })
        .then(({ data }) => setSuggestionAtTime(data.suggestion))
        .catch(() => setSuggestionAtTime(null))
        .finally(() => setSuggestionLoading(false))
    }, 800)
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current) }
  }, [videoId, videoTime])

  return (
    <div className="results">
      {videoUrl && (
        <VideoPlayer 
          videoUrl={videoUrl} 
          videoId={videoId}
          currentTime={seekTime}
          onTimeUpdate={setVideoTime}
          suggestionAtTime={suggestionAtTime}
          suggestionLoading={suggestionLoading}
          playerChar={characters?.player}
        />
      )}

      {characters && (characters.player || characters.opponent) && (
        <div className="matchup-card">
          <div className="matchup-vs">
            <div className="matchup-player">
              <span className="matchup-label">You</span>
              <span className="matchup-char">{formatCharName(characters.player)}</span>
            </div>
            <span className="matchup-vs-text">vs</span>
            <div className="matchup-opponent">
              <span className="matchup-label">Opponent</span>
              <span className="matchup-char">{formatCharName(characters.opponent)}</span>
            </div>
          </div>
        </div>
      )}

      {summary && (
        <div className="summary-card">
          <h2>AI Coach Analysis</h2>
          <p className="summary-text">{summary}</p>
        </div>
      )}

      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-value">{formatTime(stats.duration)}</div>
            <div className="stat-label">Duration</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{yourMaxPercent}%</div>
            <div className="stat-label">Max Damage Taken</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{opponentMaxPercent}%</div>
            <div className="stat-label">Max Damage Dealt</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{youWon ? 'Won' : 'Lost'}</div>
            <div className="stat-label">Result</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{tips?.length || 0}</div>
            <div className="stat-label">Key Moments</div>
          </div>
        </div>
      )}

      {tips && tips.length > 0 && stats && (
        <Timeline 
          tips={tips} 
          duration={stats.duration} 
          onSeek={handleTipClick}
        />
      )}

      {tips && tips.length > 0 && (
        <div className="tips-section">
          <h2>Key Moments</h2>
          {tips.map((tip, i) => {
            const tipKey = `tip-${i}-${tip.timestamp}-${tip.type}`
            const isSaved = savedIds.has(tipKey)
            return (
              <div 
                key={i} 
                className={`tip-card clickable ${getSeverityClass(tip.severity)}`}
                onClick={() => handleTipClick(tip.timestamp)}
              >
                <div className="tip-timestamp">{formatTime(tip.timestamp)}</div>
                <div className="tip-content">
                  <div className="tip-message">{tip.message}</div>
                  {tip.ai_advice && (
                    <div className="tip-ai-advice">{tip.ai_advice}</div>
                  )}
                  <div className="tip-meta">
                    <span className="tip-type">{tip.type.replace('_', ' ')}</span>
                    <button
                      type="button"
                      className={`save-tip-btn ${isSaved ? 'saved' : ''}`}
                      onClick={(e) => {
                        if (!isSaved) {
                          saveSuggestion({
                            character: characters?.player ? String(characters.player).trim() : 'Unknown',
                            message: [tip.message, tip.ai_advice].filter(Boolean).join(' — '),
                            type: tip.type,
                            severity: tip.severity,
                            timestamp: tip.timestamp,
                            videoId: videoId,
                            videoName: videoId ? `${videoId}.mp4` : null,
                          })
                          setSavedIds(prev => new Set(prev).add(tipKey))
                        }
                        e.stopPropagation()
                      }}
                      disabled={isSaved}
                    >
                      {isSaved ? 'Saved' : 'Save to my list'}
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {(!tips || tips.length === 0) && (
        <div className="summary-card">
          <p>No specific coaching tips detected. Try uploading a longer match or ensure the video shows the game UI clearly.</p>
        </div>
      )}

      <div className="analysis-actions">
        {videoId && (
          <button 
            className={`save-analysis-btn ${analysisSaved ? 'saved' : ''}`}
            onClick={handleSaveAnalysis}
            disabled={analysisSaved || savingAnalysis}
          >
            {savingAnalysis ? 'Saving...' : analysisSaved ? 'Analysis Saved!' : 'Save Analysis'}
          </button>
        )}
        <button className="reset-btn" onClick={onReset}>
          Analyze Another Replay
        </button>
      </div>
    </div>
  )
}
