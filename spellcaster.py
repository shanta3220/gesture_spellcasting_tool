import cv2
import mediapipe as mp
import pyautogui
import time
from collections import deque

# Setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, max_num_hands=2)
mp_drawing = mp.solutions.drawing_utils
cap = cv2.VideoCapture(1)

pyautogui.FAILSAFE = False

last_cast_time = {}
cooldown_sec = 2
gesture_hold = {"label": None, "start_time": 0}
HOLD_DURATION = 0.05

right_hand_x_history = deque(maxlen=3)
right_hand_y_history = deque(maxlen=3)
turning_left = turning_right = looking_up = looking_down = False

left_hand_movement = {"w": False, "a": False, "s": False, "d": False}

# --- Helpers ---
def cast_spell(spell_key, name):
    now = time.time()
    if spell_key not in last_cast_time or (now - last_cast_time[spell_key]) > cooldown_sec:
        pyautogui.press(spell_key)
        print(f"✨ Cast {name} (key {spell_key})")
        last_cast_time[spell_key] = now
        return name
    return None

def is_finger_up(lm, tip, pip):
    return lm[tip].y < lm[pip].y - 0.02

def get_finger_states(lm):
    return {
        "thumb": lm[4].x > lm[3].x,
        "index": is_finger_up(lm, 8, 6),
        "middle": is_finger_up(lm, 12, 10),
        "ring": is_finger_up(lm, 16, 14),
        "pinky": is_finger_up(lm, 20, 18)
    }

def is_open_palm(states):
    return states["index"] and states["middle"] and states["ring"] and states["pinky"] and not states["thumb"]

def is_fist(states):
    return not any(states.values())

def is_two_fingers_up(states):
    return states["index"] and states["middle"] and not states["ring"] and not states["pinky"]

def is_index_middle_ring_up(states):
    return states["index"] and states["middle"] and states["ring"] and not states["pinky"]

def is_index_middle_ring_pinky_up(states):
    return states["index"] and states["middle"] and states["ring"] and states["pinky"] and not states["thumb"]

def is_point_forward(states):
    return states["index"] and not any(states[f] for f in ["middle", "ring", "pinky"])

def is_both_hands_fist(results):
    if len(results.multi_hand_landmarks) < 2:
        return False
    lm1 = results.multi_hand_landmarks[0].landmark
    lm2 = results.multi_hand_landmarks[1].landmark
    return is_fist(get_finger_states(lm1)) and is_fist(get_finger_states(lm2))

# --- Main Loop ---
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)
    gesture_label = "None"
    spell_key = None
    now = time.time()

    turning_left = turning_right = looking_up = looking_down = False
    left_hand_movement = {k: False for k in left_hand_movement}

    stop_all = is_both_hands_fist(results) if results.multi_hand_landmarks else False

    if results.multi_hand_landmarks and results.multi_handedness:
        for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
            lm = hand_landmarks.landmark
            hand_label = results.multi_handedness[i].classification[0].label
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            states = get_finger_states(lm)
            hand_x = lm[0].x
            hand_y = lm[0].y

            if hand_label == "Right":
                if is_open_palm(states):
                    right_hand_x_history.append(hand_x)
                    right_hand_y_history.append(hand_y)
                    if len(right_hand_x_history) >= 3:
                        dx = right_hand_x_history[-1] - right_hand_x_history[0]
                        dy = right_hand_y_history[-1] - right_hand_y_history[0]
                        if dx > 0.01:
                            turning_right = True
                        elif dx < -0.01:
                            turning_left = True
                        if dy < -0.01:
                            looking_up = True
                        elif dy > 0.01:
                            looking_down = True

                # Spells
                if is_fist(states):
                    gesture_label = "Time Stop"
                    spell_key = '8'
                elif is_two_fingers_up(states):
                    gesture_label = "Stun"
                    spell_key = '2'
                elif is_index_middle_ring_up(states):
                    gesture_label = "Heal"
                    spell_key = '3'
                elif is_index_middle_ring_pinky_up(states) and not (turning_left or turning_right or looking_up or looking_down):
                    gesture_label = "Barrier"
                    spell_key = '4'
                elif is_point_forward(states):
                    gesture_label = "Laser"
                    spell_key = '1'

                # Right thumb toward camera = "a"
                if lm[4].z < lm[3].z and not any(states[f] for f in ["index", "middle", "ring", "pinky"]):
                    left_hand_movement["a"] = True

            elif hand_label == "Left" and not stop_all:
                if is_fist(states) or (states["pinky"] and not any(states[f] for f in ["thumb", "index", "middle", "ring"])):
                    left_hand_movement = {k: False for k in left_hand_movement}
                elif states["thumb"] and all(states[f] for f in ["index", "middle", "ring", "pinky"]):
                    left_hand_movement["w"] = True
                elif states["index"] and states["middle"] and not any(states[f] for f in ["ring", "pinky", "thumb"]):
                    left_hand_movement["s"] = True
                elif states["thumb"] and not any(states[f] for f in ["index", "middle", "ring", "pinky"]):
                    left_hand_movement["d"] = True

    # Handle camera
    if turning_right:
        pyautogui.keyDown('right'); pyautogui.keyUp('left')
    elif turning_left:
        pyautogui.keyDown('left'); pyautogui.keyUp('right')
    else:
        pyautogui.keyUp('left'); pyautogui.keyUp('right')

    if looking_up:
        pyautogui.keyDown('up'); pyautogui.keyUp('down')
    elif looking_down:
        pyautogui.keyDown('down'); pyautogui.keyUp('up')
    else:
        pyautogui.keyUp('up'); pyautogui.keyUp('down')

    # Handle WASD
    for key, active in left_hand_movement.items():
        if active: pyautogui.keyDown(key)
        else: pyautogui.keyUp(key)

    # Spells (hold logic)
    if gesture_label != "None" and spell_key is not None:
        if gesture_label != gesture_hold["label"]:
            gesture_hold["label"] = gesture_label
            gesture_hold["start_time"] = now
        elif now - gesture_hold["start_time"] >= HOLD_DURATION:
            cast_spell(spell_key, gesture_label)
            gesture_hold["label"] = None
    else:
        gesture_hold["label"] = None

    # Show
    label_ascii = gesture_label.encode('ascii', 'ignore').decode()
    cv2.putText(frame, f"Gesture: {label_ascii}", (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow("Spellcaster", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
