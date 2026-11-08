import { useEffect, useRef, useState } from 'react'
import { SAY, SAY_GLYPH } from '../data.js'
import { useKinesis } from '../engine/kinesis.jsx'
import { preload, speakAsUser } from '../engine/speak.js'
import Glyph from '../ui/Glyph.jsx'

// Scene 2 (?scene=2), scripted. Nothing moves on its own: one phrase waits
// in the frame. Holding a clench fills it; at 1.5 s it is spoken out loud in
// his voice (ElevenLabs). The hold starts by itself ?at= seconds after the
// page opens (default 4), or hold Space or C. R resets for another take.
const HOLD_MS = 1500
const PHRASE = SAY[0]
const AT = Number(new URLSearchParams(location.search).get('at') ?? 4)

export default function HoldSay() {
  const k = useKinesis()
  const [done, setDone] = useState(false)
  const [take, setTake] = useState(0)
  const fillRef = useRef(null)
  const others = SAY.slice(1, 5).map((t) => ({ t, g: SAY_GLYPH[SAY.indexOf(t)] }))

  useEffect(() => { preload(PHRASE) }, [])

  useEffect(() => {
    if (!AT) return
    const t = setTimeout(() => k.perform('hold', HOLD_MS + 500), AT * 1000)
    return () => clearTimeout(t)
  }, [take]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const key = (e) => { if (e.key.toLowerCase() === 'r') { setDone(false); setTake((n) => n + 1) } }
    window.addEventListener('keydown', key)
    return () => window.removeEventListener('keydown', key)
  }, [])

  useEffect(() => {
    if (done) return
    let raf
    let held = 0
    let last = performance.now()
    const tick = (now) => {
      const dt = now - last
      last = now
      held = (k.levelsRef.current.clench || 0) >= 0.6 ? held + dt : Math.max(0, held - dt * 3)
      const p = Math.min(1, held / HOLD_MS)
      if (fillRef.current) fillRef.current.style.transform = `scaleY(${p})`
      if (p >= 1) { setDone(true); speakAsUser(PHRASE); return }
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [done, take]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <section className="holdsay" aria-label="Say it">
      <div className={`hold-main ${done ? 'said-now' : ''}`}>
        <i ref={fillRef} className="hold-fill" aria-hidden="true" />
        <span className="well"><Glyph name="water" className="cell-glyph" /></span>
        <span className="hold-label">{PHRASE}</span>
        <span className="hold-hint">{done ? 'Said out loud' : 'Hold a clench to say it'}</span>
      </div>
      <ul className="hold-rest" aria-label="Other phrases">
        {others.map(({ t, g }) => (
          <li key={t}><Glyph name={g} className="cell-glyph" />{t}</li>
        ))}
      </ul>
      <div className="said-panel hold-said" aria-live="polite">
        {done && (
          <p className="said">
            <span className="said-wave" aria-hidden="true"><i /><i /><i /><i /></span>
            {PHRASE}
          </p>
        )}
      </div>
    </section>
  )
}
