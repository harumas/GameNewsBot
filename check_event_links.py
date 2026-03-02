import json
import urllib.request
import re
from datetime import datetime
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def check_event_links(json_file_path):
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    warnings = []
    
    for event in data.get('events', []):
        url = event.get('url')
        name = event.get('name')
        date_start = event.get('date_start')
        
        if not url or not date_start:
            continue
            
        try:
            event_year = int(date_start.split('-')[0])
        except ValueError:
            continue
            
        try:
            # Adding headers to spoof user agent so some sites don't block urllib
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            response = urllib.request.urlopen(req, timeout=10)
            final_url = response.geturl()
            html = response.read()
            
            # Check 1: Does the final redirected URL contain an old year?
            old_years = [str(event_year - i) for i in range(1, 4)]
            for old_y in old_years:
                if old_y in final_url and str(event_year) not in final_url:
                    warnings.append(f"[{name}] URL specifically points to an old year ({old_y}): {final_url}")
                    break
            
            # Check 2: Does the page title heavily feature last year?
            try:
                html_text = html.decode('utf-8', errors='ignore')
                title_match = re.search(r'<title[^>]*>(.*?)</title>', html_text, re.IGNORECASE | re.DOTALL)
                
                if title_match:
                    title_text = title_match.group(1).strip()
                    for old_y in old_years:
                        if old_y in title_text and str(event_year) not in title_text:
                            warnings.append(f"[{name}] Page title seems outdated, mentions {old_y}: '{title_text.strip()}'")
                            break
            except Exception:
                pass
                        
        except Exception as e:
            warnings.append(f"[{name}] Failed to fetch URL ({url}): {str(e)}")
            
    if warnings:
        logging.warning("--- EVENT LINK WARNINGS FOUND ---")
        for w in warnings:
            print(f"⚠️  {w}")
        return 1
    else:
        logging.info("All event links appear to be healthy and current.")
        return 0

if __name__ == "__main__":
    file_path = "docs/data/events.json"
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    sys.exit(check_event_links(file_path))
