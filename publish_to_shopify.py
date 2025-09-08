#!/usr/bin/env python3
"""
Simple script to publish tournament data to Shopify using Bonjour database
Updates the /pages/attendance page via theme template
"""
import os
import sys
import json
import httpx
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Add paths for imports
sys.path.insert(0, '/home/ubuntu/claude/tournament_tracker')
sys.path.insert(0, '/home/ubuntu/claude/tournament_tracker/utils')

# Load environment variables
load_dotenv('/home/ubuntu/claude/tournament_tracker/.env')

# Import database and models
from utils.database import session_scope
from models.tournament_models import Tournament, Player, Organization
from polymorphic_core import announcer

def get_tournament_data():
    """Get tournament data using Bonjour database"""
    announcer.announce(
        "Shopify Publisher",
        ["Fetching tournament data for Shopify publication"]
    )
    
    with session_scope() as session:
        # Get all tournaments and group by primary contact/owner
        all_tournaments = session.query(Tournament).all()
        
        # Group tournaments by organizer (primary_contact or owner_name)
        org_groups = {}
        for t in all_tournaments:
            # Use primary_contact if available, otherwise owner_name
            org_key = t.primary_contact or t.owner_name or 'Unknown'
            
            if org_key not in org_groups:
                org_groups[org_key] = []
            org_groups[org_key].append(t)
        
        # Build organization data
        organizations = []
        for org_name, tournaments in org_groups.items():
            tournament_count = len(tournaments)
            total_attendance = sum(t.num_attendees or 0 for t in tournaments)
            
            if tournament_count > 0:  # Only include orgs with tournaments
                organizations.append({
                    'name': org_name,
                    'tournament_count': tournament_count,
                    'total_attendance': total_attendance
                })
        
        # Get recent tournaments (last 90 days)
        from datetime import datetime, timedelta
        cutoff_timestamp = int((datetime.now() - timedelta(days=90)).timestamp())
        recent_tournaments = session.query(Tournament).filter(
            Tournament.start_at >= cutoff_timestamp
        ).all()
        
        # Sort by date (newest first)
        recent_tournaments.sort(key=lambda t: t.start_at or 0, reverse=True)
        
        tournaments = []
        for t in recent_tournaments:
            org_name = t.primary_contact or t.owner_name or 'Unknown'
            # Convert timestamp to datetime
            date_str = 'TBD'
            if t.start_at:
                date_str = datetime.fromtimestamp(t.start_at).isoformat()
            
            tournaments.append({
                'name': t.name,
                'date': date_str,
                'attendees': t.num_attendees or 0,
                'organization': org_name,
                'city': t.city or '',
                'state': t.addr_state or ''
            })
        
        # Get top players by calculating points from placements
        from models.tournament_models import TournamentPlacement
        from utils.points_system import get_points
        
        # Get all placements
        all_placements = session.query(TournamentPlacement).all()
        
        # Calculate points per player
        player_stats = {}
        for placement in all_placements:
            # Get player name from related player object
            if not placement.player:
                continue
            player_name = placement.player.name
            if not player_name:
                continue
                
            if player_name not in player_stats:
                player_stats[player_name] = {
                    'name': player_name,
                    'points': 0,
                    'events': 0,
                    'first_places': 0,
                    'top_3s': 0
                }
            
            # Add points for this placement (field is 'placement' not 'standing')
            points = get_points(placement.placement)
            player_stats[player_name]['points'] += points
            player_stats[player_name]['events'] += 1
            
            if placement.placement == 1:
                player_stats[player_name]['first_places'] += 1
            if placement.placement <= 3:
                player_stats[player_name]['top_3s'] += 1
        
        # Convert to list and sort by points
        players = list(player_stats.values())
        players.sort(key=lambda p: p['points'], reverse=True)
        
        announcer.announce(
            "Shopify Publisher",
            [
                f"Found {len(organizations)} organizations",
                f"Found {len(tournaments)} recent tournaments",
                f"Found {len(players)} top players"
            ]
        )
        
        return organizations, tournaments, players

