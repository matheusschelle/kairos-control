"""
KAIROS // CONTROL - Hand Gesture Mouse Control
Controla o mouse do PC atraves de gestos da mao captados pela camera.
Usa a nova API MediaPipe Tasks (HandLandmarker).
"""
import os
import sys

# Desabilita cores ANSI do click/colorama (evita Windows error 6)
os.environ['NO_COLOR'] = '1'
os.environ['ANSI_COLORS_DISABLED'] = '1'
os.environ['TERM'] = 'dumb'

# Suprime o logger do werkzeug
import logging
logging.getLogger('werkzeug').disabled = True
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# Monkey-patch do click pra evitar problemas com console Windows
try:
    import click
    click.echo = lambda *args, **kwargs: print(args[0] if args else '', flush=True)
    click.secho = lambda *args, **kwargs: print(args[0] if args else '', flush=True)
except Exception:
    pass

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import pyautogui
import numpy as np
import base64
import threading
import time
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

SCREEN_W, SCREEN_H = pyautogui.size()

# Caminho do modelo
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'hand_landmarker.task')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'kairos_digital_2026'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Conexoes do esqueleto da mao
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),         # polegar
    (0, 5), (5, 6), (6, 7), (7, 8),         # indicador
    (5, 9), (9, 10), (10, 11), (11, 12),    # medio
    (9, 13), (13, 14), (14, 15), (15, 16),  # anelar
    (13, 17), (17, 18), (18, 19), (19, 20), # mindinho
    (0, 17),                                 # palma
]

state = {
    'running': False,
    'gesture': 'IDLE',
    'fps': 0,
    'last_click': 0,
    'smoothing': 5,
    'clicking_enabled': True,
    'control_enabled': True,
}

position_history = []


def get_finger_states(landmarks):
    """Detecta dedos abertos (1) ou fechados (0).
    landmarks: lista de 21 landmarks com .x .y .z
    """
    tips = [4, 8, 12, 16, 20]
    fingers = []

    # Polegar (eixo X)
    if landmarks[tips[0]].x < landmarks[tips[0] - 1].x:
        fingers.append(1)
    else:
        fingers.append(0)

    # Outros (eixo Y)
    for i in range(1, 5):
        if landmarks[tips[i]].y < landmarks[tips[i] - 2].y:
            fingers.append(1)
        else:
            fingers.append(0)

    return fingers


def detect_gesture(fingers):
    if fingers == [0, 1, 0, 0, 0]:
        return 'MOVE'
    elif fingers == [0, 1, 1, 0, 0]:
        return 'CLICK'
    elif fingers == [1, 1, 0, 0, 0]:
        return 'RIGHT_CLICK'
    elif fingers == [0, 1, 1, 1, 0]:
        return 'SCROLL_UP'
    elif fingers == [0, 1, 1, 1, 1]:
        return 'SCROLL_DOWN'
    elif fingers == [1, 1, 1, 1, 1]:
        return 'PAUSE'
    elif fingers == [0, 0, 0, 0, 0]:
        return 'FIST'
    else:
        return 'IDLE'


def smooth_position(x, y):
    global position_history
    position_history.append((x, y))
    if len(position_history) > state['smoothing']:
        position_history.pop(0)
    avg_x = sum(p[0] for p in position_history) / len(position_history)
    avg_y = sum(p[1] for p in position_history) / len(position_history)
    return int(avg_x), int(avg_y)


def draw_hand(frame, landmarks, w, h):
    """Desenha esqueleto da mao com cores neon KAIROS."""
    # Linhas
    for a, b in HAND_CONNECTIONS:
        x1, y1 = int(landmarks[a].x * w), int(landmarks[a].y * h)
        x2, y2 = int(landmarks[b].x * w), int(landmarks[b].y * h)
        cv2.line(frame, (x1, y1), (x2, y2), (255, 180, 255), 2)

    # Pontos
    for lm in landmarks:
        x, y = int(lm.x * w), int(lm.y * h)
        cv2.circle(frame, (x, y), 4, (220, 50, 255), -1)
        cv2.circle(frame, (x, y), 6, (255, 220, 255), 1)


def draw_hourglass(frame, cx, cy, size, color=(255, 43, 214), thickness=2):
    """Desenha ampulheta KAIROS (estilo logo) no frame."""
    s = size // 2
    pts_top = np.array([
        [cx - s, cy - s],
        [cx + s, cy - s],
        [cx, cy],
    ], np.int32)
    pts_bot = np.array([
        [cx, cy],
        [cx + s, cy + s],
        [cx - s, cy + s],
    ], np.int32)
    cv2.polylines(frame, [pts_top], True, color, thickness, cv2.LINE_AA)
    cv2.polylines(frame, [pts_bot], True, color, thickness, cv2.LINE_AA)
    # Bordas externas
    cv2.line(frame, (cx - s - 4, cy - s), (cx + s + 4, cy - s), color, thickness, cv2.LINE_AA)
    cv2.line(frame, (cx - s - 4, cy + s), (cx + s + 4, cy + s), color, thickness, cv2.LINE_AA)


