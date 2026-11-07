import { useNav } from '../App.jsx'
import Board from '../ui/Board.jsx'

const LAYOUT = {
  columns: '1.35fr 1fr 1fr',
  rows: '1fr 1fr',
  areas: '"talk call tasks" "talk media report"',
}

export default function Home() {
  const { go } = useNav()
  const items = [
    { id: 'talk', area: 'talk', kind: 'big', glyph: 'talk', label: 'Talk', sub: 'Reply to what you hear, in your own voice', onSelect: () => go('talk') },
    { id: 'call', area: 'call', glyph: 'call', label: 'Call', sub: 'Mom, Sam, Dr. Patel', onSelect: () => go('call') },
    { id: 'tasks', area: 'tasks', glyph: 'task', label: 'Get it done', sub: 'Refill due Thursday', onSelect: () => go('tasks') },
    { id: 'media', area: 'media', glyph: 'media', label: 'Read and listen', sub: 'Page 112 of Project Hail Mary', onSelect: () => go('media') },
    { id: 'report', area: 'report', glyph: 'report', label: 'Report', sub: 'Today, ready for Dr. Patel', onSelect: () => go('report') },
  ]
  return <Board scanKey="home" items={items} layout={LAYOUT} onHelp={() => go('help')} />
}
