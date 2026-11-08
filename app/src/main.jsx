import { StrictMode, useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import '@fontsource-variable/atkinson-hyperlegible-next'
import './styles.css'
import App from './App.jsx'
import Caregiver from './screens/Caregiver.jsx'
import { KinesisProvider } from './engine/kinesis.jsx'
import { unlockAudio } from './engine/speak.js'

window.addEventListener('pointerdown', unlockAudio, { once: true })
window.addEventListener('keydown', unlockAudio, { once: true })

function Root() {
  const [hash, setHash] = useState(location.hash)
  useEffect(() => {
    const on = () => setHash(location.hash)
    window.addEventListener('hashchange', on)
    return () => window.removeEventListener('hashchange', on)
  }, [])
  if (hash.startsWith('#/caregiver')) return <Caregiver />
  return (
    <KinesisProvider>
      <App />
    </KinesisProvider>
  )
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Root />
  </StrictMode>,
)
