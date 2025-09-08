#!/usr/bin/env python3
"""
Compact Shopify publisher that stays under 50KB limit
"""
import os
import sys
import json
import httpx
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Add paths
sys.path.insert(0, '/home/ubuntu/claude/tournament_tracker')
sys.path.insert(0, '/home/ubuntu/claude/tournament_tracker/utils')

# Load environment
load_dotenv('/home/ubuntu/claude/tournament_tracker/.env')

from utils.database import session_scope
from models.tournament_models import Tournament, TournamentPlacement, Organization
from utils.points_system import get_points
from polymorphic_core import announcer

def generate_compact_html():
    """Generate compact HTML under 50KB limit"""
    
    with session_scope() as session:
        # Get organizations from the database
        all_orgs = session.query(Organization).all()
        
        # Build org data using proper organization names
        organizations = []
        for org in all_orgs:
            # Get tournament count and attendance from relationships
            tournament_count = len(org.tournaments) if hasattr(org, 'tournaments') else 0
            total_attendance = sum(t.num_attendees or 0 for t in org.tournaments) if hasattr(org, 'tournaments') else 0
            
            if tournament_count > 0:  # Only include orgs with tournaments
                organizations.append({
                    'name': org.display_name[:30] if org.display_name else 'Unknown',  # Use display_name
                    'count': tournament_count,
                    'attendance': total_attendance
                })
        
        # If no orgs in DB, fall back to grouping tournaments
        if not organizations:
            all_tournaments = session.query(Tournament).all()
            org_groups = {}
            for t in all_tournaments:
                org_key = t.primary_contact or t.owner_name or 'Unknown'
                if org_key not in org_groups:
                    org_groups[org_key] = []
                org_groups[org_key].append(t)
            
            for org_name, tournaments in org_groups.items():
                if tournaments:
                    organizations.append({
                        'name': org_name[:30],
                        'count': len(tournaments),
                        'attendance': sum(t.num_attendees or 0 for t in tournaments)
                    })
        
        # Sort by attendance (no limit)
        organizations.sort(key=lambda x: x['attendance'], reverse=True)
        
        # Get all player rankings (no limit)
        all_placements = session.query(TournamentPlacement).all()
        player_stats = {}
        
        for placement in all_placements:
            if not placement.player or not placement.player.gamer_tag:
                continue
            gamer_tag = placement.player.gamer_tag[:20]  # Use gamer_tag instead of name
            if gamer_tag not in player_stats:
                player_stats[gamer_tag] = {'pts': 0, 'ev': 0, '1st': 0}
            
            player_stats[gamer_tag]['pts'] += get_points(placement.placement)
            player_stats[gamer_tag]['ev'] += 1
            if placement.placement == 1:
                player_stats[gamer_tag]['1st'] += 1
        
        players = sorted(
            [{'n': k, **v} for k, v in player_stats.items()],
            key=lambda x: x['pts'],
            reverse=True
        )  # No limit - show all players
    
    # Generate compact HTML with inline styles
    pacific_time = datetime.now(timezone(timedelta(hours=-7)))
    updated = pacific_time.strftime("%b %d %I:%M%p")
    
    html = f"""<style>
body{{font-family:sans-serif;margin:20px;max-width:1000px;margin:0 auto;padding:20px}}
table{{width:85%;margin:20px auto;border-collapse:collapse}}
th{{background:#f8f9fa;padding:2px 4px;text-align:left;font-weight:600;color:#2c3e50}}
th.ctr{{text-align:center}}
td{{padding:2px 4px;border-bottom:1px solid #ddd;text-align:left}}
td.ctr{{text-align:center}}
.r{{font-weight:bold;color:#667eea;text-align:center}}
.tabs{{display:flex;gap:10px;margin:20px 0;border-bottom:2px solid #ddd}}
.tab{{padding:10px 20px;background:none;border:none;cursor:pointer;color:#666}}
.tab.active{{color:#667eea;border-bottom:3px solid #667eea;margin-bottom:-2px}}
.panel{{display:none}}
.panel.active{{display:block}}
.update{{text-align:center;color:#999;font-size:11px;margin-top:20px}}
</style>
<div class="tabs">
<button class="tab active" onclick="st('p')">Players</button>
<button class="tab" onclick="st('o')">Organizations</button>
</div>
<div id="p" class="panel active">
<table>
<thead><tr><th class="ctr">#</th><th>Player</th><th class="ctr">Points</th><th class="ctr">Events</th><th class="ctr">Wins</th></tr></thead>
<tbody>"""
    
    for i, p in enumerate(players, 1):
        html += f'<tr><td class="r">{i}</td><td>{p["n"]}</td><td class="ctr">{p["pts"]}</td><td class="ctr">{p["ev"]}</td><td class="ctr">{p["1st"]}</td></tr>'
    
    html += """</tbody></table></div>
<div id="o" class="panel">
<table>
<thead><tr><th class="ctr">#</th><th>Organization</th><th class="ctr">Events</th><th class="ctr">Attendance</th></tr></thead>
<tbody>"""
    
    for i, org in enumerate(organizations, 1):
        html += f'<tr><td class="r">{i}</td><td>{org["name"]}</td><td class="ctr">{org["count"]}</td><td class="ctr">{org["attendance"]}</td></tr>'
    
    html += f"""</tbody></table></div>
<p class="update">Updated: {updated}</p>
<script>
function st(t){{
document.querySelectorAll('.tab').forEach(b=>b.classList.remove('active'));
document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
event.target.classList.add('active');
document.getElementById(t).classList.add('active');
}}
</script>"""
    
    return html

