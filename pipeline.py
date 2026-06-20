"""End-to-end shot pipeline: divot photo -> impact model -> ball flight -> shot card.

What comes from the DIVOT (your real mat, working now):
  club path (axis), strike quality (clean/fat/thin, heel/toe), strike efficiency.
What comes from the SWING VIDEO (Phase 3, not built yet) and is passed in here
as estimates for now: club head speed, face angle, attack angle.

Usage:
  python pipeline.py struck.jpg --club 7iron --club-speed 84
  python pipeline.py struck.jpg --club driver --club-speed 110 --face -1.5
"""
import argparse, cv2
import divot, impact, flight

# play-area width assumed for converting normalised heel/toe to mm.
# measure your mat's playing surface once and set this exactly.
PLAY_WIDTH_MM = 250.0


def axis_to_path(axis_deg):
    """OpenCV ellipse angle -> club path relative to the vertical target line.
    Near-vertical divot => near-zero path. Sign provisional until the swing
    video resolves divot direction; + = path aimed right (in-to-out for RH)."""
    p = axis_deg - 180 if axis_deg > 90 else axis_deg
    return round(p, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--club", default="7iron", choices=list(impact.CLUBS))
    ap.add_argument("--club-speed", type=float, required=True, help="mph (from swing video later)")
    ap.add_argument("--face", type=float, default=None, help="face angle deg, + = right (default: square to path)")
    ap.add_argument("--attack", type=float, default=None, help="attack angle deg (default: club preset)")
    ap.add_argument("--out", default="shot_overlay.png")
    args = ap.parse_args()

    d = divot.read_divot(args.image)
    cv2.imwrite(args.out, d.pop("overlay"))

    path = axis_to_path(d["path_axis_deg"])
    face = path if args.face is None else args.face        # square unless given
    heel_toe_mm = d["offset_norm"][0] * (PLAY_WIDTH_MM / 2)

    lp = impact.compute_launch(args.club_speed, args.club, face_deg=face, path_deg=path,
                               attack_deg=args.attack, strike_eff=d["strike_eff"],
                               heel_toe_mm=heel_toe_mm)
    shot = flight.simulate(lp["ball_speed_mph"], lp["launch_deg"], lp["azimuth_deg"],
                           lp["backspin_rpm"], lp["sidespin_rpm"])

    shape = "straight"
    if lp["sidespin_rpm"] > 250: shape = "fade/slice (right)"
    elif lp["sidespin_rpm"] < -250: shape = "draw/hook (left)"

    print(f"""
========================  SHOT  ========================
  Club            {args.club}   (head speed {args.club_speed:.0f} mph, estimated)
  --- read from your divot ---
  Strike          {d['lateral']}, {d['low_point']}
  Club path       {path:+.1f} deg   (axis {d['path_axis_deg']:.0f}, dir provisional)
  Strike quality  {d['strike_eff']:.2f}
  --- ball launch (impact model) ---
  Ball speed      {lp['ball_speed_mph']:.0f} mph   (smash {lp['smash']:.2f})
  Launch          {lp['launch_deg']:.1f} deg up, {lp['azimuth_deg']:+.1f} deg start
  Spin            {lp['backspin_rpm']:.0f} back / {lp['sidespin_rpm']:+.0f} side
  --- ball flight ---
  Carry           {shot['carry_yd']:.0f} yd
  Total           {shot['total_yd']:.0f} yd
  Apex            {shot['apex_ft']:.0f} ft
  Offline         {shot['offline_yd']:+.0f} yd   ({shape})
  Descent         {shot['descent_deg']:.0f} deg
========================================================
overlay: {args.out}
""")


if __name__ == "__main__":
    main()
