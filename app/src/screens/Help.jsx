import { useEffect, useRef, useState } from 'react'
import { useNav } from '../App.jsx'
import { CARE_LIST } from '../data.js'
import { useKinesis } from '../engine/kinesis.jsx'
import Board from '../ui/Board.jsx'

export default function Help({ reason, text }) {
  const k = useKinesis()
  const { go } = useNav()
  const sent = useRef(false)
  const [at] = useState(() => new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }).toLowerCase())

  useEffect(() => {
    if (sent.current || reason === 'seizure') return // the monitor already alerted
    sent.current = true
    k.act({ action: 'help' })
  }, [k, reason])

  const items = [
    { id: 'ok', area: 'a', kind: 'big', glyph: 'check', label: "I'm okay now", sub: 'Tells everyone it is resolved', onSelect: () => { k.act({ action: 'help_clear' }); k.say('Told everyone you are okay'); go('home') } },
    { id: 'call', area: 'b', glyph: 'call', label: 'Call Linda', onSelect: () => go('calling', { contact: 'linda' }) },
  ]

  return (
    <>
      <div className="panel" aria-live="assertive">
        {reason === 'seizure' ? (
          <>
            <h1 className="screen-title" style={{ fontSize: 'var(--t-xxl)' }}>Seizure-like activity</h1>
            <p className="screen-lede">Kinesis noticed a sustained, rhythmic change in brain activity at {at}. {CARE_LIST.join(' and ')} were alerted. The episode is logged for Dr. Patel. This is a warning, not a diagnosis.</p>
          </>
        ) : (
          <>
            <h1 className="screen-title" style={{ fontSize: 'var(--t-xxl)' }}>Help is on the way</h1>
            <p className="screen-lede">{CARE_LIST.join(' and ')} were alerted at {at}. Kinesis said "I need help" out loud.</p>
          </>
        )}
      </div>
      <Board scanKey="help" items={items} layout={{ columns: '1.4fr 1fr', rows: '1fr', areas: '"a b"' }} help={false} />
    </>
  )
}
