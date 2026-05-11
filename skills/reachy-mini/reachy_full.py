#!/usr/bin/env python3
"""
Reachy Mini Full Skill - Kompletní API pro Reachy Mini Lite
Všechny funkce: pohyb, TTS, kamery, mikrofony, vize
"""

import json
import time
import asyncio
import tempfile
import subprocess
import threading
import websocket
import numpy as np
from pathlib import Path
from typing import Optional, List, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
import requests
import cv2


class Direction(Enum):
    """Směry pro pohled/otočení"""
    LEFT = -1
    CENTER = 0
    RIGHT = 1
    UP = -2
    DOWN = 2


@dataclass
class HeadPose:
    """Pozice hlavy"""
    x: float = 0.0
    y: float = 0.0  
    z: float = 0.0
    roll: float = 0.0   # Náklon do stran
    pitch: float = 0.0  # Nahoru/dolu (-0.4 až 0.4)
    yaw: float = 0.0    # Vlevo/vpravo (-0.5 až 0.5)


@dataclass
class RobotState:
    """Kompletní stav robota"""
    head: HeadPose
    body_yaw: float
    antennas: List[float]
    timestamp: float
    motor_temperatures: dict = None


@dataclass
class SoundSource:
    """Detekovaný zvukový zdroj z DoA"""
    azimuth: float      # Horizontalní úhel (-180° až 180°)
    elevation: float    # Vertikální úhel (-90° až 90°)
    confidence: float   # Jistota detekce (0-1)
    timestamp: float


