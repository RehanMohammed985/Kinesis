import { useNav } from '../App.jsx'
import { TASKS } from '../data.js'
import Board from '../ui/Board.jsx'

const LAYOUT = { columns: '1fr 1fr 1fr', rows: '1fr 1fr', areas: '"refill ride groceries" "tell_family appointment back"' }

export default function Tasks() {
  const { go } = useNav()
  const items = [
    ...TASKS.map((t) => ({ id: t.id, area: t.id, label: t.label, sub: t.sub, onSelect: () => go('plan', { task: t.id }) })),
    { id: 'back', area: 'back', kind: 'quiet', glyph: 'back', label: 'Back', onSelect: () => go('home') },
  ]
  return (
    <>
      <div className="panel">
        <h1 className="screen-title">Get it done</h1>
        <p className="screen-lede">Pick a task. You will see every step before anything happens.</p>
      </div>
      <Board scanKey="tasks" items={items} layout={LAYOUT} onHelp={() => go('help')} onBack={() => go('home')} />
    </>
  )
}
