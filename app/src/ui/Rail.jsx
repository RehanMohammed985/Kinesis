import { useEffect, useState } from 'react'
import { INPUTS, PERSON } from '../data.js'
import { useKinesis } from '../engine/kinesis.jsx'

function now() {
  const d = new Date()
  const h = d.getHours()
  return {
    time: d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }).toLowerCase(),
    day: d.toLocaleDateString([], { weekday: 'long', month: 'long', day: 'numeric' }),
    greet: h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : 'Good evening',
  }
}

export default function Rail({ onSetup }) {
  const k = useKinesis()
  const [t, setT] = useState(now)
  useEffect(() => {
    const id = setInterval(() => setT(now()), 15000)
    return () => clearInterval(id)
  }, [])
  const on = k.quality.filter((q) => q.state !== 'off')
  const good = k.quality.filter((q) => q.state === 'good').length
  const anyBad = k.quality.some((q) => q.state === 'bad')
  const back = INPUTS[k.profile.back]

  return (
    <header className="rail">
      <span className="rail-me" aria-hidden="true">{PERSON.name[0]}</span>
      <span className="rail-hello">
        <b>{t.greet}, {PERSON.name}</b>
        <small>{t.day}, {t.time}</small>
      </span>
      <span className="rail-spacer" />
      <span className={`pill ${k.mode !== 'core' ? 'sim' : k.streaming === false ? 'warn' : 'live'}`}>
        <span className="bars" aria-hidden="true"><i /><i /><i /></span>
        {k.mode !== 'core' ? 'Simulator' : k.streaming === false ? 'No data from headset' : k.streaming ? 'Headset on' : 'Connecting'}
      </span>
      {on.length > 0 && (
        <span className={`pill ${anyBad ? 'warn' : ''}`}>
          <span className={`dot ${anyBad ? 'bad' : 'on'}`} />
          {good} of {k.quality.length} sensors
        </span>
      )}
      <span className="pill keys-hint">
        <b>{INPUTS[k.profile.select].name}</b> chooses{back ? <>, <b>{back.name.toLowerCase()}</b> goes back</> : null}
        {INPUTS[k.profile.rest] ? <>, <b>{INPUTS[k.profile.rest].name.toLowerCase()}</b> pauses</> : null}
      </span>
      {k.spokenScan && <span className="pill"><b>Spoken scanning</b></span>}
      <button className="rail-link" onClick={onSetup}>Setup</button>
      <a className="rail-link" href="#/caregiver" target="_blank" rel="noreferrer">Caregiver</a>
    </header>
  )
}
