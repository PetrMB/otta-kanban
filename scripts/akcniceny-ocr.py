#!/usr/bin/env python3
"""
Akcniceny OCR - Scans price flyers for special offers using OCR
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

try:
    import pytesseract
    from PIL import Image
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    print("Warning: pytesseract or PIL not available. Using mock mode.")

# Configuration
SCAN_DIR = Path.home() / ".openclaw" / "workspace" / "akcniceny" / "scans"
OUTPUT_DIR = Path.home() / ".openclaw" / "workspace" / "akcniceny" / "results"

def setup_dirs():
    """Create necessary directories"""
    SCAN_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def scan_images():
    """Scan for images in the scans directory"""
    if not SCAN_DIR.exists():
        return []
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
    images = []
    
    for file_path in SCAN_DIR.iterdir():
        if file_path.suffix.lower() in image_extensions:
            images.append(file_path)
    
    return sorted(images)

def ocr_image(image_path):
    """Perform OCR on an image and extract text"""
    if not PYTESSERACT_AVAILABLE:
        return f"[Mock OCR] Text extracted from: {image_path.name}"
    
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang='ces')
        return text
    except Exception as e:
        return f"Error processing {image_path.name}: {str(e)}"

def search_for_keywords(text, keywords=None):
    """Search for specific keywords in OCR text"""
    if keywords is None:
        keywords = [
            "sleva", "akce", "výprodej", "zlevněno", "akční",
            "2 for 1", "buy one get one", "dárky", " zdarma"
        ]
    
    found = []
    text_lower = text.lower()
    
    for keyword in keywords:
        if keyword.lower() in text_lower:
            found.append(keyword)
    
    return found

def process_scans():
    """Main processing function"""
    results = {
        "timestamp": datetime.now().isoformat(),
        "scanned_files": [],
        "findings": [],
        "errors": []
    }
    
    setup_dirs()
    
    images = scan_images()
    
    if not images:
        return {
            **results,
            "errors": ["No image files found in scans directory"],
            "summary": "No images to process"
        }
    
    for image_path in images:
        results["scanned_files"].append(str(image_path))
        
        print(f"Processing: {image_path.name}")
        
        # Perform OCR
        text = ocr_image(image_path)
        
        # Search for keywords
        found_keywords = search_for_keywords(text)
        
        if found_keywords:
            finding = {
                "file": image_path.name,
                "keywords_found": found_keywords,
                "found_items": len(found_keywords)
            }
            results["findings"].append(finding)
            print(f"  ✓ Found {len(found_keywords)} offer(s)")
        else:
            print(f"  - No special offers detected")
    
    return results

def save_results(results):
    """Save results to JSON file"""
    output_file = OUTPUT_DIR / f"akcniceny-result-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    return str(output_file)

def format_report(results):
    """Format results for display/communication"""
    lines = []
    
    lines.append("=" * 50)
    lines.append("📈 AKČNÍ CENY - OCR VÝSLEDEK")
    lines.append("=" * 50)
    lines.append(f"Datum zpracování: {results['timestamp']}")
    lines.append("")
    
    if results.get('summary'):
        lines.append(f"✅ {results['summary']}")
        return "\n".join(lines)
    
    lines.append(f"Zpracované soubory: {len(results.get('scanned_files', []))}")
    lines.append(f"Nalezené akce: {len(results.get('findings', []))}")
    lines.append("")
    
    if results.get('errors'):
        lines.append("❌ Chyby:")
        for error in results['errors']:
            lines.append(f"   - {error}")
        lines.append("")
    
    if results.get('findings'):
        lines.append("🔍 Nalezené akční nabídky:")
        for finding in results['findings']:
            lines.append(f"  📄 {finding['file']}")
            lines.append(f"     → {', '.join(finding['keywords_found'])}")
        lines.append("")
    
    summary_parts = []
    if results.get('scanned_files'):
        summary_parts.append(f"zpracováno {len(results['scanned_files'])} obrázků")
    if results.get('findings'):
        summary_parts.append(f"nalezeno {len(results['findings'])} akcí")
    
    if summary_parts:
        lines.append(f"📊 Shrnutí: {'; '.join(summary_parts)}")
    
    return "\n".join(lines)

def main():
    print("🚀 Spouštím kontrolu akčních letáků...")
    print()
    
    results = process_scans()
    
    # Save results
    output_file = save_results(results)
    print()
    print(f"💾 Výsledky uloženy do: {output_file}")
    print()
    
    # Format and display report
    report = format_report(results)
    print(report)
    
    # Return JSON for programmatic use
    return json.dumps(results, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ Přerušeno uživatelem")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Neočekávaná chyba: {str(e)}")
        sys.exit(1)
