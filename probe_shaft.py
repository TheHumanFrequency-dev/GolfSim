import cv2, numpy as np
img = cv2.imread("frames/m235.png")
print("shape (h,w,c):", img.shape)
h, w = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
H,S,V = hsv[:,:,0], hsv[:,:,1], hsv[:,:,2]
# "white tape" = bright + low saturation
white = ((V > 195) & (S < 70)).astype(np.uint8)*255
# how much bright-white where?
ys, xs = np.where(white>0)
print("white px:", len(xs))
if len(xs):
    print("x range", xs.min(), xs.max(), "y range", ys.min(), ys.max())
# save a side-by-side: original (dimmed) with white mask in red
vis = (img*0.5).astype(np.uint8)
vis[white>0] = (0,0,255)
cv2.imwrite("frames/mask235.png", vis)
print("saved mask235.png")
