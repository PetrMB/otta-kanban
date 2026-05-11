#!/usr/bin/env python3
"""
Reachy Mini TTS Daemon - Rozšíření existujícího daemonu o TTS s animací
Nepotřebuje USB přístup, komunikuje s daemonem na :8000 přes HTTP API
"""

import asyncio
import json
import time
import tempfile
import subprocess
import threading
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn


class TTSRequest(BaseModel):
    text: str
    voice: str = "Zuzana"  # macOS voice
    volume: int = 80
    animate: bool = True
    gesture: Optional[str] = None  # "wave", "nod", "shake"


class SimpleMove(BaseModel):
    head_pitch: Optional[float] = None
    head_yaw: Optional[float] = None
    body_yaw: Optional[float] = None
    antennas: Optional[list] = None
    duration: float = 1.0


# Configuration
ORIGINAL_DAEMON = "http://localhost:8000"
TTS_PORT = 8765

app = FastAPI(
    title="Reachy Mini TTS Extension",
    description="TTS s animací pro Reachy Mini - rozšíření stávajícího daemonu",
    version="0.3.0"
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"])


async def check_original_daemon():
    """Kontrola zda běží původní daemon"""
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{ORIGINAL_DAEMON}/api/health", timeout=2.0)
            return r.status_code == 200
    except:
        return False


async def move_head_for_speaking(duration: float):
    """Pohyb hlavy do mluvení pozice"""
    try:
        async with httpx.AsyncClient() as client:
            # Pohyb dopředu a lehce nahoru
            await client.post(
                f"{ORIGINAL_DAEMON}/api/move/goto",
                json={
                    "head_pose": {"x": 0.005, "y": 0, "z": 0.005, "roll": 0, "pitch": -0.1, "yaw": 0},
                    "body_yaw": 0.05,
                    "antennas": [0.3, -0.3],
                    "duration": 0.5,
                    "interpolation": "ease_in_out"
                },
                timeout=5.0
            )
    except Exception as e:
        print(f"Move error: {e}")


async def return_to_neutral():
    """Návrat do neutrální pozice"""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{ORIGINAL_DAEMON}/api/move/goto",
                json={
                    "head_pose": {"x": 0, "y": 0, "z": 0, "roll": 0, "pitch": 0, "yaw": 0},
                    "body_yaw": 0,
                    "antennas": [0, 0],
                    "duration": 1.0,
                    "interpolation": "ease_in_out"
                },
                timeout=5.0
            )
    except Exception as e:
        print(f"Return error: {e}")


async def gesture_during_speech(gesture: str, duration: float):
    """Gesto během mluvení"""
    try:
        async with httpx.AsyncClient() as client:
            if gesture == "wave":
                # Mávání anténkama
                for _ in range(3):
                    await client.post(
                        f"{ORIGINAL_DAEMON}/api/move/goto",
                        json={
                            "head_pose": {"x": 0, "y": 0, "z": 0, "roll": 0, "pitch": -0.1, "yaw": 0},
                            "body_yaw": 0,
                            "antennas": [0.8, -0.8],
                            "duration": 0.3,
                            "interpolation": "minjerk"
                        },
                        timeout=3.0
                    )
                    await asyncio.sleep(0.3)
                    await client.post(
                        f"{ORIGINAL_DAEMON}/api/move/goto",
                        json={
                            "head_pose": {"x": 0, "y": 0, "z": 0, "roll": 0, "pitch": -0.1, "yaw": 0},
                            "body_yaw": 0,
                            "antennas": [0, 0],
                            "duration": 0.3,
                            "interpolation": "minjerk"
                        },
                        timeout=3.0
                    )
                    await asyncio.sleep(0.3)
            
            elif gesture == "nod":
                # Přikyvování během mluvení
                start = time.time()
                while time.time() - start < duration:
                    await client.post(
                        f"{ORIGINAL_DAEMON}/api/move/goto",
                        json={
                            "head_pose": {"x": 0, "y": 0, "z": 0, "roll": 0, "pitch": -0.2, "yaw": 0},
                            "body_yaw": 0,
                            "antennas": [0.2, -0.2],
                            "duration": 0.4,
                            "interpolation": "minjerk"
                        },
                        timeout=3.0
                    )
                    await asyncio.sleep(0.4)
                    await client.post(
                        f"{ORIGINAL_DAEMON}/api/move/goto",
                        json={
                            "head_pose": {"x": 0, "y": 0, "z": 0, "roll": 0, "pitch": 0, "yaw": 0},
                            "body_yaw": 0,
                            "antennas": [0.2, -0.2],
                            "duration": 0.4,
                            "interpolation": "minjerk"
                        },
                        timeout=3.0
                    )
                    await asyncio.sleep(0.4)
    except Exception as e:
        print(f"Gesture error: {e}")


