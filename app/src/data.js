// Demo content. The core replaces most of this with real data over the
// WebSocket (profile, replies, plans). Names and places are placeholders.

export const PERSON = {
  name: 'Maya',
  fullName: 'Maya Okafor',
  about: '34, ALS diagnosed 2 years ago, former high school chemistry teacher, lives with her partner Sam in Raleigh',
}

export const CONTACTS = [
  { id: 'mom', name: 'Mom', sub: 'Ada Okafor', initials: 'A' },
  { id: 'sam', name: 'Sam', sub: 'Partner', initials: 'S' },
  { id: 'dr_patel', name: 'Dr. Patel', sub: 'Neurologist', initials: 'P' },
  { id: 'nurse', name: 'Nurse line', sub: 'Duke Health, 24 hours', initials: 'N' },
  { id: 'ama', name: 'Ama', sub: 'Sister', initials: 'A' },
]

export const CARE_LIST = ['Sam', 'Nurse line']

export const HEARD_SAMPLES = [
  { speaker: 'Dr. Patel', text: 'How did you sleep last night?' },
  { speaker: 'Sam', text: 'Do you want to watch something tonight?' },
  { speaker: 'Mom', text: 'Are you warm enough in here?' },
]

export const CANNED_REPLIES = {
  'How did you sleep last night?': [
    'Not great, I woke up a lot',
    'Pretty well, thanks',
    'My back kept me up',
    'Can we talk about it later?',
  ],
  'Do you want to watch something tonight?': [
    'Yes, something funny please',
    'Not tonight, I am tired',
    'What were you thinking?',
    'Can we finish the show from Sunday?',
  ],
  'Are you warm enough in here?': [
    'I am a little cold',
    'Yes, I am fine',
    'Could you open the window?',
    'Can I have a blanket?',
  ],
}

export const TASKS = [
  {
    id: 'refill',
    label: 'Refill my prescription',
    sub: 'Riluzole, due Thursday',
    steps: [
      ['Find the prescription', 'Riluzole 50 mg, last filled Oct 9'],
      ['Call the pharmacy', 'Walgreens, Hillsborough St'],
      ['Confirm pickup time', 'Ready today at 4:30 pm'],
      ['Text Sam to pick it up', '"Can you grab my meds at 4:30?"'],
    ],
  },
  {
    id: 'ride',
    label: 'Book a ride',
    sub: 'Wheelchair van',
    steps: [
      ['Check my calendar', 'Clinic visit Tuesday 10:00 am'],
      ['Request an accessible van', 'GoRaleigh Access'],
      ['Confirm pickup', 'Tuesday 9:15 am at home'],
      ['Add it to my calendar', 'Reminder 30 minutes before'],
    ],
  },
  {
    id: 'groceries',
    label: 'Order groceries',
    sub: 'Same as last week',
    steps: [
      ['Copy last week\'s order', '14 items from Harris Teeter'],
      ['Swap what is out of stock', 'Greek yogurt for Skyr'],
      ['Pick a delivery window', 'Sunday 2 to 4 pm'],
      ['Place the order', 'Charged to the card on file'],
    ],
  },
  {
    id: 'tell_family',
    label: 'Tell my family I\'m okay',
    sub: 'Mom, Ama, Sam',
    steps: [
      ['Write the message', '"Good day today. Love you."'],
      ['Send to Mom', 'iMessage'],
      ['Send to Ama', 'iMessage'],
      ['Send to Sam', 'iMessage'],
    ],
  },
  {
    id: 'appointment',
    label: 'Book an appointment',
    sub: 'Speech therapy',
    steps: [
      ['Find open times', 'Duke Speech Clinic'],
      ['Pick the first morning slot', 'Thursday Nov 12, 9:30 am'],
      ['Book it', 'Confirmation 48213'],
      ['Book a ride for it', 'Wheelchair van, 8:45 am'],
    ],
  },
]

export const NOTES = [
  'My back hurt',
  'I slept badly',
  'Good energy today',
  'Harder to swallow',
  'Short of breath',
  'Muscle cramps',
]

export const REPORT = {
  doctor: 'Dr. Patel',
  facts: [
    ['143', 'choices made'],
    ['2', 'calls'],
    ['5', 'messages sent'],
    ['1', 'help request'],
    ['0', 'seizure-like episodes'],
    ['6:40', 'hours monitored'],
  ],
  // signal quality by hour, 0..1
  hours: [0.92, 0.95, 0.9, 0.88, 0.62, 0.58, 0.85, 0.9, 0.93, 0.91, 0.7, 0.86],
  notes: [
    ['9:12 am', 'My back hurt'],
    ['1:40 pm', 'Muscle cramps'],
  ],
  brain: {
    seizure_like: [],
    rest_periods: 3,
    rest_minutes: 4.5,
    alpha_peak_hz: 9.8,
    baseline_dar: 1.4,
    alerts: [],
  },
}

export const SENSORS = [
  // site, board channel, position on the head map (0..1, top is the nose)
  { ch: 5, site: 'Fp1', x: 0.42, y: 0.16 },
  { ch: 6, site: 'T7', x: 0.1, y: 0.5 },
  { ch: 4, site: 'POz', x: 0.5, y: 0.73 },
  { ch: 2, site: 'O1', x: 0.38, y: 0.86 },
  { ch: 1, site: 'Oz', x: 0.5, y: 0.9 },
  { ch: 3, site: 'O2', x: 0.62, y: 0.86 },
]

export const INPUTS = {
  clench: { name: 'Clench', how: 'Clench your jaw' },
  blink2: { name: 'Double blink', how: 'Blink twice' },
  alpha: { name: 'Eyes closed', how: 'Close your eyes for a second' },
  look: { name: 'Look', how: 'Look at a flashing square' },
}

export const ROLES = {
  select: 'chooses',
  back: 'goes back',
  rest: 'pauses',
}

export const LOOK_TILES = [
  { label: 'Yes', hz: 6.67 },
  { label: 'No', hz: 8.57 },
  { label: 'Help', hz: 10 },
  { label: 'Call Sam', hz: 12 },
]
