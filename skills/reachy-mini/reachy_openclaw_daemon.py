#!/usr/bin/env python3
"""
Reachy Mini OpenClaw Daemon - plná integrace s OpenClaw
Bez nutnosti desktop app - přímé USB serial ovládání
"""

import sys
import json
import time
import asyncio
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Přidáme reachy-mini libs
sys.path.insert(0, str(Path.home() / ".venvs/reachy-mini/lib/python3.13/site-packages"))

try:
    from reachy_mini_motor_controller import ReachyMiniMotorController
    HAVE_CONTROLLER = True
except ImportError:
    HAVE_CONTROLLER = False


# ============ Modely ============
class HeadPose(BaseModel):
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0


class GotoRequest(BaseModel):
    head_pose: HeadPose = HeadPose()
    body_yaw: float = 0.0
    antennas: List[float] = [0.0, 0.0]
    duration: float = 1.0
    interpolation: str = "minjerk"


class TTSRequest(BaseModel):
    text: str
    voice: str = "Zuzana"  # macOS voice
    volume: int = 80
    animate: bool = True  # Pohyb hlavy při mluvení


class SimpleMove(BaseModel):
    body_yaw: Optional[float] = None
    head_pitch: Optional[float] = None
    head_yaw: Optional[float] = None
    left_antenna: Optional[float] = None
    right_antenna: Optional[float] = None
    duration: float = 1.0


# ============ Globals ============
daemon_state = {
    "controller": None,
    "running": False,
    "motor_states": {},
    "last_update": 0,
}

MOTOR_IDS = {
    "body": 10,
    "stewart_1": 11, "stewart_2": 12, "stewart_3": 13,
    "stewart_4": 14, "stewart_5": 15, "stewart_6": 16,
    "right_antenna": 17, "left_antenna": 18,
}


# ============ Motor Control ============
def find_reachy_port():
    """Najde Reachy USB serial port"""
    import serial.tools.list_ports
    ports = list(serial.tools.list_ports.comports())
    
    for p in ports:
        # Reachy Mini Lite detekce
        if any(x in p.device.lower() for x in ["usbmodem", "ttyusb", "cu.usb"]):
            if "serial" in p.description.lower() or p.vid == 0x1a86:
                return p.device
    
    # Fallback
    return "/dev/cu.usbmodem5B420750561"


def init_controller():
    """Inicializuje motor controller"""
    if not HAVE_CONTROLLER:
        print("⚠️ Motor controller not available")
        return None
    
    port = find_reachy_port()
    print(f"🔌 Trying {port}...")
    
    try:
        ctrl = ReachyMiniMotorController(port, 1000000)
        if ctrl.connect():
            print(f"✓ Motors connected!")
            return ctrl
    except Exception as e:
        print(f"✗ Connection failed: {e}")
    
    return None


def set_motor_position(motor_id: int, position: float):
    """Nastaví pozici motoru"""
    ctrl = daemon_state.get("controller")
    if not ctrl:
        return False
    try:
        ctrl.set_goal_position(motor_id, position)
        return True
    except Exception as e:
        print(f"Motor {motor_id} error: {e}")
        return False


def get_motor_states():
    """Přečte stav všech motorů"""
    ctrl = daemon_state.get("controller")
    if not ctrl:
        return {}
    
    states = {}
    for name, mid in MOTOR_IDS.items():
        try:
            pos = ctrl.get_position(mid)
            states[mid] = {"name": name, "position": pos}
        except:
            states[mid] = {"name": name, "position": None, "error": "read_failed"}
    return states


# ============ TTS System ============
def speak_with_robot(text: str, voice: str = "Zuzana", volume: int = 80, animate: bool = True):
    """
    Generuje TTS a přehraje ho přes Reachy s pohyby
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        aiff = f"{tmpdir}/speech.aiff"
        wav = f"{tmpdir}/speech.wav"
        
        # 1. Generace TTS
        result = subprocess.run(
            ["say", "-v", voice, text, "-o", aiff],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return {"error": "TTS generation failed"}
        
        # 2. Konverze na WAV
        subprocess.run(
            ["afconvert", aiff, wav, "-f", "WAVE", "-d", "LEI16@44100"],
            capture_output=True
        )
        
        # 3. Upload na Reachy (pokud běží původní daemon)
        import requests
        try:
            # Zkusíme původní daemon na portu 8000
            with open(wav, "rb") as f:
                upload = requests.post(
                    "http://localhost:8000/api/media/sounds/upload",
                    files={"file": f},
                    timeout=5
                )
            
            if upload.status_code == 200:
                # Přehrání
                play = requests.post(
                    "http://localhost:8000/api/media/play_sound",
                    json={"file": "speech.wav", "volume": volume},
                    timeout=5
                )
                
                if animate and daemon_state.get("controller"):
                    # Během mluvení - jemné pohyby
                    speak_animation(text)
                
                return {"status": "ok", "source": "original_daemon"}
                
        except Exception as e:
            print(f"Original daemon unavailable: {e}")
        
        # Fallback - lokální přehrání
        subprocess.run(["afplay", "-v", str(volume/100), wav])
        
        return {"status": "ok", "source": "local_fallback"}


def speak_animation(text: str):
    """Animace hlavy při mluvení"""
    ctrl = daemon_state.get("controller")
    if not ctrl:
        return
    
    # Odhad délky textu (rychlejší než přesný výpočet)
    duration = len(text) * 0.08  # ~80ms na znak
    
    # Pohyb do mluvení pozice
    set_motor_position(MOTOR_IDS["stewart_1"], -0.15)
    set_motor_position(MOTOR_IDS["stewart_4"], -0.15)
    set_motor_position(MOTOR_IDS["body"], 0.05)
    set_motor_position(MOTOR_IDS["left_antenna"], 0.3)
    set_motor_position(MOTOR_IDS["right_antenna"], -0.3)
    
    # Čekáme na konec mluvení...
    time.sleep(min(duration, 10))
    
    # Návrat
    set_motor_position(MOTOR_IDS["stewart_1"], 0)
    set_motor_position(MOTOR_IDS["stewart_4"], 0)
    set_motor_position(MOTOR_IDS["body"], 0)
    set_motor_position(MOTOR_IDS["left_antenna"], 0)
    set_motor_position(MOTOR_IDS["right_antenna"], 0)


# ============ FastAPI App ============
app = FastAPI(
    title="Reachy Mini OpenClaw Daemon",
    description="Lightweight daemon pro OpenClaw integraci",
    version="0.2.0"
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"])


@app.on_event("startup")
async def startup():
    """Startup inicializace"""
    print("🦾 Reachy Mini OpenClaw Daemon starting...")
    daemon_state["controller"] = init_controller()
    daemon_state["running"] = True
    print(f"✓ Running at http://localhost:8765")
    print(f"  Robot connected: {daemon_state['controller'] is not None}")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup"""
    daemon_state["running"] = False
    ctrl = daemon_state.get("controller")
    if ctrl:
        try:
            ctrl.disconnect()
        except:
            pass