def generate_tts(text: str, voice: str) -> Path:
    """Generuje TTS pomocí macOS say"""
    with tempfile.TemporaryDirectory() as tmpdir:
        aiff_path = Path(tmpdir) / "speech.aiff"
        wav_path = Path(tmpdir) / "speech.wav"
        
        # Generace
        subprocess.run(
            ["say", "-v", voice, text, "-o", str(aiff_path)],
            capture_output=True, check=True
        )
        
        # Konverze na WAV 44.1kHz 16bit
        subprocess.run(
            ["afconvert", str(aiff_path), str(wav_path), "-f", "WAVE", "-d", "LEI16@44100"],
            capture_output=True, check=True
        )
        
        # Copy to persistent location for upload
        persistent = Path("/tmp/reachy_tts_speech.wav")
        wav_path.replace(persistent)
        
        return persistent


def get_audio_duration(text: str) -> float:
    """Odhad délky zvuku z textu"""
    # ~80-100ms na znak pro češtinu
    return max(len(text) * 0.09, 1.0)


@app.get("/api/health")
async def health():
    """Health check"""
    original_ok = await check_original_daemon()
    return {
        "status": "ok",
        "tts_daemon": "running",
        "original_daemon_connected": original_ok,
        "original_daemon_url": ORIGINAL_DAEMON,
        "features": ["tts", "animation", "gestures"]
    }


@app.post("/api/speak")
async def speak(req: TTSRequest, background_tasks: BackgroundTasks):
    """
    TTS s animací
    - Generuje zvuk přes macOS say
    - Přehraje přes původní daemon
    - Animuje hlavu během mluvení
    """
    # Kontrola původního daemonu
    if not await check_original_daemon():
        raise HTTPException(status_code=503, detail="Original daemon not available")
    
    # Odhad délky
    duration = get_audio_duration(req.text)
    
    # Generace TTS (sync - rychlé)
    try:
        wav_path = generate_tts(req.text, req.voice)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {e}")
    
    # Upload zvuku na původní daemon
    try:
        async with httpx.AsyncClient() as client:
            with open(wav_path, "rb") as f:
                upload = await client.post(
                    f"{ORIGINAL_DAEMON}/api/media/sounds/upload",
                    files={"file": ("speech.wav", f, "audio/wav")},
                    timeout=10.0
                )
            if upload.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Upload failed: {upload.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload error: {e}")
    
    # Pohyb do mluvení pozice (async, nečekáme)
    asyncio.create_task(move_head_for_speaking(duration))
    
    # Gesto na pozadí
    if req.gesture:
        asyncio.create_task(gesture_during_speech(req.gesture, duration))
    elif req.animate:
        # Default nodding
        asyncio.create_task(gesture_during_speech("nod", duration))
    
    # Přehrání zvuku
    try:
        async with httpx.AsyncClient() as client:
            play = await client.post(
                f"{ORIGINAL_DAEMON}/api/media/play_sound",
                json={"file": "speech.wav", "volume": req.volume},
                timeout=5.0
            )
    except Exception as e:
        print(f"Playback warning: {e}")
    
    # Návrat do neutrální pozice po skončení
    async def delayed_return():
        await asyncio.sleep(duration + 0.5)
        await return_to_neutral()
    
    asyncio.create_task(delayed_return())
    
    return {
        "status": "ok",
        "text": req.text,
        "voice": req.voice,
        "estimated_duration": duration,
        "animation": req.animate,
        "gesture": req.gesture
    }


@app.get("/api/speak/quick")
async def quick_speak(text: str, voice: str = "Zuzana", animate: bool = True):
    """Rychlý TTS přes GET (pro jednoduché použití)"""
    req = TTSRequest(text=text, voice=voice, animate=animate)
    return await speak(req, None)


@app.post("/api/move/direct")
async def direct_move(req: SimpleMove):
    """Přímý pohyb přes originální daemon"""
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{ORIGINAL_DAEMON}/api/move/goto",
                json={
                    "head_pose": {
                        "x": 0, "y": 0, "z": 0,
                        "roll": 0,
                        "pitch": req.head_pitch or 0,
                        "yaw": req.head_yaw or 0
                    },
                    "body_yaw": req.body_yaw or 0,
                    "antennas": req.antennas or [0, 0],
                    "duration": req.duration,
                    "interpolation": "minjerk"
                },
                timeout=5.0
            )
            return {"status": "ok", "original_response": r.json()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/state")
async def get_state():
    """Proxy pro stav z původního daemonu"""
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{ORIGINAL_DAEMON}/api/state/full", timeout=5.0)
            return r.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Cannot reach original daemon: {e}")


def main():
    print("=" * 60)
    print("🎙️ Reachy Mini TTS Extension v0.3.0")
    print("=" * 60)
    print(f"TTS API:     http://localhost:{TTS_PORT}/api/speak")
    print(f"Quick TTS:   http://localhost:{TTS_PORT}/api/speak/quick?text=Ahoj")
    print(f"Health:      http://localhost:{TTS_PORT}/api/health")
    print(f"Proxy state: http://localhost:{TTS_PORT}/api/state")
    print("-" * 60)
    print(f"Original daemon: {ORIGINAL_DAEMON}")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=TTS_PORT, log_level="warning")


if __name__ == "__main__":
    main()
