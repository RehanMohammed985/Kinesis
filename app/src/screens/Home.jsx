import { useNav } from '../App.jsx'
import { CONTACTS, HEARD_SAMPLES, REPORT, SAY, TASKS } from '../data.js'
import Board from '../ui/Board.jsx'

// The three things a day runs on, first: say something, get something done,
// reach someone. The lens starts on Say it. Every tile shows what is behind it.
const LAYOUT = {
  columns: '1.3fr 1fr 1fr',
  rows: '1.5fr 1fr',
  areas: '"say do reach" "talk media report"',
  phone: { columns: '1fr 1fr', rows: '1.3fr 1fr 1fr 0.62fr', areas: '"say say" "do reach" "talk media" "report report"' },
}

export default function Home() {
  const { go } = useNav()
  const family = CONTACTS.slice(0, 3)
  const task = TASKS[0]
  const heard = HEARD_SAMPLES[0]
  const items = [
    {
      id: 'say', area: 'say', kind: 'big hero', glyph: 'say', label: 'Say it', sub: 'Out loud, in your own voice',
      extra: SAY.slice(0, 3).map((t) => <i key={t}>{t}</i>), onSelect: () => go('say'),
    },
    {
      id: 'do', area: 'do', glyph: 'task', label: 'Get it done', sub: 'Kinesis does the steps for you',
      extra: <span className="next"><em>Next</em>{task.label}<small>{task.sub}</small></span>, onSelect: () => go('tasks'),
    },
    {
      id: 'reach', area: 'reach', glyph: 'call', label: 'Call or text', sub: family.map((c) => c.name).join(', '),
      extra: <span className="faces">{family.map((c) => <b key={c.id}>{c.initials}</b>)}<small><s />Linda is home</small></span>, onSelect: () => go('call'),
    },
    {
      id: 'talk', area: 'talk', kind: 'compact', glyph: 'talk', label: 'Talk', sub: 'Reply to what you hear',
      extra: <span className="quote"><b>{`\u201C${heard.text}\u201D`}</b><small>{heard.speaker}</small></span>, onSelect: () => go('talk'),
    },
    {
      id: 'media', area: 'media', kind: 'compact', glyph: 'media', label: 'Read and listen', sub: 'Lonesome Dove',
      extra: <span className="progress"><span><i style={{ width: `${(112 / 858) * 100}%` }} /></span><small>Page 112 of 858</small></span>, onSelect: () => go('media'),
    },
    {
      id: 'report', area: 'report', kind: 'compact', glyph: 'report', label: 'Report', sub: 'Today, for Dr. Patel',
      extra: <span className="spark">{REPORT.hours.map((h, i) => <i key={i} style={{ height: `${h * 100}%` }} />)}</span>, onSelect: () => go('report'),
    },
  ]
  return <Board scanKey="home" items={items} layout={LAYOUT} onHelp={() => go('help')} />
}
