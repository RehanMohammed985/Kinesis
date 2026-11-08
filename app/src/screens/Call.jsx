import { useNav } from '../App.jsx'
import { CONTACTS } from '../data.js'
import Board from '../ui/Board.jsx'

// Who to reach. Family first, then the care team.
const LAYOUT = {
  columns: 'repeat(3, 1fr)',
  rows: '1fr 1fr 0.42fr',
  areas: '"linda maria david" "grace dr_patel nurse" "back back back"',
  phone: { columns: '1fr 1fr', rows: 'repeat(3, 1fr) 0.5fr', areas: '"linda maria" "david grace" "dr_patel nurse" "back back"' },
}

export default function Call() {
  const { go } = useNav()
  const items = [
    ...CONTACTS.map((c) => ({
      id: c.id, area: c.id, avatar: c.initials, label: c.name, sub: c.sub,
      onSelect: () => go('contact', { contact: c.id }),
    })),
    { id: 'back', area: 'back', kind: 'quiet', glyph: 'back', label: 'Back', onSelect: () => go('home') },
  ]
  return (
    <>
      <div className="panel">
        <h1 className="screen-title">Call or text</h1>
      </div>
      <Board scanKey="call" items={items} layout={LAYOUT} onHelp={() => go('help')} onBack={() => go('home')} />
    </>
  )
}
