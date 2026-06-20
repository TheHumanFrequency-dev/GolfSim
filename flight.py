"""Ball flight physics: drag + Magnus lift, integrated with RK4.
Coordinates (metres): x downrange (target), y up, z right.
Spin sign convention: sidespin_rpm > 0 => right curve for a right-handed golfer.
Aero coefficients are calibratable; defaults land standard benchmarks within a
few yards. This is a practice-grade model, not a launch monitor.
"""
import numpy as np

M = 0.04593          # ball mass kg
R = 0.021335         # ball radius m
A = np.pi * R * R    # cross-section m^2
RHO = 1.225          # air density kg/m^3
G = np.array([0.0, -9.81, 0.0])

MPH = 0.44704
RPM = 2 * np.pi / 60.0
YARD = 1.09361


def _coeffs(spin_factor):
    # Tuned to TrackMan tour benchmarks (driver/7i/wedge within ~5%).
    cd = 0.22 + 0.30 * min(spin_factor, 0.5)      # drag rises with spin
    cl = min(0.10 + 0.80 * spin_factor, 0.33)     # lift saturates
    return cd, cl


def _accel(v, omega):
    speed = np.linalg.norm(v)
    if speed < 1e-6:
        return G.copy()
    s = R * np.linalg.norm(omega) / speed
    cd, cl = _coeffs(s)
    drag = -0.5 * RHO * A * cd * speed * v / M
    magnus_dir = np.cross(omega, v)
    n = np.linalg.norm(magnus_dir)
    lift = np.zeros(3) if n < 1e-9 else \
        (0.5 * RHO * A * cl * speed * speed * (magnus_dir / n)) / M
    return G + drag + lift


def simulate(ball_speed_mph, launch_deg, azimuth_deg,
             backspin_rpm, sidespin_rpm=0.0, dt=0.002):
    v0 = ball_speed_mph * MPH
    th, az = np.radians(launch_deg), np.radians(azimuth_deg)
    v = np.array([v0 * np.cos(th) * np.cos(az),
                  v0 * np.sin(th),
                  v0 * np.cos(th) * np.sin(az)])
    travel = v / np.linalg.norm(v)
    up = np.array([0.0, 1.0, 0.0])
    back_axis = np.cross(travel, up)
    back_axis /= np.linalg.norm(back_axis)
    omega = backspin_rpm * RPM * back_axis + sidespin_rpm * RPM * (-up)

    p = np.zeros(3)
    pts = [p.copy()]
    while True:
        k1 = _accel(v, omega)
        k2 = _accel(v + 0.5 * dt * k1, omega)
        k3 = _accel(v + 0.5 * dt * k2, omega)
        k4 = _accel(v + dt * k3, omega)
        v = v + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        p = p + v * dt
        pts.append(p.copy())
        if p[1] < 0 or len(pts) > 20000:
            break

    pts = np.array(pts)
    carry = pts[-1, 0] * YARD
    side = pts[-1, 2] * YARD
    apex = pts[:, 1].max() * YARD * 3  # ft
    descent = np.degrees(np.arctan2(-v[1], np.hypot(v[0], v[2])))
    roll = max(0.0, carry * (0.18 * max(0.0, (45 - descent) / 45)))
    return {
        "carry_yd": round(carry, 1),
        "total_yd": round(carry + roll, 1),
        "apex_ft": round(apex, 1),
        "offline_yd": round(side, 1),
        "descent_deg": round(descent, 1),
        "trajectory": pts,
    }


if __name__ == "__main__":
    print("Driver  :", {k: v for k, v in simulate(167, 13, 0, 2686).items() if k != "trajectory"})
    print("7-iron  :", {k: v for k, v in simulate(120, 16, 0, 6500).items() if k != "trajectory"})
    print("PW      :", {k: v for k, v in simulate(102, 24, 0, 9000).items() if k != "trajectory"})
    print("Slice 7i:", {k: v for k, v in simulate(120, 16, 2, 6500, sidespin_rpm=900).items() if k != "trajectory"})
