import { useNav } from '../App.jsx'
import { CONTACTS } from '../data.js'
import Board from '../ui/Board.jsx'

const LAYOUT = { columns: '1fr 1fr 1fr', rows: '1fr 1fr', areas: '"mom sam dr_patel" "nurse ama back"' }

export default function Call() {
  const { go } = useNav()
  const items = [
    ...CONTACTS.map((c) => ({
      id: c.id, area: c.id, avatar: c.initials, label: c.name, sub: c.sub,
      onSelect: () => go('calling', { contact: c.id }),
    })),
    { id: 'back', area: 'back', kind: 'quiet', glyph: 'back', label: 'Back', onSelect: () => go('home') },
  ]
  return <Board scanKey="call" items={items} layout={LAYOUT} onHelp={() => go('help')} onBack={() => go('home')} />
}
