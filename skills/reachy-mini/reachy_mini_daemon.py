#!/usr/bin/env python3
"""
Reachy Mini Lite Daemon - Lightweight API bez desktop app
Přímá komunikace s Dynamixel motory přes USB serial
"""

import sys
import json
import time
import asyncio
import threading
from contextlib import asynccontextmanager
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List
from pathlib import Path

# Přidáme cestu k reachy-mini knihovnám
sys.path.insert(0, str(Path.home() / ".venvs/reachy-mini/lib/python3.13/site-packages"))

try:
    from reachy_mini_motor_controller import ReachyMiniMotorController
    HAVE_MOTOR_CONTROLLER = True
except ImportError:
    HAVE_MOTOR_CONTROLLER = False
    print("⚠️ Motor controller not available - running in mock mode")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn


@dataclass
class MotorState:
    """Stav jednoho motoru"""
    id: int
    position: float  # radiány
    temperature: float  # °C
    load: float  # %
    voltage: float  # V
    error: Optional[str] = None


@dataclass
class RobotState:
    """Kompletní stav robota"""
    head_pose: dict  # x, y, z, roll, pitch, yaw
    body_yaw: float
    antennas: List[float]  # [left, right]
    timestamp: float
    motors: Dict[int, MotorState]


# Request/Response modely
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


class SoundRequest(BaseModel):
    file: str
    volume: int = 80


# Global state
daemon_state = {
    "running": False,
    "controller": None,
    "motors": {},
    "target_state": None,
    "current_state": None,
    "last_update": 0,
}


# Motor IDs podle dokumentace
MOTOR_IDS = {
    "body_rotation": 10,
    "stewart_1": 11, "stewart_2": 12, "stewart_3": 13,
    "stewart_4": 14, "stewart_5": 15, "stewart_6": 16,
    "right_antenna": 17,
    "left_antenna": 18,
}


def init_controller():
    """Inicializuje motor controller"""
    if not HAVE_MOTOR_CONTROLLER:
        return None
    
    try:
        # Auto-detect serial port (Reachy Mini Lite má VID:PID 1a86:55d3)
        import serial.tools.list_ports
        ports = list(serial.tools.list_ports.comports())
        reachy_port = None
        
        for p in ports:
            # Reachy Mini Lite se detekuje jako CH340/CH341 nebo usbmodem
            if "1a86" in p.hwid or "ch340" in p.description.lower() or "usbmodem" in p.device.lower():
                reachy_port = p.device
                break
        
        if not reachy_port:
            # Fallback na známý port
            reachy_port = "/dev/cu.usbmodem5B420750561"
        
        print(f"🔌 Connecting to Reachy Mini on {reachy_port}...")
        
        # Inicializace controlleru
        controller = ReachyMiniMotorController(reachy_port, 1000000)
        
        if controller.connect():
            print("✓ Connected to motors!")
            daemon_state["controller"] = controller
            daemon_state["running"] = True
            return controller
        else:
            print("✗ Failed to connect to motors")
            return None
            
    except Exception as e:
        print(f"✗ Motor controller error: {e}")
        return None


def read_motor_states():
    """Přečte stav všech motorů"""
    controller = daemon_state.get("controller")
    if not controller:
        return {}
    
    states = {}
    try:
        for name, motor_id in MOTOR_IDS.items():
            try:
                # Čtení pozice, teploty, napětí
                pos = controller.get_position(motor_id)
                temp = controller.get_temperature(motor_id) if hasattr(controller, 'get_temperature') else 25.0
                volt = controller.get_voltage(motor_id) if hasattr(controller, 'get_voltage') else 7.0
                
                states[motor_id] = MotorState(
                    id=motor_id,
                    position=pos,
                    temperature=temp,
                    load=0.0,
                    voltage=volt
                )
            except Exception as e:
                states[motor_id] = MotorState(
                    id=motor_id, position=0.0, temperature=0.0,
                    load=0.0, voltage=0.0, error=str(e)
                )
    except Exception as e:
        print(f"Motor read error: {e}")
    
    return states


def update_state_loop():
    """Background thread pro čtení stavu motorů"""
    while daemon_state["running"]:
        try:
            states = read_motor_states()
            daemon_state["motors"] = states
            daemon_state["last_update"] = time.time()
            
            # Vypočítáme odhadovanou pozici hlavy z motorů Stewart platformy
            # (zde je zjednodušený výpočet, reálně by se použila kinematika)
            if 11 in states and 16 in states:
                # Odhad hlavy z průměru motorů
                m11 = states[11].position
                m16 = states[16].position
                
                daemon_state["current_state"] = {
                    "head_pose": {
                        "x": 0.0, "y": 0.0, "z": (m11 + m16) / 2,
                        "roll": 0.0, "pitch": 0.0, "yaw": 0.0
                    },
                    "body_yaw": states.get(10, MotorState(10, 0, 0, 0, 0)).position,
                    "antennas": [
                        states.get(18, MotorState(18, 0, 0, 0, 0)).position,
                        states.get(17, MotorState(17, 0, 0, 0, 0)).position
                    ],
                    "timestamp": time.time()
                }
            
        except Exception as e:
            print(f"State loop error: {e}")
        
        time.sleep(0.02)  # 50Hz update rate


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    # Startup
    print("🚀 Starting Reachy Mini Lite Daemon...")
    
    if init_controller():
        # Start background thread pro čtení stavu
        thread = threading.Thread(target=update_state_loop, daemon=True)
        thread.start()
        print("✓ Daemon running at http://localhost:8765")
    else:
        print("⚠️ Running in MOCK mode (no real robot)")
        daemon_state["running"] = True
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")
    daemon_state["running"] = False
    controller = daemon_state.get("controller")
    if controller:
        try:
            controller.disconnect()
        except:
            pass


