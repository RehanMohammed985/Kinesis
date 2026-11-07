import { useState } from 'react'
import { useNav } from '../App.jsx'
import { NOTES, REPORT } from '../data.js'
import { useKinesis } from '../engine/kinesis.jsx'
import Board from '../ui/Board.jsx'

// The day's log, written from what Kinesis can actually measure plus notes the
// person chose. Sending it is a confirm, like every other outbound action.
export default function Report() {
  const k = useKinesis()
  const { go } = useNav()
  const [view, setView] = useState('summary') // summary | note | confirm
  const [notes, setNotes] = useState(REPORT.notes)

  const now = () => new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }).toLowerCase()

  let items, layout
  if (view === 'note') {
    items = [
      ...NOTES.map((n, i) => ({ id: `n${i}`, area: `n${i}`, kind: 'reply', label: n, onSelect: () => { setNotes((ns) => [...ns, [now(), n]]); k.say('Note added'); setView('summary') } })),
      { id: 'back', area: 'back', kind: 'quiet', glyph: 'back', label: 'Back', onSelect: () => setView('summary') },
    ]
    layout = { columns: '1fr 1fr 1fr 0.7fr', rows: '1fr 1fr', areas: '"n0 n1 n2 back" "n3 n4 n5 back"' }
  } else if (view === 'confirm') {
    items = [
      { id: 'cancel', area: 'a', kind: 'safe', glyph: 'cross', label: 'Cancel', sub: 'Nothing is sent', onSelect: () => setView('summary') },
      { id: 'send', area: 'b', glyph: 'send', label: `Send to ${REPORT.doctor}`, sub: 'Through the patient portal', onSelect: () => { k.act({ action: 'report', recipient: 'dr_patel', recipientName: REPORT.doctor }); setView('summary') } },
    ]
    layout = { columns: '1fr 1fr', rows: '1fr', areas: '"a b"' }
  } else {
    items = [
      { id: 'send', area: 'send', glyph: 'send', label: `Send to ${REPORT.doctor}`, onSelect: () => setView('confirm') },
      { id: 'note', area: 'note', glyph: 'note', label: 'Add a note', sub: 'How you feel, in your words', onSelect: () => setView('note') },
      { id: 'back', area: 'back', kind: 'quiet', glyph: 'back', label: 'Back', onSelect: () => go('home') },
    ]
    layout = { columns: '1.2fr 1fr 0.7fr', rows: '1fr', areas: '"send note back"' }
  }

  const max = Math.max(...REPORT.hours)

  return (
    <>
      <div className="panel report">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <h1 className="screen-title">Today</h1>
          <div className="facts">
            {REPORT.facts.map(([n, l]) => (
              <div key={l} className="fact"><b>{n}</b><span>{l}</span></div>
            ))}
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div className="hours">
            <span>Signal quality by hour</span>
            <div className="hours-bars" aria-hidden="true">
              {REPORT.hours.map((v, i) => <i key={i} className={v < 0.7 ? 'low' : ''} style={{ height: `${(v / max) * 100}%` }} />)}
            </div>
            <div className="hours-axis"><span>8 am</span><span>2 pm</span><span>7 pm</span></div>
          </div>
          <div className="notes">
            {notes.slice(-3).map(([t, n], i) => <p key={i}><span>{t}</span>{n}</p>)}
          </div>
          <p className="privacy"><b>Included:</b> counts, signal quality, your notes. <b>Never included:</b> raw brain data or guesses about mood.</p>
        </div>
      </div>
      <Board scanKey={`report-${view}`} items={items} layout={layout} onHelp={() => go('help')} onBack={() => (view === 'summary' ? go('home') : setView('summary'))} />
    </>
  )
}
