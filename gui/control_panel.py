import tkinter as tk
from PIL import Image, ImageTk
import cv2
from events.event import EventLoop
from kuka.constants import CLASSIFY_HEIGHT
from vision.detect import process_frame, is_object_centered
from vision.classify import classify_object, dispose_of_object
from kuka.comms import movehome, queuegrip, queuemove
from kuka.utils import pixels2mm, width2angle
from kuka_comm_lib import KukaRobot
import rp.pi_constants as const


class ControlPanel(tk.Tk):
    """
    GUI Control Panel for the Waste Sorting Robot.
    """
    eloop: EventLoop

    def __init__(self, robot: KukaRobot, rp_socket, title="Waste Sorter"):
        """
        Initialize the Control Panel GUI.

        :param self: Self instance
        :param robot: Robot instance for controlling the KUKA robot
        :param rp_socket: Raspberry Pi socket for communication
        :param title: Window title
        """
        super().__init__()

        self.title("Waste Sorter")      # set title of main window
        self.geometry("1200x800")       # set size of main window
        self.configure(bg="#2596be")
  
        self.create_video_frame()
        self.create_labels()

        self.lock = True                # Init Lock as true to prevent processing before ready

        self.robot = robot
        self.eloop = EventLoop(self.after)

        self.rp_socket = rp_socket

        # Get robot to starting position
        queuemove(self.eloop, self.robot, lambda: movehome(self.robot))
        queuegrip(self.eloop, const.COMMAND_CLOSE, self.rp_socket)
        
        self.eloop.run(self.free_lock)  # Free lock as initial setup done
        self.eloop.start()

    def create_video_frame(self):
        """
        Create the video frame in the GUI.
        
        :param self: Self instance
        """
        self.frame_video = tk.Frame(self, width=600, height=400, bg="#2596be")
        self.frame_video.grid(row=0, column=0, padx=10, pady=10)

        self.label_img = tk.Label(self.frame_video, width=600, height=400, bg="#2596be")
        self.label_img.grid(row=0, column=0, padx=10, pady=10)

    def create_labels(self):
        """
        Create the labels in the GUI.
        
        :param self: Self instance
        """

        # Object Details Labels
        self.object_label = tk.Label(self, text="Object Details", bg="white", fg="black", font=("Arial", 25))
        self.object_label.place(x=750, y=50)

        self.object_detected_label = tk.Label(self, text="Object Detected : False", bg="#f08c64", fg="white", font=("Ubuntu", 20))
        self.object_detected_label.place(x=720, y=150)

        self.object_x_label = tk.Label(self, text="X : ", bg="#f08c64", fg="white", font=("Ubuntu", 18))
        self.object_x_label.place(x=700, y=200)

        self.object_y_label = tk.Label(self, text="Y : ", bg="#f08c64", fg="white", font=("Ubuntu", 18))
        self.object_y_label.place(x=850, y=200)

        self.object_height_label = tk.Label(self, text="Height : ", bg="#f08c64", fg="white", font=("Ubuntu", 18))
        self.object_height_label.place(x=700, y=250)

        self.object_width_label = tk.Label(self, text="Width : ", bg="#f08c64", fg="white", font=("Ubuntu", 18))
        self.object_width_label.place(x=850, y=250)


        # Arm Position Labels
        self.arm_label = tk.Label(self, text="Arm Coordinates ", bg="white", fg="black", font=("Arial", 25))
        self.arm_label.place(x=720, y=350)

        self.x_label = tk.Label(self, text="X: ", bg="#f08c64", fg="white", font=("Ubuntu", 18))
        self.x_label.place(x=720, y=450)

        self.y_label = tk.Label(self, text="Y: ", bg="#f08c64", fg="white", font=("Ubuntu", 18))
        self.y_label.place(x=800, y=450)

        self.z_label = tk.Label(self, text="Z: ", bg="#f08c64", fg="white", font=("Ubuntu", 18))
        self.z_label.place(x=880, y=450)

        self.a_label = tk.Label(self, text="A: ", bg="#f08c64", fg="white", font=("Ubuntu", 18))
        self.a_label.place(x=700, y=550)

        self.b_label = tk.Label(self, text="B: ", bg="#f08c64", fg="white", font=("Ubuntu", 18))
        self.b_label.place(x=800, y=550)

        self.c_label = tk.Label(self, text="C: ", bg="#f08c64", fg="white", font=("Ubuntu", 18))
        self.c_label.place(x=900, y=550)

        self.class_label = tk.Label(self, text="Object Type: ")
        self.class_label.place(x=250, y=500)
        
        self.quit_button = tk.Button(self, text = "Quit Safely", bg = "red", fg = "white", font = ("Arial", 30), command = self.quit)
        self.quit_button.place(x=700, y=600)

    # TODO: Implement safe quit button functionality
    def quit(self):
        pass
        
    def free_lock(self):
        """
        Free the lock to allow processing of new objects.
        
        :param self: Self instance
        """
        self.lock = False

    def obtain_lock(self):
        """
        Obtain the lock to prevent processing of new objects.
        
        :param self: Self instance

        :return: True if lock obtained, False otherwise
        """
        if not self.lock:
            self.lock = True
            print("Lock obtained")
            return True
        return False

    def update_label(self, label, text):
        """
        Update the text of a label.
        
        :param self: Self instance
        :param label: Label to update
        :param text: New text for the label
        """
        label.config(text=text)
    
    def update_pos_labels(self, current_pos):
        """
        Update the position labels with the current robot coordinates.
        
        :param self: Self instance
        :param current_pos: Current position of the robot
        """
        self.update_label(label=self.x_label, text=f"X: {current_pos.x}")
        self.update_label(label=self.y_label, text=f"Y: {current_pos.y}")
        self.update_label(label=self.z_label, text=f"Z: {current_pos.z}")
        self.update_label(label=self.a_label, text=f"A: {current_pos.a}")
        self.update_label(label=self.b_label, text=f"B: {current_pos.b}")
        self.update_label(label=self.c_label, text=f"C: {current_pos.c}")


    def video_stream(self, cap: cv2.VideoCapture, model_d, model_c):
        """
        Video stream processing loop.

        :param self: Self instance
        :param cap: OpenCV VideoCapture object
        :param model_d: Object detection model
        :param model_c: Object classification model
        """
        _, frame = cap.read()

        processed_frame, is_detected, x_pixel, y_pixel, w_pixel, h_pixel = (
            process_frame(frame, model_d)
        )

        self.update_label(self.object_detected_label, "Object Detected : " + str(is_detected))

        # Begin critical section
        if is_detected and not self.lock:

            print("In critical section...")

            self.lock = True

            # Having pixels shown first can be confusing?
            # self.update_label(self.object_x_label, "X : " + str(x_pixel))
            # self.update_label(self.object_y_label, "Y : " + str(y_pixel))
            # self.update_label(self.object_height_label, "Height : " + str(h_pixel))
            # self.update_label(self.object_width_label, "Width : " + str(w_pixel))

            # Repeat until object is centered on screen

            # TODO: Currently reading 1 image only; not in correct position but thinking that it is
            print("Centering object...")
            while not is_object_centered(x_pixel, y_pixel, w_pixel, h_pixel):
                print("Object not centered, adjusting position...")
                _, frame = cap.read()
                processed_frame, is_detected, x_pixel, y_pixel, w_pixel, h_pixel = (
                    process_frame(frame, model_d)
                )

                # x and y are inverted due to camera orientation
                y_mm, x_mm, w_mm, h_mm = pixels2mm(x_pixel, y_pixel, w_pixel, h_pixel)

                self.update_label(self.object_x_label, "X :" + str(x_mm) + "mm")
                self.update_label(self.object_y_label, "Y :" + str(y_mm) + "mm")
                self.update_label(self.object_height_label, "Height :" + str(w_mm) + "mm")
                self.update_label(self.object_width_label, "Width :" + str(h_mm) + "mm")

                queuemove(
                    self.eloop,
                    self.robot,
                    lambda: self.robot.goto(x=x_mm, y=y_mm, z=CLASSIFY_HEIGHT),
                )

                if not is_detected:
                    self.lock = False
                    movehome()
                    return

            # Classify object and dispose of it
            self.eloop.run(lambda: dispose_of_object(self.rp_socket, self.eloop, self.robot, self.free_lock, classify_object(model_c, cap, self.class_label), (x_mm, y_mm)))

        processed_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(processed_frame)

        img_pil_resized = img_pil.resize((600, 400), Image.LANCZOS)

        img_tk = ImageTk.PhotoImage(image=img_pil_resized)

        self.label_img.img_tk = img_tk
        self.label_img.configure(image=img_tk)

        current_pos = self.robot.get_current_position()
        self.update_pos_labels(current_pos)

        self.label_img.after(
            20, self.video_stream, cap, model_d, model_c
        )
