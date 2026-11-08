import { useEffect } from 'react'
import { useNav } from '../App.jsx'
import { SENSORS } from '../data.js'
import { useKinesis } from '../engine/kinesis.jsx'

// Fit: the first thing a caregiver sees. Sensors come on one at a time (the
// Knight enables channels sequentially), each is scored from the raw stream,
// and anything not reading well gets a plain instruction.
const BOX = { x: 40, y: 78, size: 420 }
const pos = (s) => ({ cx: BOX.x + s.x * BOX.size, cy: BOX.y + s.y * BOX.size })

const REASON = {
  ok: 'Reading well',
  flat: 'Not touching skin',
  railed: 'Pressed too hard or paste too thick',
  noise: 'Picking up noise',
  no_alpha: 'No response when eyes close',
  off: 'Turning on',
}

export default function Fit() {
  const k = useKinesis()
  const { go } = useNav()
  useEffect(() => { k.powerOn() }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const q = Object.fromEntries(k.quality.map((c) => [c.ch, c]))
  const off = k.quality.filter((c) => c.state === 'off').length
  const good = k.quality.filter((c) => c.state === 'good').length
  const issues = k.quality.filter((c) => c.state === 'fair' || c.state === 'bad')
  const total = k.quality.length
  const warming = off > 0

  return (
    <section className="fit" aria-label="Headset fit">
      <svg className="head" viewBox="0 0 500 540" role="img" aria-label="Top view of the head showing each sensor">
        <path className="nose" d="M222 92 L250 46 L278 92" />
        <ellipse className="ear" cx="34" cy="288" rx="22" ry="44" />
        <ellipse className="ear" cx="466" cy="288" rx="22" ry="44" />
        <circle className="skull" cx="250" cy="288" r="214" />
        <circle className="grid-line" cx="250" cy="288" r="150" />
        <circle className="grid-line" cx="250" cy="288" r="78" />
        <path className="grid-line" d="M250 76V500M38 288H462" />
        {SENSORS.map((s) => {
          const c = q[s.ch] || { state: 'off' }
          const { cx, cy } = pos(s)
          const below = s.y < 0.5
          return (
            <g
              key={s.ch}
              className={`node ${c.state} ${c.justOn ? 'on-now' : ''}`}
              onClick={() => k.fixSensor(s.ch)}
              role="button"
              aria-label={`${s.site}: ${REASON[c.reason] || c.state}`}
            >
              <circle cx={cx} cy={cy} r={c.state === 'off' ? 16 : 21} />
              <text x={cx} y={below ? cy + 44 : cy - 32} textAnchor="middle">{s.site}</text>
            </g>
          )
        })}
      </svg>

      <div className="fixes">
        {k.mode !== 'core' && (
          <p className="nodata sim">
            <b>Simulator: these readings are pretend.</b> The app is not connected to the Kinesis core, so it is not reading
            the headset. Start the core (python -m kinesis.server --port ...) and this screen switches to the real sensors.
          </p>
        )}
        {k.mode === 'core' && k.streaming === false && (
          <p className="nodata">
            <b>No data is coming from the headset.</b> Check the USB cable, quit the EXG Visualizer, and restart the core.
            To find the problem, run <b>python scripts/check_headset.py</b>.
          </p>
        )}
        <div>
          <h1 className="screen-title">Fit the headset</h1>
          <p className="screen-lede">
            {warming ? `Turning on sensor ${total - off + 1} of ${total}.` : 'Each sensor is checked against live signal. Fix anything not green before calibrating.'}
          </p>
        </div>
        <div className="fix-count">
          {good} <small>of {total} reading well</small>
        </div>
        {issues.length > 0 ? (
          <ul className="fix-list">
            {issues.map((c) => (
              <li key={c.ch} className={c.state}>
                <span className="site">{c.site}</span>
                <span>
                  <b>{REASON[c.reason]}.</b> <span className="why">{c.prompt}</span>
                </span>
              </li>
            ))}
          </ul>
        ) : (
          !warming && <p className="screen-lede">All sensors are reading well.</p>
        )}
        <p className="hair-note">
          <b>Braids, locs, or coily hair:</b> seat each spike in a part line rather than on top of hair, and let the comfort pads rest on the braids to hold the frame. Paste only the sensors this screen flags.
        </p>
        <div className="row">
          <button className="btn" disabled={warming} onClick={() => go('calibrate')}>
            {issues.some((i) => i.state === 'bad') ? 'Calibrate anyway' : 'Start calibration'}
          </button>
          <button className="btn ghost" onClick={() => go('home')}>Skip to home</button>
        </div>
      </div>
    </section>
  )
}