# FastAPI app
app = FastAPI(
    title="Reachy Mini Lite Daemon",
    description="Lightweight daemon pro Reachy Mini bez desktop app",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/api/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "daemon": "reachy_mini_lite",
        "has_robot": daemon_state["controller"] is not None,
        "mock_mode": not HAVE_MOTOR_CONTROLLER or daemon_state["controller"] is None,
        "motors_connected": len(daemon_state.get("motors", {})) > 0
    }


@app.get("/api/daemon/status")
async def daemon_status():
    """Status daemonu"""
    return {
        "type": "daemon_status",
        "robot_name": "reachy_mini",
        "state": "running" if daemon_state["running"] else "stopped",
        "wireless_version": False,
        "desktop_app_daemon": False,  # Tohle je náš lightweight daemon!
        "lite_daemon": True,
        "simulation_enabled": False,
        "mockup_sim_enabled": daemon_state["controller"] is None,
        "backend_status": {
            "ready": daemon_state["controller"] is not None,
            "motor_control_mode": "enabled" if daemon_state["controller"] else "disabled",
            "last_alive": daemon_state.get("last_update"),
            "control_loop_stats": {}
        }
    }


@app.get("/api/state/full")
async def get_state():
    """Aktuální stav robota"""
    current = daemon_state.get("current_state", {
        "head_pose": {"x": 0, "y": 0, "z": 0, "roll": 0, "pitch": 0, "yaw": 0},
        "body_yaw": 0,
        "antennas": [0, 0],
        "timestamp": time.time()
    })
    
    return {
        **current,
        "control_mode": "enabled" if daemon_state["controller"] else "disabled",
        "motors": {k: asdict(v) for k, v in daemon_state.get("motors", {}).items()}
    }


@app.post("/api/move/goto")
async def move_goto(request: GotoRequest):
    """Pohyb na cílovou pozici"""
    controller = daemon_state.get("controller")
    
    if not controller:
        # Mock mode - jen uložíme target
        daemon_state["target_state"] = {
            "head_pose": request.head_pose.dict(),
            "body_yaw": request.body_yaw,
            "antennas": request.antennas
        }
        return {"uuid": f"mock-{time.time()}", "status": "mock_accepted"}
    
    try:
        # Konverze head pose na Stewart platform motor positions
        # (zjednodušený výpočet - reálně by se použila inverzní kinematika)
        
        # Body rotation
        if request.body_yaw != 0:
            controller.set_goal_position(MOTOR_IDS["body_rotation"], request.body_yaw)
        
        # Antény
        if len(request.antennas) >= 2:
            controller.set_goal_position(MOTOR_IDS["left_antenna"], request.antennas[0])
            controller.set_goal_position(MOTOR_IDS["right_antenna"], request.antennas[1])
        
        # Head (zjednodušeně - reálně IK)
        # Stewart platform by vyžadovala kinematický výpočet
        
        return {"uuid": f"move-{time.time()}", "status": "accepted"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/move/play/wake_up")
async def wake_up():
    """Wake up animace"""
    controller = daemon_state.get("controller")
    
    if not controller:
        return {"uuid": f"wake-mock-{time.time()}"}
    
    # Sekvenční pohyb
    try:
        # Antény nahoru
        controller.set_goal_position(MOTOR_IDS["left_antenna"], 0.5)
        controller.set_goal_position(MOTOR_IDS["right_antenna"], -0.5)
        time.sleep(0.5)
        
        # Zpátky
        controller.set_goal_position(MOTOR_IDS["left_antenna"], 0)
        controller.set_goal_position(MOTOR_IDS["right_antenna"], 0)
        
        return {"uuid": f"wake-{time.time()}", "status": "playing"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/motors/status")
async def motors_status():
    """Status motorů"""
    return {
        "mode": "enabled" if daemon_state["controller"] else "disabled",
        "motors": {k: asdict(v) for k, v in daemon_state.get("motors", {}).items()}
    }


@app.get("/docs")
async def docs():
    """Přesměrování na Swagger UI"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse("/docs")


@app.get("/openapi.json")
async def openapi():
    """OpenAPI schema"""
    return app.openapi()


def main():
    """Hlavní funkce"""
    print("🦾 Reachy Mini Lite Daemon v0.1.0")
    print("=" * 40)
    print("API: http://localhost:8765")
    print("Docs: http://localhost:8765/docs")
    print("=" * 40)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8765,
        log_level="info"
    )


if __name__ == "__main__":
    main()