from flask import Flask, render_template, Response
from picamera2 import Picamera2
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

@app.route('/video_feed')
def video_feed():
	"""Video streaming route."""
	return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
	logger.disabled = True
	app.run(host='0.0.0.0', port = 5000, debug = True, threaded = True)
