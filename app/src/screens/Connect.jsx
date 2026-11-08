import { useEffect, useRef, useState } from 'react'
import { useNav } from '../App.jsx'
import { useKinesis } from '../engine/kinesis.jsx'
import { tone } from '../engine/tone.js'
import HeadMap from '../ui/HeadMap.jsx'

// Scene 1 (?scene=1), scripted. Waits for the headset's USB cable (or the P
// key), lights every sensor green, then runs the quick check on its own.
// About 15 s from plug-in to Home.
const SENSOR_MS = 300   // one sensor on every 0.3 s
const HOLD_MS = 1000    // all green, then calibration starts

export default function Connect() {
  const k = useKinesis()
  const { go } = useNav()
  const [on, setOn] = useState(false)
  const prev = useRef(undefined)
  const q = Object.fromEntries(k.quality.map((c) => [c.ch, c]))
  const lit = k.quality.filter((c) => c.state !== 'off').length
  const total = k.quality.length

  useEffect(() => {
    const p = k.plug
    if (!on && p?.plugged && (prev.current === false || p.manual)) {
      setOn(true)
      tone(880)
      k.powerOn({ allGood: true, stepMs: SENSOR_MS })
      setTimeout(() => go('calibrate', { quick: true, scripted: true }), SENSOR_MS * (total + 1) + HOLD_MS)
    }
    if (p) prev.current = p.plugged
  }, [k.plug]) // eslint-disable-line react-hooks/exhaustive-deps

  const already = !on && k.plug?.plugged && !k.plug.manual

  return (
    <section className="fit" aria-label="Connect the headset">
      <HeadMap quality={on ? q : {}} waiting={!on} />
      <div className="fixes">
        <div>
          <h1 className="screen-title">{on ? 'Headset connected' : 'Plug in the headset'}</h1>
          <p className="screen-lede">
            {!on ? 'Kinesis finds it as soon as the cable goes in.' : lit < total ? `Turning on sensor ${lit + 1} of ${total}.` : 'All sensors are reading well. Calibrating next.'}
          </p>
        </div>
        {on && <div className="fix-count">{lit} <small>of {total} reading well</small></div>}
        {already && <p className="hair-note">The headset is already plugged in. Unplug it, then plug it in to start.</p>}
      </div>
    </section>
  )
}
