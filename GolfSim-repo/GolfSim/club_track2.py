import cv2, numpy as np, glob, os
FRAMES = sorted(glob.glob("frames/ds/f*.png"))
def idx_of(f): return int(os.path.basename(f)[1:5])

def head_motion(prev, cur):
    """club head = lower end of MOVING bright tape (motion-gated, kills static clutter)."""
    g0 = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY); g1 = cv2.cvtColor(cur, cv2.COLOR_BGR2GRAY)
    motion = cv2.absdiff(g1, g0) > 22
    hsv = cv2.cvtColor(cur, cv2.COLOR_BGR2HSV); S,V = hsv[:,:,1], hsv[:,:,2]
    white = (V > 180) & (S < 85)
    roi = np.zeros(white.shape, np.uint8); roi[770:1780, 110:990] = 1
    cand = (motion & white & roi.astype(bool)).astype(np.uint8)
    cand = cv2.morphologyEx(cand, cv2.MORPH_CLOSE, np.ones((9,9), np.uint8))
    ys, xs = np.where(cand > 0)
    if len(xs) < 25: return None
    # head = lowest cluster: take the 15% lowest points, use their median
    cut = np.percentile(ys, 85)
    sel = ys >= cut
    hx, hy = np.median(xs[sel]), np.median(ys[sel])
    return float(hx), float(hy), int(len(xs))

traj = []
for i in range(1, len(FRAMES)):
    prev = cv2.imread(FRAMES[i-1]); cur = cv2.imread(FRAMES[i])
    r = head_motion(prev, cur)
    if r: traj.append((idx_of(FRAMES[i]), r[0], r[1], r[2]))
traj = np.array(traj)
print(f"tracked {len(traj)}/{len(FRAMES)-1}")
# print the arc (frame, y) compactly to see the downswing descend->lowpoint->ascend
arc = " ".join(f"{int(t[0])}:{int(t[2])}" for t in traj[::2])
print("frame:head_y ->", arc)
imp = int(np.argmax(traj[:,2]))
print(f"\nlowest-head (impact) frame {int(traj[imp,0])} at ({traj[imp,1]:.0f},{traj[imp,2]:.0f})")
def d(a,b): return float(np.hypot(a[1]-b[1], a[2]-b[2]))
sw = traj[max(0,imp-3):imp+1]
steps=[d(sw[k+1],sw[k]) for k in range(len(sw)-1)]
print("px/frame into impact:", [f"{s:.1f}" for s in steps])
np.save("frames/traj2.npy", traj)
# overlay on impact frame
base = cv2.imread([f for f in FRAMES if f.endswith(f"f{int(traj[imp,0]):04d}.png")][0])
for k in range(len(traj)-1):
    cv2.line(base,(int(traj[k,1]),int(traj[k,2])),(int(traj[k+1,1]),int(traj[k+1,2])),(0,255,255),2)
    cv2.circle(base,(int(traj[k,1]),int(traj[k,2])),3,(0,140,255),-1)
cv2.circle(base,(int(traj[imp,1]),int(traj[imp,2])),11,(0,0,255),2)
cv2.imwrite("frames/track2.png", base); print("saved track2.png")
