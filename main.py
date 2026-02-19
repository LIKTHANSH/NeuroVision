"""
NeuroVision - Home Appliance Controller
Author: LIKTHANSH
Description: Controls home appliances via eye blinks detected using MediaPipe FaceMesh.
             Sends serial commands to Arduino UNO over USB.

Usage:
    python main.py
"""

import cv2
import mediapipe as mp
import numpy as np
import time
import serial
import serial.tools.list_ports


# ─── Serial Port Setup ────────────────────────────────────────────────────────

def connect_to_serial(port_name, baud_rate):
    """Attempts to connect to the given serial port. Returns serial object or None."""
    try:
        ser = serial.Serial(port_name, baud_rate, timeout=1)
        print(f"[OK] Connected to {port_name}")
        return ser
    except serial.SerialException as e:
        print(f"[ERROR] Could not open port '{port_name}': {e}")
        return None


available_ports = serial.tools.list_ports.comports()
if not available_ports:
    print("[ERROR] No serial ports found. Please ensure your Arduino is connected.")
    exit()

print("\nAvailable serial ports:")
port_devices = sorted(list(set([p.device for p in available_ports])))
for i, device in enumerate(port_devices):
    print(f"  [{i+1}] {device}")

chosen_port = None
while chosen_port is None:
    try:
        selection = input("\nSelect port number: ")
        port_index = int(selection) - 1
        if 0 <= port_index < len(port_devices):
            chosen_port = port_devices[port_index]
        else:
            print("Invalid number. Try again.")
    except (ValueError, IndexError):
        print("Please enter a valid number.")

BAUD_RATE = 9600
ser = connect_to_serial(chosen_port, BAUD_RATE)
if ser is None:
    print("\n[ABORTED] Check your COM port and Arduino connection.")
    exit()

time.sleep(2)  # Allow serial connection to stabilize


# ─── Menu Configuration ───────────────────────────────────────────────────────

colors = ["RED", "YELLOW", "BLUE", "WHITE"]
color_values = {
    "RED":    (0, 0, 255),
    "YELLOW": (0, 255, 255),
    "BLUE":   (255, 0, 0),
    "WHITE":  (255, 255, 255),
}

current_color_index = 0
cursor_time = time.time()
last_blink_time = 0
BLINK_COOLDOWN = 1.5   # Seconds between valid blinks
SCROLL_INTERVAL = 0.8  # Seconds per menu item


# ─── MediaPipe Setup ──────────────────────────────────────────────────────────

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True, max_num_faces=1)
cap = cv2.VideoCapture(0)


# ─── Eye Aspect Ratio (EAR) ───────────────────────────────────────────────────

# Landmark indices for left and right eye outlines (MediaPipe refined)
LEFT_EYE_OUTLINE  = [33,  160, 158, 133, 153, 144]
RIGHT_EYE_OUTLINE = [362, 385, 387, 263, 373, 380]


def get_eye_aspect_ratio(landmarks, eye_indices, w, h):
    """Computes EAR for a given eye using 6 landmark points."""
    pts = [(int(landmarks[i].x * w), int(landmarks[i].y * h)) for i in eye_indices]
    A = np.linalg.norm(np.array(pts[1]) - np.array(pts[5]))
    B = np.linalg.norm(np.array(pts[2]) - np.array(pts[4]))
    C = np.linalg.norm(np.array(pts[0]) - np.array(pts[3]))
    return (A + B) / (2.0 * C)


# ─── Main Loop ────────────────────────────────────────────────────────────────

print("\n[RUNNING] NeuroVision started. Blink to toggle appliances. Press ESC to quit.\n")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    h, w, _ = frame.shape
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)

    # Draw scrolling color menu
    menu = np.zeros((200, 600, 3), np.uint8)
    rect_width = 600 // len(colors)
    for i, color in enumerate(colors):
        tl = (i * rect_width, 0)
        br = ((i + 1) * rect_width, 200)
        cv2.rectangle(menu, tl, br, color_values[color], -1)
        cv2.putText(menu, color, (tl[0] + 15, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 2)
        if i == current_color_index:
            cv2.rectangle(menu, tl, br, (0, 0, 0), 5)  # Highlight selected

    # Blink detection
    blink_detected = False
    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            left_ear  = get_eye_aspect_ratio(face_landmarks.landmark, LEFT_EYE_OUTLINE,  w, h)
            right_ear = get_eye_aspect_ratio(face_landmarks.landmark, RIGHT_EYE_OUTLINE, w, h)
            ear = (left_ear + right_ear) / 2.0

            if ear < 0.2:
                if (time.time() - last_blink_time) > BLINK_COOLDOWN:
                    blink_detected = True
                    last_blink_time = time.time()
                    cv2.putText(frame, "BLINK!", (50, 100),
                                cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 4)
            break

    # Scroll menu cursor
    if time.time() - cursor_time > SCROLL_INTERVAL:
        current_color_index = (current_color_index + 1) % len(colors)
        cursor_time = time.time()

    # Send command on blink
    if blink_detected:
        command = colors[current_color_index] + "_TOGGLE"
        print(f"[BLINK] Sending: {command}")
        ser.write((command + "\n").encode("utf-8"))
        time.sleep(0.1)
        if ser.in_waiting:
            reply = ser.readline().decode("utf-8", errors="ignore").strip()
            if reply:
                print(f"[ARDUINO] {reply}")

    cv2.imshow("Color Menu", menu)
    cv2.imshow("NeuroVision - Webcam", frame)

    if cv2.waitKey(1) & 0xFF == 27:  # ESC
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
if ser.is_open:
    ser.close()
    print("[OK] Serial port closed.")