def draw_kairos_overlay(frame):
    """Adiciona branding KAIROS DIGITAL no frame da camera."""
    h, w, _ = frame.shape

    # Watermark central semi-transparente (ampulheta grande no fundo)
    overlay = frame.copy()
    draw_hourglass(overlay, w // 2, h // 2, 200, color=(255, 100, 230), thickness=1)
    cv2.addWeighted(overlay, 0.08, frame, 0.92, 0, frame)

    # Logo superior esquerdo: ampulheta + texto
    draw_hourglass(frame, 35, 35, 35, color=(255, 43, 214), thickness=2)
    cv2.putText(frame, "KAIROS", (75, 30),
                cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 220, 255), 2, cv2.LINE_AA)
    cv2.putText(frame, "DIGITAL", (75, 50),
                cv2.FONT_HERSHEY_DUPLEX, 0.45, (255, 43, 214), 1, cv2.LINE_AA)

    # Tagline inferior direito
    text = "// TIME IS YOUR ADVANTAGE"
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_DUPLEX, 0.4, 1)
    cv2.putText(frame, text, (w - tw - 12, h - 12),
                cv2.FONT_HERSHEY_DUPLEX, 0.4, (180, 220, 255), 1, cv2.LINE_AA)


def camera_loop():
    if not os.path.exists(MODEL_PATH):
        print(f"[ERRO] Modelo nao encontrado em: {MODEL_PATH}")
        return

    # Configura HandLandmarker
    BaseOptions = mp.tasks.BaseOptions
    HandLandmarker = mp.tasks.vision.HandLandmarker
    HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
    VisionRunningMode = mp.tasks.vision.RunningMode

    options = HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=VisionRunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.6,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print("[ERRO] Camera nao encontrada!")
        return

    print(f"[KAIROS] Camera ativa. Tela alvo: {SCREEN_W}x{SCREEN_H}")
    state['running'] = True

    with HandLandmarker.create_from_options(options) as landmarker:
        prev_time = time.time()
        start_time = time.time()

        while state['running']:
            ret, frame = cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # MediaPipe Image
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

            # Timestamp em ms
            timestamp_ms = int((time.time() - start_time) * 1000)

            result = landmarker.detect_for_video(mp_image, timestamp_ms)

            gesture = 'IDLE'

            if result.hand_landmarks:
                landmarks = result.hand_landmarks[0]

                # Desenha esqueleto
                draw_hand(frame, landmarks, w, h)

                fingers = get_finger_states(landmarks)
                gesture = detect_gesture(fingers)

                # Ponto do indicador
                idx = landmarks[8]
                cam_x, cam_y = int(idx.x * w), int(idx.y * h)

                # Mapeia para a tela
                screen_x = np.interp(cam_x, [80, w - 80], [0, SCREEN_W])
                screen_y = np.interp(cam_y, [80, h - 80], [0, SCREEN_H])
                screen_x, screen_y = smooth_position(screen_x, screen_y)

                now = time.time()
                if state['control_enabled']:
                    if gesture == 'MOVE':
                        pyautogui.moveTo(screen_x, screen_y, duration=0)
                    elif gesture == 'CLICK' and state['clicking_enabled']:
                        if now - state['last_click'] > 0.5:
                            pyautogui.click()
                            state['last_click'] = now
                    elif gesture == 'RIGHT_CLICK' and state['clicking_enabled']:
                        if now - state['last_click'] > 0.7:
                            pyautogui.rightClick()
                            state['last_click'] = now
                    elif gesture == 'SCROLL_UP':
                        pyautogui.scroll(40)
                    elif gesture == 'SCROLL_DOWN':
                        pyautogui.scroll(-40)

                # Indicador visual destacado
                cv2.circle(frame, (cam_x, cam_y), 12, (220, 80, 255), -1)
                cv2.circle(frame, (cam_x, cam_y), 22, (255, 220, 255), 2)

            # FPS
            now = time.time()
            fps = 1 / (now - prev_time) if (now - prev_time) > 0 else 0
            prev_time = now
            state['fps'] = round(fps, 1)
            state['gesture'] = gesture

            # === BRANDING KAIROS no frame ===
            draw_kairos_overlay(frame)

            # Envia frame via WebSocket
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            jpg_b64 = base64.b64encode(buffer).decode('utf-8')

            socketio.emit('frame', {
                'image': jpg_b64,
                'gesture': gesture,
                'fps': state['fps'],
            })

            time.sleep(0.01)

    cap.release()
    print("[KAIROS] Camera encerrada.")


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('connect')
def on_connect():
    print("[KAIROS] Cliente conectado.")
    emit('status', {'msg': 'Conectado ao bridge KAIROS'})


@socketio.on('toggle_clicks')
def on_toggle_clicks(data):
    state['clicking_enabled'] = data.get('enabled', True)


@socketio.on('toggle_control')
def on_toggle_control(data):
    state['control_enabled'] = data.get('enabled', True)


@socketio.on('set_smoothing')
def on_set_smoothing(data):
    state['smoothing'] = int(data.get('value', 5))


if __name__ == '__main__':
    print("""
    =========================================
       KAIROS // CONTROL - bridge ativo
    =========================================
       Dashboard:  http://localhost:8000
       Tela alvo:  {} x {}
    =========================================
    """.format(SCREEN_W, SCREEN_H))

    cam_thread = threading.Thread(target=camera_loop, daemon=True)
    cam_thread.start()

    try:
        socketio.run(app, host='0.0.0.0', port=8000, debug=False,
                     allow_unsafe_werkzeug=True, log_output=False, use_reloader=False)
    except OSError as e:
        print(f"[ERRO] Nao foi possivel iniciar servidor: {e}")
        input("Pressione Enter para sair...")
