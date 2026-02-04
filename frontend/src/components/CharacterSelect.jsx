import { useState, useEffect } from 'react'
import axios from 'axios'

const API_URL = 'http://localhost:8000/api'

export default function CharacterSelect({ onSelect, playerChar, opponentChar, onPlayerChange, onOpponentChange, youAreP1 = true }) {
  const [characters, setCharacters] = useState([])
  const [searchPlayer, setSearchPlayer] = useState('')
  const [searchOpponent, setSearchOpponent] = useState('')
  const [showPlayerDropdown, setShowPlayerDropdown] = useState(false)
  const [showOpponentDropdown, setShowOpponentDropdown] = useState(false)

  useEffect(() => {
    axios.get(`${API_URL}/characters`)
      .then(res => setCharacters(res.data.characters))
      .catch(err => console.error('Failed to load characters:', err))
  }, [])

  const filterCharacters = (search) => {
    if (!search) return characters
    return characters.filter(c => 
      c.toLowerCase().includes(search.toLowerCase())
    )
  }

  const selectPlayer = (char) => {
    onSelect(char, opponentChar)
    onPlayerChange?.(char)
    setSearchPlayer('')
    setShowPlayerDropdown(false)
  }

  const selectOpponent = (char) => {
    onSelect(playerChar, char)
    onOpponentChange?.(char)
    setSearchOpponent('')
    setShowOpponentDropdown(false)
  }

  // Build the two picker components
  const playerPicker = (
    <div className="character-picker">
      <label>Your Character</label>
      <div className="dropdown-wrapper">
        <input
          type="text"
          placeholder={playerChar || "Search characters..."}
          value={searchPlayer}
          onChange={(e) => {
            setSearchPlayer(e.target.value)
            setShowPlayerDropdown(true)
          }}
          onFocus={() => setShowPlayerDropdown(true)}
          onBlur={() => setTimeout(() => setShowPlayerDropdown(false), 200)}
        />
        {showPlayerDropdown && (
          <div className="dropdown-list">
            {filterCharacters(searchPlayer).map(char => (
              <div 
                key={char} 
                className={`dropdown-item ${char === playerChar ? 'selected' : ''}`}
                onClick={() => selectPlayer(char)}
              >
                {char}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )

  const opponentPicker = (
    <div className="character-picker">
      <label>Opponent Character</label>
      <div className="dropdown-wrapper">
        <input
          type="text"
          placeholder={opponentChar || "Search characters..."}
          value={searchOpponent}
          onChange={(e) => {
            setSearchOpponent(e.target.value)
            setShowOpponentDropdown(true)
          }}
          onFocus={() => setShowOpponentDropdown(true)}
          onBlur={() => setTimeout(() => setShowOpponentDropdown(false), 200)}
        />
        {showOpponentDropdown && (
          <div className="dropdown-list">
            {filterCharacters(searchOpponent).map(char => (
              <div 
                key={char} 
                className={`dropdown-item ${char === opponentChar ? 'selected' : ''}`}
                onClick={() => selectOpponent(char)}
              >
                {char}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )

  return (
    <div className="character-select">
      <div className="character-select-grid">
        {/* Left side: Player's char if P1, Opponent's char if P2 */}
        {youAreP1 ? playerPicker : opponentPicker}
        
        <div className="vs-divider"></div>
        
        {/* Right side: Opponent's char if P1, Player's char if P2 */}
        {youAreP1 ? opponentPicker : playerPicker}
      </div>
    </div>
  )
}
