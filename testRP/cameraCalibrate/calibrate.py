import numpy as np
import cv2
import glob

# --- Configuration ---
# Number of inner corners (cols, rows)
chessboard_size = (9, 6) 
# Size of a square in meters (e.g., 0.025m for 25mm)
square_size = 0.020
# ---------------------

# Prepare object points (0,0,0), (1,0,0), ..., (8,5,0)
objp = np.zeros((chessboard_size[0] * chessboard_size[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:chessboard_size[0], 0:chessboard_size[1]].T.reshape(-1, 2)
objp *= square_size

# Arrays to store object points and image points
objpoints = [] # 3d point in real world space
imgpoints = [] # 2d points in image plane

images = glob.glob('calibration_img_*.jpg')

for fname in images:
    img = cv2.imread(fname)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Find the chess board corners
    ret, corners = cv2.findChessboardCorners(gray, chessboard_size, None)
    
    if ret == True:
        objpoints.append(objp)
        imgpoints.append(corners)
        
        # Draw and display the corners
        cv2.drawChessboardCorners(img, chessboard_size, corners, ret)
        cv2.imshow('img', img)
        cv2.waitKey(100)

cv2.destroyAllWindows()

# Calibrate Camera
ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

print("Camera Matrix:\n", mtx)
print("\nDistortion Coefficients:\n", dist)

# Save results
np.savez("calibration_data.npz", mtx=mtx, dist=dist)
print("\nCalibration data saved to calibration_data.npz")
