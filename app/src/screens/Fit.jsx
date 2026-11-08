import { useEffect } from 'react'
import { useNav } from '../App.jsx'
import { useKinesis } from '../engine/kinesis.jsx'
import HeadMap, { REASON } from '../ui/HeadMap.jsx'

// Fit: the first thing a caregiver sees. Sensors come on one at a time (the
// Knight enables channels sequentially), each is scored from the raw stream,
// and anything not reading well gets a plain instruction.
export default function Fit() {
  const k = useKinesis()
  const { go } = useNav()
  useEffect(() => { k.powerOn() }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Without the core there is no headset to read: show nothing rather than pretend numbers.
  const live = k.mode === 'core'
  const q = live ? Object.fromEntries(k.quality.map((c) => [c.ch, c])) : {}
  const off = k.quality.filter((c) => c.state === 'off').length
  const good = k.quality.filter((c) => c.state === 'good').length
  const issues = k.quality.filter((c) => c.state === 'fair' || c.state === 'bad')
  const total = k.quality.length
  const warming = off > 0

  return (
    <section className="fit" aria-label="Headset fit">
      <HeadMap quality={q} onTap={(ch) => k.fixSensor(ch)} />

      <div className="fixes">
        {!live && (
          <p className="nodata">
            <b>Not connected to the headset.</b> Start the Kinesis core in a terminal
            (python -m kinesis.server --port ...), leave it running, then reload this page.
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
            {!live ? 'Each sensor appears here once the headset is connected.' : warming ? `Turning on sensor ${total - off + 1} of ${total}.` : 'Each sensor is checked against live signal. Fix anything not green before calibrating.'}
          </p>
        </div>
        <div className="fix-count">
          {live ? <>{good} <small>of {total} reading well</small></> : <small>No headset connected</small>}
        </div>
        {!live ? null : issues.length > 0 ? (
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
          live && !warming && <p className="screen-lede">All sensors are reading well.</p>
        )}
        <p className="hair-note">
          <b>Braids, locs, or coily hair:</b> seat each spike in a part line rather than on top of hair, and let the comfort pads rest on the braids to hold the frame. Paste only the sensors this screen flags.
        </p>
        <div className="row">
          <button className="btn" disabled={warming} onClick={() => go('calibrate')}>
            {issues.some((i) => i.state === 'bad') ? 'Calibrate anyway' : 'Start calibration'}
          </button>
          <button className="btn ghost" onClick={() => go('calibrate', { quick: true })}>Quick check, 10 s</button>
          <button className="btn ghost" onClick={() => go('home')}>Skip to home</button>
        </div>
      </div>
    </section>
  )
}