@app.get("/api/health")
def health():
    """Health check"""
    return {
        "status": "ok",
        "has_robot": daemon_state["controller"] is not None,
        "mock_mode": not HAVE_CONTROLLER,
    }


@app.get("/api/state")
def get_state():
    """Robot state"""
    motors = get_motor_states() if daemon_state["controller"] else {}
    
    return {
        "control_mode": "enabled" if daemon_state["controller"] else "disabled",
        "head_pose": {"x": 0, "y": 0, "z": 0, "roll": 0, "pitch": 0, "yaw": 0},
        "body_yaw": motors.get(10, {}).get("position", 0),
        "antennas": [
            motors.get(18, {}).get("position", 0),
            motors.get(17, {}).get("position", 0)
        ],
        "timestamp": time.time(),
        "motors": motors
    }


@app.post("/api/move/simple")
def simple_move(req: SimpleMove):
    """Jednoduchý pohyb"""
    results = {}
    
    if req.body_yaw is not None:
        results["body"] = set_motor_position(MOTOR_IDS["body"], req.body_yaw)
    
    # Head pitch (zjednodušené - stewart_1 a stewart_4)
    if req.head_pitch is not None:
        pitch = req.head_pitch
        results["head_pitch_1"] = set_motor_position(MOTOR_IDS["stewart_1"], pitch * 0.5)
        results["head_pitch_4"] = set_motor_position(MOTOR_IDS["stewart_4"], pitch * 0.5)
    
    if req.left_antenna is not None:
        results["left_antenna"] = set_motor_position(MOTOR_IDS["left_antenna"], req.left_antenna)
    
    if req.right_antenna is not None:
        results["right_antenna"] = set_motor_position(MOTOR_IDS["right_antenna"], req.right_antenna)
    
    return {"status": "ok", "results": results}


@app.post("/api/speak")
def speak(req: TTSRequest):
    """TTS s animací"""
    result = speak_with_robot(
        req.text,
        voice=req.voice,
        volume=req.volume,
        animate=req.animate
    )
    return result


@app.post("/api/gesture/{gesture}")
def play_gesture(gesture: str):
    """Přednastavené gesto"""
    ctrl = daemon_state.get("controller")
    if not ctrl:
        return {"error": "No robot connected"}
    
    if gesture == "wave":
        # Mávání anténkama
        for i in range(3):
            set_motor_position(MOTOR_IDS["left_antenna"], 0.8)
            set_motor_position(MOTOR_IDS["right_antenna"], -0.8)
            time.sleep(0.3)
            set_motor_position(MOTOR_IDS["left_antenna"], 0)
            set_motor_position(MOTOR_IDS["right_antenna"], 0)
            time.sleep(0.3)
        return {"status": "ok", "gesture": "wave"}
    
    elif gesture == "nod":
        # Přikyvování
        for i in range(2):
            set_motor_position(MOTOR_IDS["stewart_1"], -0.2)
            set_motor_position(MOTOR_IDS["stewart_4"], -0.2)
            time.sleep(0.5)
            set_motor_position(MOTOR_IDS["stewart_1"], 0.2)
            set_motor_position(MOTOR_IDS["stewart_4"], 0.2)
            time.sleep(0.5)
        return {"status": "ok", "gesture": "nod"}
    
    elif gesture == "shake":
        # Zakroutení hlavou
        set_motor_position(MOTOR_IDS["body"], 0.3)
        time.sleep(0.3)
        set_motor_position(MOTOR_IDS["body"], -0.3)
        time.sleep(0.3)
        set_motor_position(MOTOR_IDS["body"], 0)
        return {"status": "ok", "gesture": "shake"}
    
    elif gesture == "reset":
        # Reset všech motorů
        for mid in MOTOR_IDS.values():
            set_motor_position(mid, 0)
        return {"status": "ok", "gesture": "reset"}
    
    return {"error": f"Unknown gesture: {gesture}"}


def main():
    print("=" * 50)
    print("🦾 Reachy Mini OpenClaw Daemon v0.2.0")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8765, log_level="warning")


if __name__ == "__main__":
    main()
