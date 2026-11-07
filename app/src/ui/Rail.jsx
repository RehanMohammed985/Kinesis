import { useEffect, useState } from 'react'
import { INPUTS, PERSON } from '../data.js'
import { useKinesis } from '../engine/kinesis.jsx'

function clock() {
  return new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }).toLowerCase()
}

export default function Rail({ onSetup }) {
  const k = useKinesis()
  const [time, setTime] = useState(clock)
  useEffect(() => {
    const t = setInterval(() => setTime(clock()), 15000)
    return () => clearInterval(t)
  }, [])
  const on = k.quality.filter((q) => q.state !== 'off')
  const good = k.quality.filter((q) => q.state === 'good').length
  const anyBad = k.quality.some((q) => q.state === 'bad')

  return (
    <header className="rail">
      <span className="rail-name">{PERSON.name}</span>
      <span className="rail-time">{time}</span>
      <span className="rail-spacer" />
      <span className="rail-item">
        <span className={`dot ${k.mode === 'core' ? 'on' : 'sim'}`} />
        {k.mode === 'core' ? <strong>Headset on</strong> : <strong>Simulator</strong>}
      </span>
      {on.length > 0 && (
        <span className="rail-item">
          <span className={`dot ${anyBad ? 'bad' : 'on'}`} />
          {good} of {k.quality.length} sensors good
        </span>
      )}
      <span className="rail-item">
        <strong>{INPUTS[k.profile.select].name}</strong> chooses
      </span>
      {k.spokenScan && <span className="rail-item"><strong>Spoken scanning</strong></span>}
      <button className="rail-link" onClick={onSetup}>Setup</button>
      <a className="rail-link" href="#/caregiver" target="_blank" rel="noreferrer">Caregiver view</a>
    </header>
  )
}
