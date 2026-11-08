// Hand-drawn line glyphs, one stroke weight, so the board reads as one set.
const P = {
  talk: (
    <>
      <path d="M9 9h30a5 5 0 0 1 5 5v15a5 5 0 0 1-5 5H23l-9 7v-7H9a5 5 0 0 1-5-5V14a5 5 0 0 1 5-5z" />
      <path d="M14 19h14M14 25h20" />
    </>
  ),
  call: (
    <path d="M15 5l6 1.5 3 9-4.5 3.5a25 25 0 0 0 10.5 10.5l3.5-4.5 9 3 1.5 6c0 3.3-2.7 6-6 6C21 40 8 27 8 11c0-3.3 2.7-6 6-6z" />
  ),
  task: (
    <>
      <path d="M8 12l3.5 3.5L18 9" />
      <path d="M24 12h17M8 24h33M8 36h33" />
    </>
  ),
  media: (
    <>
      <path d="M5 10c6.5-2.5 13-2 19 2 6-4 12.5-4.5 19-2v28c-6.5-2-13-1.5-19 2-6-3.5-12.5-4-19-2z" />
      <path d="M24 12v28" />
    </>
  ),
  report: (
    <>
      <path d="M11 4h19l9 9v31H11z" />
      <path d="M30 4v9h9" />
      <path d="M18 36V28M25 36V22M32 36v-6" />
    </>
  ),
  help: (
    <>
      <path d="M24 6c-7 0-12 5-12 12v9l-4 6h32l-4-6v-9c0-7-5-12-12-12z" />
      <path d="M19 38a5 5 0 0 0 10 0" />
    </>
  ),
  back: <path d="M20 12L8 24l12 12M9 24h31" />,
  more: (
    <>
      <path d="M39 22a15 15 0 1 0-4 11" />
      <path d="M40 10v12H28" />
    </>
  ),
  look: (
    <>
      <path d="M3 24s8-13 21-13 21 13 21 13-8 13-21 13S3 24 3 24z" />
      <circle cx="24" cy="24" r="6" />
    </>
  ),
  note: (
    <>
      <path d="M10 6h28v36H10z" />
      <path d="M17 16h14M17 23h14M17 30h8" />
    </>
  ),
  send: <path d="M5 23L43 6 33 43l-9-15-19-5zM24 28l19-22" />,
  hangup: <path d="M4 28c11-9 29-9 40 0l-3 7-8-2-1-6c-4-1.5-10-1.5-16 0l-1 6-8 2z" />,
  page: <path d="M14 10l14 14-14 14M30 10l0 28" />,
  pageBack: <path d="M34 10L20 24l14 14M18 10v28" />,
  play: <path d="M14 8l26 16-26 16z" />,
  pause: <path d="M15 9v30M33 9v30" />,
  read: (
    <>
      <path d="M6 18h8l10-9v30l-10-9H6z" />
      <path d="M32 17a10 10 0 0 1 0 14M37 12a17 17 0 0 1 0 24" />
    </>
  ),
  check: <path d="M8 25l10 10L40 13" />,
  say: (
    <>
      <path d="M10 43v-9c-4-3-6-8-6-13C4 12 11 5 20 5c8 0 14 6 14 13l4 8h-4v5a3 3 0 0 1-3 3h-6v9" />
      <path d="M40 15a8 8 0 0 1 0 11M44 10a15 15 0 0 1 0 21" />
    </>
  ),
  text: (
    <>
      <path d="M6 10h36v24H24l-10 8v-8H6z" />
      <path d="M13 19h22M13 26h14" />
    </>
  ),
  cross: <path d="M12 12l24 24M36 12L12 36" />,
}

export default function Glyph({ name, className = 'cell-glyph' }) {
  const d = P[name]
  if (!d) return null
  return (
    <svg className={className} viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="3.4"
      strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {d}
    </svg>
  )
}
