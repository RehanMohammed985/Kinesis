import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { CARE_LIST, CONTACTS, SENSORS } from '../data.js'
import { speakAsUser } from './speak.js'

// The engine. Connects to the Python core over WebSocket (docs/PROTOCOL.md).
// When there is no core it runs a simulator driven by the keyboard, so the
// app always demos. Fast-changing values (signal levels, traces) live in refs
// and are drawn with requestAnimationFrame, so React does not re-render at 30 Hz.

const Ctx = createContext(null)
export const useKinesis = () => useContext(Ctx)

const LANES = ['clench', 'blink', 'alpha']
const HISTORY = 240 // samples per lane, ~8 s at 30 Hz
export const LEVEL_KEY = { clench: 'clench', blink2: 'blink', alpha: 'alpha', look: 'look' }

// The dev server forwards /core to the Kinesis core (app/vite.config.js), so a
// phone or iPad that opened this page reaches the headset through the same
// address. ?core=ws://host:8765 still connects straight to a core elsewhere.
const coreUrl = () =>
  new URLSearchParams(location.search).get('core') ||
  `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/core`

const initialQuality = () =>
  SENSORS.map((s) => ({ ch: s.ch, site: s.site, state: 'off', reason: 'off' }))

// What the simulator pretends each electrode reads once powered on.
const SIM_READINGS = {
  2: { state: 'fair', reason: 'noise', prompt: 'Press it down a quarter turn.' },
  6: { state: 'bad', reason: 'flat', prompt: 'Move it a few millimeters into a part line.' },
}

