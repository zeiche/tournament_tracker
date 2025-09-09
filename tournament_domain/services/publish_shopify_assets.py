#!/usr/bin/env python3
"""
Shopify publisher that uses separate CSS and data assets
Following Shopify best practices for theme development
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
from models.tournament_models import Tournament, TournamentPlacement
from utils.points_system import get_points
from polymorphic_core import announcer

def get_tournament_data():
    """Get tournament data from database"""
    
    with session_scope() as session:
        # Get tournaments grouped by organizer
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
                    'name': org_name,
                    'tournament_count': len(tournaments),
                    'total_attendance': sum(t.num_attendees or 0 for t in tournaments)
                })
        
        # Sort by attendance
        organizations.sort(key=lambda x: x['total_attendance'], reverse=True)
        
        # Get player rankings
        all_placements = session.query(TournamentPlacement).all()
        player_stats = {}
        
        for placement in all_placements:
            if not placement.player:
                continue
            name = placement.player.name
            if name not in player_stats:
                player_stats[name] = {
                    'points': 0, 
                    'events': 0, 
                    'first_places': 0,
                    'top_3s': 0
                }
            
            player_stats[name]['points'] += get_points(placement.placement)
            player_stats[name]['events'] += 1
            if placement.placement == 1:
                player_stats[name]['first_places'] += 1
            if placement.placement <= 3:
                player_stats[name]['top_3s'] += 1
        
        players = []
        for name, stats in player_stats.items():
            players.append({
                'name': name,
                **stats
            })
        players.sort(key=lambda x: x['points'], reverse=True)
        
        # Get recent tournaments
        cutoff_timestamp = int((datetime.now() - timedelta(days=90)).timestamp())
        recent_tournaments = []
        for t in all_tournaments:
            if t.start_at and t.start_at >= cutoff_timestamp:
                recent_tournaments.append({
                    'name': t.name,
                    'date': datetime.fromtimestamp(t.start_at).strftime('%Y-%m-%d'),
                    'attendees': t.num_attendees or 0,
                    'organization': t.primary_contact or t.owner_name or 'Unknown',
                    'city': t.city or '',
                    'state': t.addr_state or ''
                })
        
        recent_tournaments.sort(key=lambda x: x['date'], reverse=True)
        
        return {
            'organizations': organizations[:50],  # Top 50
            'players': players[:50],  # Top 50
            'tournaments': recent_tournaments[:100],  # Recent 100
            'last_updated': datetime.now(timezone(timedelta(hours=-7))).isoformat()
        }

def create_css_asset():
    """Create CSS for tournament rankings"""
    
    css_content = """
/* Tournament Rankings Styles */
.tournament-rankings {
    font-family: var(--font-body-family);
    color: var(--color-foreground);
    padding: 2rem 0;
}

.tournament-header {
    text-align: center;
    margin-bottom: 3rem;
}

.tournament-title {
    font-size: 2.5rem;
    font-weight: var(--font-heading-weight);
    margin-bottom: 0.5rem;
    color: var(--color-foreground);
}

.tournament-subtitle {
    font-size: 1.1rem;
    color: rgb(var(--color-foreground), 0.75);
    margin-bottom: 0.5rem;
}

.tournament-updated {
    font-size: 0.875rem;
    color: rgb(var(--color-foreground), 0.5);
}

.tournament-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    margin: 2rem 0;
}

.stat-card {
    background: var(--gradient-base-accent-1);
    color: var(--color-base-solid-button-labels);
    padding: 1.5rem;
    border-radius: var(--card-corner-radius);
    text-align: center;
}

.stat-value {
    font-size: 2rem;
    font-weight: bold;
    margin-bottom: 0.25rem;
}

.stat-label {
    font-size: 0.875rem;
    opacity: 0.9;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.tournament-tabs {
    display: flex;
    gap: 1rem;
    margin: 2rem 0 1rem;
    border-bottom: 2px solid rgb(var(--color-border));
    overflow-x: auto;
}

.tab-button {
    padding: 0.75rem 1.5rem;
    background: none;
    border: none;
    cursor: pointer;
    font-size: 1rem;
    color: rgb(var(--color-foreground), 0.75);
    transition: color 0.2s;
    white-space: nowrap;
}

.tab-button:hover {
    color: var(--color-foreground);
}

.tab-button.active {
    color: var(--color-link);
    border-bottom: 3px solid var(--color-link);
    margin-bottom: -2px;
}

.tab-panel {
    display: none;
    animation: fadeIn 0.3s;
}

.tab-panel.active {
    display: block;
}

.tournament-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 1rem;
}

.tournament-table th {
    background: rgb(var(--color-background), 0.5);
    padding: 0.75rem;
    text-align: left;
    font-weight: 600;
    font-size: 0.875rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    border-bottom: 2px solid rgb(var(--color-border));
}

