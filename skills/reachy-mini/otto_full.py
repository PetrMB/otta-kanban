#!/usr/bin/env python3
"""
OTTO Full Integration - Reachy Mini s audiem, kamerou a pohyby
Bez nutnosti desktop aplikace
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / ".openclaw/workspace/skills/reachy-mini"))

from otto_audio import OttoAudio, SoundEvent
from otto_vision import OttoVision, PersonState
from typing import Optional, Callable
import time
import threading


class OttoReachy:
    """
    Kompletní Reachy Mini integrace
    
    Features:
    - Přímé USB motor control (port 8765)
    - Audio DoA (směrové mikrofony)
    - Kamera (face detection)
    - Reakce na zvuky a pohledy
    """
    
    def __init__(self, api_url: str = "http://localhost:8765"):
        self.api_url = api_url
        self.audio = OttoAudio()
        self.vision = OttoVision()
        self._reaction_callbacks: list = []
        self._running = False
        
    def connect(self) -> bool:
        """Připojí se k robotovi"""
        try:
            import requests
            r = requests.get(f"{self.api_url}/api/health", timeout=2)
            if r.status_code == 200:
                print("✓ Connected to Reachy Mini")
                return True
        except:
            pass
        print("✗ Cannot connect to daemon")
        return False
    
    def start_interactive(self):
        """Spustí interaktivní režim"""
        self._running = True
        
        # Start audio
        print("🎤 Starting audio...")
        self.audio.on_sound(self._on_sound)
        self.audio.start()
        
        # Start vision (pokud je dostupná)
        try:
            print("👁️ Starting vision...")
            self.vision.start()
            threading.Thread(target=self._vision_loop, daemon=True).start()
        except Exception as e:
            print(f"⚠️ Vision not available: {e}")
        
        print("\n🤖 OTTO is ready and listening!")
        print("   - Clap to get attention")
        print("   - Speak to trigger response")
        print("   - Show face to get tracking")
    
    def _on_sound(self, event: SoundEvent):
        """Reakce na zvuk"""
        print(f"🎵 Sound from {event.azimuth:.0f}° (intensity: {event.intensity:.2f})")
        
        if event.intensity > 0.5:  # Loud sound
            self._react_to_attention(event)
    
    def _react_to_attention(self, event: SoundEvent):
        """Reaguje na zvuk pozornosti"""
        import requests
        
        # Podívá se směrem zvuku
        yaw = event.azimuth / 180 * 0.5  # map -180..180 to -0.5..0.5
        
        requests.post(f"{self.api_url}/api/move/goto", json={
            "head_pose": {"pitch": -0.1, "yaw": yaw, "roll": 0, "x": 0, "y": 0, "z": 0},
            "body_yaw": 0,
            "antennas": [0.3, -0.3],
            "duration": 0.5
        })
        
        if event.is_speech:
            # Řeč - přikývni
            requests.post(f"{self.api_url}/api/speak", json={
                "text": "Ano? Slyším tě!",
                "animate": True
            })
        else:
            # Jen zvuk - zamávej
            self._wave()
    
    def _vision_loop(self):
        """Background vision processing"""
        import requests
        
        while self._running:
            try:
                state = self.vision.get_state()
                if state.detected and state.face:
                    # Face tracking
                    face = state.face
                    yaw = (face.center_x - 0.5) * 2 * 0.5
                    pitch = (face.center_y - 0.5) * 2 * 0.4
                    
                    requests.post(f"{self.api_url}/api/move/goto", json={
                        "head_pose": {"pitch": pitch, "yaw": yaw, "roll": 0, "x": 0, "y": 0, "z": 0},
                        "body_yaw": 0,
                        "antennas": [0.2, -0.2],
                        "duration": 0.3
                    })
                time.sleep(0.1)
            except:
                time.sleep(0.5)
    
    def _wave(self):
        """Zamávání"""
        import requests
        
        for _ in range(2):
            requests.post(f"{self.api_url}/api/move/goto", json={
                "head_pose": {"pitch": 0, "yaw": 0, "roll": 0, "x": 0, "y": 0, "z": 0},
                "antennas": [0.8, -0.8],
                "duration": 0.3
            })
            time.sleep(0.3)
            requests.post(f"{self.api_url}/api/move/goto", json={
                "head_pose": {"pitch": 0, "yaw": 0, "roll": 0, "x": 0, "y": 0, "z": 0},
                "antennas": [0, 0],
                "duration": 0.3
            })
            time.sleep(0.3)
    
    def say(self, text: str, animate: bool = True):
        """Promluví text"""
        import requests
        requests.post(f"{self.api_url}/api/speak", json={
            "text": text,
            "animate": animate
        })
    
    def stop(self):
        """Zastaví vše"""
        self._running = False
        self.audio.stop()
        self.vision.stop()
        print("✓ Stopped")


# Main
if __name__ == "__main__":
    print("=" * 50)
    print("🤖 OTTO Full Integration")
    print("=" * 50)
    
    otto = OttoReachy()
    
    if not otto.connect():
        print("\n❌ Make sure daemon is running:")
        print("   python3 otto_daemon.py")
        sys.exit(1)
    
    try:
        otto.start_interactive()
        print("\nPress Ctrl+C to stop...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        otto.stop()
        print("\n✓ Goodbye!")
