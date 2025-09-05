#!/usr/bin/env python3
"""Generate a self-contained Liquid template with embedded rankings data."""

import json
from datetime import datetime
from tournament_models import Player, TournamentPlacement, Tournament
from session_utils import get_session
from collections import Counter

def generate_liquid_template():
    """Generate Liquid template with embedded rankings data."""
    
    with get_session() as session:
        # Get all players with points
        players = session.query(Player).all()
        
        player_data = []
        for player in players:
            # Calculate points from placements
            player_points = sum(p.points_earned for p in player.placements)
            if player_points > 0:
                # Get placements for top finishes
                placements = session.query(TournamentPlacement).filter(
                    TournamentPlacement.player_id == player.id,
                    TournamentPlacement.placement <= 8
                ).order_by(TournamentPlacement.placement).limit(20).all()
                
                player_data.append((
                    player.id,
                    player.name,
                    player_points,
                    len(player.placements),
                    placements
                ))
        
        # Sort by points
        player_data.sort(key=lambda x: x[2], reverse=True)
        
        # Format data for Liquid
        rankings_data = []
        for rank, (player_id, name, points, events, placements) in enumerate(player_data[:20], 1):
            # Count top finishes
            finish_counts = Counter()
            for p in placements:
                if p.placement <= 3:
                    place_str = ["1st", "2nd", "3rd"][p.placement - 1]
                else:
                    place_str = f"{p.placement}th"
                finish_counts[place_str] += 1
            
            # Format finish string
            finishes_str = ", ".join([f"{pos}({count})" for pos, count in sorted(finish_counts.items())])
            
            rankings_data.append({
                "rank": rank,
                "name": name,
                "points": points,
                "events": events,
                "topFinishes": finishes_str or "No top 8 finishes"
            })
    
    # Generate Liquid template
    template = '''{% comment %}
  Tournament Rankings - Self-Contained Version
  Generated: ''' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '''
{% endcomment %}

{% capture rankings_data %}
''' + json.dumps(rankings_data, indent=2) + '''
{% endcapture %}

{% assign players = rankings_data | parse_json %}

<div class="tournament-rankings">
  <style>
    .tournament-rankings {
      max-width: 900px;
      margin: 2rem auto;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    .rankings-header {
      text-align: center;
      margin-bottom: 2rem;
    }
    
    .rankings-header h2 {
      font-size: 2rem;
      margin-bottom: 0.5rem;
      color: #2c3e50;
    }
    
    .rankings-table {
      width: 100%;
      border-collapse: collapse;
      background: white;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      border-radius: 8px;
      overflow: hidden;
    }
    
    .rankings-table th {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 14px;
      text-align: left;
      font-weight: 600;
      text-transform: uppercase;
      font-size: 13px;
      letter-spacing: 0.5px;
    }
    
    .rankings-table td {
      padding: 12px 14px;
      border-bottom: 1px solid #e8e8e8;
    }
    
    .rankings-table tbody tr:last-child td {
      border-bottom: none;
    }
    
    .rankings-table tr:hover {
      background: #f8f9fa;
      transition: background 0.2s;
    }
    
    .rank-badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 32px;
      height: 32px;
      border-radius: 50%;
      font-weight: bold;
      font-size: 14px;
    }
    
    .rank-1 { 
      background: linear-gradient(135deg, #FFD700, #FFA500);
      color: #333;
      box-shadow: 0 2px 4px rgba(255, 215, 0, 0.3);
    }
    
    .rank-2 { 
      background: linear-gradient(135deg, #C0C0C0, #B8B8B8);
      color: #333;
      box-shadow: 0 2px 4px rgba(192, 192, 192, 0.3);
    }
    
    .rank-3 { 
      background: linear-gradient(135deg, #CD7F32, #B87333);
      color: white;
      box-shadow: 0 2px 4px rgba(205, 127, 50, 0.3);
    }
    
    .rank-other { 
      background: #6c757d;
      color: white;
    }
    
    .player-name {
      font-weight: 600;
      color: #2c3e50;
      font-size: 15px;
    }
    
    .points-value {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 4px 10px;
      border-radius: 20px;
      font-size: 14px;
      font-weight: 600;
      display: inline-block;
    }
    
    .events-count {
      color: #6c757d;
      font-size: 14px;
    }
    
    .top-finishes {
      font-size: 13px;
      color: #495057;
    }
    
    .last-updated {
      text-align: center;
      margin-top: 1.5rem;
      color: #6c757d;
      font-size: 13px;
      font-style: italic;
    }
    
    @media (max-width: 640px) {
      .rankings-table {
        font-size: 14px;
      }
      
      .rankings-table th,
      .rankings-table td {
        padding: 8px;
      }
      
      .top-finishes {
        font-size: 12px;
      }
    }
  </style>
  
  <div class="rankings-header">
    <h2>Tournament Rankings</h2>
    <p>San Diego Melee Power Rankings</p>
  </div>
  
  <table class="rankings-table">
    <thead>
      <tr>
        <th>Rank</th>
        <th>Player</th>
        <th>Points</th>
        <th>Events</th>
        <th>Top Finishes</th>
      </tr>
    </thead>
    <tbody>
      {% for player in players %}
        <tr>
          <td>
            {% if player.rank == 1 %}
              <span class="rank-badge rank-1">{{ player.rank }}</span>
            {% elsif player.rank == 2 %}
              <span class="rank-badge rank-2">{{ player.rank }}</span>
            {% elsif player.rank == 3 %}
              <span class="rank-badge rank-3">{{ player.rank }}</span>
            {% else %}
              <span class="rank-badge rank-other">{{ player.rank }}</span>
            {% endif %}
          </td>
          <td class="player-name">{{ player.name }}</td>
          <td><span class="points-value">{{ player.points }}</span></td>
          <td class="events-count">{{ player.events }}</td>
          <td class="top-finishes">{{ player.topFinishes }}</td>
        </tr>
      {% endfor %}
    </tbody>
  </table>
  
  <div class="last-updated">
    Last updated: {{ 'now' | date: '%B %d, %Y at %l:%M %p' }}
  </div>
</div>'''
    
    return template

def main():
    """Generate and save the Liquid template."""
    template = generate_liquid_template()
    
    # Save to file
    output_file = 'shopify_rankings_embedded.liquid'
    with open(output_file, 'w') as f:
        f.write(template)
    
    print(f"✅ Generated self-contained Liquid template: {output_file}")
    print("📋 Copy this template to your Shopify theme")
    print("📝 To update: Run this script again and replace the template")

if __name__ == "__main__":
    main()