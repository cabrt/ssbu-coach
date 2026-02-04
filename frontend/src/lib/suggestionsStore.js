const STORAGE_KEY = 'smash_coach_suggestions'

function getStored() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function setStored(list) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list))
  } catch (e) {
    console.warn('Could not save suggestions', e)
  }
}

/**
 * @param {{ character: string, message: string, type: string, severity: string, timestamp?: number, videoId?: string, videoName?: string }} item
 * @returns {string} id of the saved suggestion
 */
export function saveSuggestion(item) {
  const list = getStored()
  const id = `s-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
  const entry = {
    id,
    character: (item.character || 'Unknown').trim(),
    message: item.message || '',
    type: item.type || 'info',
    severity: item.severity || 'info',
    timestamp: item.timestamp,
    videoId: item.videoId || null,
    videoName: item.videoName || null,
    savedAt: new Date().toISOString(),
  }
  list.push(entry)
  setStored(list)
  return id
}

/**
 * @returns {Array<{ id: string, character: string, message: string, type: string, severity: string, timestamp?: number, savedAt: string }>}
 */
export function getSuggestions() {
  return getStored()
}

/**
 * @returns {{ [character: string]: Array }}
 */
export function getSuggestionsByCharacter() {
  const list = getStored()
  const byChar = {}
  for (const s of list) {
    const c = s.character || 'Unknown'
    if (!byChar[c]) byChar[c] = []
    byChar[c].push(s)
  }
  // sort each character's list by savedAt descending
  for (const c of Object.keys(byChar)) {
    byChar[c].sort((a, b) => new Date(b.savedAt) - new Date(a.savedAt))
  }
  return byChar
}

/**
 * @param {string} id
 */
export function removeSuggestion(id) {
  const list = getStored().filter((s) => s.id !== id)
  setStored(list)
}