def update_shopify(html_content):
    """Update Shopify with compact HTML"""
    
    print(f"HTML size: {len(html_content)} bytes")
    
    if len(html_content) > 49000:
        print("WARNING: HTML might be too large!")
    
    token = os.getenv('SHOPIFY_ACCESS_TOKEN')
    domain = os.getenv('SHOPIFY_DOMAIN')
    headers = {'X-Shopify-Access-Token': token, 'Content-Type': 'application/json'}
    
    with httpx.Client(timeout=60.0) as client:
        # Get theme
        resp = client.get(f'https://{domain}/admin/api/2023-10/themes.json', headers=headers)
        themes = resp.json()['themes']
        theme_id = next(t['id'] for t in themes if t.get('role') == 'main')
        
        # Get current template
        asset_url = f'https://{domain}/admin/api/2023-10/themes/{theme_id}/assets.json'
        resp = client.get(asset_url, headers=headers, params={'asset[key]': 'templates/page.attendance.json'})
        
        if resp.status_code == 200:
            current_data = json.loads(resp.json()['asset']['value'])
            
            # Update the section
            section_key = 'tournament_html_1756176130'
            current_data['sections'][section_key]['settings']['custom_liquid'] = html_content
            
            # Send update
            update_data = {
                'asset': {
                    'key': 'templates/page.attendance.json',
                    'value': json.dumps(current_data, indent=2)
                }
            }
            
            resp = client.put(asset_url, headers=headers, json=update_data)
            
            if resp.status_code in [200, 201]:
                return True
            else:
                print(f"Error: {resp.status_code}")
                print(resp.text[:500])
                return False
    
    return False

def main():
    print("=== Compact Shopify Publisher ===")
    print("Generating compact HTML...")
    
    html = generate_compact_html()
    
    # Save locally
    with open('compact_output.html', 'w') as f:
        f.write(html)
    print(f"Saved to compact_output.html ({len(html)} bytes)")
    
    if len(html) < 49000:
        print("\nUpdating Shopify...")
        if update_shopify(html):
            print("✅ Successfully published!")
            print("View at: https://backyardtryhards.com/pages/attendance")
        else:
            print("❌ Failed to publish")
    else:
        print(f"ERROR: HTML too large ({len(html)} bytes), must be under 50KB")

if __name__ == "__main__":
    main()