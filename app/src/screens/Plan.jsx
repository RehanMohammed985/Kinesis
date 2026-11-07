import { useEffect, useRef, useState } from 'react'
import { useNav } from '../App.jsx'
import { TASKS } from '../data.js'
import { useKinesis } from '../engine/kinesis.jsx'
import Board from '../ui/Board.jsx'

// One selection, many actions. The agent's plan is shown in full; the lens
// starts on Cancel; nothing runs until the person chooses Go ahead.
export default function Plan({ task = 'refill' }) {
  const k = useKinesis()
  const { go } = useNav()
  const base = TASKS.find((t) => t.id === task) || TASKS[0]
  const [plan, setPlan] = useState({ id: `t-${task}`, title: base.label, steps: base.steps.map(([what, detail]) => ({ what, detail })) })
  const [phase, setPhase] = useState('review') // review | running | done
  const [status, setStatus] = useState([]) // per step: undefined | 'running' | 'done'
  const asked = useRef(false)
  const coreRuns = useRef(false) // true once the core's agent sends a plan or step

  // ask the core's agent for a real plan; keep the local one if it does not answer
  useEffect(() => {
    if (asked.current) return
    asked.current = true
    k.send({ type: 'action', action: 'task', task })
  }, [k, task])

  useEffect(
    () =>
      k.subscribe((msg) => {
        if (msg.type === 'plan' || msg.type === 'step') coreRuns.current = true
        if (msg.type === 'plan') setPlan({ id: msg.id, title: msg.title, steps: msg.steps.map((s) => (typeof s === 'string' ? { what: s } : s)) })
        if (msg.type === 'step') {
          setStatus((st) => { const n = [...st]; n[msg.index] = msg.status; return n })
          if (msg.detail) setPlan((p) => ({ ...p, steps: p.steps.map((s, i) => (i === msg.index ? { ...s, detail: msg.detail } : s)) }))
        }
      }),
    [k],
  )

  // simulator: run the steps
  useEffect(() => {
    if (phase !== 'running' || coreRuns.current) return
    let i = 0
    const timers = []
    const next = () => {
      if (i >= plan.steps.length) { setPhase('done'); return }
      const at = i
      setStatus((st) => { const n = [...st]; n[at] = 'running'; return n })
      timers.push(setTimeout(() => {
        setStatus((st) => { const n = [...st]; n[at] = 'done'; return n })
        i += 1
        next()
      }, 1300))
    }
    next()
    return () => timers.forEach(clearTimeout)
  }, [phase]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (coreRuns.current && phase === 'running' && status.length === plan.steps.length && status.every((s) => s === 'done')) setPhase('done')
  }, [status, phase, plan.steps.length])

  const items =
    phase === 'review'
      ? [
          { id: 'cancel', area: 'a', kind: 'safe', glyph: 'cross', label: 'Cancel', sub: 'Nothing is sent', onSelect: () => { k.send({ type: 'cancel', id: plan.id }); go('tasks') } },
          { id: 'go', area: 'b', kind: 'go', glyph: 'check', label: 'Go ahead', sub: `Runs ${plan.steps.length} steps`, onSelect: () => { k.send({ type: 'confirm', id: plan.id }); setPhase('running') } },
        ]
      : phase === 'running'
        ? [{ id: 'stop', area: 'a', kind: 'safe', glyph: 'cross', label: 'Stop', sub: 'Finished steps stay done', onSelect: () => { k.send({ type: 'cancel', id: plan.id }); go('home') } }]
        : [
            { id: 'home', area: 'a', glyph: 'back', label: 'Back home', onSelect: () => go('home') },
            { id: 'another', area: 'b', glyph: 'task', label: 'Another task', onSelect: () => go('tasks') },
          ]

  const layout = items.length === 2 ? { columns: '1fr 1fr', rows: '1fr', areas: '"a b"' } : { columns: '1fr', rows: '1fr', areas: '"a"' }
  const done = status.filter((s) => s === 'done').length

  return (
    <>
      <div className="panel plan">
        <h1 className="screen-title">{plan.title}</h1>
        <p className="screen-lede">
          {phase === 'review' && 'Here is what Kinesis will do. Nothing happens until you choose Go ahead.'}
          {phase === 'running' && `Working on it. ${done} of ${plan.steps.length} done.`}
          {phase === 'done' && 'Done. Everything below went through.'}
        </p>
        <ol className="plan-steps">
          {plan.steps.map((s, i) => (
            <li key={i} className={status[i] || ''}>
              <span className="n">{status[i] === 'done' ? '✓' : i + 1}</span>
              <span className="what">
                {s.what}
                {s.detail && <span className="detail">{s.detail}</span>}
              </span>
              <span className="state">{status[i] === 'done' ? 'Done' : status[i] === 'running' ? 'Working' : ''}</span>
            </li>
          ))}
        </ol>
      </div>
      <Board scanKey={`plan-${phase}`} items={items} layout={layout} help={phase !== 'running'} onHelp={() => go('help')} onBack={phase === 'review' ? () => go('tasks') : undefined} />
    </>
  )
}