class ReachyMiniFull:
    """
    Kompletní Reachy Mini API
    
    Použití:
        reachy = ReachyMiniFull()
        
        # Základní pohyby
        reachy.look_at(Direction.LEFT)
        reachy.nod()
        reachy.wave()
        
        # Mluvení s animací
        reachy.say("Ahoj!", gesture="wave")
        
        # Reakce na zvuk
        source = reachy.wait_for_sound(timeout=5.0)
        if source:
            reachy.look_at_direction(source.azimuth)
            reachy.say("Slyšel jsem tě!")
        
        # Kamera
        frame = reachy.get_camera_frame()
        
        # Procházení
        reachy.explore_around()
    """
    
    def __init__(self, 
                 api_url: str = "http://localhost:8000",
                 camera_url: str = "http://localhost:8443",
                 websocket_url: str = "ws://localhost:8000/api/state/ws/full"):
        self.api_url = api_url
        self.camera_url = camera_url
        self.ws_url = websocket_url
        self._session = requests.Session()
        self._state_callbacks = []
        self._sound_callbacks = []
        self._current_state = None
        self._ws_thread = None
        self._running = False
        self._last_doa = None
        
    # ============ Low-level API ============
    
    def _api_get(self, endpoint: str, timeout: float = 5.0) -> dict:
        r = self._session.get(f"{self.api_url}{endpoint}", timeout=timeout)
        r.raise_for_status()
        return r.json()
    
    def _api_post(self, endpoint: str, data: dict, timeout: float = 10.0) -> dict:
        r = self._session.post(f"{self.api_url}{endpoint}", json=data, timeout=timeout)
        r.raise_for_status()
        return r.json()
    
    def is_ready(self) -> bool:
        """Kontrola připojení"""
        try:
            r = self._session.get(f"{self.api_url}/api/health", timeout=2.0)
            return r.status_code == 200
        except:
            return False
    
    def get_state(self) -> RobotState:
        """Aktuální stav"""
        s = self._api_get("/api/state/full")
        hp = s.get('head_pose', {})
        return RobotState(
            head=HeadPose(
                x=hp.get('x', 0),
                y=hp.get('y', 0),
                z=hp.get('z', 0),
                roll=hp.get('roll', 0),
                pitch=hp.get('pitch', 0),
                yaw=hp.get('yaw', 0)
            ),
            body_yaw=s.get('body_yaw', 0),
            antennas=s.get('antennas_position', [0, 0]),
            timestamp=s.get('timestamp', time.time())
        )
    
    # ============ WebSocket State Streaming ============
    
    def start_state_stream(self, callback: Callable[[RobotState], None]):
        """
        Spustí WebSocket stream stavu robota
        callback: funkce volaná při každém novém stavu
        """
        self._state_callbacks.append(callback)
        
        if self._ws_thread is None or not self._ws_thread.is_alive():
            self._running = True
            self._ws_thread = threading.Thread(target=self._websocket_loop, daemon=True)
            self._ws_thread.start()
    
    def _websocket_loop(self):
        """Background WebSocket loop"""
        while self._running:
            try:
                ws = websocket.create_connection(self.ws_url, timeout=5.0)
                while self._running:
                    msg = ws.recv()
                    data = json.loads(msg)
                    
                    # Update current state
                    hp = data.get('head_pose', {})
                    state = RobotState(
                        head=HeadPose(
                            x=hp.get('x', 0), y=hp.get('y', 0), z=hp.get('z', 0),
                            roll=hp.get('roll', 0), pitch=hp.get('pitch', 0), yaw=hp.get('yaw', 0)
                        ),
                        body_yaw=data.get('body_yaw', 0),
                        antennas=data.get('antennas_position', [0, 0]),
                        timestamp=data.get('timestamp', time.time())
                    )
                    self._current_state = state
                    
                    # Call callbacks
                    for cb in self._state_callbacks:
                        try:
                            cb(state)
                        except:
                            pass
                            
            except Exception as e:
                print(f"WebSocket error: {e}")
                time.sleep(1.0)
    
    def stop_state_stream(self):
        """Zastaví WebSocket stream"""
        self._running = False
        self._state_callbacks.clear()
    
    # ============ Movement - Low Level ============
    
    def goto(self, 
             pose: Optional[HeadPose] = None,
             body_yaw: Optional[float] = None,
             antennas: Optional[List[float]] = None,
             duration: float = 1.0,
             interpolation: str = "minjerk") -> dict:
        """Přímý pohyb na pozici"""
        if pose is None:
            pose = HeadPose()
            
        return self._api_post("/api/move/goto", {
            "head_pose": {
                "x": pose.x, "y": pose.y, "z": pose.z,
                "roll": pose.roll, "pitch": pose.pitch, "yaw": pose.yaw
            },
            "body_yaw": body_yaw or 0,
            "antennas": antennas or [0, 0],
            "duration": duration,
            "interpolation": interpolation
        })
    
    def goto_angles(self,
                    head_pitch: Optional[float] = None,
                    head_yaw: Optional[float] = None,
                    head_roll: Optional[float] = None,
                    body_yaw: Optional[float] = None,
                    left_antenna: Optional[float] = None,
                    right_antenna: Optional[float] = None,
                    duration: float = 1.0):
        """Pohyb pomocí jednotlivých úhlů"""
        current = self.get_state()
        
        pose = HeadPose(
            pitch=head_pitch if head_pitch is not None else current.head.pitch,
            yaw=head_yaw if head_yaw is not None else current.head.yaw,
            roll=head_roll if head_roll is not None else current.head.roll
        )
        
        ants = current.antennas.copy()
        if left_antenna is not None:
            ants[0] = left_antenna
        if right_antenna is not None:
            ants[1] = right_antenna
            
        return self.goto(
            pose=pose,
            body_yaw=body_yaw if body_yaw is not None else current.body_yaw,
            antennas=ants,
            duration=duration
        )
    
    def reset(self, duration: float = 2.0):
        """Návrat do výchozí pozice"""
        return self.goto(HeadPose(), 0, [0, 0], duration)
    
    # ============ Movement - High Level ============
    
    def look_at(self, direction: Direction, intensity: float = 1.0):
        """
        Podívá se daným směrem
        intensity: 0-1 (jak moc se otočí)
        """
        if direction == Direction.LEFT:
            return self.goto_angles(head_yaw=-0.5 * intensity, duration=0.8)
        elif direction == Direction.RIGHT:
            return self.goto_angles(head_yaw=0.5 * intensity, duration=0.8)
        elif direction == Direction.UP:
            return self.goto_angles(head_pitch=-0.3 * intensity, duration=0.8)
        elif direction == Direction.DOWN:
            return self.goto_angles(head_pitch=0.3 * intensity, duration=0.8)
        elif direction == Direction.CENTER:
            return self.goto_angles(head_pitch=0, head_yaw=0, duration=1.0)
    
    def look_at_direction(self, azimuth_degrees: float, elevation_degrees: float = 0):
        """
        Podívá se na konkrétní směr (z DoA mikrofonů)
        azimuth: -180° (vlevo) až 180° (vpravo), 0 = předek
        elevation: -90° (nahoru) až 90° (dolu)
        """
        # Mapování úhlů na pitch/yaw
        # azimuth -> head_yaw (-0.5 až 0.5 rad)
        # elevation -> head_pitch (-0.4 až 0.4 rad)
        
        yaw = np.clip(azimuth_degrees / 180 * 0.5, -0.5, 0.5)
        pitch = np.clip(-elevation_degrees / 90 * 0.4, -0.4, 0.4)
        
        return self.goto_angles(head_yaw=yaw, head_pitch=pitch, duration=1.0)
    
    def wave(self, count: int = 3, speed: float = 0.3):
        """Zamávání anténkama"""
        for i in range(count):
            self.goto_angles(left_antenna=0.8, right_antenna=-0.8, duration=speed)
            time.sleep(speed)
            self.goto_angles(left_antenna=0, right_antenna=0, duration=speed)
            time.sleep(speed)
    
    def nod(self, count: int = 2):
        """Přikyvování"""
        for i in range(count):
            self.goto_angles(head_pitch=-0.25, duration=0.4)
            time.sleep(0.4)
            self.goto_angles(head_pitch=0.1, duration=0.4)
            time.sleep(0.4)
        self.goto_angles(head_pitch=0, duration=0.4)
    
    def shake_head(self, count: int = 2):
        """Zakroutení hlavou (ne)"""
        for i in range(count):
            self.goto_angles(head_yaw=-0.4, duration=0.35)
            time.sleep(0.35)
            self.goto_angles(head_yaw=0.4, duration=0.35)
            time.sleep(0.35)
        self.goto_angles(head_yaw=0, duration=0.4)
    
    def tilt_head(self, direction: Direction):
        """Nakloní hlavu (na soucit/interest)"""
        if direction == Direction.LEFT:
            return self.goto_angles(head_roll=-0.2, duration=0.8)
        elif direction == Direction.RIGHT:
            return self.goto_angles(head_roll=0.2, duration=0.8)
    
    def explore_around(self, sectors: int = 5):
        """Prohlédne si okolí"""
        angles = np.linspace(-0.6, 0.6, sectors)
        for angle in angles:
            self.goto_angles(head_yaw=angle, head_pitch=-0.1, duration=1.0)
            time.sleep(1.2)
        self.look_at(Direction.CENTER)
    
    # ============ TTS & Speech ============
    
    def say(self, text: str, 
            voice: str = "Zuzana",
            animate: bool = True,
            gesture: Optional[str] = None,
            look_at_source: Optional[SoundSource] = None) -> dict:
        """
        Promluví text s animací
        
        Args:
            text: Co říct
            voice: Hlas (Zuzana, Samantha, etc.)
            animate: Pohybovat se během mluvení?
            gesture: "wave", "nod", "shake" - gesto během mluvení
            look_at_source: Pokud je zadán SoundSource, podívá se tam
        """
        # Pokud máme zdroj zvuku, podíváme se tam
        if look_at_source:
            self.look_at_direction(look_at_source.azimuth, look_at_source.elevation)
        
        # Vygeneruj TTS
        with tempfile.TemporaryDirectory() as tmpdir:
            aiff = Path(tmpdir) / "speech.aiff"
            wav = Path(tmpdir) / "speech.wav"
            
            subprocess.run(
                ["say", "-v", voice, text, "-o", str(aiff)],
                capture_output=True, check=True
            )
            subprocess.run(
                ["afconvert", str(aiff), str(wav), "-f", "WAVE", "-d", "LEI16@44100"],
                capture_output=True, check=True
            )
            
            # Upload
            with open(wav, "rb") as f:
                self._session.post(
                    f"{self.api_url}/api/media/sounds/upload",
                    files={"file": f},
                    timeout=10.0
                )
        
        # Odhad délky
        duration = len(text) * 0.09
        
        # Animace na pozadí
        if animate:
            threading.Thread(
                target=self._speak_animation,
                args=(duration, gesture),
                daemon=True
            ).start()
        
        # Přehrání
        self._api_post("/api/media/play_sound", {
            "file": "speech.wav",
            "volume": 80
        })
        
        return {"text": text, "duration": duration, "animated": animate}
    
    def _speak_animation(self, duration: float, gesture: Optional[str]):
        """Animace během mluvení"""
        start = time.time()
        
        # Počáteční pozice
        self.goto_angles(head_pitch=-0.1, left_antenna=0.2, right_antenna=-0.2, duration=0.5)
        time.sleep(0.5)
        
        # Gesto nebo nodding
        if gesture == "wave":
            self.wave(count=int(duration / 0.6))
        elif gesture == "shake":
            self.shake_head(count=int(duration / 0.7))
        else:
            # Default nodding
            while time.time() - start < duration:
                self.goto_angles(head_pitch=-0.2, duration=0.4)
                time.sleep(0.4)
                if time.time() - start >= duration:
                    break
                self.goto_angles(head_pitch=-0.05, duration=0.4)
                time.sleep(0.4)
        
        # Návrat
        time.sleep(0.3)
        self.reset(duration=1.0)
    
    # ============ Direction of Arrival (DoA) ============
    
    def get_sound_source(self) -> Optional[SoundSource]:
        """
        Získá aktuální detekovaný zvukový zdroj z mikrofonního pole
        Vrací None pokud není detekován žádný zvuk
        """
        try:
            # Zkusíme načíst z WebSocket nebo API
            state = self._api_get("/api/state/full")
            doa = state.get('doa')  # Direction of Arrival
            
            if doa:
                return SoundSource(
                    azimuth=doa.get('azimuth', 0),
                    elevation=doa.get('elevation', 0),
                    confidence=doa.get('confidence', 0.5),
                    timestamp=time.time()
                )
        except:
            pass
        return None
    
    def wait_for_sound(self, timeout: float = 10.0, 
                       min_confidence: float = 0.3) -> Optional[SoundSource]:
        """
        Čeká na zvuk z určitého směru
        
        Args:
            timeout: Kolik sekund čekat
            min_confidence: Minimální jistota detekce (0-1)
            
        Returns:
            SoundSource nebo None pokud timeout
        """
        start = time.time()
        while time.time() - start < timeout:
            source = self.get_sound_source()
            if source and source.confidence >= min_confidence:
                self._last_doa = source
                return source
            time.sleep(0.1)
        return None
    
    def listen_and_respond(self, 
                          response_text: str = "Ano? Slyším tě!",
                          timeout: float = 5.0) -> Optional[SoundSource]:
        """
        Naslouchá, a když uslyší zvuk, podívá se tam a odpoví
        """
        source = self.wait_for_sound(timeout)
        if source:
            self.say(response_text, look_at_source=source)
        return source
    
    # ============ Camera ============
    
    def get_camera_frame(self) -> Optional[np.ndarray]:
        """
        Získá aktuální snímek z kamery
        
        Returns:
            numpy array (BGR formát pro OpenCV) nebo None
        """
        try:
            # Zkusíme snapshot endpoint (pokud existuje)
            r = self._session.get(f"{self.camera_url}/snapshot", timeout=5.0)
            if r.status_code == 200:
                img_array = np.frombuffer(r.content, dtype=np.uint8)
                return cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        except:
            pass
        return None
    
    def start_camera_stream(self, callback: Callable[[np.ndarray], None]):
        """
        Spustí kontinuální stream z kamery (pokud je dostupný)
        """
        def stream_loop():
            while True:
                frame = self.get_camera_frame()
                if frame is not None:
                    callback(frame)
                time.sleep(0.033)  # ~30fps
        
        threading.Thread(target=stream_loop, daemon=True).start()
    
    # ============ High Level Behaviors ============
    
    def greet(self, name: Optional[str] = None):
        """Pozdrav s máváním"""
        text = f"Ahoj {name}!" if name else "Ahoj!"
        self.say(text, gesture="wave")
    
    def react_to_surprise(self):
        """Reakce na překvapení"""
        self.goto_angles(head_pitch=-0.3, body_yaw=0.1, duration=0.3)
        self.wave(count=2, speed=0.2)
        self.say("Ou!", animate=False)
        time.sleep(0.5)
        self.reset()
    
    def think(self, duration: float = 2.0):
        """Dělá, že přemýšlí (nakloní hlavu nahoru)"""
        self.goto_angles(head_pitch=-0.3, head_roll=0.1, duration=0.8)
        time.sleep(duration)
        self.goto_angles(head_pitch=0, head_roll=0, duration=0.5)
    
    def yes_no(self, decision: bool):
        """Ano/ne gesto"""
        if decision:
            self.nod(count=2)
            self.say("Ano", animate=False)
        else:
            self.shake_head(count=2)
            self.say("Ne", animate=False)
    
    def celebrate(self):
        """Oslava - třepení anténkama a kývání"""
        self.say("Juchů!", gesture="wave")
        for i in range(3):
            self.goto_angles(head_pitch=-0.2, head_yaw=-0.2, duration=0.3)
            time.sleep(0.3)
            self.goto_angles(head_pitch=-0.2, head_yaw=0.2, duration=0.3)
            time.sleep(0.3)
        self.reset()
    
    def attention_mode(self, duration: float = 30.0):
        """
        Attention mode - robot sleduje zvuky a na ně reaguje
        """
        start = time.time()
        print(f"🎤 Attention mode - listening for {duration}s...")
        
        while time.time() - start < duration:
            source = self.wait_for_sound(timeout=2.0, min_confidence=0.4)
            if source:
                print(f"  Sound from azimuth={source.azimuth:.1f}°")
                self.look_at_direction(source.azimuth)
                self.tilt_head(Direction.RIGHT if source.azimuth > 0 else Direction.LEFT)
                time.sleep(1.0)
                self.reset(duration=0.8)
        
        print("✓ Attention mode finished")