export function KinesisProvider({ children }) {
  const [mode, setMode] = useState('sim') // 'core' | 'sim'
  const [streaming, setStreaming] = useState(null) // core only: is the headset sending data
  const [profile, setProfile] = useState({ select: 'clench', back: 'blink2', rest: 'clench2' })
  const [quality, setQuality] = useState(initialQuality)
  const [toast, setToast] = useState(null)
  const [spokenScan, setSpokenScan] = useState(false)
  const [showKeys, setShowKeys] = useState(false)
  const [server, setServer] = useState({ voice: false, replies: false })

  const levelsRef = useRef({ clench: 0, blink: 0, alpha: 0, look: { scores: [0, 0, 0, 0], best: -1, margin: 0 } })
  const historyRef = useRef(Object.fromEntries(LANES.map((k) => [k, new Float32Array(HISTORY)])))
  const headRef = useRef(0)
  const firedRef = useRef({})
  const listeners = useRef(new Set())
  const wsRef = useRef(null)
  const modeRef = useRef(mode)
  modeRef.current = mode
  const demoRef = useRef(null)

  const emit = useCallback((msg) => {
    if (msg.type === 'event') firedRef.current[LEVEL_KEY[msg.input] || msg.input] = performance.now()
    for (const fn of listeners.current) fn(msg)
  }, [])

  const subscribe = useCallback((fn) => {
    listeners.current.add(fn)
    return () => listeners.current.delete(fn)
  }, [])

  const send = useCallback((msg) => {
    const ws = wsRef.current
    if (ws && ws.readyState === 1) ws.send(JSON.stringify(msg))
  }, [])

  const say = useCallback((text, ms = 2600) => {
    setToast(text)
    clearTimeout(say.t)
    say.t = setTimeout(() => setToast(null), ms)
  }, [])

  // ---------- server capabilities ----------
  useEffect(() => {
    fetch('/api/status').then((r) => r.json()).then(setServer).catch(() => {})
  }, [])

  // ---------- core connection ----------
  useEffect(() => {
    let stopped = false
    let retry
    const connect = () => {
      let ws
      try { ws = new WebSocket(coreUrl()) } catch { retry = setTimeout(connect, 3000); return }
      wsRef.current = ws
      ws.onopen = () => setMode('core')
      ws.onclose = () => {
        if (wsRef.current === ws) wsRef.current = null
        setMode('sim')
        setStreaming(null)
        if (!stopped) retry = setTimeout(connect, 3000)
      }
      ws.onerror = () => ws.close()
      ws.onmessage = (e) => {
        let msg
        try { msg = JSON.parse(e.data) } catch { return }
        if (msg.type === 'levels') {
          Object.assign(levelsRef.current, msg)
          return
        }
        if (msg.type === 'status') { setStreaming(Boolean(msg.streaming)); return }
        if (msg.type === 'hello' && msg.profile) setProfile((p) => ({ ...p, ...msg.profile }))
        if (msg.type === 'quality') {
          setQuality((q) => q.map((c) => msg.channels.find((m) => m.ch === c.ch) || c))
        }
        if (msg.type === 'calibration' && msg.done && msg.profile) setProfile((p) => ({ ...p, ...msg.profile }))
        if (msg.type === 'notice') say(msg.text, 6000)
        emit(msg)
      }
    }
    connect()
    return () => {
      stopped = true
      clearTimeout(retry)
      wsRef.current?.close()
    }
  }, [emit]) // eslint-disable-line react-hooks/exhaustive-deps

  // ---------- demo: replay a recorded seizure ----------
  // With the core: it mixes a real recorded seizure (Bonn dataset) into the live
  // signal and the real detector raises the alert. Without it: simulated.
  const demoSeizure = useCallback(() => {
    if (modeRef.current === 'core') {
      send({ type: 'demo_seizure' })
      return
    }
    setTimeout(() => {
      const when = new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }).toLowerCase()
      emit({ type: 'alert', kind: 'seizure_like', text: `Kinesis detected seizure-like brain activity on Walter at ${when}. Please check on them now.` })
    }, 8000)
  }, [send, emit])

  // ---------- simulator ----------
  useEffect(() => {
    const held = new Set()
    let lastBlink = 0
    let clenchArmed = true
    let alphaSince = 0
    let alphaFired = false

    const down = (e) => {
      if (e.repeat || e.metaKey || e.ctrlKey || e.altKey) return
      const k = e.key.toLowerCase()
      if (k === '?' || (k === '/' && e.shiftKey)) { setShowKeys((v) => !v); return }
      if (k === 's') { setSpokenScan((v) => !v); return }
      if (k === 'x') { demoRef.current?.(); return }
      if (modeRef.current !== 'sim') return
      if (k === 'c' || k === 'e') held.add(k)
      if (k === 'd') { levelsRef.current.clench = 1.3; emit({ type: 'event', input: 'clench2' }) }
      if (k === 'b') {
        const now = performance.now()
        levelsRef.current.blink = 1.25
        if (now - lastBlink < 600) {
          emit({ type: 'event', input: 'blink2' })
          lastBlink = 0
        } else lastBlink = now
      }
      if (['1', '2', '3', '4'].includes(k)) {
        const target = Number(k) - 1
        const scores = [0.18, 0.2, 0.17, 0.21].map((v, i) => (i === target ? 0.72 : v))
        levelsRef.current.look = { scores, best: target, margin: 0.5 }
        emit({ type: 'event', input: 'look', target })
      }
    }
    const up = (e) => held.delete(e.key.toLowerCase())
    window.addEventListener('keydown', down)
    window.addEventListener('keyup', up)

    let raf
    let last = performance.now()
    let acc = 0
    const tick = (now) => {
      const dt = Math.min(64, now - last)
      last = now
      const L = levelsRef.current
      if (modeRef.current === 'sim') {
        const n = () => (Math.random() - 0.5) * 0.06
        const ease = (v, target, rate) => v + (target - v) * (1 - Math.exp(-dt / rate))
        L.clench = Math.max(0, ease(L.clench, held.has('c') ? 1.35 : 0.06, held.has('c') ? 260 : 120) + n())
        L.blink = Math.max(0, ease(L.blink, 0.04, 70) + n() * 0.5)
        L.alpha = Math.max(0, ease(L.alpha, held.has('e') ? 1.45 : 0.3, 380) + n())
        if (L.clench >= 1 && clenchArmed) {
          clenchArmed = false
          emit({ type: 'event', input: 'clench' })
        }
        if (L.clench < 0.45) clenchArmed = true
        if (L.alpha >= 1) {
          if (!alphaSince) alphaSince = now
          if (!alphaFired && now - alphaSince > 1000) {
            alphaFired = true
            emit({ type: 'event', input: 'alpha' })
          }
        } else {
          alphaSince = 0
          alphaFired = false
        }
        const look = L.look
        look.scores = look.scores.map((s) => s + (0.2 - s) * 0.02)
        if (Math.max(...look.scores) < 0.3) look.best = -1
      }
      acc += dt
      while (acc >= 33) {
        acc -= 33
        const h = headRef.current
        for (const k of LANES) historyRef.current[k][h] = L[k]
        headRef.current = (h + 1) % HISTORY
      }
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('keydown', down)
      window.removeEventListener('keyup', up)
    }
  }, [emit])

  // ---------- sensors ----------
  // Mirrors the Knight's enable sequence: channels come on one at a time.
  const powerOn = useCallback(() => {
    if (modeRef.current === 'core') {
      send({ type: 'fit', action: 'start' })
      return
    }
    setQuality(initialQuality())
    SENSORS.forEach((s, i) => {
      setTimeout(() => {
        setQuality((q) =>
          q.map((c) =>
            c.ch === s.ch ? { ...c, ...(SIM_READINGS[s.ch] || { state: 'good', reason: 'ok' }), justOn: true } : { ...c, justOn: false },
          ),
        )
      }, 650 * (i + 1))
    })
    setTimeout(() => setQuality((q) => q.map((c) => ({ ...c, justOn: false }))), 650 * (SENSORS.length + 1))
  }, [send])

  const fixSensor = useCallback((ch) => {
    if (modeRef.current === 'core') return
    setQuality((q) => q.map((c) => (c.ch === ch && c.state !== 'off' ? { ...c, state: 'good', reason: 'ok', prompt: undefined } : c)))
  }, [])

  // ---------- outputs ----------
  const outbox = useCallback((msg) => {
    fetch('/api/outbox', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ from: 'Walter', ...msg }),
    }).catch(() => {})
  }, [])

  const act = useCallback(
    (action) => {
      send({ type: 'action', ...action })
      const contact = CONTACTS.find((c) => c.id === action.contact)
      switch (action.action) {
        case 'speak':
          speakAsUser(action.text)
          break
        case 'message':
          outbox({ kind: 'message', to: contact?.name, text: action.text, voice: Boolean(action.voice) })
          say(action.voice ? `Sent to ${contact?.name}, with a voice message` : `Sent to ${contact?.name}`)
          break
        case 'help':
          outbox({ kind: 'help', to: CARE_LIST.join(', '), text: 'Walter needs help' })
          speakAsUser('I need help')
          break
        case 'note':
          say('Note added')
          break
        case 'help_clear':
          outbox({ kind: 'message', to: CARE_LIST.join(', '), text: "I'm okay now" })
          break
        case 'call':
          outbox({ kind: 'call', to: contact?.name, text: `Calling ${contact?.name}` })
          break
        case 'report':
          outbox({ kind: 'report', to: action.recipientName, text: "Today's report" })
          say(`Sent to ${action.recipientName}`)
          break
        case 'media':
          say(action.label)
          break
        default:
          break
      }
    },
    [send, outbox, say],
  )

  demoRef.current = demoSeizure

  const value = useMemo(
    () => ({
      mode, streaming, profile, setProfile, quality, powerOn, fixSensor,
      subscribe, emit, send, act, say, toast,
      levelsRef, historyRef, headRef, firedRef,
      spokenScan, setSpokenScan, showKeys, setShowKeys, server, demoSeizure, outbox,
    }),
    [mode, streaming, profile, quality, powerOn, fixSensor, subscribe, emit, send, act, say, toast, spokenScan, showKeys, server, demoSeizure, outbox],
  )
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}
