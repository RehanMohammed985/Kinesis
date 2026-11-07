import { useEffect, useRef } from 'react'
import { INPUTS, ROLES } from '../data.js'
import { useKinesis } from '../engine/kinesis.jsx'

// Live traces for each input, with the threshold line. The lane for the
// input that chooses is outlined; a lane flashes yellow when it fires.
const LANES = [
  { key: 'clench', input: 'clench' },
  { key: 'blink', input: 'blink2' },
  { key: 'alpha', input: 'alpha' },
]
const MAX = 1.5

function roleOf(profile, input) {
  for (const [role, which] of Object.entries(profile)) if (which === input && ROLES[role]) return ROLES[role]
  return null
}

export default function SignalStrip() {
  const k = useKinesis()
  const canvases = useRef({})
  const lanes = useRef({})

  useEffect(() => {
    let raf
    const draw = (now) => {
      for (const { key } of LANES) {
        const c = canvases.current[key]
        const lane = lanes.current[key]
        if (!c || !lane) continue
        const dpr = window.devicePixelRatio || 1
        const w = c.clientWidth
        const h = c.clientHeight
        if (c.width !== w * dpr) { c.width = w * dpr; c.height = h * dpr }
        const g = c.getContext('2d')
        g.setTransform(dpr, 0, 0, dpr, 0, 0)
        g.clearRect(0, 0, w, h)
        const hist = k.historyRef.current[key]
        const head = k.headRef.current
        const n = hist.length
        const y = (v) => h - 3 - (Math.min(v, MAX) / MAX) * (h - 6)
        const thr = y(1)

        // above-threshold area
        g.fillStyle = 'rgba(244, 194, 27, 0.55)'
        g.beginPath()
        g.moveTo(0, thr)
        for (let i = 0; i < n; i++) {
          const v = hist[(head + i) % n]
          g.lineTo((i / (n - 1)) * w, Math.min(thr, y(v)))
        }
        g.lineTo(w, thr)
        g.closePath()
        g.fill()

        // threshold
        g.strokeStyle = 'rgba(29, 42, 46, 0.35)'
        g.setLineDash([3, 6])
        g.lineWidth = 2
        g.beginPath()
        g.moveTo(0, thr)
        g.lineTo(w, thr)
        g.stroke()
        g.setLineDash([])

        // trace
        g.strokeStyle = getComputedStyle(lane).color
        g.lineWidth = 2.5
        g.lineJoin = 'round'
        g.beginPath()
        for (let i = 0; i < n; i++) {
          const v = hist[(head + i) % n]
          const px = (i / (n - 1)) * w
          if (i === 0) g.moveTo(px, y(v))
          else g.lineTo(px, y(v))
        }
        g.stroke()

        const fired = k.firedRef.current[key]
        lane.classList.toggle('fired', Boolean(fired && now - fired < 380))
      }
      raf = requestAnimationFrame(draw)
    }
    raf = requestAnimationFrame(draw)
    return () => cancelAnimationFrame(raf)
  }, [k.historyRef, k.headRef, k.firedRef])

  return (
    <div className="strip" aria-label="Live signals">
      {LANES.map(({ key, input }) => {
        const role = roleOf(k.profile, input)
        const primary = k.profile.select === input
        return (
          <div key={key} ref={(el) => (lanes.current[key] = el)} className={`lane ${primary ? 'primary' : ''} ${role ? '' : 'off'}`}>
            <span className="lane-name">{INPUTS[input].name}</span>
            <span className="lane-role">{role ? <b>{role}</b> : 'not used'}</span>
            <canvas ref={(el) => (canvases.current[key] = el)} />
          </div>
        )
      })}
    </div>
  )
}
