import cv2
import numpy as np
import os
import time
import subprocess
from gpiozero import LED, Servo
from gpiozero.pins.pigpio import PiGPIOFactory

factory = PiGPIOFactory()

# Initialize Traffic Lights
red_light_lane1 = LED(13)
green_light_lane1 = LED(27)
red_light_lane2 = LED(22)
green_light_lane2 = LED(10)

# Initialize Servo Motor
servo = Servo(18, pin_factory=factory)

# Define paths
darknet_path = "./darknet"  
cfg_file = "cfg/yolov3-tiny.cfg" 
weights_file = "yolov3-tiny.weights"  
input_image = "lane_pic.jpg"  # Path to the input image
output_image = "predictions.jpg"  # Path where the result image will be saved

def run_darknet_detection(darknet_path, cfg_file, weights_file, input_image, output_image):
    # Construct the command
    command = [darknet_path, "detect", cfg_file, weights_file, input_image]
    
    process = subprocess.run(command, capture_output=True, text=True)
    
    if process.returncode != 0:
        print("Error running Darknet command:")
        print(process.stderr)
        return None
    else:
        print("Darknet command output:")
        print(process.stdout)
        print(f"Detection results saved to {output_image}")
        return process.stdout

def parse_detection_output(output):
    # Parse the Darknet output to determine if cars are detected
    if "car" in output:
        print("Car detected in the image.")
        return True
    else:
        print("No car detected in the image.")
        return False


def capture_image(file_name):
    """Capture image using fswebcam."""
    directory = "/darknet/data"

    if not os.path.exists(directory):
        os.makedirs(directory)
    
    file_path = os.path.join(directory, file_name)
    cmd = ['fswebcam', '-r', '640x480', '--jpeg', '85', '--no-banner', file_name]
    subprocess.run(cmd)
    print(f"image saved to file{file_path}")

def control_traffic_light(cycle_time=60):
    while True:
        green_light_lane1.on()
        red_light_lane2.on()
        green_light_lane2.off()
        red_light_lane1.off()
        print("lane1 green on")
        
        start_time = time.time()
        while time.time() - start_time < cycle_time:
            time_left = cycle_time - (time.time() - start_time)
            if time_left <= 30:
                # Rotate servo to Lane 1
                servo.max()
                time.sleep(1)

                capture_image('lane_pic.jpg')
                time.sleep(3)
                
                # Read the captured image
                output = run_darknet_detection(darknet_path, cfg_file, weights_file, input_image, output_image)
                
                if output is None:
                    print("Failed to load image")
                    continue

                # Detect cars
                car_detected = parse_detection_output(output)
                
                if not car_detected:
                    time.sleep(5)
                    green_light_lane1.off()
                    red_light_lane2.off()
                    green_light_lane2.on()
                    red_light_lane1.on()
                    time.sleep(5)
                    start_time = time.time()
                    print("lane2 green on by no detection")
                    break
            time.sleep(1)

        green_light_lane2.on()
        red_light_lane1.on()
        green_light_lane1.off()
        red_light_lane2.off()
        print("lane2 green on")

        start_time = time.time()
        while time.time() - start_time < cycle_time:
            time_left = cycle_time - (time.time() - start_time)
            if time_left <= 30:
                # Rotate servo to Lane 2
                servo.min()
                time.sleep(1)

                capture_image('lane_pic.jpg')
                
                # Read the captured image
                output = run_darknet_detection(darknet_path, cfg_file, weights_file, input_image,output_image)
                
                if output is None:
                    print("Failed to load image")
                    continue

                # Detect cars
                car_detected = parse_detection_output(output)
                
                if not car_detected:
                    time.sleep(5)
                    green_light_lane2.off()
                    red_light_lane1.off()
                    green_light_lane1.on()
                    red_light_lane2.on()
                    time.sleep(5)
                    start_time = time.time()
                    print("lane1 green on by no detection")
                    break
            time.sleep(1)

# Start traffic control
control_traffic_light()
