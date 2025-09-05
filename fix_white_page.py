#!/usr/bin/env python3
"""Fix the white page issue - restore working content"""
import os
import requests
import json
from datetime import datetime
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

from database import session_scope
from tournament_models import Player, TournamentPlacement
from sqlalchemy import func, desc, case

SHOPIFY_DOMAIN = os.getenv('SHOPIFY_DOMAIN')
SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')

headers = {
    'X-Shopify-Access-Token': SHOPIFY_ACCESS_TOKEN,
    'Content-Type': 'application/json'
}

print("Fixing white page issue...")

with session_scope() as session:
    # Get ALL players
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

# Build simple HTML WITHOUT problematic CSS
html = f"""<div>
<h1 style="text-align: center; margin-bottom: 20px;">Player Rankings - {datetime.now().strftime('%B %d, %Y')}</h1>
<p style="text-align: center; margin-bottom: 30px;">Points: 1st=10, 2nd=7, 3rd=5, 4th=3, 5th-6th=2, 7th-8th=1</p>

<table style="width: 100%; border-collapse: collapse; margin: 0 auto;">
<thead>
<tr style="background-color: #333; color: white;">
<th style="padding: 10px; text-align: left;">Rank</th>
<th style="padding: 10px; text-align: left;">Player</th>
<th style="padding: 10px; text-align: center;">Points</th>
<th style="padding: 10px; text-align: center;">Events</th>
<th style="padding: 10px; text-align: center;">1st Places</th>
</tr>
</thead>
<tbody>"""

for i, p in enumerate(player_stats, 1):
    tag = p.gamer_tag or f"Player {p.id}"
    pts = int(p.total_points or 0)
    evts = p.tournament_count or 0
    wins = p.first_places or 0
    
    # Add row styling
    if i <= 3:
        row_style = 'style="background-color: #ffffcc;"'
    elif i <= 10:
        row_style = 'style="background-color: #f0f8ff;"'
    elif i % 2 == 0:
        row_style = 'style="background-color: #f9f9f9;"'
    else:
        row_style = ''
    
    html += f"""
<tr {row_style}>
<td style="padding: 8px; border-bottom: 1px solid #ddd;">{i}</td>
<td style="padding: 8px; border-bottom: 1px solid #ddd;">{tag}</td>
<td style="padding: 8px; text-align: center; border-bottom: 1px solid #ddd; font-weight: bold;">{pts}</td>
<td style="padding: 8px; text-align: center; border-bottom: 1px solid #ddd;">{evts}</td>
<td style="padding: 8px; text-align: center; border-bottom: 1px solid #ddd;">{wins}</td>
</tr>"""

html += """
</tbody>
</table>
</div>"""

print(f"HTML size: {len(html)} bytes")

# Update theme
themes_url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/themes.json"
response = requests.get(themes_url, headers=headers)
theme_id = None

if response.status_code == 200:
    themes = response.json().get('themes', [])
    for theme in themes:
        if theme.get('role') == 'main':
            theme_id = theme.get('id')
            break

if theme_id:
    template_key = "templates/page.attendance.json"
    get_url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/themes/{theme_id}/assets.json"
    params = {'asset[key]': template_key}
    
    template_response = requests.get(get_url, headers=headers, params=params)
    
    if template_response.status_code == 200:
        asset = template_response.json().get('asset', {})
        content = asset.get('value', '')
        
        try:
            data = json.loads(content)
            
            # Update custom-liquid section
            for section_id, section in data.get('sections', {}).items():
                if section.get('type') == 'custom-liquid':
                    section['settings']['custom_liquid'] = html
                    print(f"Updating section: {section_id}")
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
                print(f"✅ Fixed! Page restored with all {len(player_stats)} players")
                print("View at: https://backyardtryhards.com/pages/attendance")
            else:
                print(f"❌ Failed: {update_response.status_code}")
                
        except json.JSONDecodeError as e:
            print(f"JSON error: {e}")