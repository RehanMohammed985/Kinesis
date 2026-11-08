import { useEffect, useRef, useState } from 'react'
import { useNav } from '../App.jsx'
import { INPUTS } from '../data.js'
import { useKinesis } from '../engine/kinesis.jsx'

// Calibration at a steady pace. Each attempt is cued: get ready, do it now,
// relax. Only an input seen inside the "now" window counts, so one long
// clench can never count twice and nothing races ahead. With the headset on,
// the core learns this person's own clench and double blink from these steps
// (kinesis/signal/learned.py), then the double clench step checks the result.
const STEPS = [
  { id: 'rest', label: 'Stay still', cue: 'Stay still and relaxed', hint: 'This sets the quiet level for every sensor.', seconds: 6 },
  { id: 'clench', label: 'Clench', input: 'clench', reps: 5, now: 'Clench now', hint: 'Clench your jaw firmly for half a second, then let go.' },
  { id: 'blink2', label: 'Double blink', input: 'blink2', reps: 5, now: 'Blink twice now', hint: 'Two quick, firm blinks.' },
  { id: 'clench2', label: 'Double clench', input: 'clench2', reps: 3, now: 'Clench twice now', hint: 'Two quick clenches, close together.' },
]
const PHASE_MS = { ready: 1400, now: 2200, relax: 1600 }
const PROFILE = { select: 'clench', back: 'blink2', rest: 'clench2' }

function tone(freq = 660) {
  try {
    const ctx = new AudioContext()
    const o = ctx.createOscillator()
    const g = ctx.createGain()
    o.frequency.value = freq
    g.gain.setValueAtTime(0.0001, ctx.currentTime)
    g.gain.exponentialRampToValueAtTime(0.18, ctx.currentTime + 0.02)
    g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.35)
    o.connect(g).connect(ctx.destination)
    o.start()
    o.stop(ctx.currentTime + 0.4)
  } catch { /* no audio */ }
}

