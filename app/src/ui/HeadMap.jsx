import { SENSORS } from '../data.js'

// Top view of the head with each sensor, colored by its contact state.
// quality: { [ch]: { state, reason, justOn } }
const BOX = { x: 40, y: 78, size: 420 }
const pos = (s) => ({ cx: BOX.x + s.x * BOX.size, cy: BOX.y + s.y * BOX.size })

export const REASON = {
  ok: 'Reading well',
  flat: 'Not touching skin',
  railed: 'Pressed too hard or paste too thick',
  noise: 'Picking up noise',
  no_alpha: 'No response when eyes close',
  off: 'Turning on',
}

export default function HeadMap({ quality = {}, onTap, waiting = false }) {
  return (
    <svg className={`head ${waiting ? 'waiting' : ''}`} viewBox="0 0 500 540" role="img" aria-label="Top view of the head showing each sensor">
      <path className="nose" d="M222 92 L250 46 L278 92" />
      <ellipse className="ear" cx="34" cy="288" rx="22" ry="44" />
      <ellipse className="ear" cx="466" cy="288" rx="22" ry="44" />
      <circle className="skull" cx="250" cy="288" r="214" />
      <circle className="grid-line" cx="250" cy="288" r="150" />
      <circle className="grid-line" cx="250" cy="288" r="78" />
      <path className="grid-line" d="M250 76V500M38 288H462" />
      {SENSORS.map((s) => {
        const c = quality[s.ch] || { state: 'off' }
        const { cx, cy } = pos(s)
        const below = s.y < 0.5
        return (
          <g
            key={s.ch}
            className={`node ${c.state} ${c.justOn ? 'on-now' : ''}`}
            onClick={() => onTap?.(s.ch)}
            role="button"
            aria-label={`${s.site}: ${REASON[c.reason] || c.state}`}
          >
            <circle cx={cx} cy={cy} r={c.state === 'off' ? 16 : 21} />
            <text x={cx} y={below ? cy + 44 : cy - 32} textAnchor="middle">{s.site}</text>
          </g>
        )
      })}
    </svg>
  )
}
