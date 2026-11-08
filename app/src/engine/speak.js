// Two voices.
// The user's own voice (ElevenLabs clone through /api/speak, cached on disk by
// the dev server so repeat phrases cost no credits). Falls back to system
// speech if no key is set.
// The guide voice reads options during spoken scanning. It is only for the
// user, so it uses free system speech and never spends credits.

// One audio element for the whole session. iPhone and iPad only let a page
// play sound after the person has touched it once; the first tap anywhere
// plays a silent clip on this element, and from then on it can play phrases
// chosen by headset inputs too.
const player = typeof Audio !== 'undefined' ? new Audio() : null
const SILENT = 'data:audio/wav;base64,UklGRrQBAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YZABAACAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICA'
const memo = new Map()
let unlocked = false

export function unlockAudio() {
  if (unlocked || !player) return
  unlocked = true
  player.src = SILENT
  player.play().catch(() => { unlocked = false })
  if ('speechSynthesis' in window) {
    const u = new SpeechSynthesisUtterance(' ')
    u.volume = 0
    window.speechSynthesis.speak(u)
  }
}

// Fetch a phrase ahead of time so it plays the instant it is chosen.
export async function preload(text) {
  if (!text || memo.has(text)) return
  try {
    const r = await fetch('/api/speak', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text }) })
    if (r.ok) memo.set(text, URL.createObjectURL(await r.blob()))
  } catch { /* plays on demand instead */ }
}

export async function speakAsUser(text) {
  if (!text) return
  stopAll()
  try {
    let url = memo.get(text)
    if (!url) {
      const r = await fetch('/api/speak', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      })
      if (!r.ok) throw new Error(await r.text())
      url = URL.createObjectURL(await r.blob())
      memo.set(text, url)
    }
    player.src = url
    await player.play()
  } catch {
    systemSay(text, { rate: 1 })
  }
}

export function speakAsGuide(text) {
  if (!text) return
  systemSay(text, { rate: 1.1, volume: 0.8 })
}

function systemSay(text, { rate = 1, volume = 1 } = {}) {
  if (!('speechSynthesis' in window)) return
  window.speechSynthesis.cancel()
  const u = new SpeechSynthesisUtterance(text)
  u.rate = rate
  u.volume = volume
  window.speechSynthesis.speak(u)
}

export function stopAll() {
  if (player && !player.paused) player.pause()
  if ('speechSynthesis' in window) window.speechSynthesis.cancel()
}
