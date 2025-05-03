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

# Gesture hold tracking
gesture_hold = {"label": None, "start_time": 0}
HOLD_DURATION = 0.1  # seconds

# Camera tracking
hand_x_history = deque(maxlen=5)
hand_y_history = deque(maxlen=5)
turning_left = False
turning_right = False
looking_up = False
looking_down = False

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

def is_both_hands_open(results):
    if len(results.multi_hand_landmarks) < 2:
        return False
    lm1 = results.multi_hand_landmarks[0].landmark
    lm2 = results.multi_hand_landmarks[1].landmark
    return is_open_palm(get_finger_states(lm1)) and is_open_palm(get_finger_states(lm2))

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

    if results.multi_hand_landmarks:
        handedness = results.multi_handedness

        if is_both_hands_open(results):
            gesture_label = "Time Stop"
            spell_key = '8'
        else:
            for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
                lm = hand_landmarks.landmark
                hand_label = handedness[i].classification[0].label
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                states = get_finger_states(lm)
                hand_x = lm[0].x
                hand_y = lm[0].y

                if is_open_palm(states):
                    hand_x_history.append(hand_x)
                    hand_y_history.append(hand_y)
                    if len(hand_x_history) >= 3:
                        delta_x = hand_x_history[-1] - hand_x_history[0]
                        delta_y = hand_y_history[-1] - hand_y_history[0]
                        if delta_x > 0.02:
                            turning_right = True
                        elif delta_x < -0.02:
                            turning_left = True
                        if delta_y < -0.02:
                            looking_up = True
                        elif delta_y > 0.02:
                            looking_down = True
                else:
                    hand_x_history.clear()
                    hand_y_history.clear()

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

                if gesture_label != "None":
                    break

    # Handle camera turning with mouse movement instead of keys
    if turning_right:
        pyautogui.keyDown('right')
        pyautogui.keyUp('left')
    elif turning_left:
        pyautogui.keyDown('left')
        pyautogui.keyUp('right')
    else:
        pyautogui.keyUp('left')
        pyautogui.keyUp('right')

    # Handle camera looking up and down
    if looking_up:
        pyautogui.keyDown('up')
        pyautogui.keyUp('down')
    elif looking_down:
        pyautogui.keyDown('down')
        pyautogui.keyUp('up')
    else:
        pyautogui.keyUp('up')
        pyautogui.keyUp('down')

    # Hold gesture to confirm before casting
    if gesture_label != "None" and spell_key is not None:
        if gesture_label != gesture_hold["label"]:
            gesture_hold["label"] = gesture_label
            gesture_hold["start_time"] = now
        elif now - gesture_hold["start_time"] >= HOLD_DURATION:
            cast_spell(spell_key, gesture_label)
            gesture_hold["label"] = None
    else:
        gesture_hold["label"] = None

    # Display
    label_ascii = gesture_label.encode('ascii', 'ignore').decode()
    cv2.putText(frame, f"Gesture: {label_ascii}", (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow("Spellcaster", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
