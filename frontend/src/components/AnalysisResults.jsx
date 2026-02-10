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
    case 'critical': return 'severity-high'
    case 'notable': return 'severity-notable'
    case 'positive': return 'severity-positive'
    case 'info': return 'severity-info'
    default: return ''
  }
}

function SkillProfileCard({ skillProfile }) {
  if (!skillProfile) return null

  const tier = skillProfile.tier || 'mid'
  const score = skillProfile.overall_score || 0
  const confidence = skillProfile.confidence || 0
  const strengths = skillProfile.strengths || []
  const weaknesses = skillProfile.weaknesses || []
  const metrics = skillProfile.metrics || {}

  const tierColors = {
    low: '#f97316',
    mid: '#eab308',
    high: '#22c55e',
    top: '#3b82f6',
  }

  const tierLabels = {
    low: 'Beginner',
    mid: 'Intermediate',
    high: 'Advanced',
    top: 'Competitive',
  }

  return (
    <div className="skill-profile-card">
      <h2>Skill Profile</h2>
      <p className="skill-explainer">
        Each metric is scored 0–100 based on this match. Higher is always better. Your overall score is a weighted average of all 8 metrics.
      </p>
      <div className="skill-tier-display">
        <span className="skill-tier-badge" style={{ borderColor: tierColors[tier], color: tierColors[tier] }}>
          {tierLabels[tier] || tier.toUpperCase()}
        </span>
        <span className="skill-score">{Math.round(score)}/100</span>
        {confidence < 0.6 && (
          <span className="skill-confidence-note">Low confidence (short match)</span>
        )}
      </div>

      <div className="skill-metrics-grid">
        {Object.entries(metrics).map(([key, m]) => (
          <div key={key} className="skill-metric">
            <div className="skill-metric-bar-bg">
              <div
                className="skill-metric-bar-fill"
                style={{ width: `${Math.min(100, m.score)}%`, backgroundColor: tierColors[tier] }}
              />
            </div>
            <div className="skill-metric-info">
              <span className="skill-metric-label">{m.label}</span>
              <span className="skill-metric-score">{Math.round(m.score)}</span>
            </div>
          </div>
        ))}
      </div>

      {(strengths.length > 0 || weaknesses.length > 0) && (
        <div className="skill-sw-row">
          {strengths.length > 0 && (
            <div className="skill-sw-col">
              <span className="skill-sw-title strength">Strengths</span>
              {strengths.map((s, i) => <span key={i} className="skill-sw-tag strength">{s}</span>)}
            </div>
          )}
          {weaknesses.length > 0 && (
            <div className="skill-sw-col">
              <span className="skill-sw-title weakness">Areas to Improve</span>
              {weaknesses.map((w, i) => <span key={i} className="skill-sw-tag weakness">{w}</span>)}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function HabitsSection({ habits }) {
  if (!habits || habits.length === 0) return null

  const severityColors = {
    critical: '#ef4444',
    notable: '#f59e0b',
    info: '#3b82f6',
  }

  return (
    <div className="habits-section">
      <h2>Detected Habits</h2>
      {habits.map((habit, i) => (
        <div key={i} className="habit-card" style={{ borderLeftColor: severityColors[habit.severity] || '#555' }}>
          <div className="habit-header">
            <span className="habit-severity" style={{ color: severityColors[habit.severity] }}>
              {habit.severity?.toUpperCase()}
            </span>
            <span className="habit-occurrences">{habit.occurrences}x</span>
          </div>
          <div className="habit-description">{habit.description}</div>
          <div className="habit-evidence">{habit.evidence}</div>
          <div className="habit-suggestion">{habit.suggestion}</div>
        </div>
      ))}
    </div>
  )
}

function TopFocusAreas({ focusAreas }) {
  if (!focusAreas || focusAreas.length === 0) return null

  const rankColors = ['#ef4444', '#f59e0b', '#3b82f6']

  return (
    <div className="focus-areas-section">
      <h2>Top Things to Work On</h2>
      {focusAreas.map((area, i) => (
        <div key={i} className="focus-area-card">
          <div className="focus-area-header">
            <span className="focus-area-rank" style={{ backgroundColor: rankColors[i] || '#555' }}>
              #{i + 1}
            </span>
            <span className="focus-area-title">{area.title}</span>
            <span className="focus-area-stat">{area.stat_line}</span>
          </div>
          <div className="focus-area-explanation">{area.explanation}</div>
          {area.drills && area.drills.length > 0 && (
            <div className="focus-area-drills">
              {area.drills.map((drill, j) => (
                <div key={j} className="focus-area-drill">{drill}</div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

function OpponentReport({ report, opponentName }) {
  if (!report) return null

  const formatCharName = (name) => {
    if (!name) return 'Opponent'
    return name.charAt(0).toUpperCase() + name.slice(1)
  }
  const oppDisplay = formatCharName(opponentName)

  return (
    <div className="opponent-report-section">
      <h2>Opponent Scouting Report</h2>

      {report.deaths && report.deaths.length > 0 && (
        <div className="opponent-subsection">
          <h3>How {oppDisplay} beat you</h3>
          <div className="opponent-deaths">
            {report.deaths.map((d, i) => (
              <div key={i} className={`opponent-death-entry${d.flag === 'early kill' ? ' early-kill' : ''}`}>
                <span className="death-percent">{Math.round(d.kill_percent)}%</span>
                <span className="death-description">{d.description}</span>
                {d.burst_damage > 0 && !d.description.includes('taking') && (
                  <span className="death-burst">({Math.round(d.burst_damage)}% burst)</span>
                )}
              </div>
            ))}
            {report.avg_kill_percent > 0 && (
              <div className="death-avg">Avg kill percent: {Math.round(report.avg_kill_percent)}%</div>
            )}
          </div>
        </div>
      )}

      {report.neutral_description && (
        <div className="opponent-subsection">
          <h3>Their neutral game</h3>
          <span className={`neutral-badge neutral-${report.neutral_tendency}`}>
            {report.neutral_tendency}
          </span>
          <p className="opponent-neutral-desc">{report.neutral_description}</p>
        </div>
      )}

      {report.exploitable_patterns && report.exploitable_patterns.length > 0 && (
        <div className="opponent-subsection">
          <h3>What you can exploit</h3>
          <ul className="opponent-exploitable">
            {report.exploitable_patterns.map((p, i) => (
              <li key={i}>{p}</li>
            ))}
          </ul>
        </div>
      )}

      {report.character_tips && report.character_tips.length > 0 && (
        <div className="opponent-subsection">
          <h3>Tips vs {oppDisplay}</h3>
          <ul className="opponent-char-tips">
            {report.character_tips.map((tip, i) => (
              <li key={i}>{tip}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function MatchupGamePlan({ gameplan, playerChar, opponentChar }) {
  if (!gameplan) return null

  const formatCharName = (name) => {
    if (!name) return 'Unknown'
    return name.charAt(0).toUpperCase() + name.slice(1)
  }

  const sections = [
    { key: 'win_conditions', title: 'Win Conditions', icon: 'target' },
    { key: 'watch_for', title: 'Watch For', icon: 'warning' },
    { key: 'neutral_approach', title: 'Neutral Approach', icon: 'neutral' },
    { key: 'key_interactions', title: 'Key Interactions', icon: 'key' },
  ]

  return (
    <div className="gameplan-section">
      <h2>{formatCharName(playerChar)} vs {formatCharName(opponentChar)} Game Plan</h2>
      {sections.map(({ key, title }) => {
        const items = gameplan[key]
        if (!items || items.length === 0) return null
        return (
          <div key={key} className="gameplan-subsection">
            <h3>{title}</h3>
            <ul className="gameplan-list">
              {items.map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
          </div>
        )
      })}
    </div>
  )
}

function TrendsSection({ character, refreshKey }) {
  const [trends, setTrends] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!character) return
    setLoading(true)
    axios.get(`${API_URL}/trends/${character}`)
      .then(({ data }) => setTrends(data))
      .catch(() => setTrends(null))
      .finally(() => setLoading(false))
  }, [character, refreshKey])

  if (loading || !trends || trends.games_played < 2) return null

  const { comparison, games_played, win_rate } = trends

  const METRIC_LABELS = {
    damage_per_opening: 'Punish Game',
    kill_efficiency: 'Kill Efficiency',
    edgeguard_rate: 'Edgeguarding',
    death_percent: 'Survival/DI',
    post_death_vulnerability: 'Post-Death',
    combo_quality: 'Combo Quality',
    neutral_duration: 'Neutral Game',
    lead_conversion: 'Lead Conversion',
    overall_score: 'Overall Score',
  }

  return (
    <div className="trends-section">
      <h2>Your Trends ({games_played} games)</h2>
      <div className="trends-summary">
        <span className="trends-stat">{games_played} games</span>
        <span className="trends-stat">{win_rate}% win rate</span>
      </div>
      <div className="trends-metrics">
        {Object.entries(comparison).map(([key, data]) => (
          <div key={key} className="trends-metric-row">
            <span className="trends-metric-label">{METRIC_LABELS[key] || key}</span>
            <span className="trends-metric-current">{Math.round(data.current)}</span>
            <span className={`trends-metric-delta ${data.delta > 0 ? 'positive' : data.delta < 0 ? 'negative' : ''}`}>
              {data.delta > 0 ? '+' : ''}{Math.round(data.delta)}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function AnalysisResults({ analysis, videoUrl, onReset }) {
  const { coaching, game_states, video_id: videoId } = analysis
  const { summary, stats, tips, characters, skill_profile, habits, top3_focus_areas, opponent_report, matchup_gameplan } = coaching || {}
  const [seekTime, setSeekTime] = useState(null)
  const [savedIds, setSavedIds] = useState(new Set())
  const [videoTime, setVideoTime] = useState(0)
  const [suggestionAtTime, setSuggestionAtTime] = useState(null)
  const [suggestionLoading, setSuggestionLoading] = useState(false)
  const [analysisSaved, setAnalysisSaved] = useState(false)
  const [savingAnalysis, setSavingAnalysis] = useState(false)
  const [showAllTips, setShowAllTips] = useState(false)
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

      <MatchupGamePlan gameplan={matchup_gameplan} playerChar={characters?.player} opponentChar={characters?.opponent} />

      <TopFocusAreas focusAreas={top3_focus_areas} />

      <OpponentReport report={opponent_report} opponentName={characters?.opponent} />

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

      <SkillProfileCard skillProfile={skill_profile} />

      <TrendsSection character={characters?.player} refreshKey={analysisSaved} />

      <HabitsSection habits={habits} />

      {tips && tips.length > 0 && stats && (
        <Timeline
          tips={tips}
          duration={stats.duration}
          onSeek={handleTipClick}
          seekTime={seekTime}
        />
      )}

      {(() => {
        if (!tips || tips.length === 0) return (
          <div className="summary-card">
            <p>No specific coaching tips detected. Try uploading a longer match or ensure the video shows the game UI clearly.</p>
          </div>
        )

        const priorityTips = tips.filter(t => t.priority === 'high')
        const normalTips = tips.filter(t => t.priority !== 'high')

        const renderTipCard = (tip, i) => {
          const tipKey = `tip-${i}-${tip.timestamp}-${tip.type}`
          const isSaved = savedIds.has(tipKey)
          return (
            <div
              key={tipKey}
              className={`tip-card clickable ${getSeverityClass(tip.severity)} ${tip.priority === 'high' ? 'priority-high' : ''}`}
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
                  {videoId && (
                    <button
                      type="button"
                      className="clip-export-btn"
                      onClick={(e) => {
                        e.stopPropagation()
                        window.open(`${API_URL}/clip/${videoId}/${tip.timestamp}`)
                      }}
                    >
                      Export Clip
                    </button>
                  )}
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
        }

        return (
          <>
            {priorityTips.length > 0 && (
              <div className="tips-section priority-tips-section">
                <h2>Priority Moments</h2>
                {priorityTips.map((tip, i) => renderTipCard(tip, i))}
              </div>
            )}

            {normalTips.length > 0 && (
              <div className="tips-section">
                <button
                  type="button"
                  className="show-all-tips-btn"
                  onClick={() => setShowAllTips(prev => !prev)}
                >
                  {showAllTips ? 'Hide' : 'Show'} all {normalTips.length} other moments
                </button>
                {showAllTips && normalTips.map((tip, i) => renderTipCard(tip, priorityTips.length + i))}
              </div>
            )}
          </>
        )
      })()}

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
