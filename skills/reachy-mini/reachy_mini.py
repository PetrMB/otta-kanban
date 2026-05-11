#!/usr/bin/env python3
"""
Reachy Mini Skill - Simple Python API pro Reachy Mini
Bez daemonu, přímé volání HTTP API původního daemonu na :8000
"""

import json
import time
import tempfile
import subprocess
import threading
from pathlib import Path
from typing import Optional, List
import requests


class ReachyMini:
    """Simple API pro Reachy Mini robot"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self._animating = False
        
    def _post(self, endpoint: str, data: dict, timeout: float = 10.0) -> dict:
        """POST request k daemonu"""
        r = requests.post(f"{self.base_url}{endpoint}", json=data, timeout=timeout)
        r.raise_for_status()
        return r.json()
    
    def _get(self, endpoint: str, timeout: float = 5.0) -> dict:
        """GET request k daemonu"""
        r = requests.get(f"{self.base_url}{endpoint}", timeout=timeout)
        r.raise_for_status()
        return r.json()
    
    # ============ Základní pohyby ============
    
    def goto(self, 
             head_pitch: Optional[float] = None,
             head_yaw: Optional[float] = None, 
             head_roll: Optional[float] = None,
             body_yaw: Optional[float] = None,
             left_antenna: Optional[float] = None,
             right_antenna: Optional[float] = None,
             duration: float = 1.0) -> dict:
        """
        Pohyb na cílovou pozici.
        
        Args:
            head_pitch: -0.4 (nahoru) až 0.4 (dolu)
            head_yaw: -0.5 (vlevo) až 0.5 (vpravo)
            body_yaw: -3.14 až 3.14 (radiány)
            antennas: [-0.8, 0.8] (vlevo, vpravo)
            duration: délka pohybu v sekundách
        """
        head_pose = {
            "x": 0, "y": 0, "z": 0,
            "roll": head_roll or 0,
            "pitch": head_pitch or 0, 
            "yaw": head_yaw or 0
        }
        
        antennas = [0, 0]
        if left_antenna is not None:
            antennas[0] = left_antenna
        if right_antenna is not None:
            antennas[1] = right_antenna
            
        return self._post("/api/move/goto", {
            "head_pose": head_pose,
            "body_yaw": body_yaw or 0,
            "antennas": antennas,
            "duration": duration,
            "interpolation": "minjerk"
        })
    
    def reset(self, duration: float = 2.0) -> dict:
        """Vrátí robota do výchozí pozice"""
        return self.goto(
            head_pitch=0, head_yaw=0, head_roll=0,
            body_yaw=0, left_antenna=0, right_antenna=0,
            duration=duration
        )
    
    # ============ Přednastavené pohyby ============
    
    def wave(self, count: int = 3, speed: float = 0.3) -> dict:
        """Zamávání anténkama"""
        for i in range(count):
            self.goto(left_antenna=0.8, right_antenna=-0.8, duration=speed)
            time.sleep(speed)
            self.goto(left_antenna=0, right_antenna=0, duration=speed)
            time.sleep(speed)
        return {"gesture": "wave", "count": count}
    
    def nod(self, count: int = 2, speed: float = 0.5) -> dict:
        """Přikyvování hlavou"""
        for i in range(count):
            self.goto(head_pitch=-0.2, duration=speed)
            time.sleep(speed)
            self.goto(head_pitch=0.1, duration=speed)
            time.sleep(speed)
        self.goto(head_pitch=0, duration=speed)
        return {"gesture": "nod", "count": count}
    
    def shake(self, count: int = 2, speed: float = 0.4) -> dict:
        """Zakroutení hlavou (body_yaw)"""
        for i in range(count):
            self.goto(body_yaw=0.3, duration=speed)
            time.sleep(speed)
            self.goto(body_yaw=-0.3, duration=speed)
            time.sleep(speed)
        self.goto(body_yaw=0, duration=speed)
        return {"gesture": "shake", "count": count}
    
    def look_around(self) -> dict:
        """Rozhlédne se do všech stran"""
        self.goto(head_yaw=-0.4, duration=1.0)
        time.sleep(1.0)
        self.goto(head_yaw=0.4, duration=1.0)
        time.sleep(1.0)
        self.goto(head_yaw=0, head_pitch=-0.2, duration=1.0)
        time.sleep(1.0)
        self.reset()
        return {"gesture": "look_around"}
    
    # ============ TTS s animací ============
    
    def speak(self, text: str, voice: str = "Zuzana", 
              animate: bool = True, gesture: Optional[str] = None) -> dict:
        """
        Přečte text nahlas s doprovodným pohybem.
        
        Args:
            text: text k přečtení
            voice: macOS voice (Zuzana=čeština, Samantha=angličtina)
            animate: True = pohyb hlavy během mluvení
            gesture: "wave", "nod", "shake" nebo None
        """
        # 1. Vygeneruj TTS
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
            
            # 2. Nahraj zvuk na Reachy
            with open(wav, "rb") as f:
                upload = requests.post(
                    f"{self.base_url}/api/media/sounds/upload",
                    files={"file": f},
                    timeout=10.0
                )
            upload.raise_for_status()
        
        # 3. Odhad délky
        duration = len(text) * 0.09
        
        # 4. Animace na pozadí
        if animate:
            self._animate_speech(duration, gesture)
        
        # 5. Přehrání
        requests.post(
            f"{self.base_url}/api/media/play_sound",
            json={"file": "speech.wav", "volume": 80},
            timeout=5.0
        )
        
        return {
            "status": "ok",
            "text": text,
            "voice": voice,
            "duration": duration,
            "animated": animate
        }
    
    def _animate_speech(self, duration: float, gesture: Optional[str]):
        """Animace během mluvení v background threadu"""
        def animate():
            # Pohyb do mluvení pozice
            self.goto(head_pitch=-0.15, body_yaw=0.05, 
                     left_antenna=0.3, right_antenna=-0.3, 
                     duration=0.5)
            time.sleep(0.5)
            
            # Gesto nebo default nodding
            start = time.time()
            if gesture == "wave":
                self.wave(count=int(duration/0.6), speed=0.3)
            elif gesture == "nod":
                while time.time() - start < duration:
                    self.goto(head_pitch=-0.2, duration=0.4)
                    time.sleep(0.4)
                    self.goto(head_pitch=0, duration=0.4)
                    time.sleep(0.4)
            elif gesture == "shake":
                self.shake(count=int(duration/0.8), speed=0.4)
            else:
                # Default: jemné pohyby
                while time.time() - start < duration:
                    self.goto(head_pitch=-0.15 + 0.05, 
                             head_yaw=0.05,
                             duration=0.3)
                    time.sleep(0.4)
            
            # Návrat
            time.sleep(0.5)
            self.reset(duration=1.0)
        
        threading.Thread(target=animate, daemon=True).start()
    
    # ============ Info ============
    
    def state(self) -> dict:
        """Vrátí aktuální stav robota"""
        return self._get("/api/state/full")
    
    def is_ready(self) -> bool:
        """Kontrola zda je robot připraven"""
        try:
            r = requests.get(f"{self.base_url}/api/health", timeout=2.0)
            return r.status_code == 200
        except:
            return False


# Jednoduché použití:
# from reachy_mini import ReachyMini
# reachy = ReachyMini()
# reachy.speak("Ahoj Petře!")
# reachy.wave()

if __name__ == "__main__":
    # Demo
    r = ReachyMini()
    print("Reachy Mini Skill Demo")
    print(f"Ready: {r.is_ready()}")
    
    if r.is_ready():
        print("\n1. Mávání...")
        r.wave(count=2)
        
        print("\n2. Mluvení...")
        r.speak("Ahoj, já jsem Reachy Mini a umím mluvit i se hýbat!")
        
        print("\n3. Reset...")
        r.reset()
        
        print("\nDone!")
