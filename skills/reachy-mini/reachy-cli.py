#!/usr/bin/env python3
"""
Reachy Mini CLI - jednoduché ovládání z příkazové řádky
"""

import sys
import argparse
from reachy_mini import ReachyMini


def main():
    parser = argparse.ArgumentParser(description="Reachy Mini Robot Control")
    parser.add_argument("--host", default="localhost:8000", help="Daemon URL")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # speak
    speak_parser = subparsers.add_parser("speak", help="MLuvení s animací")
    speak_parser.add_argument("text", help="Text k přečtení")
    speak_parser.add_argument("--voice", default="Zuzana", help="Hlas (Zuzana/Samantha)")
    speak_parser.add_argument("--no-animate", action="store_true", help="Bez pohybu")
    speak_parser.add_argument("--gesture", choices=["wave", "nod", "shake"], help="Gesto")
    
    # wave
    subparsers.add_parser("wave", help="Zamávej anténkama")
    
    # nod  
    subparsers.add_parser("nod", help="Přikyvuj hlavou")
    
    # shake
    subparsers.add_parser("shake", help="Zakrout hlavou")
    
    # reset
    subparsers.add_parser("reset", help="Vrať do výchozí pozice")
    
    # state
    subparsers.add_parser("state", help="Zobraz stav")
    
    # look
    subparsers.add_parser("look", help="Rozhlédni se")
    
    # goto
    goto_parser = subparsers.add_parser("goto", help="Přesuň na pozici")
    goto_parser.add_argument("--pitch", type=float, help="Hlava nahoru/dolu (-0.4 až 0.4)")
    goto_parser.add_argument("--yaw", type=float, help="Hlava vlevo/vpravo (-0.5 až 0.5)")
    goto_parser.add_argument("--body", type=float, help="Tělo (-3.14 až 3.14)")
    goto_parser.add_argument("--ant-l", type=float, help="Levá anténa")
    goto_parser.add_argument("--ant-r", type=float, help="Pravá anténa")
    goto_parser.add_argument("--duration", "-d", type=float, default=1.0, help="Délka pohybu")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    base_url = f"http://{args.host}"
    r = ReachyMini(base_url)
    
    if not r.is_ready():
        print(f"❌ Reachy Mini není dostupný na {base_url}")
        print("   Zapni desktop app nebo daemon!")
        sys.exit(1)
    
    try:
        if args.command == "speak":
            print(f"🎙️  Mluvím: \"{args.text}\"")
            result = r.speak(args.text, args.voice, 
                           animate=not args.no_animate,
                           gesture=args.gesture)
            print(f"✓ Hotovo ({result['duration']:.1f}s)")
            
        elif args.command == "wave":
            print("👋 Mávám...")
            r.wave()
            print("✓ Hotovo")
            
        elif args.command == "nod":
            print("🙂 Přikyvuji...")
            r.nod()
            print("✓ Hotovo")
            
        elif args.command == "shake":
            print("😵 Kroutím hlavou...")
            r.shake()
            print("✓ Hotovo")
            
        elif args.command == "reset":
            print("😐 Resetuji pozici...")
            r.reset()
            print("✓ Hotovo")
            
        elif args.command == "state":
            state = r.state()
            print("📊 Stav Reachy Mini:")
            hp = state.get('head_pose', {})
            print(f"   Hlava: pitch={hp.get('pitch', 0):.2f}, yaw={hp.get('yaw', 0):.2f}")
            print(f"   Tělo: yaw={state.get('body_yaw', 0):.2f}")
            ants = state.get('antennas_position', [0, 0])
            print(f"   Antény: L={ants[0]:.2f}, R={ants[1]:.2f}")
            
        elif args.command == "look":
            print("👀 Rozhlížím se...")
            r.look_around()
            print("✓ Hotovo")
            
        elif args.command == "goto":
            print(f"🤖 Pohybuji se...")
            r.goto(
                head_pitch=args.pitch,
                head_yaw=args.yaw,
                body_yaw=args.body,
                left_antenna=args.ant_l,
                right_antenna=args.ant_r,
                duration=args.duration
            )
            print("✓ Hotovo")
            
    except Exception as e:
        print(f"❌ Chyba: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
