// Two voices.
// The user's own voice (ElevenLabs clone through /api/speak, cached on disk by
// the dev server so repeat phrases cost no credits). Falls back to system
// speech if no key is set.
// The guide voice reads options during spoken scanning. It is only for the
// user, so it uses free system speech and never spends credits.

let current = null
const memo = new Map()

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
    current = new Audio(url)
    await current.play()
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
  if (current) {
    current.pause()
    current = null
  }
  if ('speechSynthesis' in window) window.speechSynthesis.cancel()
}
