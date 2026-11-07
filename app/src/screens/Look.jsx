import { useEffect, useRef, useState } from 'react'
import { useNav } from '../App.jsx'
import { LOOK_TILES } from '../data.js'
import { useKinesis } from '../engine/kinesis.jsx'
import Board from '../ui/Board.jsx'

// Look mode (SSVEP). Each tile flickers at its own rate; the visual cortex
// follows whichever one the person looks at, and the core reads it from the
// occipital sensors (kinesis/signal/ssvep.py, no training needed). Rates need
// a 60 Hz display. Shown only after a photosensitivity notice.
export default function Look() {
  const { go } = useNav()
  const [started, setStarted] = useState(false)
  if (!started) {
    const items = [
      { id: 'back', area: 'a', kind: 'safe', glyph: 'back', label: 'Not now', onSelect: () => go('home') },
      { id: 'start', area: 'b', glyph: 'look', label: 'Start flashing', sub: 'Look at a square to choose it', onSelect: () => setStarted(true) },
    ]
    return (
      <>
        <div className="notice">
          <h1 className="screen-title">Look to choose</h1>
          <p className="screen-lede" style={{ margin: 0 }}>
            Four squares will flash at slightly different speeds, between 8 and 15 times a second. Look at one and Kinesis reads which from the back of your head. Do not use this if flashing light has ever caused you a seizure or migraine.
          </p>
        </div>
        <Board scanKey="look-notice" items={items} layout={{ columns: '1fr 1fr', rows: '1fr', areas: '"a b"' }} onHelp={() => go('help')} onBack={() => go('home')} />
      </>
    )
  }
  return <Tiles />
}

function Tiles() {
  const k = useKinesis()
  const { go } = useNav()
  const canvases = useRef([])
  const tiles = useRef([])
  const [chosen, setChosen] = useState(null)

  const choose = (i) => {
    setChosen(i)
    const t = LOOK_TILES[i]
    setTimeout(() => {
      setChosen(null)
      if (t.label === 'Help') go('help')
      else if (t.label === 'Call Sam') go('calling', { contact: 'sam' })
      else { k.act({ action: 'speak', text: t.label }); k.say(`Said: ${t.label}`) }
    }, 450)
  }

  // tell the core to start reading which square is being looked at
  useEffect(() => {
    k.send({ type: 'look', on: true })
    return () => k.send({ type: 'look', on: false })
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(
    () =>
      k.subscribe((msg) => {
        if (msg.type !== 'event') return
        if (msg.input === 'look') choose(msg.target)
        if (msg.input === k.profile.back) go('home')
      }),
    [k], // eslint-disable-line react-hooks/exhaustive-deps
  )

  useEffect(() => {
    let raf
    const t0 = performance.now()
    const draw = (now) => {
      const t = (now - t0) / 1000
      const best = k.levelsRef.current.look?.best ?? -1
      LOOK_TILES.forEach((tile, i) => {
        const c = canvases.current[i]
        if (c) {
          const g = c.getContext('2d')
          const on = Math.sin(2 * Math.PI * tile.hz * t) >= 0
          g.fillStyle = on ? '#f7f8f5' : '#1d2a2e'
          g.fillRect(0, 0, c.width, c.height)
        }
        tiles.current[i]?.classList.toggle('best', best === i)
      })
      raf = requestAnimationFrame(draw)
    }
    raf = requestAnimationFrame(draw)
    return () => cancelAnimationFrame(raf)
  }, [k.levelsRef])

  return (
    <>
      <div className="panel">
        <h1 className="screen-title">Look at a square</h1>
        <p className="screen-lede">The yellow frame shows what Kinesis thinks you are looking at. {k.profile.back === 'blink2' ? 'Double blink' : 'Clench'} to leave.</p>
      </div>
      <div className="look">
        {LOOK_TILES.map((t, i) => (
          <button key={t.label} ref={(el) => (tiles.current[i] = el)} className={`look-tile ${chosen === i ? 'committed' : ''}`} onClick={() => choose(i)}>
            <canvas ref={(el) => (canvases.current[i] = el)} width="8" height="8" aria-hidden="true" />
            <span className="label">{t.label}<small>{t.hz} Hz</small></span>
          </button>
        ))}
      </div>
    </>
  )
}
