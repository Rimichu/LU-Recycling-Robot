import cv2
import warnings

def process_frame(frame, model):
    """
    Process a video frame to detect objects using the provided model.
    
    :param frame: Input video frame in BGR format
    :param model: Object detection model

    :return: Tuple containing:
             - is_detected (bool): Whether an object is detected near the center
             - x_pixel (int): X coordinate of detected object
             - y_pixel (int): Y coordinate of detected object
             - w_pixel (int): Width of detected object
             - h_pixel (int): Height of detected object
    """
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Run model

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        results = model(img)

    # Get result as DataFrame
    df = results.pandas().xyxy[0]

    is_detected = False

    if df.empty:
        return is_detected, 0, 0, 0, 0

    # Get the width of the frame
    frame_width = frame.shape[1]
    frame_mid_x = frame_width // 2  # Screen midpoint (x-axis)

    x_pixel = 0
    y_pixel = 0
    h_pixel = 0
    w_pixel = 0

    df["area"] = (df["xmax"] - df["xmin"]) * (df["ymax"] - df["ymin"])

    largest = df.loc[df["area"].idxmax()]

    confidence = largest["confidence"]

    if confidence < 0.1:
        return is_detected, 0, 0, 0, 0

    # Coordinates
    x_min = int(largest["xmin"])
    y_min = int(largest["ymin"])
    x_max = int(largest["xmax"])
    y_max = int(largest["ymax"])

    # Draw rectangle
    cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

    # Calculate the midpoint of the rectangle
    x_mid = (x_min + x_max) // 2
    y_mid = (y_min + y_max) // 2
    h_pixel = y_max - y_min
    w_pixel = x_max - x_min

    # Draw a red dot at the center of the rectangle
    cv2.circle(frame, (x_mid, y_mid), 5, (0, 0, 255), -1)

    # Determine if the detected object is near the center of the frame
    # Threshold ensures accuracy of robot moveing to location
    if abs(x_mid - frame_mid_x) < 500: # 500 is a large threshold, used for testing, and can be adjusted later
        is_detected = True

    return is_detected, x_min, y_min, w_pixel, h_pixel