"""Swing + club capture from a 240fps slow-mo video.  ***NOT FUNCTIONAL YET — NEEDS A CLIP.***

240fps changes the game vs 60fps. At impact the club head moves ~6 in/frame
(7-iron) to ~8 in/frame (driver), vs ~2 ft at 60fps. That's trackable: you get a
frame within a few inches of the ball and can measure the club through impact.

WHAT 240fps UNLOCKS (measured, not estimated):
  - club head SPEED: head centroid across the last downswing frames / 4.17 ms.
    Expect ~+/-10-15% on a phone, not launch-monitor exact, but real. The
    --club-speed baseline drops from required input to a sanity check.
  - attack angle: vertical shape of the head path through the impact zone.
  - club path: head trajectory direction through the ball. This also RESOLVES the
    divot's 180-deg direction ambiguity (you see which way the club travelled).
  - tempo / sequencing / posture: easy.
The weak link stays FACE ANGLE: a single phone cam can't reliably resolve clubface
orientation at impact. Keep it approximate (shaft/hand proxy) and let the divot +
ball start direction anchor curve and direction.

THE CONSTRAINT FLIPS FROM SHUTTER TO LIGHT: slo-mo splits the same light across 4x
more frames, and phones force auto-exposure in slo-mo (no manual shutter). You
don't set the shutter, you FEED it light so it picks a fast one. Flood the scene.
Outdoors midday is ideal; indoors, as bright and even as possible. Dim 240fps is
noisy, blurry, untrackable.

HOW TO SHOOT IT (one camera per job is cleaner):
  - SWING: phone on a tripod, locked still, DOWN-THE-LINE (behind the hands, on the
    target line, ~waist height). Best angle for reading the club. Keep the whole mat
    in frame too as a known-size scale reference. One swing per clip.
  - DIVOT: a separate straight-on still of the mat (exactly like the photos that
    already work), plus a 1s empty-mat still for the reference frame.
  - Measure your mat's playing surface once -> converts pixels to real club speed.

OUTPUT: measured club speed + attack + path, tempo/sequence metrics, resolved divot
direction, and the impact frame index.

NOTE: the real club tracker gets built and TUNED against your actual frames — same
way the divot reader came together first try once I had your photos. Untested CV on
fast-moving footage is what breaks; real frames make it solid.
"""

def analyze_swing(video_path, mat_width_mm=None, club_speed_baseline_mph=None):
    try:
        import mediapipe  # noqa: F401
    except ImportError:
        raise SystemExit(
            "swing.py needs mediapipe:  pip install mediapipe\n"
            "Then shoot a 240fps down-the-line clip in bright light (see header).")
    raise NotImplementedError(
        "Club capture is stubbed pending a real 240fps clip. Send one shot per the "
        "header instructions (plus a straight-on divot still and mat dimensions) and "
        "this becomes the next build step.")


if __name__ == "__main__":
    print(__doc__)
