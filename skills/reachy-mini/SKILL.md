# Reachy Mini Control

Skill pro ovládání Reachy Mini humanoidního robota od Pollen Robotics.

## Capabilities

- 🤖 Připojení k robotovi (USB/WiFi)
- 🎮 Ovládání pozice hlavy, těla a antén
- 📊 Čtení aktuálního stavu robotů
- 📹 Přístup ke kameře (WebRTC/WebSocket)
- 🔊 Audio (Direction of Arrival)
- 🛡️ Bezpečnostní limity (automatické ořezávání)

## Architektura

Robot komunikuje přes FastAPI daemon:
- **REST API**: `http://localhost:8000`
- **WebSocket stav**: `ws://localhost:8000/api/state/ws/full`
- **WebRTC kamera**: `http://localhost:8443`
- **Zenoh pub/sub**: `reachy_mini/*`

## Motor IDs

| Motor | ID | Typ | Pozice |
|-------|-----|-----|--------|
| body_rotation | 10 | XC330-M288-PG | Základna (yaw) |
| stewart_1-6 | 11-16 | XL330-M288-T | Stewart platforma |
| right_antenna | 17 | XL330-M077-T | Pravá anténa |
| left_antenna | 18 | XL330-M077-T | Levá anténa |

## Bezpečnostní limity

- Body Yaw: [-180°, 180°]
- Head Pitch/Roll: [-40°, 40°]
- Head Yaw: [-180°, 180°]
- Body-Head Yaw rozdíl: [-65°, 65°]

## Příkazy

### Připojení
```bash
# USB (Reachy Mini Lite)
reachy-mini connect usb

# WiFi (Reachy Mini Wireless)
reachy-mini connect wifi --ip 10.42.0.1

# Kontrola stavu připojení
reachy-mini status
```

### Ovládání pozice
```bash
# Nastavit pozici hlavy (yaw, pitch, roll ve stupních)
reachy-mini head set --yaw 0 --pitch 15 --roll 0

# Nastavit rotaci těla
reachy-mini body set --yaw 45

# Nastavit antény (0-180°)
reachy-mini antenna left set --angle 90
reachy-mini antenna right set --angle 45

# Vrátit do výchozí pozice
reachy-mini reset
```

### Čtení stavu
```bash
# Aktuální pozice všech motorů
reachy-mini state

# Stream stavu (WebSocket)
reachy-mini state --stream

# Teplota motorů
reachy-mini temperature
```

### Kamera a audio
```bash
# URL pro WebRTC připojení
reachy-mini camera url

# Screenshot z kamery
reachy-mini camera screenshot

# DoA audio vizualizace
reachy-mini audio direction
```

### Choreografie
```bash
# Seznam dostupných choreografií
reachy-mini choreo list

# Přehrát choreografii
reachy-mini choreo play --name hello

# Zastavit
reachy-mini stop
```

## Python API

```python
from reachy_mini_control import ReachyMini

robot = ReachyMini()
robot.connect()

# Nastavit pozici hlavy
robot.head.set_orientation(yaw=0, pitch=15, roll=0)

# Číst stav
state = robot.get_state()
print(state.head.position)

# Vrátit do výchozí pozice
robot.reset()
```

## Poznámky

- Wireless verze: RPi 4, WiFi hotspot `reachy-mini-ap` / heslo `reachy-mini`
- Lite verze: USB-C připojení k PC
- Kamera: Sony IMX708 12MP, 1920x1080@30fps
- Audio: ReSpeaker 4-mic array, DoA detekce
- WebRTC H.264 Level 3.1 (kompatibilita se Safari/Tauri)

## Instalace

```bash
pip install reachy-mini
```

Daemon se spouští automaticky při připojení robota.