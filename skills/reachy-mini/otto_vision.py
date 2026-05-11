#!/usr/bin/env python3
"""
Otto Vision - Simple face detection using OpenCV
Bez mediapipe - používá OpenCV's Haar Cascades
"""

import cv2
import numpy as np
import time
from dataclasses import dataclass
from typing import Optional, List, Tuple
import threading


@dataclass
class FaceResult:
    """Detekovaná tvář"""
    x: int
    y: int
    width: int
    height: int
    confidence: float
    center_x: float  # Normalizované x (0-1)
    center_y: float  # Normalizované y (0-1)


@dataclass
class PersonState:
    """Stav detekce člověka"""
    detected: bool
    face: Optional[FaceResult] = None
    seen_seconds: int = 0
    last_seen: float = 0


class OttoVision:
    """
    Simple face detection pro Reachy Mini
    
    Používá OpenCV Haar Cascades - žádné mediapipe!
    """

    def __init__(self, cascade_path: Optional[str] = None):
        """
        Inicializuje detektor tváří
        
        Args:
            cascade_path: Cesta k haarcascade_frontalface_default.xml
                         Pokud None, použije OpenCV default
        """
        self.face_cascade = cv2.CascadeClassifier(
            cascade_path or cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self._camera = None
        self._running = False
        self._thread = None
        self._state = PersonState(detected=False)
        self._last_detection = 0
        self._detection_interval = 0.5  # seconds

    def start(self, camera_index: int = 0, resolution: Tuple[int, int] = (640, 480)):
        """
        Spustí video stream a detekci
        """
        self._camera = cv2.VideoCapture(camera_index)
        if not self._camera.isOpened():
            raise RuntimeError("Cannot open camera")
        
        self._camera.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
        self._camera.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
        
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Zastaví detekci"""
        self._running = False
        if self._camera:
            self._camera.release()
        if self._thread:
            self._thread.join(timeout=1.0)

    def _loop(self):
        """Background detection loop"""
        while self._running:
            try:
                ret, frame = self._camera.read()
                if not ret:
                    continue
                
                # Downscale pro rychlost
                scale = 0.5
                small = cv2.resize(frame, None, fx=scale, fy=scale)
                gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
                
                # Detect faces
                faces = self.face_cascade.detectMultiScale(
                    gray, 
                    scaleFactor=1.3, 
                    minNeighbors=5,
                    minSize=(30, 30)
                )
                
                current_time = time.time()
                
                if len(faces) > 0 and current_time - self._last_detection >= self._detection_interval:
                    # Najdi největší tvář
                    largest = max(faces, key=lambda f: f[2] * f[3])
                    x, y, w, h = largest
                    
                    # Zvětši bbox o 20%
                    padding = 20
                    x = max(0, x - padding)
                    y = max(0, y - padding)
                    w = min(gray.shape[1] - x, w + 2 * padding)
                    h = min(gray.shape[0] - y, h + 2 * padding)
                    
                    self._state = PersonState(
                        detected=True,
                        face=FaceResult(
                            x=x,
                            y=y,
                            width=w,
                            height=h,
                            confidence=1.0,
                            center_x=(x + w/2) / gray.shape[1],
                            center_y=(y + h/2) / gray.shape[0]
                        ),
                        seen_seconds=int(current_time - self._state.last_seen) if self._state.detected else 0,
                        last_seen=current_time
                    )
                    self._last_detection = current_time
                    
                elif len(faces) == 0 and self._state.detected:
                    # Reset po 2 sekundách neviditelnosti
                    if current_time - self._state.last_seen > 2.0:
                        self._state = PersonState(detected=False, last_seen=0)
                
                time.sleep(0.1)  # 10 FPS
                
            except Exception as e:
                print(f"Vision error: {e}")
                time.sleep(0.5)

    def get_state(self) -> PersonState:
        """Vrátí aktuální stav detekce"""
        return self._state

    def is_near(self, threshold: float = 0.2) -> bool:
        """
        Zjistí zda je člověk blízko (tvář v centru obrazu)
        
        Args:
            threshold: Max vzdálenost od středu (0-1)
        """
        if not self._state.detected:
            return False
        
        face = self._state.face
        if not face:
            return False
        
        # Vzdálenost od středu
        dx = abs(face.center_x - 0.5)
        dy = abs(face.center_y - 0.5)
        distance = max(dx, dy)
        
        return distance < threshold

    def look_at_face(self, robot) -> bool:
        """
        Nastaví robota aby se díval na detekovanou tvář
        
        Returns: True pokud bylo provedeno posunutí
        """
        if not self._state.detected or not self._state.face:
            return False
        
        face = self._state.face
        
        # Mapování polohy na yaw/pitch
        # center_x=0.5 -> yaw=0, center_x=0 -> yaw=-0.5, center_x=1 -> yaw=0.5
        yaw = (face.center_x - 0.5) * 2.0 * 0.5  # scale to -0.5 až 0.5
        
        # center_y=0.5 -> pitch=0, center_y=0 -> pitch=-0.4 (nahoru)
        pitch = (face.center_y - 0.5) * 2.0 * 0.4
        
        # Omezení
        yaw = np.clip(yaw, -0.5, 0.5)
        pitch = np.clip(pitch, -0.4, 0.4)
        
        print(f"Looking at face: yaw={yaw:.2f}, pitch={pitch:.2f}")
        
        try:
            robot.goto_angles(head_yaw=yaw, head_pitch=pitch, duration=1.0)
            return True
        except Exception as e:
            print(f"Look error: {e}")
            return False


# Demo
if __name__ == "__main__":
    print("Otto Vision Demo - čeká na tvář...")
    
    vision = OttoVision()
    
    # Try to find camera
    try:
        vision.start()
        print("✓ Camera started")
    except RuntimeError as e:
        print(f"✗ Camera error: {e}")
        print("  Try: python3 -c 'import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())'")
        exit(1)
    
    try:
        while True:
            state = vision.get_state()
            if state.detected:
                f = state.face
                print(f"❤️  FACE DETECTED at ({f.center_x:.2f}, {f.center_y:.2f})")
                if vision.is_near(threshold=0.15):
                    print("  → Person is NEAR (center of frame)")
            else:
                print(f"  Waiting... ({vision._state.seen_seconds}s)")
            
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass
    finally:
        vision.stop()
        print("\n✓ Stopped")