export default function Calibrate() {
  const k = useKinesis()
  const { go } = useNav()
  const [step, setStep] = useState(0)
  const [rep, setRep] = useState(0)
  const [phase, setPhase] = useState('ready')
  const [hits, setHits] = useState({}) // step id -> array of true/false per rep
  const [learned, setLearned] = useState(null)
  const [done, setDone] = useState(false)
  const [, tick] = useState(0)
  const phaseStart = useRef(performance.now())
  const hitThisRep = useRef(false)

  const current = STEPS[step]

  // tell the core which step this is
  useEffect(() => {
    if (!current) return
    k.send({ type: 'calibrate', step: current.id })
    setRep(0)
    setPhase(current.seconds ? 'hold' : 'ready')
    phaseStart.current = performance.now()
  }, [step]) // eslint-disable-line react-hooks/exhaustive-deps

  // the clock: rest is one timed hold, the others cycle ready -> now -> relax
  useEffect(() => {
    if (!current || done) return
    let id
    const ms = current.seconds ? current.seconds * 1000 : PHASE_MS[phase]
    const startedAt = phaseStart.current
    const frame = () => {
      tick((n) => n + 1)
      if (performance.now() - startedAt < ms) { id = requestAnimationFrame(frame); return }
      phaseStart.current = performance.now()
      if (current.seconds) { next(); return }
      if (phase === 'ready') { hitThisRep.current = false; setPhase('now'); tone(700) }
      else if (phase === 'now') {
        setHits((h) => {
          const row = [...(h[current.id] || [])]
          row[rep] = hitThisRep.current
          return { ...h, [current.id]: row }
        })
        setPhase('relax')
      } else if (rep + 1 < current.reps) { setRep((r) => r + 1); setPhase('ready') }
      else next()
    }
    id = requestAnimationFrame(frame)
    return () => cancelAnimationFrame(id)
  }, [step, rep, phase, done]) // eslint-disable-line react-hooks/exhaustive-deps

  // count an input only inside the "now" window, once per attempt
  useEffect(
    () =>
      k.subscribe((msg) => {
        if (msg.type === 'calibration' && msg.step === 'model') setLearned(msg)
        const cur = STEPS[step]
        if (!cur?.input || msg.type !== 'event' || msg.input !== cur.input) return
        if (phase !== 'now' || hitThisRep.current) return
        hitThisRep.current = true
        tone(990)
        setHits((h) => {
          const row = [...(h[cur.id] || [])]
          row[rep] = true
          return { ...h, [cur.id]: row }
        })
      }),
    [step, rep, phase], // eslint-disable-line react-hooks/exhaustive-deps
  )

  function next() {
    if (step + 1 < STEPS.length) setStep((s) => s + 1)
    else {
      k.send({ type: 'calibrate', step: 'done' })
      k.setProfile(PROFILE)
      setDone(true)
    }
  }

  if (done) return <Results hits={hits} learned={learned} onAgain={() => { setHits({}); setLearned(null); setDone(false); setStep(0) }} onDone={() => go('home')} />

  const elapsed = (performance.now() - phaseStart.current) / 1000
  const total = current.seconds || PHASE_MS[phase] / 1000
  const cue = current.seconds ? current.cue : phase === 'ready' ? 'Get ready' : phase === 'now' ? current.now : 'Relax'
  const row = hits[current.id] || []

  return (
    <section className="cal" aria-label="Calibration">
      <ol className="cal-steps">
        {STEPS.map((s, i) => (
          <li key={s.id} className={i < step ? 'done' : i === step ? 'now' : ''}>
            <span className="n">{i + 1}</span>
            {s.label}
          </li>
        ))}
      </ol>
      <div className={`cal-main phase-${phase}`} aria-live="polite">
        {!current.seconds && <p className="cal-count">{current.label}, {rep + 1} of {current.reps}</p>}
        <h1 className="cal-cue">{cue}</h1>
        <p className="cal-hint">{current.hint}</p>
        <div className="cal-bar"><i style={{ width: `${Math.min(100, (elapsed / total) * 100)}%` }} /></div>
        {!current.seconds && (
          <div className="cal-meter" aria-label={`${row.filter(Boolean).length} of ${current.reps} caught`}>
            {Array.from({ length: current.reps }, (_, i) => (
              <i key={i} className={row[i] === true ? 'hit' : row[i] === false ? 'miss' : i === rep ? 'live' : ''} />
            ))}
          </div>
        )}
        <div className="row">
          <button className="btn ghost" onClick={next}>Skip this step</button>
        </div>
      </div>
    </section>
  )
}

function Results({ hits, learned, onAgain, onDone }) {
  const rows = STEPS.filter((s) => s.input).map((s) => {
    const r = hits[s.id] || []
    return { s, got: r.filter(Boolean).length }
  })
  return (
    <section className="cal-main" style={{ flex: 1 }} aria-label="Calibration result">
      <h1 className="screen-title">Clench chooses. Double blink goes back. Double clench pauses.</h1>
      <p className="screen-lede">
        {learned?.ok
          ? 'Kinesis learned your own clench and double blink from these attempts.'
          : learned
            ? 'Not enough clean attempts to learn from this time, so Kinesis keeps the model it had. Run it again with firmer attempts.'
            : 'How many attempts Kinesis caught. Run this again any time your body changes.'}
      </p>
      <ul className="ranking">
        {rows.map(({ s, got }) => (
          <li key={s.id}>
            <span className="name">{INPUTS[s.input].name}</span>
            <span className="track"><i style={{ width: `${Math.round((got / s.reps) * 100)}%` }} /></span>
            <span className="role"><b>{got} of {s.reps}</b> caught</span>
          </li>
        ))}
      </ul>
      <div className="row">
        <button className="btn" onClick={onDone}>Start using Kinesis</button>
        <button className="btn ghost" onClick={onAgain}>Run again</button>
      </div>
    </section>
  )
}
