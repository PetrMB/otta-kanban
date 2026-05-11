#!/usr/bin/env python3
"""
Otto Audio - Direction of Arrival detection pro Reachy Mini
Používá Reachy Mini USB mikrofony (16kHz stereo)
"""

import numpy as np
import time
import threading
from dataclasses import dataclass
from typing import Optional, List, Callable
from enum import Enum


class Direction(Enum):
    """Směry zvuku"""
    LEFT = -1
    CENTER = 0
    RIGHT = 1
    UNKNOWN = None


@dataclass
class SoundEvent:
    """Detekovaný zvuk"""
    azimuth: float      # -180° až 180° (0 = předek)
    elevation: float    # -90° až 90°
    intensity: float    # 0-1
    timestamp: float
    is_speech: bool     # Detekována řeč?


class OttoAudio:
    """
    Audio processing pro Reachy Mini
    
    Využívá stereo mikrofony v Reachy Mini pro:
    - Direction of Arrival (kde je zvuk)
    - VAD (Voice Activity Detection)
    - Reakce na zvuky
    """
    
    def __init__(self, sample_rate: int = 16000, chunk_size: int = 1024):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self._running = False
        self._thread = None
        self._callbacks: List[Callable[[SoundEvent], None]] = []
        self._last_event: Optional[SoundEvent] = None
        self._stream = None
        
        # Thresholdy
        self.energy_threshold = 0.01
        self.speech_threshold = 0.02
        
    def start(self):
        """Spustí audio capture"""
        try:
            import sounddevice as sd
            
            # Najdi Reachy Mini Audio
            devices = sd.query_devices()
            reachy_idx = None
            for i, dev in enumerate(devices):
                if 'Reachy' in str(dev.get('name', '')):
                    reachy_idx = i
                    print(f"✓ Found Reachy Mini Audio at index {i}")
                    break
            
            if reachy_idx is None:
                print("⚠️ Reachy Mini Audio not found, using default")
                reachy_idx = sd.default.device[0]  # default input
            
            self._running = True
            self._stream = sd.InputStream(
                device=reachy_idx,
                channels=2,  # Stereo pro DoA
                samplerate=self.sample_rate,
                blocksize=self.chunk_size,
                callback=self._audio_callback
            )
            self._stream.start()
            
            print("✓ Audio stream started")
            
        except ImportError:
            print("⚠️ sounddevice not available, install: pip install sounddevice")
        except Exception as e:
            print(f"✗ Audio error: {e}")
    
    def stop(self):
        """Zastaví audio"""
        self._running = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
    
    def _audio_callback(self, indata, frames, time_info, status):
        """Callback pro audio data"""
        if status:
            print(f"Audio status: {status}")
        
        # Stereo data - left a right kanál
        left = indata[:, 0]
        right = indata[:, 1]
        
        # Energie
        left_energy = np.sqrt(np.mean(left**2))
        right_energy = np.sqrt(np.mean(right**2))
        
        # Celková energie
        total_energy = (left_energy + right_energy) / 2
        
        if total_energy > self.energy_threshold:
            # Direction of Arrival pomocí time delay (simplified)
            # V reálném by se použil GCC-PHAT algoritmus
            
            # Poměr energie mezi kanály
            if right_energy > left_energy * 1.5:
                direction = Direction.RIGHT
                azimuth = 45.0  # pravá strana
            elif left_energy > right_energy * 1.5:
                direction = Direction.LEFT
                azimuth = -45.0  # levá strana
            else:
                direction = Direction.CENTER
                azimuth = 0.0
            
            # Detekce řeče (jednoduchá)
            is_speech = total_energy > self.speech_threshold
            
            event = SoundEvent(
                azimuth=azimuth,
                elevation=0.0,
                intensity=min(total_energy * 10, 1.0),
                timestamp=time.time(),
                is_speech=is_speech
            )
            
            self._last_event = event
            
            # Call callbacks
            for cb in self._callbacks:
                try:
                    cb(event)
                except:
                    pass
    
    def on_sound(self, callback: Callable[[SoundEvent], None]):
        """Registruje callback pro zvukové události"""
        self._callbacks.append(callback)
    
    def get_last_event(self) -> Optional[SoundEvent]:
        """Vrátí poslední zvukovou událost"""
        return self._last_event
    
    def wait_for_sound(self, timeout: float = 5.0, 
                       min_intensity: float = 0.1) -> Optional[SoundEvent]:
        """Čeká na zvuk"""
        start = time.time()
        while time.time() - start < timeout:
            if self._last_event and self._last_event.intensity >= min_intensity:
                return self._last_event
            time.sleep(0.05)
        return None
    
    def get_direction_text(self) -> str:
        """Vrátí směr jako text"""
        if not self._last_event:
            return "No sound detected"
        
        az = self._last_event.azimuth
        if az < -30:
            return "Left"
        elif az > 30:
            return "Right"
        else:
            return "Center"


# Demo
if __name__ == "__main__":
    print("Otto Audio Demo - clap your hands!")
    
    audio = OttoAudio()
    
    def on_sound(event):
        direction = "← LEFT" if event.azimuth < -30 else "→ RIGHT" if event.azimuth > 30 else "↑ CENTER"
        speech = "🗣️ SPEECH" if event.is_speech else "🔊 SOUND"
        print(f"{speech} from {direction} (intensity: {event.intensity:.2f})")
    
    audio.on_sound(on_sound)
    
    try:
        audio.start()
        print("\nListening... (Ctrl+C to stop)")
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        audio.stop()
        print("\n✓ Stopped")
