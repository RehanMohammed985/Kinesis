import { useEffect, useRef, useState } from 'react'
import { useNav } from '../App.jsx'
import { INPUTS } from '../data.js'
import { LEVEL_KEY, useKinesis } from '../engine/kinesis.jsx'

// Calibration: four cued actions, then a ranking of which input this person
// does most cleanly. The best one chooses, the next one goes back, eyes
// closed pauses. Under two minutes.
const STEPS = [
  { id: 'rest', label: 'Stay still', cue: 'Stay still and relaxed', hint: 'This sets the quiet level for every sensor.', seconds: 6 },
  { id: 'clench', label: 'Clench', cue: 'Clench your jaw', hint: 'Clench firmly, then let go. Three times.', need: 3, input: 'clench' },
  { id: 'blink2', label: 'Double blink', cue: 'Blink twice', hint: 'Two quick blinks, three times.', need: 3, input: 'blink2' },
  { id: 'alpha', label: 'Eyes closed', cue: 'Close your eyes', hint: 'Keep them closed until you hear the tone.', need: 1, input: 'alpha' },
]

function tone() {
  try {
    const ctx = new AudioContext()
    const o = ctx.createOscillator()
    const g = ctx.createGain()
    o.frequency.value = 660
    g.gain.setValueAtTime(0.0001, ctx.currentTime)
    g.gain.exponentialRampToValueAtTime(0.2, ctx.currentTime + 0.02)
    g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.5)
    o.connect(g).connect(ctx.destination)
    o.start()
    o.stop(ctx.currentTime + 0.55)
  } catch { /* no audio */ }
}

export default function Calibrate() {
  const k = useKinesis()
  const { go } = useNav()
  const [step, setStep] = useState(0)
  const [hits, setHits] = useState(0)
  const [elapsed, setElapsed] = useState(0)
  const [result, setResult] = useState(null)
  const stats = useRef({})
  const stepStart = useRef(performance.now())
  const hitsRef = useRef(0)

  const current = STEPS[step]

  // start of each step
  useEffect(() => {
    if (!current) return
    setHits(0)
    hitsRef.current = 0
    stepStart.current = performance.now()
    stats.current[current.id] = { peak: 0, times: [] }
    k.send({ type: 'calibrate', step: current.id })
  }, [step]) // eslint-disable-line react-hooks/exhaustive-deps

  // timed rest step + peak tracking
  useEffect(() => {
    if (!current) return
    let raf
    const tick = (now) => {
      const t = (now - stepStart.current) / 1000
      setElapsed(t)
      if (current.input) {
        const v = k.levelsRef.current[LEVEL_KEY[current.input]] || 0
        const s = stats.current[current.id]
        if (s && v > s.peak) s.peak = v
      }
      if (current.seconds && t >= current.seconds) { setStep((s) => s + 1); return }
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [step]) // eslint-disable-line react-hooks/exhaustive-deps

  // counting cued events
  useEffect(
    () =>
      k.subscribe((msg) => {
        if (msg.type === 'calibration' && msg.done && msg.profile) {
          finish(msg.profile.scores)
          return
        }
        const cur = STEPS[step]
        if (!cur?.input || msg.type !== 'event' || msg.input !== cur.input) return
        stats.current[cur.id].times.push((performance.now() - stepStart.current) / 1000)
        if (cur.id === 'alpha') tone()
        hitsRef.current += 1
        setHits(hitsRef.current)
        if (hitsRef.current === cur.need) setTimeout(() => setStep((s) => s + 1), 500)
      }),
    [step], // eslint-disable-line react-hooks/exhaustive-deps
  )

  // all steps done: rank
  useEffect(() => {
    if (step < STEPS.length || result) return
    const score = (id) => {
      const s = stats.current[id]
      if (!s || !s.times.length) return 0.1
      const strength = Math.min(1, s.peak / 1.4)
      const avg = s.times[s.times.length - 1] / s.times.length
      const speed = Math.max(0, Math.min(1, 1 - (avg - 1) / 5))
      return 0.6 * strength + 0.4 * speed
    }
    finish({ clench: score('clench'), blink2: score('blink2'), alpha: score('alpha'), look: k.mode === 'core' ? undefined : 0.42 })
  }, [step]) // eslint-disable-line react-hooks/exhaustive-deps

  function finish(scores) {
    const switches = ['clench', 'blink2'].sort((a, b) => scores[b] - scores[a])
    const profile = { select: switches[0], back: switches[1], rest: 'alpha' }
    k.setProfile(profile)
    setStep(STEPS.length)
    setResult({ scores, profile })
  }

  if (result) return <Results result={result} onAgain={() => { setResult(null); setStep(0) }} onDone={() => go('home')} />

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
      {current && (
        <div className="cal-main" aria-live="polite">
          <h1 className="cal-cue">{current.cue}</h1>
          <p className="cal-hint">{current.hint}</p>
          {current.seconds ? (
            <div className="cal-bar"><i style={{ width: `${Math.min(100, (elapsed / current.seconds) * 100)}%` }} /></div>
          ) : (
            <div className="cal-meter" aria-label={`${hits} of ${current.need}`}>
              {Array.from({ length: current.need }, (_, i) => <i key={i} className={i < hits ? 'hit' : ''} />)}
            </div>
          )}
          <div className="row">
            <button className="btn ghost" onClick={() => setStep((s) => s + 1)}>Skip this step</button>
          </div>
        </div>
      )}
    </section>
  )
}

function Results({ result, onAgain, onDone }) {
  const roleFor = (id) =>
    result.profile.select === id ? 'chooses' : result.profile.back === id ? 'goes back' : result.profile.rest === id ? 'pauses' : 'not used yet'
  const rows = Object.entries(result.scores)
    .filter(([, v]) => v !== undefined)
    .sort((a, b) => b[1] - a[1])
  const sentence = `${INPUTS[result.profile.select].name} will choose. ${INPUTS[result.profile.back].name} goes back. Closing your eyes pauses.`
  return (
    <section className="cal-main" style={{ flex: 1 }} aria-label="Calibration result">
      <h1 className="screen-title">{sentence}</h1>
      <p className="screen-lede">Ranked by how strong and how quick each signal was for you. Run this again any time your body changes.</p>
      <ul className="ranking">
        {rows.map(([id, v], i) => (
          <li key={id} className={i === 0 ? 'first' : ''}>
            <span className="name">{INPUTS[id].name}</span>
            <span className="track"><i style={{ width: `${Math.round(v * 100)}%` }} /></span>
            <span className="role">{id === 'look' ? 'try in look mode' : <b>{roleFor(id)}</b>}</span>
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
