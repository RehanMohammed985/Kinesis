import { useCallback, useEffect, useRef, useState } from 'react'
import { useNav } from '../App.jsx'
import { CANNED_REPLIES, HEARD_SAMPLES, PERSON } from '../data.js'
import { useKinesis } from '../engine/kinesis.jsx'
import Board from '../ui/Board.jsx'

// Talk: the room mic hears someone, four likely replies appear, the person
// picks one and it is spoken in their own voice. Replies come from the core
// (ml-agent), else from Gemini through the dev server, else canned.
const LAYOUT = { columns: '1fr 1fr 0.62fr', rows: '1fr 1fr', areas: '"r0 r1 more" "r2 r3 back"' }
const FALLBACK = ['Yes', 'No', 'Can you say that again?', 'Give me a minute']

export default function Talk() {
  const k = useKinesis()
  const { go } = useNav()
  const [heard, setHeard] = useState(HEARD_SAMPLES[0])
  const [replies, setReplies] = useState(CANNED_REPLIES[HEARD_SAMPLES[0].text])
  const [listening, setListening] = useState(false)
  const [round, setRound] = useState(0)
  const sample = useRef(0)
  const coreReplies = useRef(false)
  const lastCore = useRef(0)

  const ask = useCallback(
    async (h) => {
      setHeard(h)
      if (k.mode === 'core') {
        // the core's communication agent answers; fall back if it is slow
        const asked = performance.now()
        k.send({ type: 'heard', speaker: h.speaker, text: h.text })
        await new Promise((r) => setTimeout(r, 3500))
        if (lastCore.current > asked) return
      }
      if (CANNED_REPLIES[h.text] && !k.server.replies) { setReplies(CANNED_REPLIES[h.text]); setRound((r) => r + 1); return }
      try {
        const r = await fetch('/api/replies', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ heard: h.text, persona: PERSON, setting: 'home' }),
        })
        if (!r.ok) throw new Error()
        const { items } = await r.json()
        setReplies(items)
      } catch {
        setReplies(CANNED_REPLIES[h.text] || FALLBACK)
      }
      setRound((r) => r + 1)
    },
    [k.server.replies, k.mode], // eslint-disable-line react-hooks/exhaustive-deps
  )

  // the room mic, through the browser's speech recognition
  useEffect(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SR) return
    const rec = new SR()
    rec.continuous = true
    rec.interimResults = false
    rec.lang = 'en-US'
    rec.onstart = () => setListening(true)
    rec.onend = () => setListening(false)
    rec.onresult = (e) => {
      const text = e.results[e.results.length - 1][0].transcript.trim()
      if (text.split(' ').length >= 2) ask({ speaker: 'Someone nearby', text: text[0].toUpperCase() + text.slice(1) })
    }
    try { rec.start() } catch { /* mic not allowed */ }
    return () => { rec.onend = null; try { rec.stop() } catch { /* already stopped */ } }
  }, [ask])

  // the core's own mic and agent
  useEffect(
    () =>
      k.subscribe((msg) => {
        if (msg.type === 'heard') setHeard({ speaker: msg.speaker || 'Someone nearby', text: msg.text })
        if (msg.type === 'replies') { coreReplies.current = true; lastCore.current = performance.now(); setReplies(msg.items.slice(0, 4)); setRound((r) => r + 1) }
      }),
    [k],
  )

  const items = [
    ...replies.slice(0, 4).map((text, i) => ({
      id: `r${i}`, area: `r${i}`, kind: 'reply', label: text,
      onSelect: () => { k.act({ action: 'speak', text }); k.say(`Said: ${text}`) },
    })),
    {
      id: 'more', area: 'more', kind: 'quiet', glyph: 'more', label: 'Different replies',
      onSelect: () => {
        sample.current = (sample.current + 1) % HEARD_SAMPLES.length
        ask(listening && heard.speaker === 'Someone nearby' ? heard : HEARD_SAMPLES[sample.current])
      },
    },
    { id: 'back', area: 'back', kind: 'quiet', glyph: 'back', label: 'Back', onSelect: () => go('home') },
  ]

  return (
    <>
      <div className="panel heard" aria-live="polite">
        <span className="heard-who">
          {listening && <span className="listening" aria-hidden="true"><i /><i /><i /></span>}
          {heard.speaker} said
        </span>
        <span className="heard-text">{heard.text}</span>
      </div>
      <Board scanKey={`talk-${round}`} items={items} layout={LAYOUT} onHelp={() => go('help')} onBack={() => go('home')} />
    </>
  )
}
