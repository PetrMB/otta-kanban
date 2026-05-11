#!/bin/bash
# Reachy Mini CLI wrapper pro OpenClaw

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/reachy_mini_control.py"

# Kontrola Python závislostí
check_deps() {
    if ! python3 -c "import requests" 2>/dev/null; then
        echo "Installing required dependencies..."
        pip3 install requests websockets --quiet
    fi
}

# Main command handler
case "$1" in
    "install-deps")
        echo "Installing Reachy Mini dependencies..."
        pip3 install requests websockets --user
        ;;
    "check")
        # Kontrola dostupnosti API
        if curl -s http://localhost:8000/api/health >/dev/null 2>&1; then
            echo "✓ Reachy Mini daemon is running at localhost:8000"
            curl -s http://localhost:8000/api/health | python3 -m json.tool 2>/dev/null || true
        else
            echo "✗ Reachy Mini daemon not found at localhost:8000"
            echo "  Make sure the robot is connected and daemon is running."
            exit 1
        fi
        ;;
    "status")
        check_deps
        python3 "$PYTHON_SCRIPT" status
        ;;
    "head")
        check_deps
        shift
        python3 "$PYTHON_SCRIPT" head "$@"
        ;;
    "body")
        check_deps
        shift
        python3 "$PYTHON_SCRIPT" body "$@"
        ;;
    "antenna")
        check_deps
        shift
        python3 "$PYTHON_SCRIPT" antenna "$@"
        ;;
    "reset")
        check_deps
        python3 "$PYTHON_SCRIPT" reset
        ;;
    "stop")
        check_deps
        python3 "$PYTHON_SCRIPT" stop
        ;;
    "state")
        check_deps
        python3 "$PYTHON_SCRIPT" state "$@"
        ;;
    "temperature")
        check_deps
        python3 "$PYTHON_SCRIPT" temperature
        ;;
    "choreo")
        check_deps
        shift
        python3 "$PYTHON_SCRIPT" choreo "$@"
        ;;
    "camera")
        check_deps
        shift
        python3 "$PYTHON_SCRIPT" camera "$@"
        ;;
    "connect")
        check_deps
        shift
        python3 "$PYTHON_SCRIPT" connect "$@"
        ;;
    "help"|"--help"|"-h"|"")
        echo "Reachy Mini Control - Usage:"
        echo ""
        echo "  reachy-mini check                     # Check if daemon is running"
        echo "  reachy-mini install-deps              # Install Python dependencies"
        echo ""
        echo "Connection:"
        echo "  reachy-mini connect --usb             # Connect via USB (Lite)"
        echo "  reachy-mini connect --wifi --ip IP    # Connect via WiFi (Wireless)"
        echo "  reachy-mini status                    # Show robot state"
        echo ""
        echo "Control:"
        echo "  reachy-mini head set --yaw 0 --pitch 15 --roll 0"
        echo "  reachy-mini body set --yaw 45"
        echo "  reachy-mini antenna left set --angle 90"
        echo "  reachy-mini antenna right set --angle 45"
        echo "  reachy-mini reset                     # Reset to default position"
        echo "  reachy-mini stop                      # Stop all movements"
        echo ""
        echo "Monitoring:"
        echo "  reachy-mini state                     # Get current state (JSON)"
        echo "  reachy-mini state --stream            # Stream state (20Hz)"
        echo "  reachy-mini temperature               # Motor temperatures"
        echo ""
        echo "Choreography:"
        echo "  reachy-mini choreo list               # List available choreographies"
        echo "  reachy-mini choreo play --name hello  # Play a choreography"
        echo ""
        echo "Camera:"
        echo "  reachy-mini camera url                # Get WebRTC URL"
        echo ""
        ;;
    *)
        echo "Unknown command: $1"
        echo "Use 'reachy-mini help' for usage information."
        exit 1
        ;;
esac