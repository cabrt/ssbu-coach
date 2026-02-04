import { useState, useEffect, useRef } from 'react'

// Full body character render URLs from GitHub SmashUltimateAssets
const getCharacterImage = (name) => {
  if (!name) return null
  
  // Map character display names to internal game names
  const internalNames = {
    'Mario': 'mario', 'Donkey Kong': 'donkey', 'Link': 'link', 'Samus': 'samus',
    'Dark Samus': 'samusd', 'Yoshi': 'yoshi', 'Kirby': 'kirby', 'Fox': 'fox',
    'Pikachu': 'pikachu', 'Luigi': 'luigi', 'Ness': 'ness', 'Captain Falcon': 'captain',
    'Jigglypuff': 'purin', 'Peach': 'peach', 'Daisy': 'daisy', 'Bowser': 'koopa',
    'Ice Climbers': 'ice_climber', 'Sheik': 'sheik', 'Zelda': 'zelda', 'Dr. Mario': 'mariod',
    'Pichu': 'pichu', 'Falco': 'falco', 'Marth': 'marth', 'Lucina': 'lucina',
    'Young Link': 'younglink', 'Ganondorf': 'ganon', 'Mewtwo': 'mewtwo', 'Roy': 'roy',
    'Chrom': 'chrom', 'Mr. Game & Watch': 'gamewatch', 'Meta Knight': 'metaknight',
    'Pit': 'pit', 'Dark Pit': 'pitb', 'Zero Suit Samus': 'szerosuit',
    'Wario': 'wario', 'Snake': 'snake', 'Ike': 'ike', 'Pokemon Trainer': 'ptrainer',
    'Diddy Kong': 'diddy', 'Lucas': 'lucas', 'Sonic': 'sonic', 'King Dedede': 'dedede',
    'Olimar': 'pikmin', 'Lucario': 'lucario', 'R.O.B.': 'robot', 'Toon Link': 'toonlink',
    'Wolf': 'wolf', 'Villager': 'murabito', 'Mega Man': 'rockman', 'Wii Fit Trainer': 'wiifit',
    'Rosalina & Luma': 'rosetta', 'Little Mac': 'littlemac', 'Greninja': 'gekkouga',
    'Palutena': 'palutena', 'Pac-Man': 'pacman', 'Robin': 'reflet', 'Shulk': 'shulk',
    'Bowser Jr.': 'koopajr', 'Duck Hunt': 'duckhunt', 'Ryu': 'ryu', 'Ken': 'ken',
    'Cloud': 'cloud', 'Corrin': 'kamui', 'Bayonetta': 'bayonetta', 'Inkling': 'inkling',
    'Ridley': 'ridley', 'Simon': 'simon', 'Richter': 'richter', 'King K. Rool': 'krool',
    'Isabelle': 'shizue', 'Incineroar': 'gaogaen', 'Piranha Plant': 'packun',
    'Joker': 'jack', 'Hero': 'brave', 'Banjo & Kazooie': 'buddy', 'Terry': 'dolly',
    'Byleth': 'master', 'Min Min': 'tantan', 'Steve': 'pickel', 'Sephiroth': 'edge',
    'Pyra': 'eflame', 'Mythra': 'elight', 'Kazuya': 'demon', 'Sora': 'trail',
    'Mii Brawler': 'miifighter', 'Mii Swordfighter': 'miiswordsman', 'Mii Gunner': 'miigunner'
  }
  
  const internalName = internalNames[name]
  
  if (internalName) {
    // Use GitHub SmashUltimateAssets full body renders
    return `https://raw.githubusercontent.com/joaorb64/SmashUltimateAssets/master/chara_0_${internalName}_00.png`
  }
  
  return null
}

// Fallback to initials if image fails
const getInitials = (name) => {
  if (!name) return '?'
  return name.split(' ').map(w => w[0]).join('').substring(0, 2).toUpperCase()
}

export default function CharacterPortrait({ character, side, triggerKey }) {
  const [imageError, setImageError] = useState(false)
  const [showEffect, setShowEffect] = useState(false)
  const [isVisible, setIsVisible] = useState(false)
  const lastTrigger = useRef(null)
  
  useEffect(() => {
    if (character && triggerKey !== lastTrigger.current) {
      lastTrigger.current = triggerKey
      setImageError(false)
      setShowEffect(true)
      setIsVisible(true)
      
      const timer = setTimeout(() => setShowEffect(false), 800)
      return () => clearTimeout(timer)
    }
  }, [character, triggerKey])

  // Reset when character is cleared
  useEffect(() => {
    if (!character) {
      setIsVisible(false)
      setShowEffect(false)
    }
  }, [character])

  if (!character || !isVisible) return null

  const imageUrl = getCharacterImage(character)

  return (
    <div className={`character-portrait-full ${side} ${showEffect ? 'reveal' : ''}`}>
      {showEffect && (
        <div className="smash-effect-full">
          <div className="slash-diagonal"></div>
          <div className="flash-overlay"></div>
          <div className="impact-lines">
            {[...Array(12)].map((_, i) => (
              <div key={i} className="impact-line" style={{ '--i': i }}></div>
            ))}
          </div>
        </div>
      )}
      
      <div className="portrait-full-container">
        {!imageError && imageUrl ? (
          <img 
            src={imageUrl} 
            alt={character}
            onError={() => setImageError(true)}
            className="character-image-full"
          />
        ) : (
          <div className="character-fallback-full">
            {getInitials(character)}
          </div>
        )}
      </div>
      
      <div className={`name-banner ${side}`}>
        <span className="fighter-name">{character}</span>
      </div>
    </div>
  )
}