.tournament-table td {
    padding: 0.75rem;
    border-bottom: 1px solid rgb(var(--color-border), 0.5);
}

.tournament-table tr:hover {
    background: rgb(var(--color-background), 0.3);
}

.rank-column {
    font-weight: bold;
    color: var(--color-link);
    width: 3rem;
}

.number-column {
    text-align: right;
    font-variant-numeric: tabular-nums;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

@media screen and (max-width: 750px) {
    .tournament-title {
        font-size: 1.75rem;
    }
    
    .tournament-stats {
        grid-template-columns: 1fr;
    }
    
    .tournament-table {
        font-size: 0.875rem;
    }
    
    .tournament-table th,
    .tournament-table td {
        padding: 0.5rem;
    }
}
"""
    return css_content

def create_liquid_template():
    """Create liquid template that references CSS and data"""
    
    liquid_content = """
{% comment %}
Tournament Rankings Display
Pulls data from JSON asset and styles from CSS
{% endcomment %}

{{ 'tournament-rankings.css' | asset_url | stylesheet_tag }}

{% assign tournament_data_url = 'tournament-data.json' | asset_url %}

<div class="tournament-rankings page-width">
    <div class="tournament-header">
        <h1 class="tournament-title">🏆 Southern California FGC Tournament Rankings</h1>
        <p class="tournament-subtitle">Tracking the competitive fighting game scene in SoCal</p>
        <p class="tournament-updated" id="last-updated">Loading...</p>
    </div>
    
    <div class="tournament-stats" id="stats-container">
        <!-- Stats will be loaded here -->
    </div>
    
    <div class="tournament-tabs">
        <button class="tab-button active" data-tab="organizations">Organizations</button>
        <button class="tab-button" data-tab="players">Player Rankings</button>
        <button class="tab-button" data-tab="tournaments">Recent Tournaments</button>
    </div>
    
    <div id="organizations" class="tab-panel active">
        <table class="tournament-table">
            <thead>
                <tr>
                    <th class="rank-column">#</th>
                    <th>Organization</th>
                    <th class="number-column">Tournaments</th>
                    <th class="number-column">Total Attendance</th>
                </tr>
            </thead>
            <tbody id="orgs-tbody">
                <!-- Data will be loaded here -->
            </tbody>
        </table>
    </div>
    
    <div id="players" class="tab-panel">
        <table class="tournament-table">
            <thead>
                <tr>
                    <th class="rank-column">#</th>
                    <th>Player</th>
                    <th class="number-column">Points</th>
                    <th class="number-column">Events</th>
                    <th class="number-column">1st Places</th>
                </tr>
            </thead>
            <tbody id="players-tbody">
                <!-- Data will be loaded here -->
            </tbody>
        </table>
    </div>
    
    <div id="tournaments" class="tab-panel">
        <table class="tournament-table">
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Tournament</th>
                    <th>Organization</th>
                    <th class="number-column">Attendees</th>
                    <th>Location</th>
                </tr>
            </thead>
            <tbody id="tournaments-tbody">
                <!-- Data will be loaded here -->
            </tbody>
        </table>
    </div>
</div>

<script>
// Load tournament data from JSON asset
fetch('{{ tournament_data_url }}')
    .then(response => response.json())
    .then(data => {
        // Update last updated
        const lastUpdated = new Date(data.last_updated);
        document.getElementById('last-updated').textContent = 
            'Last updated: ' + lastUpdated.toLocaleString('en-US', {
                timeZone: 'America/Los_Angeles',
                dateStyle: 'medium',
                timeStyle: 'short'
            });
        
        // Update stats
        const statsHtml = `
            <div class="stat-card">
                <div class="stat-value">${data.organizations.length}</div>
                <div class="stat-label">Organizations</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${data.players.length}</div>
                <div class="stat-label">Top Players</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${data.tournaments.length}</div>
                <div class="stat-label">Recent Tournaments</div>
            </div>
        `;
        document.getElementById('stats-container').innerHTML = statsHtml;
        
        // Populate organizations
        const orgsHtml = data.organizations.map((org, i) => `
            <tr>
                <td class="rank-column">${i + 1}</td>
                <td>${org.name}</td>
                <td class="number-column">${org.tournament_count}</td>
                <td class="number-column">${org.total_attendance.toLocaleString()}</td>
            </tr>
        `).join('');
        document.getElementById('orgs-tbody').innerHTML = orgsHtml;
        
        // Populate players
        const playersHtml = data.players.map((player, i) => `
            <tr>
                <td class="rank-column">${i + 1}</td>
                <td>${player.name}</td>
                <td class="number-column">${player.points}</td>
                <td class="number-column">${player.events}</td>
                <td class="number-column">${player.first_places}</td>
            </tr>
        `).join('');
        document.getElementById('players-tbody').innerHTML = playersHtml;
        
        // Populate tournaments
        const tournamentsHtml = data.tournaments.map(t => `
            <tr>
                <td>${t.date}</td>
                <td>${t.name}</td>
                <td>${t.organization}</td>
                <td class="number-column">${t.attendees}</td>
                <td>${t.city}${t.state ? ', ' + t.state : ''}</td>
            </tr>
        `).join('');
        document.getElementById('tournaments-tbody').innerHTML = tournamentsHtml;
    })
    .catch(error => {
        console.error('Error loading tournament data:', error);
        document.getElementById('last-updated').textContent = 'Error loading data';
    });

// Tab switching
document.querySelectorAll('.tab-button').forEach(button => {
    button.addEventListener('click', function() {
        const tabName = this.getAttribute('data-tab');
        
        // Update buttons
        document.querySelectorAll('.tab-button').forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        
        // Update panels
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        document.getElementById(tabName).classList.add('active');
    });
});
</script>
"""
    return liquid_content

def publish_to_shopify():
    """Publish tournament data to Shopify using proper asset structure"""
    
    print("=== Shopify Asset Publisher ===")
    
    # Get tournament data
    print("Fetching tournament data...")
    data = get_tournament_data()
    print(f"Found {len(data['organizations'])} organizations, {len(data['players'])} players")
    
    token = os.getenv('SHOPIFY_ACCESS_TOKEN')
    domain = os.getenv('SHOPIFY_DOMAIN')
    headers = {'X-Shopify-Access-Token': token, 'Content-Type': 'application/json'}
    
    with httpx.Client(timeout=60.0) as client:
        # Get theme
        resp = client.get(f'https://{domain}/admin/api/2023-10/themes.json', headers=headers)
        themes = resp.json()['themes']
        theme_id = next(t['id'] for t in themes if t.get('role') == 'main')
        print(f"Using theme ID: {theme_id}")
        
        asset_url = f'https://{domain}/admin/api/2023-10/themes/{theme_id}/assets.json'
        
        # 1. Upload CSS file
        print("\n1. Uploading CSS...")
        css_data = {
            'asset': {
                'key': 'assets/tournament-rankings.css',
                'value': create_css_asset()
            }
        }
        resp = client.put(asset_url, headers=headers, json=css_data)
        if resp.status_code in [200, 201]:
            print("✅ CSS uploaded successfully")
        else:
            print(f"❌ CSS upload failed: {resp.status_code}")
            return False
        
        # 2. Upload JSON data
        print("\n2. Uploading tournament data...")
        json_data = {
            'asset': {
                'key': 'assets/tournament-data.json',
                'value': json.dumps(data, separators=(',', ':'))  # Compact JSON
            }
        }
        resp = client.put(asset_url, headers=headers, json=json_data)
        if resp.status_code in [200, 201]:
            print("✅ Data uploaded successfully")
            data_asset_url = f"https://{domain}/cdn/shop/t/{theme_id}/assets/tournament-data.json"
        else:
            print(f"❌ Data upload failed: {resp.status_code}")
            return False
        
        # 3. Update the page template
        print("\n3. Updating page template...")
        
        # Get current template
        resp = client.get(asset_url, headers=headers, params={'asset[key]': 'templates/page.attendance.json'})
        if resp.status_code == 200:
            current_template = json.loads(resp.json()['asset']['value'])
        else:
            current_template = {'sections': {}, 'order': []}
        
        # Find or create custom liquid section
        liquid_section = None
        for key, section in current_template.get('sections', {}).items():
            if section.get('type') == 'custom-liquid':
                liquid_section = key
                break
        
        if not liquid_section:
            liquid_section = 'tournament_content'
            current_template['sections'][liquid_section] = {
                'type': 'custom-liquid',
                'settings': {}
            }
            if liquid_section not in current_template.get('order', []):
                current_template.setdefault('order', []).append(liquid_section)
        
        # Update with our liquid template
        current_template['sections'][liquid_section]['settings']['custom_liquid'] = create_liquid_template()
        
        # Save template
        template_data = {
            'asset': {
                'key': 'templates/page.attendance.json',
                'value': json.dumps(current_template, indent=2)
            }
        }
        resp = client.put(asset_url, headers=headers, json=template_data)
        if resp.status_code in [200, 201]:
            print("✅ Template updated successfully")
        else:
            print(f"❌ Template update failed: {resp.status_code}")
            print(resp.text[:500])
            return False
        
        print("\n✅ All assets published successfully!")
        print(f"View at: https://backyardtryhards.com/pages/attendance")
        return True

if __name__ == "__main__":
    success = publish_to_shopify()
    sys.exit(0 if success else 1)