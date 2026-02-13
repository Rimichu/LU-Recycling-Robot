CAM_X_ANG = -20.5
CAM_Y_ANG = 33
CAM_POS = [450, 0] # Position of camera relative to robot current position (assume height is same as robot Z pos) 

# All bin positions (x,y) are the same for now, to be updated later
BIN_DICT = {
    0: [477.13, -404],
    1: [477.13, -404],
    2: [477.13, -404],
    3: [477.13, -404],
    4: [477.13, -404],
    5: [477.13, -404]
}

DETECT_HEIGHT = 1630
CLASSIFY_HEIGHT = 330
OBJECT_HEIGHT = 0

# AKA detect position
# HOME_POS = [558.46, 919.48, DETECT_HEIGHT]
# TOOL_ANGLE = [176.99, -3.00, 176.16]
# HOME_POS = [900.61, 747.95, 839.83]
# TOOL_ANGLE = [-101.08, 4.24, -96.30]
# HOME_POS = [493.10, 596.06, 1223.70]
# TOOL_ANGLE = [177.74, -0.46, 172.27]
# POS: x, y, z (mm)
# Angle: yaw, pitch, roll (degrees)
HOME_POS = [350, 720, DETECT_HEIGHT]
# TOOL_ANGLE = [174, 10, -180]
TOOL_ANGLE = [180, 0, 180] # For testing, to be adjusted later based on camera angle and object position
CONVEYOR_HEIGHT = -100 # In relation to robot home position

OFF_POS = [950, 800, OBJECT_HEIGHT]
OFF_TOOL_ANGLE = [180, 0, 180]
