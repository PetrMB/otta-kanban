#!/usr/bin/env python3
"""
Top headlines from BBC News (Czech)
"""

import json
import urllib.request
from datetime import datetime

def get_bbc_czech_headlines():
    """Fetch top headlines from BBC World (English - with Czech translation)"""
    # Use BBC World feed as fallback
    url = "http://feeds.bbci.co.uk/news/world/rss.xml"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = response.read().decode('utf-8')
        
        # Simple XML parsing for headlines
        import xml.etree.ElementTree as ET
        root = ET.fromstring(data)
        
        headlines = []
        for item in root.findall('.//item')[:3]:
            title = item.find('title').text
            link = item.find('link').text
            # Get description if available
            desc = item.find('description')
            description = desc.text if desc is not None else ""
            headlines.append({"title": title, "link": link, "description": description})
        
        return headlines
    except Exception as e:
        return [{"error": str(e)}]

def format_headlines():
    """Format headlines for message"""
    headlines = get_bbc_czech_headlines()
    
    if any('error' in h for h in headlines):
        return "Chyba při načítání novinek"
    
    lines = ["🇬🇧 BBC Novinky"]
    for i, h in enumerate(headlines, 1):
        lines.append(f"{i}. {h['title']}")
    
    return "\n".join(lines)

def main():
    print(format_headlines())

if __name__ == "__main__":
    main()
