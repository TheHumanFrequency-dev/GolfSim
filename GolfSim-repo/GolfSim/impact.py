"""Impact model: club delivery + strike -> ball launch conditions (LaunchParams).
Replaces a ball-tracking launch monitor with physics relationships (the ball
flight laws), driven by club data (speed, face, path, attack) and the divot read
(path, strike quality, heel/toe). Constants are calibratable; this is the part
you'll later refine with your own logged shots.

Signs (right-handed golfer): face_deg/path_deg > 0 = aimed right of target.
sidespin_rpm > 0 = right curve (fade/slice).
"""

# loft = effective dynamic loft at impact (deg, already accounts for typical shaft
# lean, so it's lower than static loft for irons), smash = centre-strike smash,
# aoa = default attack angle deg
CLUBS = {
    "driver": {"loft": 13.0, "smash": 1.49, "aoa": 3.0},
    "3wood":  {"loft": 16.0, "smash": 1.46, "aoa": -1.0},
    "5iron":  {"loft": 18.0, "smash": 1.40, "aoa": -3.0},
    "7iron":  {"loft": 22.0, "smash": 1.34, "aoa": -4.0},
    "9iron":  {"loft": 30.0, "smash": 1.28, "aoa": -5.0},
    "pw":     {"loft": 39.0, "smash": 1.24, "aoa": -5.0},
}


def compute_launch(club_speed_mph, club="7iron", face_deg=0.0, path_deg=0.0,
                   attack_deg=None, shaft_lean_deg=0.0,
                   strike_eff=1.0, heel_toe_mm=0.0):
    c = CLUBS[club]
    aoa = c["aoa"] if attack_deg is None else attack_deg
    dyn_loft = c["loft"] - shaft_lean_deg          # forward lean de-lofts
    spin_loft = max(dyn_loft - aoa, 0.0)

    ball_speed = club_speed_mph * c["smash"] * strike_eff
    launch = dyn_loft * 0.78 + aoa * 0.30          # launches between AoA and loft
    backspin = 2.6 * spin_loft * club_speed_mph    # rises with loft + speed
    azimuth = 0.85 * face_deg + 0.15 * path_deg    # starts mostly on the face

    # curve: face-to-path tilts the spin axis; heel/toe adds gear effect
    sidespin = 4.0 * (face_deg - path_deg) * (club_speed_mph / 100.0)
    sidespin += 6.0 * heel_toe_mm                  # +toe (>0) -> hook, see sign below

    return {
        "club": club,
        "club_speed_mph": round(club_speed_mph, 1),
        "ball_speed_mph": round(ball_speed, 1),
        "smash": round(ball_speed / club_speed_mph, 2),
        "launch_deg": round(launch, 1),
        "azimuth_deg": round(azimuth, 1),
        "backspin_rpm": round(backspin),
        "sidespin_rpm": round(sidespin),
        "spin_loft_deg": round(spin_loft, 1),
    }


if __name__ == "__main__":
    import flight
    for club, cs in [("driver", 113), ("7iron", 84), ("pw", 86)]:
        lp = compute_launch(cs, club)
        shot = flight.simulate(lp["ball_speed_mph"], lp["launch_deg"],
                               lp["azimuth_deg"], lp["backspin_rpm"], lp["sidespin_rpm"])
        print(f"{club:7s} cs={cs}  ->  ball {lp['ball_speed_mph']} / launch {lp['launch_deg']} / "
              f"spin {lp['backspin_rpm']}  =>  carry {shot['carry_yd']}yd  apex {shot['apex_ft']}ft")
