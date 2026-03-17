@startuml LU-Recycling-Robot Architecture

skinparam classAttributeIconSize 0
skinparam packageStyle rectangle
skinparam linetype ortho
skinparam shadowing false

title LU Recycling Robot — Class / Component Diagram

' ============================================================
'  MAIN APPLICATION
' ============================================================
package "main.py" as MainPkg {

    class Main <<entry point>> {
        - CALIBRATION_FILE : Path
        - LEFT_KUKA_IP_ADDRESS : str
        --
        + load_camera_calibration(path) : (ndarray, ndarray)
        + connect_to_pi(address, port) : socket
        + disconnect_from_pi(socket) : void
        + connect_to_robot(ip, speed) : KukaRobot
        + disconnect_from_robot(robot) : void
        + initialize_resources() : contextmanager
    }

    class FFmpegCapture {
        - host : str
        - port : int
        - width : int
        - height : int
        - frame_size : int
        - reconnect : bool
        - camera_matrix : ndarray
        - dist_coeffs : ndarray
        - undistort_enabled : bool
        - map1 : ndarray
        - map2 : ndarray
        - proc : Popen
        - latest_frame : ndarray
        - lock : Lock
        - running : bool
        - cmd : list[str]
        --
        + __init__(host, port, width, height, reconnect, camera_matrix, dist_coeffs)
        + _start_proc() : void
        + _reader_loop() : void
        + read() : ndarray
        + release() : void
    }
}

' ============================================================
'  GUI
' ============================================================
package "gui/" as GUIPkg {

    class ControlPanel {
        - root : Tk
        - rp_socket : socket
        - robot : KukaRobot
        - cap : FFmpegCapture
        --
        + __init__(root, rp_socket, robot, cap)
        + start() : void
        + update_frame() : void
        + send_command(cmd) : void
    }
}

' ============================================================
'  KUKA COMMUNICATION
' ============================================================
package "kuka/" as KukaPkg {

    class "constants" as KukaConstants <<module>> {
        + CAM_FRAME_WIDTH : int
        + CAM_FRAME_HEIGHT : int
    }

    class KukaRobot <<external lib>> {
        - ip_address : str
        --
        + connect() : void
        + disconnect() : void
        + set_speed(speed) : void
        + move(coords) : void
    }
}

' ============================================================
'  RASPBERRY PI  (runs on Pi hardware)
' ============================================================
package "rp/" as RPPkg {

    class "pi_constants" as PiConstants <<module>> {
        + PI_SERVER_ADDRESS : str
        + PI_SERVER_PORT : int
        + PI_CAMERA_PORT : int
        + COMMAND_OPEN : str
        + COMMAND_CLOSE : str
        + CLOCKWISE_PIN : int
        + ANTICLOCKWISE_PIN : int
    }

    class "server" as RPServer <<module>> {
        + start_camera_stream() : void
        + handle_client(socket, address, h) : void
        + while_loop(server_socket) : void
    }

    class "servo" as Servo <<module>> {
        + open_claw(h, pin_acw, pin_cw) : void
        + close_claw(h, pin_cw, pin_acw) : void
    }

    class "led" as LED <<module>> {
        + led_pattern_loop(h) : void
    }
}

' ============================================================
'  VISION / CALIBRATION
' ============================================================
package "vision/" as VisionPkg {

    class "calibrate" as Calibrate <<script>> {
        - chessboard_size : tuple
        - square_size : float
        - objp : ndarray
        --
        + find_corners(images) : (objpoints, imgpoints)
        + calibrate_camera() : (mtx, dist)
        + save_calibration(path) : void
    }

    artifact "calibration_data.npz" as CalibNPZ {
        mtx : ndarray [3×3]
        dist : ndarray [1×5]
    }
}

' ============================================================
'  EXTERNAL DEPENDENCIES
' ============================================================
package "External" as ExtPkg <<cloud>> {
    class OpenCV <<library>> {
        + initUndistortRectifyMap()
        + remap()
        + findChessboardCorners()
        + calibrateCamera()
    }

    class FFmpeg <<subprocess>> {
        + decode H.264 → raw BGR
    }

    class Picamera2 <<library>> {
        + H264Encoder
        + FileOutput
    }

    class lgpio <<library>> {
        + gpiochip_open()
        + gpio_write()
    }

    class ultralytics <<library>> {
        + YOLO
    }
}

' ============================================================
'  HARDWARE
' ============================================================
package "Hardware" as HWPkg <<node>> {
    entity "Kuka Robot Arm" as KukaHW
    entity "Raspberry Pi" as PiHW
    entity "Pi Camera" as CamHW
    entity "Servo / Claw" as ServoHW
    entity "Status LED" as LEDHW
}

' ============================================================
'  RELATIONSHIPS
' ============================================================

' -- Main orchestrates everything --
Main --> FFmpegCapture             : creates & owns
Main --> ControlPanel              : creates & passes resources
Main --> KukaRobot                 : connect / disconnect
Main ..> PiConstants               : reads address & ports
Main ..> KukaConstants             : reads frame dimensions
Main --> CalibNPZ                  : loads at startup

' -- FFmpegCapture pipeline --
FFmpegCapture --> FFmpeg           : spawns subprocess
FFmpegCapture --> OpenCV           : remap (undistort)
FFmpegCapture ..> CalibNPZ         : uses mtx & dist

' -- GUI --
ControlPanel --> FFmpegCapture     : read() frames
ControlPanel --> KukaRobot         : move commands
ControlPanel ..> PiConstants       : COMMAND_OPEN / CLOSE
ControlPanel --> Main              : send_command → rp_socket

' -- Raspberry Pi server --
RPServer --> Servo                 : open_claw / close_claw
RPServer --> LED                   : led_pattern_loop
RPServer ..> PiConstants           : all config
RPServer --> Picamera2             : start_camera_stream
Servo --> lgpio                    : GPIO write
LED --> lgpio                      : GPIO write

' -- Calibration --
Calibrate --> OpenCV               : findChessboardCorners,\ncalibrateCamera
Calibrate --> CalibNPZ             : saves

' -- Detection --
Main ..> ultralytics               : YOLO model inference

' -- Network links (TCP) --
Main -[#blue,dashed]-> RPServer    : TCP command socket\n(PI_SERVER_PORT)
FFmpegCapture -[#green,dashed]-> RPServer : TCP H.264 stream\n(PI_CAMERA_PORT)

' -- Hardware links --
RPServer -[#red,dotted]-> PiHW
Picamera2 -[#red,dotted]-> CamHW
Servo -[#red,dotted]-> ServoHW
LED -[#red,dotted]-> LEDHW
KukaRobot -[#red,dotted]-> KukaHW : Ethernet

@enduml