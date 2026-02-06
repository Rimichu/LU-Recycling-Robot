from flask import Flask, render_template, Response
import cv2
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Try to use Picamera2 for Raspberry Pi Camera Module
try:
	from picamera2 import Picamera2
	USE_PICAMERA = True
	logger.info("Using Picamera2 backend")
except ImportError:
	USE_PICAMERA = False
	logger.info("Picamera2 not available, falling back to OpenCV")

@app.route('/')
def index():
	"""Video streaming home page"""
	return render_template('index.html')

def gen():
	"""Video streaming generator function"""
	if USE_PICAMERA:
		picam2 = Picamera2()
		config = picam2.create_preview_configuration(main={"size": (640, 480), "format": "RGB888"})
		picam2.configure(config)
		picam2.start()
		logger.info("Picamera2 started at 640x480")

		try:
			while True:
				frame = picam2.capture_array()
				ret, jpeg = cv2.imencode('.jpg', frame)
				if not ret:
					logger.warning("Failed to encode frame to JPEG")
					break
				yield (b'--frame\r\n'
				b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
		except Exception as e:
			logger.error(f"Error in video stream: {e}")
		finally:
			picam2.stop()
			logger.info("Picamera2 stopped")
	else:
		vs = cv2.VideoCapture(0, cv2.CAP_V4L2)
		vs.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
		vs.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
		vs.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
		vs.set(cv2.CAP_PROP_BUFFERSIZE, 1)

		if not vs.isOpened():
			logger.error("Failed to open camera device")
			return

		try:
			while True:
				ret, frame = vs.read()
				if not ret:
					logger.warning("Failed to read frame from camera")
					break
				ret, jpeg = cv2.imencode('.jpg', frame)
				if not ret:
					break
				yield (b'--frame\r\n'
				b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
		except Exception as e:
			logger.error(f"Error in video stream: {e}")
		finally:
			vs.release()
			logger.info("Camera released")

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
