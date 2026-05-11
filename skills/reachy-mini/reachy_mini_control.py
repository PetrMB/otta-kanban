#!/usr/bin/env python3
"""
Reachy Mini Control - Python API pro ovládání Reachy Mini robota
"""

import asyncio
import json
import websockets
import requests
from dataclasses import dataclass
from typing import Optional, Dict, List, Tuple
from enum import Enum

class ReachyMiniError(Exception):
    """Base exception pro Reachy Mini"""
    pass

class ConnectionError(ReachyMiniError):
    """Chyba připojení"""
    pass

@dataclass
class HeadPosition:
    """Pozice hlavy (Stewart platform)"""
    yaw: float
    pitch: float
    roll: float
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

@dataclass
class BodyPosition:
    """Pozice těla"""
    yaw: float

@dataclass
class AntennaPosition:
    """Pozice antény"""
    angle: float

@dataclass
class RobotState:
    """Kompletní stav robota"""
    head: HeadPosition
    body: BodyPosition
    left_antenna: AntennaPosition
    right_antenna: AntennaPosition
    temperatures: Dict[int, float]
    timestamp: float

class ReachyMini:
    """
    Hlavní třída pro ovládání Reachy Mini
    """
    
    # Safety limits
    HEAD_PITCH_LIMIT = (-40, 40)
    HEAD_ROLL_LIMIT = (-40, 40)
    HEAD_YAW_LIMIT = (-180, 180)
    BODY_YAW_LIMIT = (-180, 180)
    BODY_HEAD_YAW_DIFF_LIMIT = (-65, 65)
    
    # Motor IDs
    MOTOR_BODY = 10
    MOTOR_STEWART_1 = 11
    MOTOR_STEWART_6 = 16
    MOTOR_RIGHT_ANTENNA = 17
    MOTOR_LEFT_ANTENNA = 18
    
    def __init__(self, host: str = "localhost", port: int = 8000):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.ws_url = f"ws://{host}:{port}/api/state/ws/full"
        self._connected = False
        self._state: Optional[RobotState] = None
        
    def connect(self, timeout: float = 5.0) -> bool:
        """
        Připojí se k robot daemon API
        
        Args:
            timeout: Timeout v sekundách
            
        Returns:
            True pokud připojení úspěšné
            
        Raises:
            ConnectionError: Pokud se nepodaří připojit
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/health",
                timeout=timeout
            )
            if response.status_code == 200:
                self._connected = True
                return True
            raise ConnectionError(f"Health check failed: {response.status_code}")
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(f"Cannot connect to Reachy Mini at {self.base_url}. Is the daemon running?") from e
        except Exception as e:
            raise ConnectionError(f"Connection error: {e}") from e
    
    def disconnect(self):
        """Odpojí se od robota"""
        self._connected = False
    
    @property
    def is_connected(self) -> bool:
        """Kontroluje zda je připojeno"""
        return self._connected
    
    def _clamp(self, value: float, min_val: float, max_val: float) -> float:
        """Ořeže hodnotu do bezpečného rozsahu"""
        return max(min_val, min(max_val, value))
    
    def set_head_orientation(self, yaw: float = 0, pitch: float = 0, roll: float = 0) -> bool:
        """
        Nastaví orientaci hlavy
        
        Args:
            yaw: Otáčení kolem svislé osy (-180° až 180°)
            pitch: Naklonění dopředu/dozadu (-40° až 40°)
            roll: Náklon do strany (-40° až 40°)
            
        Returns:
            True pokud příkaz proběhl úspěšně
        """
        if not self._connected:
            raise ConnectionError("Not connected to robot")
        
        # Apply safety limits
        yaw = self._clamp(yaw, *self.HEAD_YAW_LIMIT)
        pitch = self._clamp(pitch, *self.HEAD_PITCH_LIMIT)
        roll = self._clamp(roll, *self.HEAD_ROLL_LIMIT)
        
        # Check body-head yaw difference
        body_state = self.get_body_state()
        if body_state:
            yaw_diff = abs(yaw - body_state.yaw)
            if yaw_diff > 65:
                # Adjust to maintain safety limit
                if yaw > body_state.yaw:
                    yaw = body_state.yaw + 65
                else:
                    yaw = body_state.yaw - 65
        
        payload = {
            "head": {
                "yaw": yaw,
                "pitch": pitch,
                "roll": roll
            }
        }
        
        response = requests.post(
            f"{self.base_url}/api/head/orientation",
            json=payload,
            timeout=5.0
        )
        return response.status_code == 200
    
    def set_body_rotation(self, yaw: float) -> bool:
        """
        Nastaví rotaci těla
        
        Args:
            yaw: Úhel rotace (-180° až 180°)
            
        Returns:
            True pokud příkaz proběhl úspěšně
        """
        if not self._connected:
            raise ConnectionError("Not connected to robot")
        
        yaw = self._clamp(yaw, *self.BODY_YAW_LIMIT)
        
        payload = {"rotation": yaw}
        
        response = requests.post(
            f"{self.base_url}/api/body/rotation",
            json=payload,
            timeout=5.0
        )
        return response.status_code == 200
    
    def set_antenna(self, side: str, angle: float) -> bool:
        """
        Nastaví pozici antény
        
        Args:
            side: "left" nebo "right"
            angle: Úhel (0° až 180°)
            
        Returns:
            True pokud příkaz proběhl úspěšně
        """
        if not self._connected:
            raise ConnectionError("Not connected to robot")
        
        if side not in ("left", "right"):
            raise ValueError("Side must be 'left' or 'right'")
        
        angle = self._clamp(angle, 0, 180)
        
        payload = {"angle": angle}
        
        response = requests.post(
            f"{self.base_url}/api/antenna/{side}/position",
            json=payload,
            timeout=5.0
        )
        return response.status_code == 200
    
    def get_state(self) -> Optional[RobotState]:
        """
        Získá aktuální stav robota
        
        Returns:
            RobotState objekt nebo None při chybě
        """
        if not self._connected:
            raise ConnectionError("Not connected to robot")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/state",
                timeout=5.0
            )
            if response.status_code == 200:
                data = response.json()
                return self._parse_state(data)
        except Exception:
            pass
        return None
    
    def _parse_state(self, data: dict) -> RobotState:
        """Parsuje JSON state do RobotState objektu"""
        head_data = data.get("head", {})
        body_data = data.get("body", {})
        antennas = data.get("antennas", {})
        
        return RobotState(
            head=HeadPosition(
                yaw=head_data.get("yaw", 0),
                pitch=head_data.get("pitch", 0),
                roll=head_data.get("roll", 0),
                x=head_data.get("x", 0),
                y=head_data.get("y", 0),
                z=head_data.get("z", 0)
            ),
            body=BodyPosition(
                yaw=body_data.get("rotation", 0)
            ),
            left_antenna=AntennaPosition(
                angle=antennas.get("left", {}).get("angle", 0)
            ),
            right_antenna=AntennaPosition(
                angle=antennas.get("right", {}).get("angle", 0)
            ),
            temperatures=data.get("temperatures", {}),
            timestamp=data.get("timestamp", 0)
        )
    
    def get_body_state(self) -> Optional[BodyPosition]:
        """Získá stav těla"""
        state = self.get_state()
        return state.body if state else None
    
    def get_head_state(self) -> Optional[HeadPosition]:
        """Získá stav hlavy"""
        state = self.get_state()
        return state.head if state else None
    
    def reset(self) -> bool:
        """
        Vrátí robota do výchozí pozice
        
        Returns:
            True pokud příkaz proběhl úspěšně
        """
        if not self._connected:
            raise ConnectionError("Not connected to robot")
        
        response = requests.post(
            f"{self.base_url}/api/reset",
            timeout=10.0
        )
        return response.status_code == 200
    
    def stop(self) -> bool:
        """
        Zastaví všechny pohyby
        
        Returns:
            True pokud příkaz proběhl úspěšně
        """
        if not self._connected:
            raise ConnectionError("Not connected to robot")
        
        response = requests.post(
            f"{self.base_url}/api/stop",
            timeout=5.0
        )
        return response.status_code == 200
    
    def get_temperatures(self) -> Dict[int, float]:
        """
        Získá teploty všech motorů
        
        Returns:
            Dict[motor_id, temperature]
        """
        state = self.get_state()
        return state.temperatures if state else {}
    
    def get_camera_url(self) -> str:
        """
        Vrátí URL pro WebRTC připojení ke kameře
        
        Returns:
            WebRTC signaling URL
        """
        return f"http://{self.host}:8443"
    
    async def stream_state(self, callback, interval: float = 0.05):
        """
        Streamuje stav robota přes WebSocket
        
        Args:
            callback: Funkce která se zavolá s novým stavem
            interval: Interval v sekundách (default 50ms = 20Hz)
        """
        if not self._connected:
            raise ConnectionError("Not connected to robot")
        
        try:
            async with websockets.connect(self.ws_url) as websocket:
                while self._connected:
                    try:
                        message = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=interval
                        )
                        data = json.loads(message)
                        state = self._parse_state(data)
                        callback(state)
                    except asyncio.TimeoutError:
                        continue
                    except Exception:
                        break
        except Exception as e:
            raise ConnectionError(f"WebSocket error: {e}") from e
    
    def list_choreographies(self) -> List[str]:
        """
        Vrátí seznam dostupných choreografií
        
        Returns:
            List názvů choreografií
        """
        if not self._connected:
            raise ConnectionError("Not connected to robot")
        
        try:
            response = requests.get(
                f"{self.base_url}/api/choreographies",
                timeout=5.0
            )
            if response.status_code == 200:
                return response.json().get("choreographies", [])
        except Exception:
            pass
        return []
    
    def play_choreography(self, name: str) -> bool:
        """
        Přehraje choreografii
        
        Args:
            name: Název choreografie
            
        Returns:
            True pokud příkaz proběhl úspěšně
        """
        if not self._connected:
            raise ConnectionError("Not connected to robot")
        
        response = requests.post(
            f"{self.base_url}/api/choreographies/{name}/play",
            timeout=5.0
        )
        return response.status_code == 200
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


# CLI interface
if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="Reachy Mini Control")
    parser.add_argument("--host", default="localhost", help="Daemon host")
    parser.add_argument("--port", type=int, default=8000, help="Daemon port")
    
    subparsers = parser.add_subparsers(dest="command")
    
    # Connect
    connect_parser = subparsers.add_parser("connect", help="Connect to robot")
    connect_parser.add_argument("--usb", action="store_true", help="USB mode (Lite)")
    connect_parser.add_argument("--wifi", action="store_true", help="WiFi mode (Wireless)")
    connect_parser.add_argument("--ip", default="10.42.0.1", help="Robot IP for WiFi")
    
    # Status
    subparsers.add_parser("status", help="Check connection status")
    
    # State
    state_parser = subparsers.add_parser("state", help="Get robot state")
    state_parser.add_argument("--stream", action="store_true", help="Stream state")
    
    # Head
    head_parser = subparsers.add_parser("head", help="Control head")
    head_sub = head_parser.add_subparsers(dest="head_cmd")
    head_set = head_sub.add_parser("set", help="Set head orientation")
    head_set.add_argument("--yaw", type=float, default=0)
    head_set.add_argument("--pitch", type=float, default=0)
    head_set.add_argument("--roll", type=float, default=0)
    
    # Body
    body_parser = subparsers.add_parser("body", help="Control body")
    body_sub = body_parser.add_subparsers(dest="body_cmd")
    body_set = body_sub.add_parser("set", help="Set body rotation")
    body_set.add_argument("--yaw", type=float, required=True)
    
    # Antenna
    antenna_parser = subparsers.add_parser("antenna", help="Control antennas")
    antenna_parser.add_argument("side", choices=["left", "right"])
    antenna_sub = antenna_parser.add_subparsers(dest="antenna_cmd")
    antenna_set = antenna_sub.add_parser("set", help="Set antenna position")
    antenna_set.add_argument("--angle", type=float, required=True)
    
    # Reset
    subparsers.add_parser("reset", help="Reset to default position")
    
    # Stop
    subparsers.add_parser("stop", help="Stop all movements")
    
    # Temperature
    subparsers.add_parser("temperature", help="Get motor temperatures")
    
    # Choreo
    choreo_parser = subparsers.add_parser("choreo", help="Choreography commands")
    choreo_sub = choreo_parser.add_subparsers(dest="choreo_cmd")
    choreo_sub.add_parser("list", help="List choreographies")
    choreo_play = choreo_sub.add_parser("play", help="Play choreography")
    choreo_play.add_argument("--name", required=True)
    
    # Camera
    camera_parser = subparsers.add_parser("camera", help="Camera commands")
    camera_sub = camera_parser.add_subparsers(dest="camera_cmd")
    camera_sub.add_parser("url", help="Get WebRTC URL")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Determine host
    host = args.host
    if args.command == "connect" and args.wifi:
        host = args.ip
    
    robot = ReachyMini(host=host, port=args.port)
    
    try:
        if args.command == "connect":
            if robot.connect():
                print(f"✓ Connected to Reachy Mini at {host}:{args.port}")
                print(f"  Robot state: {robot.get_state()}")
            else:
                print(f"✗ Failed to connect")
                sys.exit(1)
        
        elif args.command == "status":
            if robot.connect():
                print("✓ Connected")
                state = robot.get_state()
                if state:
                    print(f"\nHead: yaw={state.head.yaw:.1f}°, pitch={state.head.pitch:.1f}°, roll={state.head.roll:.1f}°")
                    print(f"Body: yaw={state.body.yaw:.1f}°")
                    print(f"Left antenna: {state.left_antenna.angle:.1f}°")
                    print(f"Right antenna: {state.right_antenna.angle:.1f}°")
            else:
                print("✗ Not connected")
        
        elif args.command == "state":
            robot.connect()
            if args.stream:
                print("Streaming state (Ctrl+C to stop)...")
                def print_state(state):
                    print(f"\rHead: {state.head.yaw:.1f},{state.head.pitch:.1f},{state.head.roll:.1f} | "
                          f"Body: {state.body.yaw:.1f} | "
                          f"Ant: L{state.left_antenna.angle:.0f}/R{state.right_antenna.angle:.0f}", end="")
                
                try:
                    asyncio.run(robot.stream_state(print_state))
                except KeyboardInterrupt:
                    print("\nStopped")
            else:
                state = robot.get_state()
                print(json.dumps({
                    "head": {
                        "yaw": state.head.yaw,
                        "pitch": state.head.pitch,
                        "roll": state.head.roll
                    },
                    "body": {"yaw": state.body.yaw},
                    "antennas": {
                        "left": state.left_antenna.angle,
                        "right": state.right_antenna.angle
                    }
                }, indent=2))
        
        elif args.command == "head" and args.head_cmd == "set":
            robot.connect()
            if robot.set_head_orientation(args.yaw, args.pitch, args.roll):
                print(f"✓ Head set to yaw={args.yaw}°, pitch={args.pitch}°, roll={args.roll}°")
            else:
                print("✗ Failed")
        
        elif args.command == "body" and args.body_cmd == "set":
            robot.connect()
            if robot.set_body_rotation(args.yaw):
                print(f"✓ Body set to yaw={args.yaw}°")
            else:
                print("✗ Failed")
        
        elif args.command == "antenna" and args.antenna_cmd == "set":
            robot.connect()
            if robot.set_antenna(args.side, args.angle):
                print(f"✓ {args.side.capitalize()} antenna set to {args.angle}°")
            else:
                print("✗ Failed")
        
        elif args.command == "reset":
            robot.connect()
            if robot.reset():
                print("✓ Robot reset to default position")
            else:
                print("✗ Failed")
        
        elif args.command == "stop":
            robot.connect()
            if robot.stop():
                print("✓ All movements stopped")
            else:
                print("✗ Failed")
        
        elif args.command == "temperature":
            robot.connect()
            temps = robot.get_temperatures()
            print("Motor temperatures:")
            for motor_id, temp in temps.items():
                print(f"  Motor {motor_id}: {temp:.1f}°C")
        
        elif args.command == "choreo":
            robot.connect()
            if args.choreo_cmd == "list":
                choreos = robot.list_choreographies()
                print("Available choreographies:")
                for name in choreos:
                    print(f"  - {name}")
            elif args.choreo_cmd == "play":
                if robot.play_choreography(args.name):
                    print(f"✓ Playing choreography: {args.name}")
                else:
                    print("✗ Failed")
        
        elif args.command == "camera" and args.camera_cmd == "url":
            robot.connect()
            print(f"WebRTC URL: {robot.get_camera_url()}")
    
    except ConnectionError as e:
        print(f"✗ Connection error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)
    finally:
        robot.disconnect()