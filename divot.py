"""Divot reader with origin calibration.
Finds the white/silver flipped-sequin strike on the green mat, locates the mat
play area to set a coordinate frame, and reports strike quality:
  - lateral offset (toe/heel side)
  - longitudinal offset (ahead=thin tendency / behind=fat tendency); target = top
  - divot axis (club-path proxy, 180-deg ambiguous until video resolves it)
  - strike_eff (clean->1.0, off-centre lowers ball speed downstream)
Single-image colour mode (proven on the real mat). Pixel + mat-relative units.
"""
import cv2
import numpy as np


def _largest(mask, min_area):
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = [c for c in cnts if cv2.contourArea(c) >= min_area]
    return max(cnts, key=cv2.contourArea) if cnts else None


def read_divot(path, width=1200, sat_max=70, val_min=140, min_area=2000):
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(path)
    h, w = img.shape[:2]
    img = cv2.resize(img, (width, int(h * width / w)))
    H, W = img.shape[:2]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    S, V, Hue = hsv[:, :, 1], hsv[:, :, 2], hsv[:, :, 0]

    # --- play area: saturated green sequins -> bounding box -> origin (ball pos)
    green = (((Hue > 30) & (Hue < 90) & (S > 90) &
              (V > 50) & (V < 195)).astype(np.uint8) * 255)   # exclude bright felt
    green = cv2.morphologyEx(green, cv2.MORPH_CLOSE,
                             cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41)))
    gc = _largest(green, 20000)
    bx, by, bw, bh = cv2.boundingRect(gc) if gc is not None else (0, 0, W, H)
    ox, oy = bx + bw / 2, by + bh / 2          # origin = play-area centre

    # --- divot: desaturated + bright flipped sequins
    wm = ((S < sat_max) & (V > val_min)).astype(np.uint8) * 255
    wm = cv2.morphologyEx(wm, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
    wm = cv2.morphologyEx(wm, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
    c = _largest(wm, min_area)
    if c is None:
        raise ValueError("no divot found - tune sat_max/val_min/min_area")

    M = cv2.moments(c)
    cx, cy = M["m10"] / M["m00"], M["m01"] / M["m00"]
    (ex, ey), (aw, ah), ang = cv2.fitEllipse(c)
    length, widthpx = max(aw, ah), min(aw, ah)

    # mat-relative offsets in -1..1 (target = up = -y)
    off_x = (cx - ox) / (bw / 2)
    off_y = (oy - cy) / (bh / 2)               # +y => ahead of ball (toward target)
    mag = float(np.hypot(off_x, off_y))

    lateral = "centre" if abs(off_x) < 0.12 else ("toe-side" if off_x > 0 else "heel-side")
    longi = "centred" if abs(off_y) < 0.12 else ("ahead (thin tendency)" if off_y > 0
                                                 else "behind (fat tendency)")
    strike_eff = round(max(0.80, 1.0 - 0.18 * mag), 3)

    over = img.copy()
    cv2.rectangle(over, (bx, by), (bx + bw, by + bh), (0, 200, 0), 2)
    cv2.drawMarker(over, (int(ox), int(oy)), (0, 200, 0), cv2.MARKER_CROSS, 26, 2)
    cv2.drawContours(over, [c], -1, (0, 0, 255), 3)
    cv2.circle(over, (int(cx), int(cy)), 9, (255, 0, 0), -1)
    th = np.deg2rad(ang - 90)
    dx, dy, L = np.cos(th), np.sin(th), length / 2
    cv2.arrowedLine(over, (int(ex - dx * L), int(ey - dy * L)),
                    (int(ex + dx * L), int(ey + dy * L)), (0, 140, 255), 4, tipLength=0.12)

    return {
        "strike_px": [int(cx), int(cy)],
        "origin_px": [int(ox), int(oy)],
        "play_box": [bx, by, bw, bh],
        "offset_norm": [round(off_x, 3), round(off_y, 3)],
        "lateral": lateral,
        "low_point": longi,
        "path_axis_deg": round(float(ang), 1),
        "divot_len_px": round(float(length), 1),
        "divot_wid_px": round(float(widthpx), 1),
        "strike_eff": strike_eff,
        "overlay": over,
    }


if __name__ == "__main__":
    import sys, json
    r = read_divot(sys.argv[1] if len(sys.argv) > 1
                   else "/mnt/user-data/uploads/IMG_6462.jpeg")
    cv2.imwrite("divot_calibrated.png", r.pop("overlay"))
    print(json.dumps(r, indent=2))