# CLI rozhraní
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Reachy Mini Full Control")
    parser.add_argument("--host", default="localhost:8000")
    
    sub = parser.add_subparsers(dest="cmd")
    
    # Pohyby
    sub.add_parser("wave", help="Zamávej")
    sub.add_parser("nod", help="Přikyvuj")
    sub.add_parser("shake", help="Zakrout hlavou")
    sub.add_parser("reset", help="Reset pozice")
    sub.add_parser("explore", help="Rozhlédni se")
    
    # Mluvení
    p_speak = sub.add_parser("speak", help="Mluv")
    p_speak.add_argument("text")
    p_speak.add_argument("--gesture", choices=["wave", "nod", "shake"])
    
    # Interakce
    p_listen = sub.add_parser("listen", help="Naslouchej a odpověz")
    p_listen.add_argument("--response", default="Slyšel jsem tě!")
    p_listen.add_argument("--timeout", type=float, default=5.0)
    
    sub.add_parser("attention", help="Sleduj zvuky")
    sub.add_parser("greet", help="Pozdrav")
    sub.add_parser("celebrate", help="Oslavuj")
    
    args = parser.parse_args()
    
    if not args.cmd:
        parser.print_help()
        sys.exit(1)
    
    r = ReachyMiniFull(api_url=f"http://{args.host}")
    
    if not r.is_ready():
        print("❌ Reachy Mini není dostupný")
        sys.exit(1)
    
    print(f"✓ Connected to {args.host}")
    
    if args.cmd == "wave":
        r.wave()
    elif args.cmd == "nod":
        r.nod()
    elif args.cmd == "shake":
        r.shake_head()
    elif args.cmd == "reset":
        r.reset()
    elif args.cmd == "explore":
        r.explore_around()
    elif args.cmd == "speak":
        r.say(args.text, gesture=args.gesture)
    elif args.cmd == "listen":
        source = r.listen_and_respond(args.response, args.timeout)
        if source:
            print(f"  Sound from: {source.azimuth:.1f}°")
    elif args.cmd == "attention":
        r.attention_mode()
    elif args.cmd == "greet":
        r.greet()
    elif args.cmd == "celebrate":
        r.celebrate()
    
    print("✓ Done")
