#!/usr/bin/env python3
"""
OTTO Daemon - Lightweight Reachy Mini control daemon
Přímé USB serial ovládání bez desktop aplikace
"""

import sys
import json
import time
import asyncio
import threading
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn
import serial.tools.list_ports

# Přidáme reachy-mini libs
sys.path.insert(0, str(Path.home() / ".venvs/reachy-mini/lib/python3.13/site-packages"))

try:
    from reachy_mini_motor_controller import ReachyMiniMotorController
    HAVE_MOTORS = True
except ImportError:
    HAVE_MOTORS = False
    print("⚠️ Motor controller not available")

# ============ Configuration ============
DAEMON_PORT = 8765
REACHY_PORT = None  # Auto-detect
MOTOR_IDS = {
    "body": 10,
    "stewart_1": 11, "stewart_2": 12, "stewart_3": 13,
    "stewart_4": 14, "stewart_5": 15, "stewart_6": 16,
    "antenna_left": 18, "antenna_right": 17,
}

# ============ State ============
@dataclass
class RobotState:
    head_pitch: float = 0.0
    head_yaw: float = 0.0
    head_roll: float = 0.0
    body_yaw: float = 0.0
    antenna_left: float = 0.0
    antenna_right: float = 0.0
    timestamp: float = 0.0

daemon_state = {
    "controller": None,
    "running": False,
    "current": RobotState(),
    "target": RobotState(),
}

# ============ Motor Control ============

def find_reachy_port() -> Optional[str]:
    """Najde Reachy USB port"""
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        # Reachy Mini Lite má CH340/CH341 (VID 0x1a86)
        if "1a86" in p.hwid.lower() or "usbmodem" in p.device.lower():
            return p.device
    # Fallback na známý port
    return "/dev/cu.usbmodem5B420750561"

def init_controller() -> Optional[ReachyMiniMotorController]:
    """Inicializuje motor controller"""
    if not HAVE_MOTORS:
        return None
    
    port = find_reachy_port()
    if not port:
        print("✗ No Reachy port found")
        return None
    
    try:
        print(f"🔌 Connecting to {port}...")
        ctrl = ReachyMiniMotorController(port)
        print(f"✓ Controller created")
        
        # Enable torque
        ctrl.enable_torque()
        print("✓ Torque enabled")
        
        return ctrl
    except Exception as e:
        print(f"✗ Failed: {e}")
        return None

def set_motor_positions(ctrl: ReachyMiniMotorController, state: RobotState):
    """Nastaví pozice všech motorů"""
    try:
        # Body rotation
        ctrl.set_body_rotation(state.body_yaw)
        
        # Antény
        ctrl.set_antennas_positions([state.antenna_left, state.antenna_right])
        
        # Stewart platform - zjednodušený výpočet
        # Pitch -> stewart_1, stewart_4 (přední motory)
        # Yaw -> diference mezi stranami
        pitch_offset = state.head_pitch * 0.5
        yaw_offset = state.head_yaw * 0.3
        
        stewart = [
            pitch_offset + yaw_offset,   # 11
            -pitch_offset,               # 12
            pitch_offset - yaw_offset,   # 13
            pitch_offset + yaw_offset,   # 14
            -pitch_offset,               # 15
            pitch_offset - yaw_offset,   # 16
        ]
        ctrl.set_stewart_platform_position(stewart)
        
    except Exception as e:
        print(f"Motor error: {e}")

def read_motor_states(ctrl: ReachyMiniMotorController) -> Dict:
    """Přečte stav motorů"""
    try:
        positions = ctrl.read_all_positions()
        return {
            "body": positions[0] if len(positions) > 0 else 0,
            "antennas": [positions[1], positions[2]] if len(positions) > 2 else [0, 0],
            "stewart": positions[3:9] if len(positions) > 8 else [0]*6,
        }
    except:
        return {}

# Background control loop
def control_loop():
    """50Hz control loop pro pohyby"""
    ctrl = daemon_state.get("controller")
    if not ctrl:
        return
    
    while daemon_state["running"]:
        target = daemon_state["target"]
        current = daemon_state["current"]
        
        # Interpolate (simple)
        alpha = 0.1
        current.head_pitch += (target.head_pitch - current.head_pitch) * alpha
        current.head_yaw += (target.head_yaw - current.head_yaw) * alpha
        current.head_roll += (target.head_roll - current.head_roll) * alpha
        current.body_yaw += (target.body_yaw - current.body_yaw) * alpha
        current.antenna_left += (target.antenna_left - current.antenna_left) * alpha
        current.antenna_right += (target.antenna_right - current.antenna_right) * alpha
        
        # Apply to motors
        set_motor_positions(ctrl, current)
        current.timestamp = time.time()
        
        time.sleep(0.02)  # 50Hz

# ============ FastAPI ============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager"""
    global REACHY_PORT
    
    print("🚀 OTTO Daemon starting...")
    print("=" * 50)
    
    # Init motors
    daemon_state["controller"] = init_controller()
    daemon_state["running"] = True
    
    if daemon_state["controller"]:
        print("✓ Robot connected!")
        # Start control loop
        thread = threading.Thread(target=control_loop, daemon=True)
        thread.start()
    else:
        print("⚠️ Running in MOCK mode")
    
    print(f"✓ API ready at http://localhost:{DAEMON_PORT}")
    print("=" * 50)
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")
    daemon_state["running"] = False
    ctrl = daemon_state.get("controller")
    if ctrl:
        try:
            ctrl.disable_torque()
        except:
            pass

