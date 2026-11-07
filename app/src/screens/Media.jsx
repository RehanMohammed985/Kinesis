import { useState } from 'react'
import { useNav } from '../App.jsx'
import { useKinesis } from '../engine/kinesis.jsx'
import Board from '../ui/Board.jsx'

// Every control is a keypress the core forwards to the e-reader, browser, or
// music app, so this works with whatever the person already uses.
const LAYOUT = { columns: '1.3fr 1fr 1fr', rows: '1fr 1fr', areas: '"next prev read" "next music back"' }

export default function Media() {
  const k = useKinesis()
  const { go } = useNav()
  const [page, setPage] = useState(112)
  const [playing, setPlaying] = useState(false)
  const [reading, setReading] = useState(false)

  const media = (command, label) => k.act({ action: 'media', command, label })

  const items = [
    { id: 'next', area: 'next', kind: 'big', glyph: 'page', label: 'Next page', sub: `Page ${page + 1}`, onSelect: () => { setPage((p) => p + 1); media('page_next', `Page ${page + 1}`) } },
    { id: 'prev', area: 'prev', glyph: 'pageBack', label: 'Previous page', onSelect: () => { setPage((p) => Math.max(1, p - 1)); media('page_prev', `Page ${Math.max(1, page - 1)}`) } },
    { id: 'read', area: 'read', glyph: 'read', label: reading ? 'Stop reading aloud' : 'Read aloud', onSelect: () => { setReading((r) => !r); media(reading ? 'read_stop' : 'read_start', reading ? 'Stopped reading' : 'Reading aloud') } },
    { id: 'music', area: 'music', glyph: playing ? 'pause' : 'play', label: playing ? 'Pause music' : 'Play music', sub: 'Saturday playlist', onSelect: () => { setPlaying((p) => !p); media(playing ? 'pause' : 'play', playing ? 'Music paused' : 'Playing Saturday playlist') } },
    { id: 'back', area: 'back', kind: 'quiet', glyph: 'back', label: 'Back', onSelect: () => go('home') },
  ]

  return (
    <>
      <div className="panel">
        <h1 className="screen-title">Project Hail Mary</h1>
        <p className="screen-lede">Chapter 12, page {page}{playing ? '. Music playing.' : '.'}</p>
      </div>
      <Board scanKey="media" items={items} layout={LAYOUT} onHelp={() => go('help')} onBack={() => go('home')} />
    </>
  )
}
