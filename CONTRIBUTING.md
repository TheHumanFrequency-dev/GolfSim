# Contributing to GolfSim

Thanks for helping. This is a small, focused project: a camera golf sim that reads club strikes
off a sequin mat and simulates ball flight. It is a practice/feel tool, not a launch monitor —
keep contributions honest about that.

## Setup
```bash
git clone https://github.com/TheHumanFrequency-dev/GolfSim.git
cd GolfSim
pip install -r requirements.txt
```
Python 3.10+. Core deps: OpenCV, NumPy. `swing.py` additionally needs `mediapipe`.

## Run it
```bash
python flight.py                                   # physics sanity check
python divot.py path/to/strike.jpg                 # read a divot photo
python pipeline.py path/to/strike.jpg --club 7iron --club-speed 84
# open shot_visualizer.html in a browser
```

## How we validate
This project earns trust by matching reality, not by looking polished.
- **flight.py** is checked against published TrackMan tour numbers (driver/7-iron/wedge) — stay
  within a few percent.
- **divot.py** is checked against real photos of the actual mat.
- If you change the physics or the impact model, show the before/after numbers in your PR and how
  they compare to a known reference.

## Conventions
- **Calibratable constants live in one clearly-commented block per file.** Tune there; don't
  scatter magic numbers.
- **Sign conventions (right-handed golfer):** `face`/`path > 0` = aimed right; `sidespin_rpm > 0`
  = right curve. Flight coords: x downrange, y up, z right.
- **`flight.py` and `shot_visualizer.html` share the same physics** — change both together.
- Keep dependencies minimal. Prefer standard library + OpenCV + NumPy.

## Common changes
- **Add a club:** add an entry to `CLUBS` in `impact.py` (effective dynamic loft, smash, default
  AoA) and to `clubs` in `shot_visualizer.html`.
- **Tune ball flight:** the aero coefficients are in `_coeffs()` in `flight.py` (mirrored in the JS).
- **Improve the divot read:** thresholds are the `sat_max` / `val_min` / `min_area` args of
  `read_divot()`.

## Testing your change
No formal suite yet — each module's `__main__` block is its smoke test. Run the relevant ones and
confirm the numbers still look right. A real `pytest` suite (assert flight carries land in expected
ranges) is a welcome contribution.

## Pull requests
- One focused change per PR.
- Note what you validated it against (TrackMan numbers, a real mat photo, etc.).
- Don't commit personal media (swing videos, mat photos) — `.gitignore` already excludes them.

## Scope / non-goals
This is a feel and practice tool. It will not become a measurement instrument, and it won't try to
read clubface angle from a single camera. Improvements to honesty, calibration, and the club
tracker are the priorities.
