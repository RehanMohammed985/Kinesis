import { useEffect, useRef, useState } from 'react'
import { useNav } from '../App.jsx'
import { SAY, SAY_GLYPH } from '../data.js'
import { useKinesis } from '../engine/kinesis.jsx'
import Board from '../ui/Board.jsx'

// Say it: one choice, and the phrase is spoken out loud in the person's own
// voice (their ElevenLabs voice, or system speech if none is set up).
const LAYOUT = {
  columns: 'repeat(4, 1fr)',
  rows: '1fr 1fr 0.42fr',
  areas: '"s0 s1 s2 s3" "s4 s5 s6 s7" "back back back back"',
  phone: { columns: '1fr 1fr', rows: 'repeat(4, 1fr) 0.5fr', areas: '"s0 s1" "s2 s3" "s4 s5" "s6 s7" "back back"' },
}

export default function Say() {
  const k = useKinesis()
  const { go } = useNav()
  const [said, setSaid] = useState(null)
  const timer = useRef(null)
  useEffect(() => () => clearTimeout(timer.current), [])

  const say = (text) => {
    k.act({ action: 'speak', text })
    setSaid(text)
    clearTimeout(timer.current)
    timer.current = setTimeout(() => setSaid(null), 5000)
  }

  const items = [
    ...SAY.map((text, i) => ({ id: `s${i}`, area: `s${i}`, kind: 'phrase', glyph: SAY_GLYPH[i], label: text, onSelect: () => say(text) })),
    { id: 'back', area: 'back', kind: 'quiet', glyph: 'back', label: 'Back', onSelect: () => go('home') },
  ]

  return (
    <>
      <div className="panel said-panel" aria-live="polite">
        {said ? (
          <p className="said"><span className="said-wave" aria-hidden="true"><i /><i /><i /><i /></span>{said}</p>
        ) : (
          <>
            <h1 className="screen-title">Say it out loud</h1>
            <p className="screen-lede">Choose a phrase and Kinesis says it in your own voice.</p>
          </>
        )}
      </div>
      <Board scanKey="say" items={items} layout={LAYOUT} onHelp={() => go('help')} onBack={() => go('home')} />
    </>
  )
}
