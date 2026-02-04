import { useState, useEffect } from 'react'
import axios from 'axios'

const API_URL = 'http://localhost:8000/api'

export default function SavedAnalysesPage({ 
  onBack, 
  onLoad,
  // Loading state from parent (persists across navigation)
  loadingId,
  loadingType,
  loadingProgress,
  loadingEta,
  showModal,
  readyAnalysis,
  showReadyNotification,
  onStartLoading,
  onCloseModal,
  onCancelProcessing,
  onLoadReady,
  onDismissNotification,
}) {
  const [savedAnalyses, setSavedAnalyses] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchSavedAnalyses()
  }, [])

  const fetchSavedAnalyses = async () => {
    try {
      setLoading(true)
      const { data } = await axios.get(`${API_URL}/saved-analyses`)
      setSavedAnalyses(data.analyses || [])
    } catch (err) {
      setError('Failed to load saved analyses')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleLoad = (videoId, switchPerspective = false) => {
    // Delegate to parent handler
    onStartLoading(videoId, switchPerspective, savedAnalyses)
  }
  
  const formatEta = (seconds) => {
    if (seconds == null || seconds <= 0) return ''
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    if (mins > 0) {
      return `${mins}m ${secs}s`
    }
    return `${secs}s`
  }

  const handleDelete = async (videoId) => {
    if (!confirm('Are you sure you want to delete this saved analysis?')) {
      return
    }
    
    try {
      await axios.delete(`${API_URL}/saved-analysis/${videoId}`)
      setSavedAnalyses(prev => prev.filter(a => a.video_id !== videoId))
    } catch (err) {
      setError('Failed to delete analysis')
      console.error(err)
    }
  }

  const formatDate = (isoString) => {
    if (!isoString) return 'Unknown'
    const date = new Date(isoString)
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  const formatCharName = (name) => {
    if (!name) return 'Unknown'
    return name.charAt(0).toUpperCase() + name.slice(1)
  }

  return (
    <div className="saved-analyses-page">
      <button className="back-btn" onClick={onBack}>← Back</button>
      
      <h1>Saved Analyses</h1>
      <p className="page-description">Load a previously analyzed match without re-processing</p>

      {error && (
        <div className="error-message">{error}</div>
      )}

      {showModal && loadingId && (
        <div className="loading-overlay">
          <div className="loading-modal">
            <button className="modal-close-btn" onClick={onCloseModal} title="Continue in background">×</button>
            <h3>Loading Analysis</h3>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${loadingProgress}%` }} />
            </div>
            <p>Re-processing video for suggestions... {loadingProgress}%</p>
            {loadingEta != null && loadingEta > 0 && (
              <p className="loading-eta">ETA: {formatEta(loadingEta)}</p>
            )}
            <div className="modal-actions">
              <button className="modal-background-btn" onClick={onCloseModal}>
                Continue in Background
              </button>
              <button className="modal-cancel-btn" onClick={onCancelProcessing}>
                Stop Processing
              </button>
            </div>
          </div>
        </div>
      )}

      {showReadyNotification && readyAnalysis && (
        <div className="ready-notification">
          <span>Analysis ready!</span>
          <button onClick={onLoadReady}>Load Now</button>
          <button className="dismiss-btn" onClick={onDismissNotification}>×</button>
        </div>
      )}
      
      {loadingId && !showModal && (
        <div className="background-processing-indicator">
          <span>Processing in background... {loadingProgress}% (ETA: {formatEta(loadingEta)})</span>
          <button 
            className="background-stop-btn" 
            onClick={onCancelProcessing}
            title="Stop processing"
          >
            Stop
          </button>
        </div>
      )}

      {loading ? (
        <div className="loading-state">Loading saved analyses...</div>
      ) : savedAnalyses.length === 0 ? (
        <div className="empty-state">
          <p>No saved analyses yet.</p>
          <p>After analyzing a video, click "Save Analysis" to save it for later.</p>
        </div>
      ) : (
        <div className="saved-analyses-list">
          {savedAnalyses.map((analysis) => (
            <div key={analysis.video_id} className="saved-analysis-card">
              <div className="saved-analysis-info">
                <div className="saved-analysis-matchup">
                  <span className="player-char">{formatCharName(analysis.player_char)}</span>
                  <span className="vs">vs</span>
                  <span className="opponent-char">{formatCharName(analysis.opponent_char)}</span>
                </div>
                <div className="saved-analysis-meta">
                  <span className="perspective">
                    Analyzed as: {analysis.you_are_p1 ? 'P1 (Left)' : 'P2 (Right)'}
                  </span>
                  <span className="saved-date">Saved: {formatDate(analysis.saved_at)}</span>
                </div>
              </div>
              
              <div className="saved-analysis-actions">
                <button 
                  className="load-btn"
                  onClick={() => handleLoad(analysis.video_id, false)}
                  disabled={loadingId === analysis.video_id}
                >
                  {loadingId === analysis.video_id && loadingType === 'normal' ? 'Loading...' : 'Load'}
                </button>
                <button 
                  className="load-switch-btn"
                  onClick={() => handleLoad(analysis.video_id, true)}
                  disabled={loadingId === analysis.video_id}
                  title="Load from opponent's perspective"
                >
                  {loadingId === analysis.video_id && loadingType === 'switch' ? 'Loading...' : `Load as ${analysis.you_are_p1 ? 'P2' : 'P1'}`}
                </button>
                <button 
                  className="delete-btn"
                  onClick={() => handleDelete(analysis.video_id)}
                  disabled={loadingId === analysis.video_id}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