def generate_html_content():
    """Generate HTML content from Bonjour database"""
    
    # Get data from database
    print("Fetching tournament data...")
    organizations, tournaments, players = get_tournament_data()
    
    # Get counts
    total_tournaments = len(tournaments)
    total_players = len(players)
    total_orgs = len(organizations)
    
    # Get timestamp
    pacific_offset = timedelta(hours=-7)  # PDT
    pacific_tz = timezone(pacific_offset)
    utc_now = datetime.now(timezone.utc)
    pacific_time = utc_now.astimezone(pacific_tz)
    last_updated = pacific_time.strftime("%B %d, %Y at %I:%M %p Pacific")
    
    print(f"Found {total_tournaments} tournaments, {total_players} players, {total_orgs} organizations")
    
    # Generate HTML with tabbed interface
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tournament Rankings</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; margin-bottom: 10px; }}
        .subtitle {{ color: #7f8c8d; margin-bottom: 20px; }}
        .update-info {{ color: #95a5a6; font-size: 12px; margin-bottom: 30px; }}
        
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; }}
        .stat-value {{ font-size: 32px; font-weight: bold; margin-bottom: 5px; }}
        .stat-label {{ font-size: 14px; opacity: 0.9; }}
        
        .tab-nav {{ display: flex; gap: 10px; margin-bottom: 20px; border-bottom: 2px solid #e0e0e0; }}
        .tab-button {{ padding: 12px 24px; background: none; border: none; cursor: pointer; font-size: 16px; color: #7f8c8d; transition: all 0.3s; }}
        .tab-button:hover {{ color: #2c3e50; }}
        .tab-button.active {{ color: #667eea; border-bottom: 3px solid #667eea; margin-bottom: -2px; }}
        
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
        
        table {{ width: 90%; margin: 0 auto; border-collapse: collapse; }}
        th {{ background: #f8f9fa; padding: 8px 10px; text-align: left; font-weight: 600; color: #2c3e50; border-bottom: 2px solid #e0e0e0; }}
        th.center {{ text-align: center; }}
        th.right {{ text-align: right; }}
        td {{ padding: 6px 10px; border-bottom: 1px solid #f0f0f0; text-align: left; }}
        tr:hover {{ background: #f8f9fa; }}
        
        .rank-cell {{ font-weight: bold; color: #667eea; text-align: center; }}
        .name-cell {{ font-weight: 500; text-align: left; }}
        .number-cell {{ text-align: center; }}
        .right-align {{ text-align: right; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏆 Southern California FGC Tournament Rankings</h1>
        <p class="subtitle">Tracking the competitive fighting game scene in SoCal</p>
        <p class="update-info">Last updated: {last_updated}</p>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{total_orgs}</div>
                <div class="stat-label">Active Organizations</div>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                <div class="stat-value">{total_tournaments}</div>
                <div class="stat-label">Recent Tournaments</div>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                <div class="stat-value">{total_players}</div>
                <div class="stat-label">Top Players</div>
            </div>
        </div>
        
        <div class="tab-nav">
            <button class="tab-button active" onclick="showTab('organizations')">Organizations</button>
            <button class="tab-button" onclick="showTab('players')">Player Rankings</button>
            <button class="tab-button" onclick="showTab('tournaments')">Recent Tournaments</button>
        </div>
        
        <div id="organizations" class="tab-content active">
            <h2>Top Organizations by Total Attendance</h2>
            <table>
                <thead>
                    <tr>
                        <th width="60" class="center">Rank</th>
                        <th>Organization</th>
                        <th width="120" class="center">Tournaments</th>
                        <th width="150" class="center">Total Attendance</th>
                        <th width="120" class="center">Avg Attendance</th>
                    </tr>
                </thead>
                <tbody>"""
    
    # Add organization data
    if organizations:
        # Sort by total attendance
        sorted_orgs = sorted(organizations, key=lambda x: x.get('total_attendance', 0), reverse=True)
        for idx, org in enumerate(sorted_orgs[:50], 1):
            org_name = org.get('name', 'Unknown')
            tournament_count = org.get('tournament_count', 0)
            total_attendance = org.get('total_attendance', 0)
            avg_attendance = total_attendance / tournament_count if tournament_count > 0 else 0
            
            html += f"""
                    <tr>
                        <td class="rank-cell">{idx}</td>
                        <td class="name-cell">{org_name}</td>
                        <td class="number-cell">{tournament_count}</td>
                        <td class="number-cell">{total_attendance:,}</td>
                        <td class="number-cell">{avg_attendance:.1f}</td>
                    </tr>"""
    
    html += """
                </tbody>
            </table>
        </div>
        
        <div id="players" class="tab-content">
            <h2>Top Players by Points</h2>
            <table>
                <thead>
                    <tr>
                        <th width="60" class="center">Rank</th>
                        <th>Player</th>
                        <th width="100" class="center">Points</th>
                        <th width="100" class="center">Events</th>
                        <th width="100" class="center">1st Places</th>
                        <th width="100" class="center">Top 3s</th>
                        <th width="80" class="center">Win %</th>
                    </tr>
                </thead>
                <tbody>"""
    
    # Add player data
    if players:
        for idx, player in enumerate(players[:50], 1):
            name = player.get('name', 'Unknown')
            points = player.get('points', 0)
            events = player.get('events', 0)
            first_places = player.get('first_places', 0)
            top_3s = player.get('top_3s', 0)
            win_rate = (first_places / events * 100) if events > 0 else 0
            
            html += f"""
                    <tr>
                        <td class="rank-cell">{idx}</td>
                        <td class="name-cell">{name}</td>
                        <td class="number-cell">{points}</td>
                        <td class="number-cell">{events}</td>
                        <td class="number-cell">{first_places}</td>
                        <td class="number-cell">{top_3s}</td>
                        <td class="number-cell">{win_rate:.1f}%</td>
                    </tr>"""
    
    html += """
                </tbody>
            </table>
        </div>
        
        <div id="tournaments" class="tab-content">
            <h2>Recent Tournaments (Last 90 Days)</h2>
            <table>
                <thead>
                    <tr>
                        <th width="120">Date</th>
                        <th>Tournament</th>
                        <th>Organization</th>
                        <th width="120" class="center">Attendees</th>
                        <th width="150">Location</th>
                    </tr>
                </thead>
                <tbody>"""
    
    # Add tournament data
    if tournaments:
        for tournament in tournaments[:100]:  # Show more recent tournaments
            date_str = tournament.get('date', 'TBD')
            if date_str != 'TBD':
                try:
                    # Format date nicely
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    date_str = date_obj.strftime('%b %d, %Y')
                except:
                    pass
            
            name = tournament.get('name', 'Unknown')
            org = tournament.get('organization', 'Unknown')
            attendees = tournament.get('attendees', 0)
            city = tournament.get('city', '')
            state = tournament.get('state', '')
            location = f"{city}, {state}" if city else "Online"
            
            html += f"""
                    <tr>
                        <td>{date_str}</td>
                        <td class="name-cell">{name}</td>
                        <td>{org}</td>
                        <td class="number-cell">{attendees}</td>
                        <td>{location}</td>
                    </tr>"""
    
    html += """
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        function showTab(tabName) {
            // Hide all tabs
            var tabs = document.querySelectorAll('.tab-content');
            tabs.forEach(function(tab) {
                tab.classList.remove('active');
            });
            
            // Remove active from all buttons
            var buttons = document.querySelectorAll('.tab-button');
            buttons.forEach(function(button) {
                button.classList.remove('active');
            });
            
            // Show selected tab
            document.getElementById(tabName).classList.add('active');
            
            // Mark button as active
            event.target.classList.add('active');
        }
    </script>
</body>
</html>"""
    
    return html

def find_store_and_theme():
    """Find Shopify store and theme configuration using environment variables"""
    
    # Get from .env - NEVER hardcode these values!
    access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")
    if not access_token:
        raise RuntimeError("SHOPIFY_ACCESS_TOKEN not set in .env file")
    
    store_url = os.getenv("SHOPIFY_DOMAIN", "8ccd49-4.myshopify.com")
    
    # Get theme ID
    headers = {"X-Shopify-Access-Token": access_token}
    with httpx.Client(timeout=30.0) as client:
        response = client.get(f"https://{store_url}/admin/api/2023-10/themes.json", headers=headers)
        if response.status_code == 200:
            themes = response.json()["themes"]
            for theme in themes:
                if theme.get("role") == "main":
                    return store_url, theme["id"], access_token
    
    raise RuntimeError("Could not connect to Shopify store or find main theme")

def update_shopify_template(html_content):
    """Update Shopify template with HTML content"""
    
    announcer.announce(
        "Shopify Publisher",
        ["Updating Shopify /pages/attendance template"]
    )
    
    store_url, theme_id, access_token = find_store_and_theme()
    
    template = "templates/page.attendance.json"
    headers = {"X-Shopify-Access-Token": access_token, "Content-Type": "application/json"}
    
    with httpx.Client(timeout=30.0) as client:
        asset_url = f"https://{store_url}/admin/api/2023-10/themes/{theme_id}/assets.json"
        
        try:
            # Get current template
            response = client.get(asset_url, headers=headers, params={"asset[key]": template})
            if response.status_code == 200:
                current_data = json.loads(response.json()["asset"]["value"])
            else:
                # Create new template structure
                current_data = {
                    "sections": {},
                    "order": []
                }
            
            # Find or create a custom-liquid section
            custom_section_key = None
            for key, section in current_data.get("sections", {}).items():
                if section.get("type") == "custom-liquid":
                    custom_section_key = key
                    break
            
            if not custom_section_key:
                # Create new custom liquid section
                custom_section_key = "tournament_html"
                current_data["sections"][custom_section_key] = {
                    "type": "custom-liquid",
                    "settings": {}
                }
                if custom_section_key not in current_data.get("order", []):
                    current_data.setdefault("order", []).append(custom_section_key)
            
            # Update the custom liquid content in the correct section
            current_data["sections"][custom_section_key]["settings"]["custom_liquid"] = html_content
            
            # Update the template
            update_data = {
                "asset": {
                    "key": template,
                    "value": json.dumps(current_data, indent=2)
                }
            }
            
            response = client.put(asset_url, headers=headers, json=update_data)
            
            if response.status_code in [200, 201]:
                announcer.announce(
                    "Shopify Publisher",
                    ["Successfully updated Shopify template", f"URL: https://backyardtryhards.com/pages/attendance"]
                )
                return True
            else:
                announcer.announce(
                    "Shopify Publisher Error",
                    [f"Failed to update template: {response.status_code}", response.text[:200]]
                )
                print(f"Error response: {response.status_code}")
                print(f"Error text: {response.text[:500]}")
                return False
                
        except Exception as e:
            announcer.announce(
                "Shopify Publisher Error",
                [f"Exception updating template: {str(e)}"]
            )
            raise

def main():
    """Main function to publish to Shopify"""
    print("=== Shopify Publishing Script (Bonjour Edition) ===")
    print("This will update backyardtryhards.com/pages/attendance")
    print()
    
    try:
        # Announce our start
        announcer.announce(
            "Shopify Publisher",
            ["Starting Shopify publication process"]
        )
        
        # Generate HTML content
        print("Generating HTML content...")
        html_content = generate_html_content()
        
        # Save locally for debugging
        with open('shopify_output.html', 'w') as f:
            f.write(html_content)
        print(f"Saved local copy to shopify_output.html ({len(html_content):,} bytes)")
        
        # Update Shopify
        print("\nUpdating Shopify template...")
        success = update_shopify_template(html_content)
        
        if success:
            print("✅ Successfully published to Shopify!")
            print(f"View at: https://backyardtryhards.com/pages/attendance")
        else:
            print("❌ Failed to publish to Shopify")
            print("Check the error messages above for details")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())