import { useEffect, useState } from 'react'
import '../styles.css'

// What a caregiver sees on their phone: only the messages Maya chose to send.
// Open http://<laptop-ip>:5173/#/caregiver on any phone on the same wifi.
const LABEL = { help: 'Needs help', message: 'Message', call: 'Calling you', report: 'Report sent' }

function when(ts) {
  return new Date(ts).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }).toLowerCase()
}

function chime() {
  try {
    const ctx = new AudioContext()
    ;[880, 660, 880].forEach((f, i) => {
      const o = ctx.createOscillator()
      const g = ctx.createGain()
      o.frequency.value = f
      const t = ctx.currentTime + i * 0.22
      g.gain.setValueAtTime(0.0001, t)
      g.gain.exponentialRampToValueAtTime(0.25, t + 0.02)
      g.gain.exponentialRampToValueAtTime(0.0001, t + 0.2)
      o.connect(g).connect(ctx.destination)
      o.start(t)
      o.stop(t + 0.21)
    })
  } catch { /* no audio */ }
}

export default function Caregiver() {
  const [items, setItems] = useState([])
  const [live, setLive] = useState(false)

  useEffect(() => {
    fetch('/api/outbox').then((r) => r.json()).then(setItems).catch(() => {})
    const es = new EventSource('/api/outbox/stream')
    es.onopen = () => setLive(true)
    es.onerror = () => setLive(false)
    es.onmessage = (e) => {
      const msg = JSON.parse(e.data)
      setItems((xs) => [msg, ...xs])
      if (msg.kind === 'help') {
        chime()
        navigator.vibrate?.([300, 120, 300])
      }
    }
    return () => es.close()
  }, [])

  return (
    <main className="care">
      <h1>Messages from Maya</h1>
      <p className="who">{live ? 'Live. Only what Maya chooses to send shows up here.' : 'Connecting to Maya\'s Kinesis.'}</p>
      {items.length === 0 && <p className="empty">Nothing yet. When Maya sends a message or asks for help, it appears here.</p>}
      {items.map((m, i) => (
        <article key={`${m.at}-${i}`} className={`msg ${m.kind}`}>
          <span className="meta">{LABEL[m.kind] || 'Update'}{m.to ? `, to ${m.to}` : ''}, {when(m.at)}</span>
          <span className="text">{m.text}</span>
        </article>
      ))}
    </main>
  )
}
