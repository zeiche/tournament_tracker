#!/usr/bin/env python3
"""
Compact Shopify publisher that stays under the 50KB limit
Publishes only essential data as JSON embedded in a minimal template
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
from models.tournament_models import Tournament, Player, TournamentPlacement

def publish_compact():
    """Publish compact data to Shopify"""
    
    # Get environment variables
    shopify_domain = os.getenv('SHOPIFY_DOMAIN')
    shopify_token = os.getenv('SHOPIFY_ACCESS_TOKEN')
    
    if not shopify_domain or not shopify_token:
        print("Missing SHOPIFY_DOMAIN or SHOPIFY_ACCESS_TOKEN")
        return False
    
    # Get data from database
    with session_scope() as session:
        # Count total tournaments
        total_tournaments = session.query(Tournament).count()
        
        # Get recent tournaments (last 30 days) 
        recent_cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        recent_tournaments = session.query(Tournament).filter(
            Tournament.start_at > recent_cutoff
        ).order_by(Tournament.start_at.desc()).limit(20).all()
        
        # Get top organizations by tournament count
        from sqlalchemy import func
        org_stats = session.query(
            Tournament.primary_contact,
            func.count(Tournament.id).label('count'),
            func.sum(Tournament.num_attendees).label('attendance')
        ).group_by(Tournament.primary_contact).order_by(
            func.count(Tournament.id).desc()
        ).limit(15).all()
        
        # Get top players by points (simplified)
        player_points = {}
        placements = session.query(TournamentPlacement).all()
        
        for p in placements:
            player_name = p.player.gamer_tag if p.player else None
            if not player_name:
                continue
            
            # Simple points: 10 for 1st, 7 for 2nd, 5 for 3rd, 3 for 4th-8th
            points = {1: 10, 2: 7, 3: 5}.get(p.placement, 3 if p.placement <= 8 else 0)
            player_points[player_name] = player_points.get(player_name, 0) + points
        
        # Sort and get top players
        top_players = sorted(player_points.items(), key=lambda x: x[1], reverse=True)[:20]
    
    # Create minimal template with embedded data
    data = {
        'total': total_tournaments,
        'orgs': [[org or 'Unknown', count, attendance or 0] for org, count, attendance in org_stats],
        'players': [[name, points] for name, points in top_players],
        'updated': datetime.now(timezone.utc).isoformat()
    }
    
    # Create a minimal liquid template (under 50KB)
    template = f"""<script>window.tournamentData={json.dumps(data, separators=(',',':'))}</script>
<div id="tournament-tracker">
<h2>SoCal FGC Rankings</h2>
<p>Total Tournaments: <b>{total_tournaments}</b></p>
<h3>Top Organizations</h3>
<table><tr><th>Org</th><th>Events</th></tr>
{''.join(f"<tr><td>{o[0]}</td><td>{o[1]}</td></tr>" for o in data['orgs'][:10])}
</table>
<h3>Top Players</h3>
<table><tr><th>Player</th><th>Points</th></tr>
{''.join(f"<tr><td>{p[0]}</td><td>{p[1]}</td></tr>" for p in data['players'][:10])}
</table>
<p style="font-size:0.8em">Updated: {data['updated'][:10]}</p>
</div>"""
    
    # Check size
    size_kb = len(template.encode()) / 1024
    print(f"Template size: {size_kb:.1f} KB")
    
    if size_kb > 49:
        print("Template too large, trimming...")
        # Trim to fewer entries
        template = f"""<script>window.tournamentData={json.dumps(data, separators=(',',':'))}</script>
<div id="tournament-tracker">
<h2>SoCal FGC</h2>
<p>Tournaments: {total_tournaments}</p>
<h3>Top Orgs</h3>
{''.join(f"<p>{o[0]}: {o[1]}</p>" for o in data['orgs'][:5])}
<h3>Top Players</h3>
{''.join(f"<p>{p[0]}: {p[1]}pts</p>" for p in data['players'][:5])}
</div>"""
    
    # Update Shopify
    try:
        theme_id = "160792985908"
        asset_key = "templates/page.attendance.liquid"
        
        url = f"https://{shopify_domain}/admin/api/2024-01/themes/{theme_id}/assets.json"
        headers = {
            "X-Shopify-Access-Token": shopify_token,
            "Content-Type": "application/json"
        }
        
        payload = {
            "asset": {
                "key": asset_key,
                "value": template
            }
        }
        
        with httpx.Client() as client:
            response = client.put(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                print(f"✅ Published to Shopify ({size_kb:.1f} KB)")
                return True
            else:
                print(f"❌ Shopify error {response.status_code}: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = publish_compact()
    sys.exit(0 if success else 1)