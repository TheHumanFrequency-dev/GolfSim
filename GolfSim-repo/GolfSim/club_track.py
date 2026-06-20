import cv2, numpy as np, glob, os

FRAMES = sorted(glob.glob("frames/ds/f*.png"))
FPS = 240.0  # 240fps slo-mo content (confirm phone's slo-mo rate)

def club_end(img):
    """Return (head_xy, hands_xy, white_px) by isolating the white shaft tape in the lower ROI."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    S, V = hsv[:,:,1], hsv[:,:,2]
    white = ((V > 195) & (S < 70)).astype(np.uint8)
    roi = np.zeros_like(white)
    roi[780:1770, 120:985] = 1          # lower swing zone, away from bright wall
    m = (white & roi).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7,7), np.uint8))
    n, lbl, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    if n < 2:
        return None
    # largest component in ROI = the shaft tape
    i = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    area = stats[i, cv2.CC_STAT_AREA]
    if area < 60:
        return None
    pts = np.column_stack(np.where(lbl == i))      # (y,x)
    ys, xs = pts[:,0], pts[:,1]
    # endpoints along principal axis
    vx, vy, x0, y0 = cv2.fitLine(np.column_stack([xs, ys]).astype(np.float32),
                                 cv2.DIST_L2, 0, 0.01, 0.01).ravel()
    t = (xs - x0)*vx + (ys - y0)*vy
    lo, hi = np.argmin(t), np.argmax(t)
    p1 = np.array([xs[lo], ys[lo]]); p2 = np.array([xs[hi], ys[hi]])
    head = p1 if p1[1] > p2[1] else p2      # head = lower endpoint (max y)
    hands = p2 if p1[1] > p2[1] else p1
    return head.astype(float), hands.astype(float), int(area)

traj = []   # (frame_idx, hx, hy, area)
for f in FRAMES:
    idx = int(os.path.basename(f)[1:5])
    img = cv2.imread(f)
    r = club_end(img)
    if r:
        head, hands, area = r
        traj.append((idx, head[0], head[1], area))

traj = np.array(traj)
print(f"tracked {len(traj)}/{len(FRAMES)} frames")
# impact = lowest head point (max y)
imp_row = int(np.argmax(traj[:,2]))
imp_idx = int(traj[imp_row,0])
print(f"impact (lowest head) at frame {imp_idx}, head=({traj[imp_row,1]:.0f},{traj[imp_row,2]:.0f})")

# speed: head displacement per frame around impact
def disp(a,b): return float(np.hypot(a[1]-b[1], a[2]-b[2]))
win = traj[max(0,imp_row-3):imp_row+1]
steps = [disp(win[k+1], win[k]) for k in range(len(win)-1)]
v_px = np.mean(steps) if steps else 0
print(f"px/frame near impact: {[f'{s:.1f}' for s in steps]}  mean={v_px:.1f}")
print(f"=> {v_px*FPS:.0f} px/s  (x scale mm/px -> real speed)")

# attack angle: tangent of head path through impact (central diff), image y is DOWN
a = traj[max(0,imp_row-2)]; b = traj[min(len(traj)-1,imp_row+2)]
dx, dy = b[1]-a[1], b[2]-a[2]
attack = -np.degrees(np.arctan2(dy, abs(dx)))   # +ve = ascending
print(f"path tangent dx={dx:.0f} dy={dy:.0f} -> attack ~ {attack:+.1f} deg (+ascending / - descending)")
print(f"horizontal travel at impact: {'left/toward pooltable' if dx<0 else 'right'} ({abs(dx):.0f}px over 4 frames)")

np.save("frames/traj.npy", traj)
# overlay trajectory on impact frame
base = cv2.imread([f for f in FRAMES if f.endswith(f"f{imp_idx:04d}.png")][0])
for k in range(len(traj)-1):
    p = (int(traj[k,1]), int(traj[k,2])); q = (int(traj[k+1,1]), int(traj[k+1,2]))
    cv2.line(base, p, q, (0,255,255), 2)
    cv2.circle(base, p, 3, (0,140,255), -1)
ih = (int(traj[imp_row,1]), int(traj[imp_row,2]))
cv2.circle(base, ih, 10, (0,0,255), 2)
cv2.imwrite("frames/track_overlay.png", base)
print("saved track_overlay.png")
