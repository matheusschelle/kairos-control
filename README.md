# KAIROS // CONTROL

> **TIME IS YOUR ADVANTAGE**
> Hand gesture mouse control system by **KAIROS DIGITAL**.

Controle o mouse e teclado do seu PC apenas com gestos da mão, captados pela câmera. Sem hardware extra. Sem clique. Só o movimento natural da sua mão.

---

## Versões

| Versão | Onde roda | O que faz |
|--------|-----------|-----------|
| **Desktop** (Python) | No seu PC com Windows | Controla o mouse real do sistema operacional |
| **Web Demo** ([live](https://kairos-control.vercel.app)) | No navegador | Detecta gestos em tempo real (demo visual) |

---

## Desktop (versão completa)

### Requisitos
- Windows 10/11
- Python 3.10+ (testado com 3.14)
- Câmera

### Instalação
```bash
# 1. Clone
git clone https://github.com/matheus-schelle/kairos-control.git
cd kairos-control

# 2. Instale (Windows)
install.bat

# 3. Rode
start.bat
```

O dashboard abre em `http://localhost:8000`.

---

## Gestos

| Gesto | Ação |
|-------|------|
| ☝️ Indicador | Move o cursor |
| ✌️ Indicador + médio | Click esquerdo |
| 🤘 Polegar + indicador | Click direito |
| 3 dedos para cima | Scroll cima |
| 4 dedos | Scroll baixo |
| ✋ Mão aberta | Pausa |

---

## Stack

**Desktop**
- Python + OpenCV + MediaPipe Tasks
- Flask + Socket.IO
- PyAutoGUI

**Web Demo**
- MediaPipe Hands (JS)
- WebRTC (getUserMedia)
- Vanilla JS

---

## Sobre

**KAIROS DIGITAL** — Soluções com IA para acessibilidade e controle natural de interfaces.

> *Kairos* (καιρός): o momento certo, oportuno. O tempo da ação.
