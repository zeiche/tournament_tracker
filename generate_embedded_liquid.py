#!/usr/bin/env python3
"""Generate a self-contained Liquid template with embedded tournament data."""

import json
from datetime import datetime
from shopify_service import ShopifyService

def generate_embedded_liquid():
    """Generate Liquid template with all data embedded."""
    
    # Get current tournament data
    service = ShopifyService()
    data = service._gather_tournament_data()
    
    # Extract just the data we need for embedding
    embedded_data = {
        "rankings": data["rankings"][:20],  # Top 20 players
        "lastUpdated": datetime.now().strftime("%B %d, %Y at %I:%M %p")
    }
    
    template = '''{% comment %}
  Tournament Rankings - Self-Contained Shopify Template
  Generated: ''' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '''
  
  This template contains all ranking data embedded directly in the Liquid code.
  To update: Re-run the generator script and replace this template.
{% endcomment %}

{% capture rankings_json %}
''' + json.dumps(embedded_data["rankings"], indent=2) + '''
{% endcapture %}

{% assign players = rankings_json | parse_json %}

<div class="tournament-rankings-container">
  <style>
    .tournament-rankings-container {
      max-width: 1000px;
      margin: 2rem auto;
      padding: 0 1rem;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    .rankings-header {
      text-align: center;
      margin-bottom: 2rem;
      padding: 2rem;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border-radius: 12px;
    }
    
    .rankings-header h1 {
      font-size: 2.5rem;
      margin: 0 0 0.5rem 0;
      font-weight: 700;
    }
    
    .rankings-header p {
      margin: 0;
      opacity: 0.95;
      font-size: 1.1rem;
    }
    
    .rankings-table {
      width: 100%;
      border-collapse: separate;
      border-spacing: 0;
      background: white;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
      border-radius: 12px;
      overflow: hidden;
    }
    
    .rankings-table thead {
      background: #f8f9fa;
    }
    
    .rankings-table th {
      padding: 1rem;
      text-align: left;
      font-weight: 600;
      color: #495057;
      text-transform: uppercase;
      font-size: 0.75rem;
      letter-spacing: 1px;
      border-bottom: 2px solid #dee2e6;
    }
    
    .rankings-table td {
      padding: 1rem;
      border-bottom: 1px solid #f1f3f5;
    }
    
    .rankings-table tbody tr:last-child td {
      border-bottom: none;
    }
    
    .rankings-table tbody tr:hover {
      background: #f8f9fa;
      transition: background 0.15s ease;
    }
    
    /* Rank column styling */
    .rank-cell {
      font-weight: 700;
      width: 60px;
    }
    
    .rank-medal {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 36px;
      height: 36px;
      border-radius: 50%;
      font-size: 16px;
    }
    
    .rank-1 {
      background: linear-gradient(135deg, #FFD700, #FFC107);
      color: #333;
      box-shadow: 0 2px 4px rgba(255, 193, 7, 0.3);
    }
    
    .rank-2 {
      background: linear-gradient(135deg, #E5E5E5, #BDBDBD);
      color: #333;
      box-shadow: 0 2px 4px rgba(189, 189, 189, 0.3);
    }
    
    .rank-3 {
      background: linear-gradient(135deg, #CD7F32, #A0522D);
      color: white;
      box-shadow: 0 2px 4px rgba(205, 127, 50, 0.3);
    }
    
    .rank-other {
      background: #6c757d;
      color: white;
      font-size: 14px;
    }
    
    /* Player name styling */
    .player-name {
      font-weight: 600;
      color: #212529;
      font-size: 1.05rem;
    }
    
    .player-name:hover {
      color: #667eea;
      transition: color 0.15s ease;
    }
    
    /* Points styling */
    .points-badge {
      display: inline-block;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 0.25rem 0.75rem;
      border-radius: 20px;
      font-weight: 600;
      font-size: 0.9rem;
    }
    
    /* Events styling */
    .events-count {
      color: #6c757d;
      font-size: 0.95rem;
    }
    
    /* Attendance styling */
    .attendance-bar {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    
    .attendance-progress {
      flex: 1;
      height: 8px;
      background: #e9ecef;
      border-radius: 4px;
      overflow: hidden;
      max-width: 100px;
    }
    
    .attendance-fill {
      height: 100%;
      background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
      border-radius: 4px;
      transition: width 0.3s ease;
    }
    
    .attendance-text {
      color: #6c757d;
      font-size: 0.85rem;
      min-width: 35px;
    }
    
    /* Footer */
    .rankings-footer {
      margin-top: 2rem;
      padding: 1rem;
      text-align: center;
      color: #6c757d;
      font-size: 0.875rem;
    }
    
    .update-time {
      font-style: italic;
    }
    
    /* Mobile responsive */
    @media (max-width: 768px) {
      .rankings-header h1 {
        font-size: 1.75rem;
      }
      
      .rankings-table {
        font-size: 0.9rem;
      }
      
      .rankings-table th,
      .rankings-table td {
        padding: 0.75rem 0.5rem;
      }
      
      .rank-medal {
        width: 30px;
        height: 30px;
        font-size: 14px;
      }
      
      .attendance-progress {
        max-width: 60px;
      }
      
      /* Hide attendance column on mobile */
      .attendance-column {
        display: none;
      }
    }
  </style>
  
  <div class="rankings-header">
    <h1>🏆 Tournament Rankings</h1>
    <p>San Diego Melee Power Rankings - Current Season</p>
  </div>
  
  <table class="rankings-table">
    <thead>
      <tr>
        <th class="rank-cell">Rank</th>
        <th>Player</th>
        <th>Points</th>
        <th>Events</th>
        <th class="attendance-column">Attendance</th>
      </tr>
    </thead>
    <tbody>
      {% for player in players %}
        <tr>
          <td class="rank-cell">
            {% if player.rank == 1 %}
              <span class="rank-medal rank-1">1</span>
            {% elsif player.rank == 2 %}
              <span class="rank-medal rank-2">2</span>
            {% elsif player.rank == 3 %}
              <span class="rank-medal rank-3">3</span>
            {% elsif player.rank <= 10 %}
              <span class="rank-medal rank-other">{{ player.rank }}</span>
            {% else %}
              <span style="color: #6c757d; font-weight: 600;">{{ player.rank }}</span>
            {% endif %}
          </td>
          <td>
            <span class="player-name">{{ player.name }}</span>
          </td>
          <td>
            <span class="points-badge">{{ player.points }}</span>
          </td>
          <td>
            <span class="events-count">{{ player.events }}</span>
          </td>
          <td class="attendance-column">
            <div class="attendance-bar">
              <div class="attendance-progress">
                <div class="attendance-fill" style="width: {{ player.attendance }}%;"></div>
              </div>
              <span class="attendance-text">{{ player.attendance }}%</span>
            </div>
          </td>
        </tr>
      {% endfor %}
    </tbody>
  </table>
  
  <div class="rankings-footer">
    <p class="update-time">
      Last updated: ''' + embedded_data["lastUpdated"] + '''
    </p>
    <p>
      Data sourced from <a href="https://start.gg" target="_blank" style="color: #667eea;">start.gg</a>
    </p>
  </div>
</div>

{% comment %}
  Instructions for updating:
  1. Run: python3 generate_embedded_liquid.py
  2. Copy the generated shopify_embedded_rankings.liquid file
  3. Replace this template in your Shopify theme
  4. The data is now embedded and will load instantly
{% endcomment %}'''
    
    return template

def main():
    """Generate and save the embedded Liquid template."""
    print("📊 Generating embedded Liquid template...")
    
    try:
        template = generate_embedded_liquid()
        
        # Save to file
        output_file = 'shopify_embedded_rankings.liquid'
        with open(output_file, 'w') as f:
            f.write(template)
        
        print(f"✅ Successfully generated: {output_file}")
        print("\n📋 Next steps:")
        print("1. Copy the contents of shopify_embedded_rankings.liquid")
        print("2. Paste into your Shopify theme (e.g., page.tournament-rankings.liquid)")
        print("3. The rankings will display with all data embedded")
        print("\n💡 Benefits of embedded data:")
        print("- No external API calls needed")
        print("- Instant page load")
        print("- Works offline")
        print("- SEO friendly")
        
    except Exception as e:
        print(f"❌ Error generating template: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()