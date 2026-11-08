import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { useKinesis } from './engine/kinesis.jsx'
import Rail from './ui/Rail.jsx'
import SignalStrip from './ui/SignalStrip.jsx'
import Fit from './screens/Fit.jsx'
import Calibrate from './screens/Calibrate.jsx'
import Home from './screens/Home.jsx'
import Talk from './screens/Talk.jsx'
import Call from './screens/Call.jsx'
import Calling from './screens/Calling.jsx'
import Tasks from './screens/Tasks.jsx'
import Plan from './screens/Plan.jsx'
import Media from './screens/Media.jsx'
import Help from './screens/Help.jsx'
import Report from './screens/Report.jsx'
import Look from './screens/Look.jsx'
import Say from './screens/Say.jsx'
import Contact from './screens/Contact.jsx'

const Nav = createContext(null)
export const useNav = () => useContext(Nav)

const SCREENS = { fit: Fit, calibrate: Calibrate, home: Home, talk: Talk, call: Call, calling: Calling, tasks: Tasks, plan: Plan, media: Media, help: Help, report: Report, look: Look, say: Say, contact: Contact }

export default function App() {
  const k = useKinesis()
  const first = new URLSearchParams(location.search).get('start') || 'fit'
  const [route, setRoute] = useState({ name: SCREENS[first] ? first : 'fit', params: {}, n: 0 })
  const go = useCallback((name, params = {}) => setRoute((r) => ({ name, params, n: r.n + 1 })), [])

  // a seizure-like alert from the monitor opens the alarm screen
  useEffect(
    () =>
      k.subscribe((msg) => {
        if (msg.type === 'alert' && msg.kind === 'seizure_like') {
          k.outbox({ kind: 'help', to: 'Linda, Nurse line', text: msg.text })
          go('help', { reason: 'seizure', text: msg.text })
        }
      }),
    [k, go],
  )

  // simulator shortcuts that are not inputs
  useEffect(() => {
    const down = (e) => {
      if (e.repeat || e.metaKey || e.ctrlKey) return
      const key = e.key.toLowerCase()
      if (key === 'i' && k.mode === 'sim') go('calling', { contact: 'linda', incoming: true })
      if (key === 'l') go('look')
      if (key === 'h' && e.shiftKey) go('home')
    }
    window.addEventListener('keydown', down)
    return () => window.removeEventListener('keydown', down)
  }, [go, k.mode])

  const Screen = SCREENS[route.name]
  const alarm = route.name === 'help'

  return (
    <Nav.Provider value={{ go, route }}>
      <div className={`frame ${alarm ? 'alarm' : ''}`}>
        <Rail onSetup={() => go('fit')} />
        <main className="stage">
          <Screen key={route.n} {...route.params} />
        </main>
        <SignalStrip />
      </div>
      {k.toast && <div className="toast" role="status">{k.toast}</div>}
      {k.showKeys && <Keys />}
    </Nav.Provider>
  )
}

function Keys() {
  return (
    <div className="keys" role="dialog" aria-label="Simulator keys">
      <kbd>C</kbd><span>Hold to clench</span>
      <kbd>B B</kbd><span>Double blink</span>
      <kbd>E</kbd><span>Hold to close eyes</span>
      <kbd>1 to 4</kbd><span>Look at a tile</span>
      <kbd>I</kbd><span>Incoming call from Linda</span>
      <kbd>L</kbd><span>Look mode</span>
      <kbd>S</kbd><span>Spoken scanning on or off</span>
      <kbd>X</kbd><span>Replay a recorded seizure</span>
      <kbd>Shift H</kbd><span>Home</span>
      <kbd>?</kbd><span>Hide these keys</span>
    </div>
  )
}
