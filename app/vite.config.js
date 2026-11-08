import { createHash } from 'node:crypto'
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { ElevenLabsClient } from '@elevenlabs/elevenlabs-js'
import { CANNED_REPLIES, QUICK_TEXTS, SAY } from './src/data.js'

// Server-side helpers for the demo. Keys live in app/.env (never committed)
// and are only read here, so nothing secret reaches the browser bundle.
//   ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID   -> /api/speak (user's own voice)
//   GEMINI_API_KEY, GEMINI_MODEL              -> /api/replies (predicted replies)
// /api/outbox lets the caregiver page (any phone on the same wifi) receive
// the messages the user sends, live.
// /api/prewarm voices every fixed phrase once, so the demo plays instantly
// and spends no credits on stage. /core forwards to the Kinesis core.
//   KINESIS_CORE (default ws://localhost:8765)
function kinesisServer(env) {
  const cacheDir = join(process.cwd(), '.cache', 'tts')
  mkdirSync(cacheDir, { recursive: true })
  const outbox = []
  const listeners = new Set()

  const readBody = (req) =>
    new Promise((resolve) => {
      let data = ''
      req.on('data', (c) => (data += c))
      req.on('end', () => {
        try { resolve(JSON.parse(data || '{}')) } catch { resolve({}) }
      })
    })

  // The official ElevenLabs SDK. The key comes from app/.env (loaded below
  // with Vite's loadEnv), never from code, and never reaches the browser.
  const eleven = env.ELEVENLABS_API_KEY ? new ElevenLabsClient({ apiKey: env.ELEVENLABS_API_KEY }) : null

  const tts = async (text) => {
    const model = env.ELEVENLABS_MODEL || 'eleven_flash_v2_5'
    const key = createHash('sha1').update(`${env.ELEVENLABS_VOICE_ID}|${model}|${text}`).digest('hex')
    const file = join(cacheDir, `${key}.mp3`)
    if (!existsSync(file)) {
      if (!eleven) throw new Error('Set ELEVENLABS_API_KEY in app/.env')
      const audio = await eleven.textToSpeech.convert(env.ELEVENLABS_VOICE_ID, {
        text,
        modelId: model,
        outputFormat: 'mp3_44100_128',
      })
      writeFileSync(file, Buffer.from(await new Response(audio).arrayBuffer()))
    }
    return file
  }

  const json = (res, code, body) => {
    res.statusCode = code
    res.setHeader('Content-Type', 'application/json')
    res.end(JSON.stringify(body))
  }

  return {
    name: 'kinesis-server',
    configureServer(server) {
      server.middlewares.use(async (req, res, next) => {
        if (!req.url.startsWith('/api/')) return next()

        if (req.url === '/api/status') {
          return json(res, 200, {
            voice: Boolean(env.ELEVENLABS_API_KEY && env.ELEVENLABS_VOICE_ID),
            replies: Boolean(env.GEMINI_API_KEY),
          })
        }

        if (req.url === '/api/speak' && req.method === 'POST') {
          const { text } = await readBody(req)
          if (!text) return json(res, 400, { error: 'text is required' })
          if (!env.ELEVENLABS_API_KEY || !env.ELEVENLABS_VOICE_ID) {
            return json(res, 503, { error: 'Set ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID in app/.env' })
          }
          try {
            const file = await tts(text)
            res.setHeader('Content-Type', 'audio/mpeg')
            return res.end(readFileSync(file))
          } catch (e) {
            return json(res, 502, { error: String(e.message || e) })
          }
        }

        if (req.url === '/api/prewarm' && req.method === 'POST') {
          if (!env.ELEVENLABS_API_KEY || !env.ELEVENLABS_VOICE_ID) {
            return json(res, 503, { error: 'Set ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID in app/.env' })
          }
          const phrases = [...new Set([...SAY, ...QUICK_TEXTS, ...Object.values(CANNED_REPLIES).flat(),
            'I need help', 'Yes', 'No', 'Can you say that again?', 'Give me a minute'])]
          const failed = []
          for (const p of phrases) {
            try { await tts(p) } catch (e) { failed.push(`${p}: ${e.message}`) }
          }
          return json(res, failed.length ? 502 : 200, { voiced: phrases.length - failed.length, failed })
        }

        if (req.url === '/api/replies' && req.method === 'POST') {
          const { heard, persona, setting } = await readBody(req)
          if (!env.GEMINI_API_KEY) return json(res, 503, { error: 'Set GEMINI_API_KEY in app/.env' })
          const model = env.GEMINI_MODEL || 'gemini-2.5-flash'
          const prompt =
            `You help ${persona?.name || 'a person'} who cannot speak or move reply in conversation. ` +
            `About them: ${persona?.about || 'adult, uses a brain-computer interface to choose replies'}. ` +
            `Setting: ${setting || 'home'}. Someone just said: "${heard}". ` +
            'Write exactly 4 short replies they might want to say, first person, under 9 words each, ' +
            'covering different intents (agree, decline or disagree, ask something back, a feeling or need). ' +
            'Return only a JSON array of 4 strings.'
          const r = await fetch(
            `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${env.GEMINI_API_KEY}`,
            {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                contents: [{ parts: [{ text: prompt }] }],
                generationConfig: { responseMimeType: 'application/json', temperature: 0.7 },
              }),
            },
          )
          if (!r.ok) return json(res, 502, { error: `Gemini ${r.status}` })
          const body = await r.json()
          try {
            const items = JSON.parse(body.candidates[0].content.parts[0].text).slice(0, 4)
            return json(res, 200, { items })
          } catch {
            return json(res, 502, { error: 'Gemini returned something that is not a list' })
          }
        }

        if (req.url === '/api/outbox' && req.method === 'POST') {
          const msg = { ...(await readBody(req)), at: Date.now() }
          outbox.unshift(msg)
          for (const l of listeners) l.write(`data: ${JSON.stringify(msg)}\n\n`)
          return json(res, 200, { ok: true })
        }

        if (req.url === '/api/outbox' && req.method === 'GET') return json(res, 200, outbox)

        if (req.url === '/api/outbox/stream') {
          res.setHeader('Content-Type', 'text/event-stream')
          res.setHeader('Cache-Control', 'no-cache')
          res.setHeader('Connection', 'keep-alive')
          res.write(': connected\n\n')
          listeners.add(res)
          req.on('close', () => listeners.delete(res))
          return
        }

        return json(res, 404, { error: 'unknown endpoint' })
      })
    },
  }
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    plugins: [react(), kinesisServer(env)],
    server: {
      port: 5173,
      host: true,
      allowedHosts: true,
      proxy: { '/core': { target: env.KINESIS_CORE || 'ws://localhost:8765', ws: true, rewrite: () => '/' } },
    },
  }
})
