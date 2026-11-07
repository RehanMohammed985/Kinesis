import { useEffect, useState } from 'react'
import { useNav } from '../App.jsx'
import { NOTES, REPORT } from '../data.js'
import { useKinesis } from '../engine/kinesis.jsx'
import Board from '../ui/Board.jsx'

// The day's report: what Kinesis measured plus notes the person chose.
// With the core connected, the report agent builds it from the day's log
// (seizure-like episodes, resting alpha, slowing vs baseline, usage) and
// writes an HTML report for the doctor. Sending is a confirm.
export default function Report() {
  const k = useKinesis()
  const { go } = useNav()
  const [view, setView] = useState('summary') // summary | note | confirm
  const [rep, setRep] = useState({ ...REPORT, summary: null, hours: REPORT.hours.map((q) => ({ quality: q })) })
  const [notes, setNotes] = useState(REPORT.notes)

  useEffect(() => {
    k.send({ type: 'report_request' })
    return k.subscribe((msg) => {
      if (msg.type !== 'report') return
      setRep({ ...msg, doctor: msg.doctor || REPORT.doctor })
      if (msg.notes?.length) setNotes(msg.notes)
    })
  }, [k.mode]) // eslint-disable-line react-hooks/exhaustive-deps

  const now = () => new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }).toLowerCase()
  const brain = rep.brain || REPORT.brain
  const hours = (rep.hours || []).filter((h) => h.quality != null)
  const max = Math.max(1, ...hours.map((h) => h.quality))

  let items, layout
  if (view === 'note') {
    items = [
      ...NOTES.map((n, i) => ({
        id: `n${i}`, area: `n${i}`, kind: 'reply', label: n,
        onSelect: () => { setNotes((ns) => [...ns, [now(), n]]); k.act({ action: 'note', text: n }); setView('summary') },
      })),
      { id: 'back', area: 'back', kind: 'quiet', glyph: 'back', label: 'Back', onSelect: () => setView('summary') },
    ]
    layout = { columns: '1fr 1fr 1fr 0.7fr', rows: '1fr 1fr', areas: '"n0 n1 n2 back" "n3 n4 n5 back"' }
  } else if (view === 'confirm') {
    items = [
      { id: 'cancel', area: 'a', kind: 'safe', glyph: 'cross', label: 'Cancel', sub: 'Nothing is sent', onSelect: () => setView('summary') },
      { id: 'send', area: 'b', glyph: 'send', label: `Send to ${rep.doctor}`, sub: 'Full report as a file', onSelect: () => { k.act({ action: 'report', recipient: 'dr_patel', recipientName: rep.doctor }); setView('summary') } },
    ]
    layout = { columns: '1fr 1fr', rows: '1fr', areas: '"a b"' }
  } else {
    items = [
      { id: 'send', area: 'send', glyph: 'send', label: `Send to ${rep.doctor}`, onSelect: () => setView('confirm') },
      { id: 'note', area: 'note', glyph: 'note', label: 'Add a note', sub: 'How you feel, in your words', onSelect: () => setView('note') },
      { id: 'back', area: 'back', kind: 'quiet', glyph: 'back', label: 'Back', onSelect: () => go('home') },
    ]
    layout = { columns: '1.2fr 1fr 0.7fr', rows: '1fr', areas: '"send note back"' }
  }

  const seizures = brain.seizure_like || []

  return (
    <>
      <div className="panel report">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <h1 className="screen-title">Today</h1>
          <div className="facts">
            {rep.facts.map(([n, l]) => (
              <div key={l} className={`fact ${l.startsWith('seizure') && n !== '0' ? 'warn' : ''}`}><b>{n}</b><span>{l}</span></div>
            ))}
          </div>
          {rep.summary && <p className="privacy" style={{ margin: 0 }}>{rep.summary}</p>}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div className="hours brainbox">
            <span className="brain-row"><b>Seizure-like activity</b>
              <span>{seizures.length ? seizures.map((s) => `${s.at}, ${Math.round(s.duration_s)} s`).join('; ') : 'None flagged'}</span>
            </span>
            <span className="brain-row"><b>Resting alpha peak</b>
              <span>{brain.alpha_peak_hz ? `${brain.alpha_peak_hz} Hz, ${brain.rest_periods} eyes-closed rests` : 'Not measured yet'}</span>
            </span>
            <span className="brain-row"><b>Signal quality by hour</b><span /></span>
            <div className="hours-bars" aria-hidden="true">
              {hours.map((h, i) => <i key={i} className={h.quality < 0.7 ? 'low' : ''} style={{ height: `${(h.quality / max) * 100}%` }} />)}
            </div>
          </div>
          <div className="notes">
            {notes.slice(-2).map(([t, n], i) => <p key={i}><span>{t}</span>{n}</p>)}
          </div>
          <div className="row" style={{ justifyContent: 'space-between' }}>
            <p className="privacy" style={{ margin: 0 }}><b>Never included:</b> raw brain data, guesses about mood, diagnoses.</p>
            <button className="rail-link" onClick={k.demoSeizure} title="Mixes a real recorded seizure (Bonn dataset) into the live signal so the detector can be shown">
              Demo: replay a recorded seizure
            </button>
          </div>
        </div>
      </div>
      <Board scanKey={`report-${view}`} items={items} layout={layout} onHelp={() => go('help')} onBack={() => (view === 'summary' ? go('home') : setView('summary'))} />
    </>
  )
}
