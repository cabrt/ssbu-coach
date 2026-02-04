import { useState, useRef } from 'react'
import axios from 'axios'
import CharacterSelect from './CharacterSelect'
import CharacterPortrait from './CharacterPortrait'

const API_URL = 'http://localhost:8000/api'

export default function VideoUpload({ onAnalysisStart, onProgress, onAnalysisComplete, onError, onVideoSelect }) {
  const [dragging, setDragging] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [playerChar, setPlayerChar] = useState('')
  const [opponentChar, setOpponentChar] = useState('')
  const [youAreP1, setYouAreP1] = useState(true) // true = you're left/red (P1), false = you're right/blue (P2)
  const [playerTrigger, setPlayerTrigger] = useState(0)
  const [opponentTrigger, setOpponentTrigger] = useState(0)
  const fileInputRef = useRef()

  const handleCharacterSelect = (player, opponent) => {
    setPlayerChar(player || '')
    setOpponentChar(opponent || '')
  }

  const handlePlayerChange = (char) => {
    setPlayerTrigger(prev => prev + 1)
  }

  const handleOpponentChange = (char) => {
    setOpponentTrigger(prev => prev + 1)
  }

  const handleFile = (file) => {
    if (!file) return
    
    if (!file.type.startsWith('video/')) {
      alert('Please upload a video file')
      return
    }

    setSelectedFile(file)
  }

  const startAnalysis = async () => {
    if (!selectedFile) return

    const videoUrl = URL.createObjectURL(selectedFile)
    onVideoSelect?.(videoUrl)
    onAnalysisStart()
    
    try {
      const formData = new FormData()
      formData.append('file', selectedFile)
      
      // include character selections and which side you are
      let url = `${API_URL}/upload`
      const params = []
      params.push(`you_are_p1=${youAreP1 ? 'true' : 'false'}`)
      if (playerChar) params.push(`player_char=${encodeURIComponent(playerChar)}`)
      if (opponentChar) params.push(`opponent_char=${encodeURIComponent(opponentChar)}`)
      url += '?' + params.join('&')
      
      const { data } = await axios.post(url, formData)
      const videoId = data.video_id
      
      pollForResults(videoId, videoUrl)
    } catch (err) {
      console.error('Upload failed:', err)
      onError()
    }
  }

  const pollForResults = async (videoId, videoUrl) => {
    const poll = async () => {
      try {
        const { data } = await axios.get(`${API_URL}/results/${videoId}`)
        
        if (data.status === 'complete') {
          onAnalysisComplete(data, videoUrl)
          return
        }
        
        if (data.status === 'error') {
          console.error('Analysis failed:', data.error)
          onError()
          return
        }
        
        const progress = data.progress ?? 0
        // Use ETA from backend
        const etaSeconds = data.eta_seconds ?? null
        
        onProgress({ progress, status: data.status || 'processing', etaSeconds })
        setTimeout(poll, 500)
      } catch (err) {
        console.error('Poll failed:', err)
        onError()
      }
    }
    
    poll()
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    handleFile(e.dataTransfer.files[0])
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setDragging(true)
  }

  const handleDragLeave = () => {
    setDragging(false)
  }

  const clearFile = () => {
    setSelectedFile(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  return (
    <div className="upload-screen">
      {/* Left side - shows P1's character (opponent if you're P2, you if you're P1) */}
      <div className="side-portrait left">
        <CharacterPortrait 
          character={youAreP1 ? playerChar : opponentChar} 
          side="left" 
          triggerKey={youAreP1 ? playerTrigger : opponentTrigger}
        />
      </div>

      {/* Center content */}
      <div className="upload-container">
        <div 
          className={`upload-zone ${dragging ? 'dragging' : ''} ${selectedFile ? 'has-file' : ''}`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => !selectedFile && fileInputRef.current?.click()}
        >
          {selectedFile ? (
            <div className="file-selected">
              <span className="file-name">{selectedFile.name}</span>
              <button className="clear-file" onClick={(e) => { e.stopPropagation(); clearFile(); }}>
                Change
              </button>
            </div>
          ) : (
            <>
              <h2>Drop your replay here</h2>
              <p>or click to browse (.mp4, .mov, .webm)</p>
            </>
          )}
          
          <input 
            ref={fileInputRef}
            type="file" 
            accept="video/*"
            onChange={(e) => handleFile(e.target.files[0])}
          />
        </div>

        <div className="player-side-select">
          <span className="player-side-label">I am the</span>
          <div className="player-side-options">
            <label className={youAreP1 ? 'active' : ''}>
              <input
                type="radio"
                name="side"
                checked={youAreP1}
                onChange={() => setYouAreP1(true)}
              />
              <span>Left player (P1)</span>
            </label>
            <label className={!youAreP1 ? 'active' : ''}>
              <input
                type="radio"
                name="side"
                checked={!youAreP1}
                onChange={() => setYouAreP1(false)}
              />
              <span>Right player (P2)</span>
            </label>
          </div>
        </div>

        <CharacterSelect 
          onSelect={handleCharacterSelect}
          playerChar={playerChar}
          opponentChar={opponentChar}
          onPlayerChange={handlePlayerChange}
          onOpponentChange={handleOpponentChange}
          youAreP1={youAreP1}
        />

        <button 
          className="analyze-btn"
          onClick={startAnalysis}
          disabled={!selectedFile}
        >
          {selectedFile ? 'Analyze Replay' : 'Select a Video First'}
        </button>
      </div>

      {/* Right side - shows P2's character (you if you're P2, opponent if you're P1) */}
      <div className="side-portrait right">
        <CharacterPortrait 
          character={youAreP1 ? opponentChar : playerChar} 
          side="right" 
          triggerKey={youAreP1 ? opponentTrigger : playerTrigger}
        />
      </div>
    </div>
  )
}