app = FastAPI(
    title="OTTO Daemon - Reachy Mini Lite",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"])

# ============ API Endpoints ============

from pydantic import BaseModel

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

class SoundPlayRequest(BaseModel):
    file: str
    volume: int = 80

SOUNDS_DIR = Path("/tmp/reachy_sounds")
SOUNDS_DIR.mkdir(exist_ok=True)

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "daemon": "otto_daemon",
        "has_robot": daemon_state["controller"] is not None,
        "mock_mode": not HAVE_MOTORS or daemon_state["controller"] is None
    }

@app.get("/api/daemon/status")
def daemon_status():
    return {
        "type": "daemon_status",
        "robot_name": "reachy_mini",
        "state": "running" if daemon_state["running"] else "stopped",
        "otto_daemon": True,
        "has_robot": daemon_state["controller"] is not None,
        "backend_status": {
            "ready": daemon_state["controller"] is not None,
            "motor_control_mode": "enabled"
        }
    }

@app.get("/api/state/full")
def get_state():
    s = daemon_state["current"]
    return {
        "control_mode": "enabled" if daemon_state["controller"] else "disabled",
        "head_pose": {
            "x": 0, "y": 0, "z": 0,
            "roll": s.head_roll,
            "pitch": s.head_pitch,
            "yaw": s.head_yaw
        },
        "body_yaw": s.body_yaw,
        "antennas_position": [s.antenna_left, s.antenna_right],
        "timestamp": s.timestamp
    }

@app.post("/api/move/goto")
def move_goto(req: GotoRequest):
    """Pohyb na pozici"""
    target = daemon_state["target"]
    target.head_pitch = req.head_pose.pitch
    target.head_yaw = req.head_pose.yaw
    target.head_roll = req.head_pose.roll
    target.body_yaw = req.body_yaw
    if len(req.antennas) >= 2:
        target.antenna_left = req.antennas[0]
        target.antenna_right = req.antennas[1]
    
    return {"uuid": f"goto-{time.time()}", "status": "accepted"}

@app.post("/api/move/play/wake_up")
def wake_up():
    """Wake up animation"""
    target = daemon_state["target"]
    target.antenna_left = 0.8
    target.antenna_right = -0.8
    time.sleep(0.5)
    target.antenna_left = 0
    target.antenna_right = 0
    return {"uuid": f"wake-{time.time()}"}

# ============ TTS / Sound endpoints ============

@app.get("/api/media/sounds")
def list_sounds():
    """List uploaded sounds"""
    sounds = [f.name for f in SOUNDS_DIR.iterdir() if f.suffix in ['.wav', '.mp3']]
    return {"sounds": sounds}

@app.post("/api/media/sounds/upload")
async def upload_sound(file: UploadFile = File(...)):
    """Upload sound file"""
    filepath = SOUNDS_DIR / file.filename
    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)
    return {"status": "ok", "path": str(filepath)}

@app.post("/api/media/play_sound")
def play_sound(req: SoundPlayRequest):
    """Play uploaded sound via macOS afplay"""
    filepath = SOUNDS_DIR / req.file
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Sound not found")
    
    # Play using afplay
    volume = req.volume / 100
    subprocess.Popen(
        ["afplay", "-v", str(volume), str(filepath)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return {"status": "ok", "file": req.file}

class SpeakRequest(BaseModel):
    text: str
    voice: str = "Zuzana"
    volume: int = 80
    animate: bool = True

@app.post("/api/speak")
def speak(req: SpeakRequest):
    """TTS with animation - generate and play"""
    import subprocess
    import tempfile
    
    text = req.text
    voice = req.voice
    volume = req.volume
    animate = req.animate
    
    with tempfile.TemporaryDirectory() as tmpdir:
        aiff = Path(tmpdir) / "speech.aiff"
        wav = SOUNDS_DIR / "speech.wav"
        
        # Generate TTS
        subprocess.run(
            ["say", "-v", voice, text, "-o", str(aiff)],
            capture_output=True, check=True
        )
        subprocess.run(
            ["afconvert", str(aiff), str(wav), "-f", "WAVE", "-d", "LEI16@44100"],
            capture_output=True, check=True
        )
        
        # Estimate duration
        duration = len(text) * 0.09
        
        # Animate if requested
        if animate and daemon_state["controller"]:
            def animate_speech():
                # Speaking pose
                target = daemon_state["target"]
                target.head_pitch = -0.1
                target.antenna_left = 0.3
                target.antenna_right = -0.3
                time.sleep(0.5)
                
                # Nodding during speech
                start = time.time()
                while time.time() - start < duration:
                    target.head_pitch = -0.2
                    time.sleep(0.4)
                    target.head_pitch = -0.05
                    time.sleep(0.4)
                
                # Reset
                target.head_pitch = 0
                target.antenna_left = 0
                target.antenna_right = 0
            
            threading.Thread(target=animate_speech, daemon=True).start()
        
        # Play
        volume_norm = volume / 100
        subprocess.Popen(
            ["afplay", "-v", str(volume_norm), str(wav)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        return {"status": "ok", "text": req.text, "duration": duration, "animated": req.animate}

# Run
def main():
    uvicorn.run(app, host="0.0.0.0", port=DAEMON_PORT, log_level="info")

if __name__ == "__main__":
    main()
