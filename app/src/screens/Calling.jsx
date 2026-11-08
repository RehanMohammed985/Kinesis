import { useEffect, useRef, useState } from 'react'
import { useNav } from '../App.jsx'
import { CONTACTS } from '../data.js'
import { useKinesis } from '../engine/kinesis.jsx'
import Board from '../ui/Board.jsx'

// Outgoing: ringing, then connected with a timer. Incoming: answer or decline,
// with the lens starting on Answer.
export default function Calling({ contact = 'linda', incoming = false }) {
  const k = useKinesis()
  const { go } = useNav()
  const person = CONTACTS.find((c) => c.id === contact) || CONTACTS[0]
  const [phase, setPhase] = useState(incoming ? 'incoming' : 'ringing')
  const [secs, setSecs] = useState(0)
  const dialed = useRef(false)

  useEffect(() => {
    if (phase === 'ringing') {
      if (!dialed.current) { dialed.current = true; k.act({ action: 'call', contact: person.id }) }
      const t = setTimeout(() => setPhase('connected'), 3200)
      return () => clearTimeout(t)
    }
    if (phase === 'connected') {
      const t = setInterval(() => setSecs((s) => s + 1), 1000)
      return () => clearInterval(t)
    }
  }, [phase]) // eslint-disable-line react-hooks/exhaustive-deps

  const hangUp = () => {
    k.send({ type: 'action', action: 'hangup' })
    k.say(`Call with ${person.name} ended`)
    go('home')
  }

  const items =
    phase === 'incoming'
      ? [
          { id: 'answer', area: 'a', glyph: 'call', kind: 'big', label: 'Answer', onSelect: () => { k.send({ type: 'action', action: 'answer' }); setPhase('connected') } },
          { id: 'decline', area: 'b', glyph: 'hangup', label: 'Decline', sub: 'Sends "I\'ll call you back"', onSelect: () => { k.act({ action: 'message', contact: person.id, text: "Can't talk right now, I'll call you back" }); go('home') } },
        ]
      : [
          { id: 'hangup', area: 'a', glyph: 'hangup', kind: 'big', label: 'Hang up', onSelect: hangUp },
          { id: 'talk', area: 'b', glyph: 'talk', label: 'Talk', sub: 'Pick replies during the call', onSelect: () => go('talk') },
        ]

  const status =
    phase === 'incoming' ? 'is calling' : phase === 'ringing' ? 'Calling' : `${Math.floor(secs / 60)}:${String(secs % 60).padStart(2, '0')}`

  return (
    <>
      <div className="panel callcard" aria-live="polite">
        <span className={`avatar ${phase !== 'connected' ? 'ring' : ''}`} aria-hidden="true">{person.initials}</span>
        <div>
          {phase === 'ringing' && <span className="heard-who">{status}</span>}
          <h1 className="screen-title">{person.name} {phase === 'incoming' && status}</h1>
          <p className="screen-lede">{phase === 'connected' ? `Connected, ${status}` : person.sub}</p>
        </div>
      </div>
      <Board scanKey={`calling-${phase}`} items={items} layout={{ columns: '1.4fr 1fr', rows: '1fr', areas: '"a b"' }} onHelp={() => go('help')} onBack={phase === 'incoming' ? undefined : hangUp} />
    </>
  )
}
