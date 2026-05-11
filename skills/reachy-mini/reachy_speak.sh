#!/bin/bash
# Reachy Mini Speak - TTS s doprovodným pohybem hlavy

TEXT="${1:-Ahoj, já jsem Reachy Mini}"
VOICE="${2:-Zuzana}"
VOLUME="${3:-80}"

# Cleanup
tmpdir=$(mktemp -d)
trap "rm -rf $tmpdir" EXIT

aiff_file="$tmpdir/tts.aiff"
wav_file="$tmpdir/tts.wav"

echo "🎙️ Generating TTS: '$TEXT'"

# 1. Generace TTS
say -v "$VOICE" "$TEXT" -o "$aiff_file"
afconvert "$aiff_file" "$wav_file" -f WAVE -d LEI16@44100

# 2. Získání délky zvuku v sekundách (aproximativně z velikosti)
# 16bit 44.1kHz mono = ~88.2KB/s, stereo = ~176.4KB/s
filesize=$(stat -f%z "$wav_file" 2>/dev/null || stat -c%s "$wav_file")
duration=$(echo "scale=1; ($filesize - 44) / 176400" | bc)  # odecteme WAV header
if [ "$duration" = "0" ]; then duration=1; fi
echo "⏱️ Estimated duration: ${duration}s"

# 3. Nahraj zvuk
echo "📤 Uploading..."
curl -s -X POST http://localhost:8000/api/media/sounds/upload \
    -F "file=@$wav_file" \
    -H "Content-Type: multipart/form-data" > /dev/null

# 4. Pohni hlavou do "mluvení" pozice (dopředu a lehce nahoru)
echo "🤖 Moving head to speaking position..."
curl -s -X POST http://localhost:8000/api/move/goto \
    -H "Content-Type: application/json" \
    -d "{
        \"head_pose\": {\"x\": 0.005, \"y\": 0, \"z\": 0.005, \"roll\": 0.02, \"pitch\": -0.15, \"yaw\": 0},
        \"body_yaw\": 0,
        \"antennas\": [0.2, -0.2],
        \"duration\": 0.5,
        \"interpolation\": \"ease_in_out\"
    }" > /dev/null

# 5. Během čekání na pohyb, začni přehrávat
echo "🔊 Speaking..."
curl -s -X POST http://localhost:8000/api/media/play_sound \
    -H "Content-Type: application/json" \
    -d "{\"file\": \"tts.wav\", \"volume\": $VOLUME}" > /dev/null

# 6. Během mluvení - jemné pohyby hlavy (nodding)
sleep 0.3
echo "👋 Gesturing during speech..."

# Malé pohyby hlavy během mluvení - každých 0.5s
total_wait=0
while [ $total_wait -lt ${duration%.*} ]; do
    # Náhodný malý pohyb
    pitch=$(python3 -c "import random; print(f'{random.uniform(-0.1, -0.2):.3f}')")
    yaw=$(python3 -c "import random; print(f'{random.uniform(-0.05, 0.05):.3f}')")
    
    curl -s -X POST http://localhost:8000/api/move/goto \
        -H "Content-Type: application/json" \
        -d "{
            \"head_pose\": {\"x\": 0.005, \"y\": 0, \"z\": 0.005, \"roll\": 0.02, \"pitch\": $pitch, \"yaw\": $yaw},
            \"body_yaw\": 0,
            \"antennas\": [0.3, -0.3],
            \"duration\": 0.3,
            \"interpolation\": \"minjerk\"
        }" > /dev/null
    
    sleep 0.4
    total_wait=$((total_wait + 1))
done

# 7. Vrať do výchozí pozice
echo "😐 Returning to neutral..."
curl -s -X POST http://localhost:8000/api/move/goto \
    -H "Content-Type: application/json" \
    -d '{
        "head_pose": {"x": 0, "y": 0, "z": 0, "roll": 0, "pitch": 0, "yaw": 0},
        "body_yaw": 0,
        "antennas": [0, 0],
        "duration": 1.0,
        "interpolation": "ease_in_out"
    }' > /dev/null

echo "✓ Done speaking!"