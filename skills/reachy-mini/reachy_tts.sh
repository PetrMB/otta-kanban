#!/bin/bash
# Reachy Mini TTS - text-to-speech přes macOS say + Reachy repro

TEXT="${1:-Ahoj, já jsem Reachy Mini}"
VOICE="${2:-Zuzana}"  # Zuzana (Czech), Samantha (English), etc.
VOLUME="${3:-80}"

# Cleanup
tmpdir=$(mktemp -d)
trap "rm -rf $tmpdir" EXIT

aiff_file="$tmpdir/tts.aiff"
wav_file="$tmpdir/tts.wav"

echo "🎙️ Generating TTS: '$TEXT'"

# 1. Generace přes macOS say
if ! say -v "$VOICE" "$TEXT" -o "$aiff_file" 2>/dev/null; then
    echo "❌ Failed to generate TTS with voice '$VOICE'"
    echo "Available voices: say -v '?' | head -20"
    exit 1
fi

# 2. Konverze na WAV (44.1kHz 16bit - kompatibilní s Reachy)
if ! afconvert "$aiff_file" "$wav_file" -f WAVE -d LEI16@44100 2>/dev/null; then
    echo "❌ Failed to convert to WAV"
    exit 1
fi

# 3. Upload na Reachy
echo "📤 Uploading to Reachy Mini..."
upload_result=$(curl -s -X POST http://localhost:8000/api/media/sounds/upload \
    -F "file=@$wav_file" \
    -H "Content-Type: multipart/form-data")

if echo "$upload_result" | grep -q "error\|Error"; then
    echo "❌ Upload failed: $upload_result"
    exit 1
fi

echo "✓ Uploaded"

# 4. Přehrání
echo "🔊 Playing..."
play_result=$(curl -s -X POST http://localhost:8000/api/media/play_sound \
    -H "Content-Type: application/json" \
    -d "{\"file\": \"tts.wav\", \"volume\": $VOLUME}")

if echo "$play_result" | grep -q '"status": "ok"'; then
    echo "✓ Playing on Reachy Mini!"
else
    echo "❌ Playback failed: $play_result"
    exit 1
fi