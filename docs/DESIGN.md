# Kinesis app design

## Brief
The screen a person with ALS, cerebral palsy, a spinal cord injury, or a stroke uses from a bed or wheelchair, driven by one switch-like signal at a time. Its job: make the current choice unmistakable from across a room, and make the person's own signal visible as it builds toward a choice. Second audience: the caregiver. Third: judges watching on a projector.

## Point of view
An adult's personal instrument, not a children's symbol board and not a hospital monitor. Calm, plain, very legible, with one bold thing: the scan lens.

The scan lens is the yellow frame that moves across the options. While the person clenches, the lens fills from the bottom with their live signal. When the fill reaches the top, the choice is made. Brain or muscle to action, visibly, in one shape. Everything else stays quiet so the lens reads from across a room.

## Tokens

| Name | Hex | Use |
|---|---|---|
| Mineral | #DCE1DD | page ground |
| Paper | #F7F8F5 | option cells |
| Ink | #1D2A2E | text, committed cells |
| Signal | #F4C21B | the scan lens and live fill (tactile-paving yellow) |
| Alarm | #C5301F | help and anything urgent |
| Settled | #2E7457 | done, good contact |

Type: Atkinson Hyperlegible Next for everything. It was designed by the Braille Institute for low-vision readers; letterforms that are easy to confuse (I l 1, 0 O, b d) are drawn to differ. Tabular numerals for counts and times. Scale: 15 / 18 / 22 / 30 / 44 / 64 px. Weights 400, 600, 800. Sentence case everywhere.

## Layout

```
+-------------------------------------------------------------+
| Maya            2:41 pm          Headset on   Clench chooses |  status rail
+-------------------------------------------------------------+
|                         |                 |                 |
|        Talk             |      Call       |   Get it done   |
|   Answer Dr. Patel      |                 |                 |
|                         +-----------------+-----------------+
|                         |  Read & listen  |     Report      |
|                         |                 |                 |
+-------------------------------------------------------------+
|                       I need help                            |  always present, last in scan
+-------------------------------------------------------------+
| Clench  ~~~~~~~~/\~~~~~ chooses | Double blink  goes back | Eyes closed  rests |  signal strip
+-------------------------------------------------------------+
```

- Left aligned text inside cells; labels sit low in the cell so the lens fill passes behind them.
- The most used option is the biggest cell.
- Help is a persistent bar on every board and always the last stop in the scan.
- The signal strip shows each input's live trace and its threshold, and what that input does for this person (set by calibration).

## Rules
- No shadows, no gradients, no glass. Cells are defined by fill against the ground.
- Motion answers the system or the person: the lens moving, the fill rising, a commit. Nothing else moves.
- Respect reduced motion: the lens jumps instead of slides.
- Flicker tiles (look mode) only after a photosensitivity notice, and only 6 to 15 Hz.
- Words name what happens: "Call Mom", "Send to Dr. Patel", not "Submit".
- Every confirm screen starts with the lens on Cancel.
