# CLAUDE.md — working in this repo

Guidance for AI assistants (Claude Code, etc.) and new contributors. Read this before editing.

## What this is
A camera golf simulator that reads CLUB STRIKES off a reversible-sequin mat (no real
ball, no launch monitor) and turns them into a simulated ball flight. It is a
practice/feel tool, not a measurement instrument — say so, and keep the model honest.

## Prime directives
- **Honesty over precision.** The divot read is solid; the impact model is approximate
  and calibratable. Never present output as launch-monitor-accurate. Numbers are directional.
- **Keep the surface small.** Pure Python + OpenCV + NumPy. No heavy frameworks. `swing.py`
  optionally needs `mediapipe`; nothing else gets added without a strong reason.
- **Calibratable constants live in ONE place per file**, tagged in comments. Tune those;
  don't scatter magic numbers.

## Module map
| File | Role | Status |
|---|---|---|
| `flight.py` | Ball flight physics (drag + Magnus, RK4). | Validated vs TrackMan within a few % |
| `impact.py` | Club delivery + strike → launch conditions (the launch-monitor replacement). `CLUBS` holds per-club loft/smash/AoA. | Validated; constants calibratable |
| `divot.py` | Reads the white flipped-sequin divot off the green mat → strike location, path axis, quality. | Validated first-try on real mat photos |
| `pipeline.py` | divot photo → impact → flight → shot card. | Working end-to-end |
| `shot_visualizer.html` | In-browser sim; JS port of `flight.py`. Keep in sync with `flight.py`. | Working |
| `club_track2.py` | Club-head tracker off a down-the-line slow-mo clip (motion-differenced). The working architecture. | Built; needs a clean capture |
| `club_track.py` | Old largest-bright-blob tracker. Superseded; kept for reference. | Deprecated |
| `probe_shaft.py` | HSV threshold probe for the shaft tape. | Dev tool |
| `swing.py` | Full swing+club capture (mediapipe). | Stub — see header |

## Conventions you must respect
- **Flight coords (metres):** x downrange (target), y up, z right.
- **Spin sign (RH golfer):** `sidespin_rpm > 0` ⇒ right curve (fade/slice). `face_deg`/`path_deg > 0` ⇒ aimed right of target.
- **Divot frame:** target = up; +x offset = toe-side, +y offset = ahead of ball (thin tendency).
- **Effective dynamic loft** in `CLUBS` already bakes in typical shaft lean — it is lower than
  static loft for irons. Don't "correct" it back to static loft.
- If you change physics in `flight.py`, mirror it in `shot_visualizer.html` (same coefficients).

## Run / smoke-test
```bash
pip install -r requirements.txt
python flight.py     # prints driver/7i/PW/slice carries — sanity vs TrackMan
python impact.py     # impact model → flight, per club
python divot.py path/to/strike.jpg
python pipeline.py path/to/strike.jpg --club 7iron --club-speed 84
```
There is no test suite yet; each module's `__main__` block IS its smoke test. Adding a real
one is welcome (see CONTRIBUTING.md).

## Current state & the one blocker
The engine is done and validated. The club tracker is built but **blocked on capture quality**,
not code. A trackable clip needs: clear background (no spare-club bag in frame), bright tape on
the club HEAD, light on the ball, ONE swing per clip, down-the-line, 240fps. Speed also needs ONE
real measurement (mat long-side mm or club length) to convert px→mph; path and attack are scale-free.

## Hard-won gotchas (don't re-learn these)
- **iPhone 240fps slo-mo exported to a 30fps .mov keeps its 240fps temporal resolution** —
  consecutive frames ≈ 1/240 s, so you can analyze fast motion frame-by-frame off a "30fps" file.
- **Portrait iPhone video extracts to 1080×1920** despite a 1920×1080 container flag. Do pixel
  math on the extracted frame shape, not the container dims.
- **Track moving objects with motion differencing** (`absdiff` vs previous frame) so static bright
  clutter cancels. "Largest bright blob" grabs the background instead.
- **A single phone camera cannot read clubface angle.** It can read attack, path, and speed
  (speed needs a scale). Don't promise face.
- **Better capture beats heroic CV.** The divot reader worked first-try on a clean still; the
  tracker stalled on a dim, cluttered, multi-swing clip.

## What NOT to do
- Don't claim measurement-grade accuracy.
- Don't add a clubface-from-one-camera "solution."
- Don't add heavy dependencies or a framework.
- Don't scatter tuning constants; keep them in the marked block per file.
