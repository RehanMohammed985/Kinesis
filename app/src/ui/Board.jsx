import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react'
import { LEVEL_KEY, useKinesis } from '../engine/kinesis.jsx'
import { speakAsGuide } from '../engine/speak.js'
import Glyph from './Glyph.jsx'

// A scanning board. The lens moves through the items one at a time; the
// person's SELECT input commits the item under the lens, BACK goes back,
// REST pauses. A click or tap commits directly (for caregivers and testing).
//
// items: [{ id, label, sub, glyph, kind, area, avatar, onSelect }]
// layout: { columns, rows, areas } as CSS grid strings
export default function Board({ items, layout, help = true, onHelp, onBack, startAt = 0, dwell = 1800, scanKey }) {
  const k = useKinesis()
  const all = help ? [...items, { id: '__help', label: 'I need help', sub: 'Alerts Sam and the nurse line', glyph: 'help', help: true, onSelect: onHelp }] : items
  const [index, setIndex] = useState(startAt)
  const [paused, setPaused] = useState(false)
  const [committed, setCommitted] = useState(null)

  const wrapRef = useRef(null)
  const lensRef = useRef(null)
  const fillRef = useRef(null)
  const clockRef = useRef(null)
  const cellRefs = useRef({})
  const startRef = useRef(performance.now())
  const busyRef = useRef(false)
  const state = useRef({})
  state.current = { index, paused, all, onBack, profile: k.profile }

  // reset when the board changes
  useEffect(() => {
    setIndex(startAt)
    setPaused(false)
    startRef.current = performance.now()
  }, [scanKey]) // eslint-disable-line react-hooks/exhaustive-deps

  const commit = useCallback((i) => {
    if (busyRef.current) return
    const item = state.current.all[i]
    if (!item) return
    busyRef.current = true
    setIndex(i)
    setCommitted(item.id)
    setTimeout(() => {
      busyRef.current = false
      setCommitted(null)
      startRef.current = performance.now()
      item.onSelect?.()
    }, 300)
  }, [])

  // inputs
  useEffect(
    () =>
      k.subscribe((msg) => {
        if (msg.type !== 'event') return
        const { profile, index: i, onBack: back } = state.current
        if (msg.input === profile.select) {
          if (state.current.paused) { setPaused(false); startRef.current = performance.now(); return }
          commit(i)
        } else if (msg.input === profile.back) back?.()
        else if (msg.input === profile.rest) {
          setPaused((p) => !p)
          startRef.current = performance.now()
        }
      }),
    [k, commit],
  )

  // the scan clock and the live fill, drawn every frame
  useEffect(() => {
    let raf
    const tick = (now) => {
      const { paused: p, all: items } = state.current
      const progress = p || busyRef.current ? 0 : (now - startRef.current) / dwell
      if (progress >= 1) {
        startRef.current = now
        setIndex((i) => (i + 1) % items.length)
      }
      if (clockRef.current) clockRef.current.style.transform = `scaleX(${Math.min(1, progress)})`
      if (fillRef.current) {
        const key = LEVEL_KEY[state.current.profile.select]
        const v = key === 'look' ? 0 : k.levelsRef.current[key] || 0
        fillRef.current.style.height = `${Math.min(100, Math.max(0, ((v - 0.12) / 0.88) * 100))}%`
      }
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [dwell, k.levelsRef])

  // spoken scanning
  useEffect(() => {
    if (k.spokenScan && !paused) speakAsGuide(all[index]?.speak || all[index]?.label)
  }, [index, k.spokenScan, paused]) // eslint-disable-line react-hooks/exhaustive-deps

  // place the lens over the current item
  const place = useCallback(() => {
    const wrap = wrapRef.current
    const el = cellRefs.current[all[index]?.id]
    const lens = lensRef.current
    if (!wrap || !el || !lens) return
    const a = wrap.getBoundingClientRect()
    const b = el.getBoundingClientRect()
    lens.style.transform = `translate(${b.left - a.left}px, ${b.top - a.top}px)`
    lens.style.width = `${b.width}px`
    lens.style.height = `${b.height}px`
  }, [index, all])
  useLayoutEffect(place)
  useEffect(() => {
    const ro = new ResizeObserver(place)
    if (wrapRef.current) ro.observe(wrapRef.current)
    return () => ro.disconnect()
  }, [place])

  const gridItems = all.filter((i) => !i.help)
  const helpItem = all.find((i) => i.help)

  return (
    <div ref={wrapRef} style={{ position: 'relative', flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', gap: 'var(--gap)' }}>
      <div
        className="board"
        style={{ gridTemplateColumns: layout.columns, gridTemplateRows: layout.rows, gridTemplateAreas: layout.areas }}
      >
        {gridItems.map((it) => (
          <button
            key={it.id}
            ref={(el) => (cellRefs.current[it.id] = el)}
            className={`cell ${it.kind || ''} ${committed === it.id ? 'committed' : ''}`}
            style={{ gridArea: it.area }}
            onClick={() => commit(all.indexOf(it))}
            aria-current={all[index]?.id === it.id ? 'true' : undefined}
          >
            {it.avatar ? <span className="avatar small" aria-hidden="true">{it.avatar}</span> : it.glyph ? <Glyph name={it.glyph} className={`cell-glyph ${it.kind === 'big' ? 'big' : ''}`} /> : <span />}
            <span className="cell-text">
              <span className="cell-label">{it.label}</span>
              {it.sub && <span className="cell-sub">{it.sub}</span>}
            </span>
          </button>
        ))}
      </div>
      {helpItem && (
        <button
          ref={(el) => (cellRefs.current[helpItem.id] = el)}
          className={`helpbar ${committed === helpItem.id ? 'committed' : ''}`}
          onClick={() => commit(all.indexOf(helpItem))}
        >
          <Glyph name="help" />
          {helpItem.label}
          <span className="cell-sub">{helpItem.sub}</span>
        </button>
      )}
      <div ref={lensRef} className={`lens ${paused ? 'paused' : ''} ${committed ? 'flash' : ''}`} aria-hidden="true">
        <div className="lens-fill"><i ref={fillRef} /></div>
        <div className="lens-clock"><i ref={clockRef} /></div>
      </div>
      {paused && <div className="resting">Resting. {restHint(k.profile)}</div>}
    </div>
  )
}

function restHint(profile) {
  const words = { clench: 'Clench', blink2: 'Double blink', alpha: 'Close your eyes', look: 'Look' }
  return `${words[profile.select]} to carry on.`
}
