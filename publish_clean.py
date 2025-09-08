#!/usr/bin/env python3
"""
Clean Shopify publisher with proper Liquid syntax
"""
import os
import sys
import json
import httpx
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

sys.path.insert(0, '/home/ubuntu/claude/tournament_tracker')
sys.path.insert(0, '/home/ubuntu/claude/tournament_tracker/utils')

load_dotenv('/home/ubuntu/claude/tournament_tracker/.env')

from utils.database import session_scope
from models.tournament_models import Tournament, TournamentPlacement
from utils.points_system import get_points

def get_data():
    """Get tournament data"""
    with session_scope() as session:
        # Get tournaments
        all_tournaments = session.query(Tournament).all()
        
        # Group by organizer
        org_groups = {}
        for t in all_tournaments:
            org_key = t.primary_contact or t.owner_name or 'Unknown'
            if org_key not in org_groups:
                org_groups[org_key] = []
            org_groups[org_key].append(t)
        
        # Build org data
        organizations = []
        for org_name, tournaments in org_groups.items():
            if tournaments:
                organizations.append({
                    'name': org_name[:50],  # Truncate long names
                    'tournaments': len(tournaments),
                    'attendance': sum(t.num_attendees or 0 for t in tournaments)
                })
        
        organizations.sort(key=lambda x: x['attendance'], reverse=True)
        # No limit - show all organizations
        
        # Get player rankings
        all_placements = session.query(TournamentPlacement).all()
        player_stats = {}
        
        for placement in all_placements:
            if not placement.player or not placement.player.gamer_tag:
                continue
            name = placement.player.gamer_tag[:30]  # Use gamer_tag (handle) instead of real name
            if name not in player_stats:
                player_stats[name] = {'points': 0, 'events': 0, 'wins': 0}
            
            player_stats[name]['points'] += get_points(placement.placement)
            player_stats[name]['events'] += 1
            if placement.placement == 1:
                player_stats[name]['wins'] += 1
        
        players = sorted(
            [{'name': k, **v} for k, v in player_stats.items()],
            key=lambda x: x['points'],
            reverse=True
        )  # No limit - show all players
        
        return {
            'orgs': organizations,
            'players': players,
            'updated': datetime.now(timezone(timedelta(hours=-7))).strftime('%b %d, %Y %I:%M %p PST')
        }

def publish():
    """Publish to Shopify"""
    print("Getting data...")
    data = get_data()
    print(f"Got {len(data['orgs'])} orgs, {len(data['players'])} players")
    
    # Create clean Liquid template
    liquid = f"""<style>
.trk {{max-width:1200px;margin:0 auto;padding:20px;font-family:sans-serif;color:#e0e0e0}}
.trk h1 {{color:#ffffff;text-align:center}}
.trk .updated {{text-align:center;color:#b0b0b0;font-size:14px;margin-bottom:20px}}
.trk .tabs {{display:flex;gap:10px;border-bottom:2px solid #555;margin-bottom:15px}}
.trk .tab {{padding:8px 16px;background:none;border:none;cursor:pointer;color:#b0b0b0}}
.trk .tab:hover {{color:#ffffff}}
.trk .tab.active {{color:#667eea;border-bottom:3px solid #667eea;margin-bottom:-2px}}
.trk .panel {{display:none}}
.trk .panel.active {{display:block}}
.trk table {{width:100%;border-collapse:collapse}}
.trk th {{background:rgba(255,255,255,0.1);padding:6px 8px;text-align:left;font-weight:600;color:#ffffff}}
.trk td {{padding:4px 8px;border-bottom:1px solid #444;color:#e0e0e0}}
.trk .rank {{font-weight:bold;color:#8a9cff;width:50px}}
.trk .num {{text-align:right}}
</style>

<div class="trk">
<h1>🏆 Southern California FGC Tournament Rankings</h1>
<p class="updated">Last updated: {data['updated']}</p>

<div class="tabs">
<button class="tab active" onclick="showTab(event,'players')">Players</button>
<button class="tab" onclick="showTab(event,'orgs')">Organizations</button>
</div>

<div id="players" class="panel active">
<table>
<thead><tr><th>Rank</th><th>Player</th><th class="num">Points</th><th class="num">Events</th><th class="num">Wins</th></tr></thead>
<tbody>"""
    
    for i, p in enumerate(data['players'], 1):
        liquid += f'\n<tr><td class="rank">{i}</td><td>{p["name"]}</td><td class="num">{p["points"]}</td><td class="num">{p["events"]}</td><td class="num">{p["wins"]}</td></tr>'
    
    liquid += """
</tbody></table>
</div>

<div id="orgs" class="panel">
<table>
<thead><tr><th>Rank</th><th>Organization</th><th class="num">Tournaments</th><th class="num">Total Attendance</th></tr></thead>
<tbody>"""
    
    for i, org in enumerate(data['orgs'], 1):
        liquid += f'\n<tr><td class="rank">{i}</td><td>{org["name"]}</td><td class="num">{org["tournaments"]}</td><td class="num">{org["attendance"]:,}</td></tr>'
    
    liquid += """
</tbody></table>
</div>
</div>

<script>
function showTab(e,t){
  document.querySelectorAll('.trk .tab').forEach(b=>b.classList.remove('active'));
  document.querySelectorAll('.trk .panel').forEach(p=>p.classList.remove('active'));
  e.target.classList.add('active');
  document.getElementById(t).classList.add('active');
}
</script>"""
    
    print(f"Liquid template size: {len(liquid)} bytes")
    
    if len(liquid) > 49000:
        print("ERROR: Template too large!")
        return False
    
    # Upload to Shopify
    token = os.getenv('SHOPIFY_ACCESS_TOKEN')
    domain = os.getenv('SHOPIFY_DOMAIN')
    headers = {'X-Shopify-Access-Token': token, 'Content-Type': 'application/json'}
    
    with httpx.Client(timeout=60.0) as client:
        # Get theme
        resp = client.get(f'https://{domain}/admin/api/2023-10/themes.json', headers=headers)
        themes = resp.json()['themes']
        theme_id = next(t['id'] for t in themes if t.get('role') == 'main')
        
        # Get template
        asset_url = f'https://{domain}/admin/api/2023-10/themes/{theme_id}/assets.json'
        resp = client.get(asset_url, headers=headers, params={'asset[key]': 'templates/page.attendance.json'})
        template = json.loads(resp.json()['asset']['value'])
        
        # Update custom liquid section
        for key, section in template.get('sections', {}).items():
            if section.get('type') == 'custom-liquid':
                template['sections'][key]['settings']['custom_liquid'] = liquid
                break
        
        # Save
        update_data = {
            'asset': {
                'key': 'templates/page.attendance.json',
                'value': json.dumps(template, indent=2)
            }
        }
        resp = client.put(asset_url, headers=headers, json=update_data)
        
        if resp.status_code in [200, 201]:
            print("✅ Published successfully!")
            print("View at: https://backyardtryhards.com/pages/attendance")
            return True
        else:
            print(f"❌ Failed: {resp.status_code}")
            print(resp.text[:300])
            return False

if __name__ == "__main__":
    success = publish()
    sys.exit(0 if success else 1)