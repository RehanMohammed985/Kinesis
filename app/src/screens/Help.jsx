import { useEffect, useRef, useState } from 'react'
import { useNav } from '../App.jsx'
import { CARE_LIST } from '../data.js'
import { useKinesis } from '../engine/kinesis.jsx'
import Board from '../ui/Board.jsx'

export default function Help() {
  const k = useKinesis()
  const { go } = useNav()
  const sent = useRef(false)
  const [at] = useState(() => new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }).toLowerCase())

  useEffect(() => {
    if (sent.current) return
    sent.current = true
    k.act({ action: 'help' })
  }, [k])

  const items = [
    { id: 'ok', area: 'a', kind: 'big', glyph: 'check', label: "I'm okay now", sub: 'Tells everyone it is resolved', onSelect: () => { k.act({ action: 'help_clear' }); k.say('Told everyone you are okay'); go('home') } },
    { id: 'call', area: 'b', glyph: 'call', label: 'Call Sam', onSelect: () => go('calling', { contact: 'sam' }) },
  ]

  return (
    <>
      <div className="panel" aria-live="assertive">
        <h1 className="screen-title" style={{ fontSize: 'var(--t-xxl)' }}>Help is on the way</h1>
        <p className="screen-lede">{CARE_LIST.join(' and ')} were alerted at {at}. Kinesis said "I need help" out loud.</p>
      </div>
      <Board scanKey="help" items={items} layout={{ columns: '1.4fr 1fr', rows: '1fr', areas: '"a b"' }} help={false} />
    </>
  )
}
