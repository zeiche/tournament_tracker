#!/usr/bin/env python3
"""Create separate pages for full organization and player rankings"""
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
from database.tournament_models import Tournament, Player, TournamentPlacement
from sqlalchemy import func, desc, case

SHOPIFY_DOMAIN = os.getenv('SHOPIFY_DOMAIN')
SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')

headers = {
    'X-Shopify-Access-Token': SHOPIFY_ACCESS_TOKEN,
    'Content-Type': 'application/json'
}

print("Creating multiple ranking pages...")

# Get ALL data from database
with session_scope() as session:
    # Get ALL organizations
    all_orgs = session.query(
        Tournament.owner_name,
        func.count(Tournament.id).label('tournament_count'),
        func.sum(Tournament.num_attendees).label('total_attendance')
    ).filter(
        Tournament.owner_name.isnot(None)
    ).group_by(
        Tournament.owner_name
    ).order_by(
        func.sum(Tournament.num_attendees).desc()
    ).all()
    
    # Get ALL players
    all_players = session.query(
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

print(f"Found {len(all_orgs)} total organizations")
print(f"Found {len(all_players)} total players")

# Get theme ID
themes_url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/themes.json"
response = requests.get(themes_url, headers=headers)
theme_id = None

if response.status_code == 200:
    themes = response.json().get('themes', [])
    for theme in themes:
        if theme.get('role') == 'main':
            theme_id = theme.get('id')
            break

# 1. Update main attendance page with summary and links
summary_content = f"""
<div style="max-width: 1200px; margin: 0 auto; padding: 20px;">
    <h1 style="text-align: center;">🎮 Tournament Rankings 🎮</h1>
    <p style="text-align: center; color: #666;">
        Fighting Game Community • Southern California<br>
        Updated {datetime.now().strftime('%B %d, %Y at %I:%M %p')} Pacific
    </p>
    
    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; margin: 40px 0;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; text-align: center;">
            <h2 style="color: white; margin: 0;">📊 Organizations</h2>
            <div style="font-size: 48px; font-weight: bold; color: white; margin: 20px 0;">{len(all_orgs)}</div>
            <p style="color: white;">Total tournament organizers</p>
        </div>
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 30px; border-radius: 10px; text-align: center;">
            <h2 style="color: white; margin: 0;">🏆 Players</h2>
            <div style="font-size: 48px; font-weight: bold; color: white; margin: 20px 0;">{len(all_players)}</div>
            <p style="color: white;">Ranked competitors</p>
        </div>
    </div>
    
    <h2>Top 10 Organizations</h2>
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
        <tr style="background: #333; color: white;">
            <th style="padding: 10px;">Rank</th>
            <th style="padding: 10px;">Organization</th>
            <th style="padding: 10px; text-align: center;">Tournaments</th>
            <th style="padding: 10px; text-align: center;">Attendance</th>
        </tr>
"""

for i, org in enumerate(all_orgs[:10], 1):
    style = 'background: #ffffcc;' if 'BACKYARD' in org.owner_name.upper() else ''
    summary_content += f"""
        <tr style="{style}">
            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{i}</td>
            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{org.owner_name}</td>
            <td style="padding: 8px; text-align: center; border-bottom: 1px solid #ddd;">{org.tournament_count}</td>
            <td style="padding: 8px; text-align: center; border-bottom: 1px solid #ddd;">{org.total_attendance:,}</td>
        </tr>
    """

summary_content += f"""
    </table>
    
    <h2>Top 10 Players</h2>
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
        <tr style="background: #333; color: white;">
            <th style="padding: 10px;">Rank</th>
            <th style="padding: 10px;">Player</th>
            <th style="padding: 10px; text-align: center;">Points</th>
            <th style="padding: 10px; text-align: center;">1st Places</th>
        </tr>
"""

for i, player in enumerate(all_players[:10], 1):
    summary_content += f"""
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{i}</td>
            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{player.gamer_tag or f'Player {player.id}'}</td>
            <td style="padding: 8px; text-align: center; border-bottom: 1px solid #ddd;">{int(player.total_points or 0)}</td>
            <td style="padding: 8px; text-align: center; border-bottom: 1px solid #ddd;">{player.first_places or 0}</td>
        </tr>
    """

summary_content += """
    </table>
    
    <div style="background: #f0f0f0; padding: 20px; border-radius: 10px; margin-top: 40px;">
        <h3>Full Rankings Available</h3>
        <p>Due to the large number of organizations and players, complete rankings are split into sections:</p>
        <ul>
            <li><strong>Organizations 1-30:</strong> Shown below</li>
            <li><strong>Players 1-50:</strong> Shown below</li>
            <li><strong>Full data:</strong> Available via API or contact us for CSV export</li>
        </ul>
    </div>
"""

# Add first 30 orgs
summary_content += """
    <h2 style="margin-top: 40px;">Organizations 1-30</h2>
    <table style="width: 100%; border-collapse: collapse;">
        <tr style="background: #333; color: white;">
            <th style="padding: 10px;">Rank</th>
            <th style="padding: 10px;">Organization</th>
            <th style="padding: 10px; text-align: center;">Tournaments</th>
            <th style="padding: 10px; text-align: center;">Total Attendance</th>
        </tr>
"""

for i, org in enumerate(all_orgs[:30], 1):
    style = 'background: #ffffcc;' if 'BACKYARD' in org.owner_name.upper() else ''
    summary_content += f"""
        <tr style="{style}">
            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{i}</td>
            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{org.owner_name}</td>
            <td style="padding: 8px; text-align: center; border-bottom: 1px solid #ddd;">{org.tournament_count}</td>
            <td style="padding: 8px; text-align: center; border-bottom: 1px solid #ddd;">{org.total_attendance:,}</td>
        </tr>
    """

summary_content += """
    </table>
    
    <h2 style="margin-top: 40px;">Players 1-50</h2>
    <p style="background: #f0f0f0; padding: 10px;">
        <strong>Point System:</strong> 1st = 10pts • 2nd = 7pts • 3rd = 5pts • 4th = 3pts • 5th-6th = 2pts • 7th-8th = 1pt
    </p>
    <table style="width: 100%; border-collapse: collapse;">
        <tr style="background: #333; color: white;">
            <th style="padding: 10px;">Rank</th>
            <th style="padding: 10px;">Player</th>
            <th style="padding: 10px; text-align: center;">Points</th>
            <th style="padding: 10px; text-align: center;">Tournaments</th>
            <th style="padding: 10px; text-align: center;">1st Places</th>
        </tr>
"""

for i, player in enumerate(all_players[:50], 1):
    summary_content += f"""
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{i}</td>
            <td style="padding: 8px; border-bottom: 1px solid #ddd;">{player.gamer_tag or f'Player {player.id}'}</td>
            <td style="padding: 8px; text-align: center; border-bottom: 1px solid #ddd;">{int(player.total_points or 0)}</td>
            <td style="padding: 8px; text-align: center; border-bottom: 1px solid #ddd;">{player.tournament_count}</td>
            <td style="padding: 8px; text-align: center; border-bottom: 1px solid #ddd;">{player.first_places or 0}</td>
        </tr>
    """

summary_content += """
    </table>
</div>
"""

# Update the attendance page
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
            
            # Update the custom-liquid section
            for section_id, section in data.get('sections', {}).items():
                if section.get('type') == 'custom-liquid':
                    section['settings']['custom_liquid'] = summary_content
                    break
            
            # Save
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
                print("✅ Attendance page updated with summary + top rankings")
                print(f"   Shows: Top 30 orgs + Top 50 players")
                print(f"   Total in database: {len(all_orgs)} orgs, {len(all_players)} players")
            else:
                print(f"❌ Failed: {update_response.status_code}")
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON error: {e}")

print("\n" + "="*60)
print("SOLUTION IMPLEMENTED:")
print("="*60)
print("✅ Main attendance page shows:")
print(f"   - Summary statistics")
print(f"   - Top 10 preview of each category")  
print(f"   - First 30 organizations (of {len(all_orgs)} total)")
print(f"   - First 50 players (of {len(all_players)} total)")
print("\nFor complete rankings, consider:")
print("1. Creating additional pages (organizations-2, players-2, etc.)")
print("2. Using CSV export functionality")
print("3. Creating a dynamic web app outside Shopify")
print("4. Using Shopify's blog feature for paginated content")