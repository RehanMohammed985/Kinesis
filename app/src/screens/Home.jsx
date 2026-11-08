import { useNav } from '../App.jsx'
import { CONTACTS, SAY } from '../data.js'
import Board from '../ui/Board.jsx'

// The three things a day runs on, first: say something, get something done,
// reach someone. The lens starts on Say it.
const LAYOUT = {
  columns: '1.3fr 1fr 1fr',
  rows: '1.55fr 1fr',
  areas: '"say do reach" "talk media report"',
  phone: { columns: '1fr 1fr', rows: '1.3fr 1fr 1fr 0.55fr', areas: '"say say" "do reach" "talk media" "report report"' },
}

export default function Home() {
  const { go } = useNav()
  const family = CONTACTS.slice(0, 3)
  const items = [
    {
      id: 'say', area: 'say', kind: 'big', glyph: 'say', label: 'Say it', sub: 'Out loud, in your own voice',
      extra: SAY.slice(0, 3).map((t) => <i key={t}>{t}</i>), onSelect: () => go('say'),
    },
    { id: 'do', area: 'do', glyph: 'task', label: 'Get it done', sub: 'Refill my pills, book a ride', onSelect: () => go('tasks') },
    {
      id: 'reach', area: 'reach', glyph: 'call', label: 'Call or text', sub: family.map((c) => c.name).join(', '),
      extra: family.map((c) => <b key={c.id}>{c.initials}</b>), onSelect: () => go('call'),
    },
    { id: 'talk', area: 'talk', glyph: 'talk', label: 'Talk', sub: 'Reply to what you hear', onSelect: () => go('talk') },
    { id: 'media', area: 'media', glyph: 'media', label: 'Read and listen', sub: 'Lonesome Dove, page 112', onSelect: () => go('media') },
    { id: 'report', area: 'report', glyph: 'report', label: 'Report', sub: 'Today, for Dr. Patel', onSelect: () => go('report') },
  ]
  return <Board scanKey="home" items={items} layout={LAYOUT} onHelp={() => go('help')} />
}
