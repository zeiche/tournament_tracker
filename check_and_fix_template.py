#!/usr/bin/env python3
"""Check what's actually in the template and fix it"""
import os
import requests
import json
from pathlib import Path

# Load environment
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                if key and not key.startswith('export'):
                    os.environ[key] = value

SHOPIFY_DOMAIN = os.getenv('SHOPIFY_DOMAIN')
SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')

headers = {
    'X-Shopify-Access-Token': SHOPIFY_ACCESS_TOKEN,
    'Content-Type': 'application/json'
}

# Get theme
themes_url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/themes.json"
response = requests.get(themes_url, headers=headers)
theme_id = None

if response.status_code == 200:
    themes = response.json().get('themes', [])
    for theme in themes:
        if theme.get('role') == 'main':
            theme_id = theme.get('id')
            print(f"Theme ID: {theme_id}")
            break

# Get the template
template_key = "templates/page.attendance.json"
get_url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/themes/{theme_id}/assets.json"
params = {'asset[key]': template_key}

print(f"\nChecking template content...")
template_response = requests.get(get_url, headers=headers, params=params)

if template_response.status_code == 200:
    asset = template_response.json().get('asset', {})
    content = asset.get('value', '')
    
    try:
        data = json.loads(content)
        
        # Check what's in the custom-liquid section
        for section_id, section in data.get('sections', {}).items():
            if section.get('type') == 'custom-liquid':
                print(f"\nSection: {section_id}")
                liquid_content = section.get('settings', {}).get('custom_liquid', '')
                print(f"Content length: {len(liquid_content)} bytes")
                
                # Check what's in the content
                if 'Player Rankings' in liquid_content:
                    print("✅ Has Player Rankings section")
                    
                    # Count how many players
                    import re
                    rows = re.findall(r'<tr[^>]*>.*?</tr>', liquid_content, re.DOTALL)
                    print(f"Found {len(rows)} table rows")
                    
                    # Check if it's the full list
                    if len(rows) > 200:
                        print("✅ Appears to have full player list")
                    else:
                        print("❌ Seems to be truncated")
                        
                elif '🎮 Tournament Rankings 🎮' in liquid_content:
                    print("Has old full content")
                else:
                    print("Has different content")
                
                # Show first 500 chars
                print(f"\nFirst 500 chars of content:")
                print(liquid_content[:500])
                
                # Show last 500 chars
                print(f"\nLast 500 chars of content:")
                print(liquid_content[-500:])
                
    except json.JSONDecodeError as e:
        print(f"JSON error: {e}")

print("\n" + "="*60)
print("Checking live page...")
print("="*60)

# Check what the live page actually shows
live_response = requests.get("https://backyardtryhards.com/pages/attendance")
if live_response.status_code == 200:
    live_html = live_response.text
    
    # Check for specific markers
    if 'Player Rankings - ' in live_html:
        print("✅ Live page has new Player Rankings header")
    elif '🎮 Tournament Rankings 🎮' in live_html:
        print("❌ Live page has OLD content")
    else:
        print("⚠️  Live page has unknown content")
    
    # Count players on live page
    import re
    player_rows = re.findall(r'<td>\d+</td><td>[^<]+</td><td>\d+</td>', live_html)
    print(f"Live page shows {len(player_rows)} players")