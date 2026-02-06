from flask import Flask, render_template, Response
import cv2
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def index():
	"""Video streaming home page"""
	return render_template('index.html')

def gen():
	"""Video streaming generator function"""
	# Force V4L2 backend to avoid GStreamer memory issues
	vs = cv2.VideoCapture(0, cv2.CAP_V4L2)
	
	# Set camera parameters
	vs.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
	vs.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
	vs.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
	vs.set(cv2.CAP_PROP_FPS, 30)
	vs.set(cv2.CAP_PROP_BUFFERSIZE, 1)
	
	# Check if camera opened successfully
	if not vs.isOpened():
		logger.error("Failed to open camera device /dev/video0")
		return
	
	logger.info(f"Camera opened: {vs.get(cv2.CAP_PROP_FRAME_WIDTH)}x{vs.get(cv2.CAP_PROP_FRAME_HEIGHT)} @ {vs.get(cv2.CAP_PROP_FPS)} FPS")
	
	frame_count = 0
	try:
		while True:
			ret, frame = vs.read()
			if not ret:
				logger.warning(f"Failed to read frame after {frame_count} successful frames")
				break
			frame_count += 1
			ret, jpeg = cv2.imencode('.jpg', frame)
			if not ret:
				logger.warning("Failed to encode frame to JPEG")
				break
			frame = jpeg.tobytes()
			yield (b'--frame\r\n'
			b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
	except Exception as e:
		logger.error(f"Error in video stream: {e}")
	finally:
		vs.release()
		cv2.destroyAllWindows()
		logger.info(f"Camera released after {frame_count} frames")

@app.route('/video_feed')
def video_feed():
	"""Video streaming route."""
	try:
		return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')
	except Exception as e:
		logger.error(f"Error in video feed route: {e}")
		return "Error: Unable to access camera", 500

if __name__ == '__main__':
	app.run(host='0.0.0.0', port = 5000, debug = True, threaded = True)
