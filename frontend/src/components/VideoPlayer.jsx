import { useRef, useState, useEffect } from 'react'
import { saveSuggestion } from '../lib/suggestionsStore'

export default function VideoPlayer({ videoUrl, videoId, currentTime, onTimeUpdate, suggestionAtTime, suggestionLoading, playerChar }) {
  const videoRef = useRef(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [duration, setDuration] = useState(0)
  const [progress, setProgress] = useState(0)
  const [savedSuggestions, setSavedSuggestions] = useState(new Set())

  useEffect(() => {
    if (videoRef.current && currentTime !== undefined) {
      videoRef.current.currentTime = currentTime
    }
  }, [currentTime])

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration)
    }
  }

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      const current = videoRef.current.currentTime
      const d = videoRef.current.duration
      setProgress(d > 0 ? (current / d) * 100 : 0)
      onTimeUpdate?.(current)
    }
  }

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause()
      } else {
        videoRef.current.play()
      }
      setIsPlaying(!isPlaying)
    }
  }

  const handleSeek = (e) => {
    const rect = e.currentTarget.getBoundingClientRect()
    const percent = (e.clientX - rect.left) / rect.width
    if (videoRef.current) {
      videoRef.current.currentTime = percent * duration
    }
  }

  const seekRelative = (seconds) => {
    if (videoRef.current) {
      videoRef.current.currentTime += seconds
    }
  }

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="video-player">
      <div className="video-container">
        <video
          ref={videoRef}
          src={videoUrl}
          onLoadedMetadata={handleLoadedMetadata}
          onTimeUpdate={handleTimeUpdate}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
        />
      </div>
      
      <div className="video-controls">
        <div className="control-buttons">
          <button onClick={() => seekRelative(-10)} className="seek-btn">-10s</button>
          <button onClick={togglePlay} className="play-btn">
            {isPlaying ? '⏸' : '▶'}
          </button>
          <button onClick={() => seekRelative(10)} className="seek-btn">+10s</button>
        </div>
        
        <div className="progress-container" onClick={handleSeek}>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress}%` }} />
          </div>
        </div>
        
        <div className="time-display">
          {formatTime(videoRef.current?.currentTime || 0)} / {formatTime(duration)}
        </div>

        <div className="video-suggestion">
          {suggestionLoading ? (
            <p className="video-suggestion-loading">Getting suggestion...</p>
          ) : suggestionAtTime ? (
            <div className="video-suggestion-content">
              <p className="video-suggestion-text">{suggestionAtTime}</p>
              {(() => {
                const currentVideoTime = videoRef.current?.currentTime || 0
                const suggestionKey = `${Math.floor(currentVideoTime)}-${suggestionAtTime?.slice(0, 50)}`
                const isSaved = savedSuggestions.has(suggestionKey)
                return (
                  <button
                    type="button"
                    className={`save-contextual-btn ${isSaved ? 'saved' : ''}`}
                    disabled={isSaved}
                    onClick={() => {
                      if (!isSaved) {
                        saveSuggestion({
                          character: playerChar || 'Unknown',
                          message: suggestionAtTime,
                          type: 'contextual_advice',
                          severity: 'info',
                          timestamp: currentVideoTime,
                          videoId: videoId,
                          videoName: videoId ? `${videoId}.mp4` : null,
                        })
                        setSavedSuggestions(prev => new Set(prev).add(suggestionKey))
                      }
                    }}
                  >
                    {isSaved ? 'Saved!' : 'Save to my notes'}
                  </button>
                )
              })()}
            </div>
          ) : (
            <p className="video-suggestion-hint">Scrub to a moment to see contextual advice</p>
          )}
        </div>
      </div>
    </div>
  )
}
