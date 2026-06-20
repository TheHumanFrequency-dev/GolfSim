# Sequin Sim — camera golf simulator (GolfDaddy-style)

Reads club strikes off a reversible-sequin mat (no real ball) and turns them into
a simulated ball flight. Built and validated on a real mat.

## The pipeline
```
swing video ──► swing.py ──┐  (club speed, face, attack, impact frame)
                           ├─► impact.py ──► flight.py ──► shot card / visualizer
strike photo ─► divot.py ──┘  (club path, strike quality, heel/toe)
```

## What works right now
- **flight.py** — ball flight physics (drag + Magnus, RK4). Matches TrackMan tour
  numbers for driver / 7-iron / wedge within a few percent. No hardware.
- **impact.py** — club delivery + strike → launch conditions (smash, launch, spin,
  curve). The model that replaces a launch monitor. Calibratable constants.
- **divot.py** — reads the white flipped-sequin divot off the green mat: strike
  location, club-path axis, strike quality (clean/fat/thin, heel/toe). Proven on
  the real mat, first try.
- **pipeline.py** — wires it all together. Runs end-to-end on a real divot photo.
- **shot_visualizer.html** — interactive in-browser sim. Same physics as flight.py,
  ported to JS. Sliders + club presets → live trajectory, shot shape, carry/total.

## The one blocker
- **swing.py** — club + body capture from a phone video. **Not functional yet:
  it needs a slow-mo swing clip from you.** See the header in swing.py for exactly
  how to shoot it (tripod, 120/240fps, front-on, plus a 1s empty-mat reference).
  Until then, pipeline.py takes club speed / face / attack as estimates.

## Run it
```bash
pip install opencv-python-headless numpy

# read a divot photo
python divot.py struck.jpg

# full shot from a divot photo (+ estimated club speed until swing.py is live)
python pipeline.py struck.jpg --club 7iron --club-speed 84
python pipeline.py struck.jpg --club driver --club-speed 110 --face -1.5

# open shot_visualizer.html in any browser
```

## Honesty note
This is a practice/feel tool, not a measurement instrument. The divot read is
solid; the impact model is approximate and gets better as you log your own shots.
Aero and impact constants are all in one place per file, tagged calibratable.

## Next builds
1. Origin calibration is in; next is resolving the divot's path DIRECTION
   (180° ambiguity) from the swing video.
2. swing.py once you send a clip — that unlocks real club speed/face/attack.
3. Refine impact constants against your own logged shots.

## Club tracking — status (2026-06-20)
Successor to swing.py is the motion-differenced club tracker.

- **club_track2.py** — tracks the club head off a down-the-line slow-mo clip by
  motion-differencing (only the *moving* bright marker survives; static clutter
  cancels). Working architecture.
- **club_track.py** — earlier largest-bright-blob version; superseded (it locked
  onto static background clubs). Kept for reference.
- **probe_shaft.py** — HSV probe used to confirm the shaft tape isolates.

**Proven:** iPhone 240fps slo-mo is preserved inside an exported 30fps .mov
(consecutive frames ≈ 1/240 s, so fast motion is analyzable). White tape on the
shaft isolates cleanly (HSV V>195 & S<70). Down-the-line is the right angle.

**Blocker is capture, not code.** For a clean, trackable clip:
1. Clear the background — no bag of spare clubs / shiny objects in frame.
2. Tape the club HEAD (bright white/neon), not just the shaft.
3. Light the ball — lamp on the hitting area or daylight.
4. One swing per clip, striking the mat.
5. Keep down-the-line + 240fps.

**Still needed for speed:** one real measurement (mat long-side mm, or club length)
to convert pixels → mph. Path and attack are scale-free.

Feel / practice tool, not a launch monitor. The impact model is approximate and
calibratable — treat the numbers as directional.
