#!/usr/bin/env python3
"""Screenshot + Vision analysis - workflow script"""
import base64, urllib.request, json, sys, subprocess, os

def capture_screenshot(output_path):
    """Capture screenshot via nodes.run OR screencapture"""
    try:
        # Try nodes first
        result = subprocess.run(['openclaw', 'nodes', 'run', '--node', 'MacKulna', 
                                '--raw', f'/usr/sbin/screencapture -x {output_path}'],
                               capture_output=True, text=True, timeout=30)
        if 'OK' in result.stdout:
            print("✅ Screenshot via nodes.run", file=sys.stderr)
            return True
    except:
        pass
    
    # Fallback to native screencapture
    result = subprocess.run(['/usr/sbin/screencapture', '-x', output_path],
                           capture_output=True, text=True, timeout=10)
    if os.path.exists(output_path):
        print("✅ Screenshot via screencapture", file=sys.stderr)
        return True
    return False

def analyze_image(image_path, prompt="What's on this screen? Be brief in Czech."):
    """Analyze screenshot via llama3.2-vision:11b"""
    try:
        with open(image_path, 'rb') as f:
            img = base64.b64encode(f.read()).decode()
        
        data = json.dumps({
            'model': 'llama3.2-vision:11b',
            'prompt': prompt,
            'images': [img],
            'stream': False,
            'options': {'temperature': 0.3, 'num_predict': 300}
        }).encode()
        
        req = urllib.request.Request(
            'http://localhost:11434/api/generate',
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
        return resp.get('response', 'NO RESPONSE')
    except Exception as e:
        return f"ERROR: {e}"

if __name__ == '__main__':
    output_path = '/Users/otto/.openclaw/workspace/screen-analysis.png'
    result_file = '/Users/otto/.openclaw/workspace/analysis-result.txt'
    
    print("📸 Capturing screenshot...", file=sys.stderr)
    if not capture_screenshot(output_path):
        print("❌ Screenshot failed", file=sys.stderr)
        sys.exit(1)
    
    print("🔍 Analyzing...", file=sys.stderr)
    result = analyze_image(output_path)
    
    # Save result to file (bypass tool compaction)
    with open(result_file, 'w') as f:
        f.write(result)
    
    print(result)  # stdout
    print(f"✅ Result saved to: {result_file}", file=sys.stderr)
