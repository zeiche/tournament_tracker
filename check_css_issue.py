#!/usr/bin/env python3
"""Check for CSS issues in the theme"""
import os
import requests
import json
import re
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
            print(f"Theme: {theme.get('name')} (ID: {theme_id})")
            break

# Check theme CSS files
print("\n" + "="*60)
print("CHECKING THEME CSS FILES")
print("="*60)

css_files = [
    "assets/base.css",
    "assets/section-main-page.css",
    "assets/custom.css",
    "assets/theme.css"
]

for css_file in css_files:
    get_url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/themes/{theme_id}/assets.json"
    params = {'asset[key]': css_file}
    
    css_response = requests.get(get_url, headers=headers, params=params)
    
    if css_response.status_code == 200:
        asset = css_response.json().get('asset', {})
        content = asset.get('value', '')
        
        print(f"\n{css_file}: {len(content)} bytes")
        
        # Look for problematic CSS
        if 'custom-liquid' in content:
            print("  ⚠️  Found custom-liquid styles")
            # Find the relevant styles
            import re
            matches = re.findall(r'\.custom-liquid[^{]*\{[^}]*\}', content)
            for match in matches[:3]:  # Show first 3 matches
                print(f"    {match}")
        
        # Check for large padding/margin
        large_spacing = re.findall(r'(?:padding|margin)[^:]*:\s*(\d{3,}px|[5-9]\d+(?:px|rem|em))', content)
        if large_spacing:
            print(f"  ⚠️  Found large spacing: {large_spacing[:5]}")
        
        # Check for min-height
        min_heights = re.findall(r'min-height:\s*(\d+(?:px|vh|rem))', content)
        if min_heights:
            print(f"  ⚠️  Found min-height values: {min_heights[:5]}")

# Check the actual template settings
print("\n" + "="*60)
print("CHECKING TEMPLATE SETTINGS")
print("="*60)

template_key = "templates/page.attendance.json"
get_url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/themes/{theme_id}/assets.json"
params = {'asset[key]': template_key}

template_response = requests.get(get_url, headers=headers, params=params)

if template_response.status_code == 200:
    asset = template_response.json().get('asset', {})
    content = asset.get('value', '')
    
    try:
        data = json.loads(content)
        
        # Check section settings
        for section_id, section in data.get('sections', {}).items():
            print(f"\nSection: {section_id}")
            print(f"  Type: {section.get('type')}")
            
            settings = section.get('settings', {})
            
            # Check for padding/margin settings
            for key, value in settings.items():
                if 'padding' in key.lower() or 'margin' in key.lower() or 'spacing' in key.lower():
                    print(f"  ⚠️  {key}: {value}")
                elif key == 'custom_liquid':
                    # Check if CSS is embedded in the liquid
                    if '<style>' in str(value):
                        print("  ⚠️  Contains embedded <style> tags")
                        style_match = re.search(r'<style[^>]*>(.*?)</style>', str(value), re.DOTALL)
                        if style_match:
                            styles = style_match.group(1)[:200]
                            print(f"    Embedded styles: {styles}...")
                    
    except json.JSONDecodeError as e:
        print(f"JSON error: {e}")

print("\n" + "="*60)
print("SOLUTION: Adding CSS reset to content")
print("="*60)

# Update with CSS reset
from database import session_scope
from tournament_models import Player, TournamentPlacement
from sqlalchemy import func, desc, case
from datetime import datetime

with session_scope() as session:
    # Get players
    player_stats = session.query(
        Player.id,
        Player.gamer_tag,
        func.count(TournamentPlacement.id).label('tournament_count'),
        func.sum(
            case(
                (TournamentPlacement.placement == 1, 10),
                (TournamentPlacement.placement == 2, 7),
                (TournamentPlacement.placement == 3, 5),
                (TournamentPlacement.placement == 4, 3),
                (TournamentPlacement.placement == 5, 2),
                (TournamentPlacement.placement == 7, 1),
                else_=0
            )
        ).label('total_points'),
        func.count(
            case(
                (TournamentPlacement.placement == 1, 1),
                else_=None
            )
        ).label('first_places')
    ).join(
        TournamentPlacement, TournamentPlacement.player_id == Player.id
    ).group_by(
        Player.id, Player.gamer_tag
    ).order_by(
        desc('total_points')
    ).all()

print(f"Found {len(player_stats)} players")

# Build HTML with CSS reset
html = f"""<style>
/* Reset any theme CSS that might be causing issues */
.custom-liquid {{
    padding: 0 !important;
    margin: 0 !important;
    max-width: 100% !important;
    min-height: auto !important;
}}
.custom-liquid * {{
    box-sizing: border-box;
}}
.custom-liquid table {{
    margin: 20px 0;
}}
</style>

<div style="padding:20px;max-width:1400px;margin:0 auto">
<h1>Player Rankings - {datetime.now().strftime('%B %d, %Y')}</h1>
<p>Points: 1st=10, 2nd=7, 3rd=5, 4th=3, 5th-6th=2, 7th-8th=1</p>
<table style="width:100%;border-collapse:collapse;background:white">
<tr style="background:#333;color:white">
<th style="padding:8px">Rank</th>
<th style="padding:8px">Player</th>
<th style="padding:8px">Pts</th>
<th style="padding:8px">Events</th>
<th style="padding:8px">1st</th>
</tr>"""

for i, p in enumerate(player_stats, 1):
    tag = p.gamer_tag or f"P{p.id}"
    pts = int(p.total_points or 0)
    evts = p.tournament_count or 0
    wins = p.first_places or 0
    
    if i <= 10:
        html += f"""<tr style="background:#f0f8ff"><td style="padding:8px">{i}</td><td style="padding:8px"><b>{tag}</b></td><td style="padding:8px"><b>{pts}</b></td><td style="padding:8px">{evts}</td><td style="padding:8px">{wins}</td></tr>"""
    else:
        html += f"""<tr><td style="padding:8px">{i}</td><td style="padding:8px">{tag}</td><td style="padding:8px">{pts}</td><td style="padding:8px">{evts}</td><td style="padding:8px">{wins}</td></tr>"""

html += "</table></div>"

# Update template
if template_response.status_code == 200:
    try:
        data = json.loads(content)
        
        for section_id, section in data.get('sections', {}).items():
            if section.get('type') == 'custom-liquid':
                section['settings']['custom_liquid'] = html
                break
        
        updated_json = json.dumps(data, indent=2)
        
        update_payload = {
            'asset': {
                'key': template_key,
                'value': updated_json
            }
        }
        
        update_response = requests.put(
            f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/themes/{theme_id}/assets.json",
            headers=headers,
            json=update_payload
        )
        
        if update_response.status_code in [200, 201]:
            print("✅ Updated with CSS reset to fix white space!")
            print("View at: https://backyardtryhards.com/pages/attendance")
        else:
            print(f"❌ Failed: {update_response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")