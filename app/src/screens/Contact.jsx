import { useState } from 'react'
import { useNav } from '../App.jsx'
import { CONTACTS, QUICK_TEXTS } from '../data.js'
import { useKinesis } from '../engine/kinesis.jsx'
import Board from '../ui/Board.jsx'

// One person: call them, or send one of a few texts. Each text also goes as a
// voice message in the person's own voice (ElevenLabs). Texts go out through
// the core (practice mode until it is set live) and show up on the caregiver page.
const LAYOUT = {
  columns: '1.25fr 1fr 1fr',
  rows: '1fr 1fr',
  areas: '"call t0 t1" "call t2 back"',
  phone: { columns: '1fr 1fr', rows: '1.2fr 1fr 1fr', areas: '"call call" "t0 t1" "t2 back"' },
}

export default function Contact({ contact = 'linda' }) {
  const k = useKinesis()
  const { go } = useNav()
  const person = CONTACTS.find((c) => c.id === contact) || CONTACTS[0]
  const [sent, setSent] = useState(null)

  const text = (t) => {
    k.act({ action: 'message', contact: person.id, text: t, voice: true })
    setSent(t)
  }

  const items = [
    { id: 'call', area: 'call', kind: 'big', glyph: 'call', label: `Call ${person.name}`, onSelect: () => go('calling', { contact: person.id }) },
    ...QUICK_TEXTS.map((t, i) => ({ id: `t${i}`, area: `t${i}`, kind: 'phrase', glyph: 'text', label: t, sub: 'Text and voice message', onSelect: () => text(t) })),
    { id: 'back', area: 'back', kind: 'quiet', glyph: 'back', label: 'Back', onSelect: () => go('call') },
  ]

  return (
    <>
      <div className="panel callcard" aria-live="polite">
        <span className="avatar" aria-hidden="true">{person.initials}</span>
        <div>
          <h1 className="screen-title">{person.name}</h1>
          <p className="screen-lede">{sent ? <>Sent: <b>{sent}</b></> : person.sub}</p>
        </div>
      </div>
      <Board scanKey={`contact-${person.id}`} items={items} layout={LAYOUT} onHelp={() => go('help')} onBack={() => go('call')} />
    </>
  )
}
