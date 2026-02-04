import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import VideoUpload from './components/VideoUpload'
import AnalysisResults from './components/AnalysisResults'
import CharacterSuggestionsPage from './pages/CharacterSuggestionsPage'
import SavedAnalysesPage from './pages/SavedAnalysesPage'
import './App.css'

const API_URL = 'http://localhost:8000/api'

function formatTime(seconds) {
  if (seconds == null) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function formatEta(seconds) {
  if (seconds == null || seconds <= 0) return ''
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  if (mins > 0) {
    return `${mins}m ${secs}s`
  }
  return `${secs}s`
}

function TipVideoViewer({ tipVideo, onBack }) {
  const videoRef = useRef(null)
  const [isReady, setIsReady] = useState(false)

  useEffect(() => {
    // Seek to start time once video is loaded
    if (videoRef.current && isReady && tipVideo.startTime != null) {
      videoRef.current.currentTime = tipVideo.startTime
      videoRef.current.play().catch(() => {}) // Auto-play, ignore if blocked
    }
  }, [isReady, tipVideo.startTime])

  const { suggestion } = tipVideo

  return (
    <div className="tip-video-viewer">
      <header className="tip-video-header">
        <button type="button" className="back-btn" onClick={onBack}>
          ← Back to suggestions
        </button>
        <h2>Reviewing saved tip</h2>
      </header>

      <div className="tip-video-content">
        <div className="tip-video-wrapper">
          <video
            ref={videoRef}
            src={tipVideo.videoUrl}
            controls
            onLoadedMetadata={() => setIsReady(true)}
          />
        </div>

        <div className="tip-video-info">
          <div className="tip-video-suggestion-card">
            <p className="tip-video-message">{suggestion?.message}</p>
            <div className="tip-video-meta">
              <span className="tip-video-time">@{formatTime(suggestion?.timestamp)}</span>
              <span className="tip-video-type">{suggestion?.type?.replace('_', ' ')}</span>
            </div>
          </div>
          <p className="tip-video-note">
            Video starts 5 seconds before the tip timestamp for context.
          </p>
        </div>
      </div>
    </div>
  )
}

function App() {
  const [view, setView] = useState('home') // 'home' | 'suggestions' | 'saved' | 'watch-tip'
  const [analysis, setAnalysis] = useState(null)
  const [videoUrl, setVideoUrl] = useState(null)
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [progressStatus, setProgressStatus] = useState('') // 'extracting' | 'analyzing'
  const [etaSeconds, setEtaSeconds] = useState(null)
  const [tipVideo, setTipVideo] = useState(null) // { videoUrl, startTime, suggestion }
  
  // Saved analysis loading state (persists across page navigation)
  const [savedLoadingId, setSavedLoadingId] = useState(null)
  const [savedLoadingType, setSavedLoadingType] = useState(null)
  const [savedLoadingProgress, setSavedLoadingProgress] = useState(0)
  const [savedLoadingEta, setSavedLoadingEta] = useState(null)
  const [savedShowModal, setSavedShowModal] = useState(false)
  const [savedReadyAnalysis, setSavedReadyAnalysis] = useState(null)
  const [savedShowReadyNotification, setSavedShowReadyNotification] = useState(false)
  
  // Refs for background processing
  const savedProcessingRef = useRef(null)
  const savedAbortControllerRef = useRef(null)

  const handleReset = () => {
    setAnalysis(null)
    if (videoUrl) {
      URL.revokeObjectURL(videoUrl)
    }
    setVideoUrl(null)
    setProgress(0)
  }

  const handleLoadSaved = (savedAnalysis, savedVideoUrl) => {
    setAnalysis(savedAnalysis)
    setVideoUrl(savedVideoUrl)
    setView('home')
    // Clear any pending ready analysis
    setSavedReadyAnalysis(null)
    setSavedShowReadyNotification(false)
  }

  const handleStartSavedLoading = async (videoId, switchPerspective, savedAnalyses) => {
    // If there's already a ready analysis for this video, load it immediately
    if (savedReadyAnalysis && savedReadyAnalysis.videoId === videoId) {
      handleLoadSaved(savedReadyAnalysis.data, savedReadyAnalysis.videoUrl)
      return
    }
    
    try {
      setSavedLoadingId(videoId)
      setSavedLoadingType(switchPerspective ? 'switch' : 'normal')
      setSavedLoadingProgress(0)
      setSavedShowModal(true)
      setSavedShowReadyNotification(false)
      
      const estimatedSeconds = switchPerspective ? 180 : 120
      setSavedLoadingEta(estimatedSeconds)
      
      const startTime = Date.now()
      const etaInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000)
        const remaining = Math.max(0, estimatedSeconds - elapsed)
        setSavedLoadingEta(remaining)
        setSavedLoadingProgress(Math.min(95, Math.floor((elapsed / estimatedSeconds) * 100)))
      }, 1000)
      
      const abortController = new AbortController()
      savedAbortControllerRef.current = abortController
      savedProcessingRef.current = { etaInterval, videoId }
      
      const analysisData = savedAnalyses.find(a => a.video_id === videoId)
      const youAreP1 = switchPerspective ? !analysisData.you_are_p1 : analysisData.you_are_p1
      
      const { data } = await axios.get(`${API_URL}/load-analysis/${videoId}`, {
        params: { you_are_p1: youAreP1 ? 'true' : 'false' },
        signal: abortController.signal
      })
      
      clearInterval(etaInterval)
      savedProcessingRef.current = null
      savedAbortControllerRef.current = null
      
      const loadedVideoUrl = `${API_URL}/video/${videoId}`
      
      // Check if modal is still showing (user didn't background it)
      // We need to check the current state, but since this is async, we'll use a ref or just load
      setSavedLoadingProgress(100)
      setSavedLoadingEta(0)
      
      // Store the ready analysis - will be loaded when user clicks or if modal still open
      setSavedReadyAnalysis({ videoId, data, videoUrl: loadedVideoUrl })
      setSavedShowReadyNotification(true)
      setSavedShowModal(false)
      
    } catch (err) {
      if (axios.isCancel(err) || err.name === 'CanceledError' || err.code === 'ERR_CANCELED') {
        console.log('Processing cancelled by user')
      } else {
        console.error('Failed to load analysis:', err)
      }
    } finally {
      setSavedLoadingId(null)
      setSavedLoadingType(null)
      setSavedLoadingProgress(0)
      setSavedLoadingEta(null)
      savedAbortControllerRef.current = null
    }
  }

  const handleCloseSavedModal = () => {
    setSavedShowModal(false)
  }

  const handleCancelSavedProcessing = () => {
    if (savedAbortControllerRef.current) {
      savedAbortControllerRef.current.abort()
      savedAbortControllerRef.current = null
    }
    if (savedProcessingRef.current?.etaInterval) {
      clearInterval(savedProcessingRef.current.etaInterval)
      savedProcessingRef.current = null
    }
    setSavedLoadingId(null)
    setSavedLoadingType(null)
    setSavedLoadingProgress(0)
    setSavedLoadingEta(null)
    setSavedShowModal(false)
    setSavedReadyAnalysis(null)
    setSavedShowReadyNotification(false)
  }

  const handleLoadReadyAnalysis = () => {
    if (savedReadyAnalysis) {
      handleLoadSaved(savedReadyAnalysis.data, savedReadyAnalysis.videoUrl)
    }
  }

  const handleWatchTipVideo = ({ videoUrl, videoId, startTime, suggestion }) => {
    setTipVideo({ videoUrl, videoId, startTime, suggestion })
    setView('watch-tip')
  }

  // Global background processing indicator (shows on all pages except saved analyses page)
  const globalBackgroundIndicator = savedLoadingId && !savedShowModal && view !== 'saved' && (
    <div className="background-processing-indicator global">
      <span>Loading saved analysis... {savedLoadingProgress}% (ETA: {formatEta(savedLoadingEta)})</span>
      <button 
        className="background-stop-btn" 
        onClick={handleCancelSavedProcessing}
        title="Stop processing"
      >
        Stop
      </button>
    </div>
  )

  // Global ready notification (shows on all pages)
  const globalReadyNotification = savedShowReadyNotification && savedReadyAnalysis && view !== 'saved' && (
    <div className="ready-notification">
      <span>Analysis ready!</span>
      <button onClick={handleLoadReadyAnalysis}>Load Now</button>
      <button className="dismiss-btn" onClick={() => setSavedShowReadyNotification(false)}>×</button>
    </div>
  )

  if (view === 'suggestions') {
    return (
      <div className="app">
        {globalBackgroundIndicator}
        {globalReadyNotification}
        <CharacterSuggestionsPage 
          onBack={() => setView('home')} 
          onWatchVideo={handleWatchTipVideo}
        />
      </div>
    )
  }

  if (view === 'watch-tip' && tipVideo) {
    return (
      <div className="app">
        {globalBackgroundIndicator}
        {globalReadyNotification}
        <TipVideoViewer 
          tipVideo={tipVideo}
          onBack={() => {
            setTipVideo(null)
            setView('suggestions')
          }}
        />
      </div>
    )
  }

  if (view === 'saved') {
    return (
      <div className="app">
        <SavedAnalysesPage 
          onBack={() => setView('home')} 
          onLoad={handleLoadSaved}
          // Pass loading state as props
          loadingId={savedLoadingId}
          loadingType={savedLoadingType}
          loadingProgress={savedLoadingProgress}
          loadingEta={savedLoadingEta}
          showModal={savedShowModal}
          readyAnalysis={savedReadyAnalysis}
          showReadyNotification={savedShowReadyNotification}
          onStartLoading={handleStartSavedLoading}
          onCloseModal={handleCloseSavedModal}
          onCancelProcessing={handleCancelSavedProcessing}
          onLoadReady={handleLoadReadyAnalysis}
          onDismissNotification={() => setSavedShowReadyNotification(false)}
        />
      </div>
    )
  }

  return (
    <div className={`app ${analysis ? 'has-results' : ''}`}>
      {globalBackgroundIndicator}
      {globalReadyNotification}
      <header>
        <h1>
          <button type="button" className="header-title-btn" onClick={handleReset}>
            Smash Coach
          </button>
        </h1>
        <p>Upload a replay to get AI-powered coaching feedback</p>
        <nav className="app-nav">
          <button type="button" className="nav-link-btn" onClick={() => setView('suggestions')}>
            My character suggestions →
          </button>
          <button type="button" className="nav-link-btn" onClick={() => setView('saved')}>
            Saved analyses →
          </button>
        </nav>
      </header>

      <main>
        {!analysis && !loading && (
          <VideoUpload 
            onAnalysisStart={() => {
              setLoading(true)
              setProgress(0)
              setProgressStatus('')
              setEtaSeconds(null)
            }}
            onProgress={({ progress: p, status, etaSeconds: eta }) => {
              setProgress(p)
              setProgressStatus(status === 'analyzing' ? 'analyzing' : 'extracting')
              setEtaSeconds(eta ?? null)
            }}
            onVideoSelect={setVideoUrl}
            onAnalysisComplete={(data, url) => {
              setAnalysis(data)
              setVideoUrl(url)
              setLoading(false)
            }}
            onError={() => setLoading(false)}
          />
        )}

        {loading && (
          <div className="loading">
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress}%` }} />
            </div>
            <p>
              {progressStatus === 'analyzing' ? 'Analyzing gameplay...' : 'Extracting frames...'} {progress}%
            </p>
            {etaSeconds != null && etaSeconds > 0 && progress < 100 && (
              <p className="loading-eta">
                ~{etaSeconds >= 60 ? `${Math.floor(etaSeconds / 60)} min ${etaSeconds % 60} s` : `${etaSeconds} s`} left
              </p>
            )}
          </div>
        )}

        {analysis && (
          <AnalysisResults 
            analysis={analysis}
            videoUrl={videoUrl}
            onReset={handleReset}
          />
        )}
      </main>
    </div>
  )
}

export default App
