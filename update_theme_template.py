#!/usr/bin/env python3
"""Update the theme template file directly"""
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

# Get database data
from database import session_scope
from tournament_models import Tournament
from sqlalchemy import func

SHOPIFY_DOMAIN = os.getenv('SHOPIFY_DOMAIN')
SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')

headers = {
    'X-Shopify-Access-Token': SHOPIFY_ACCESS_TOKEN,
    'Content-Type': 'application/json'
}

print("Gathering fresh tournament data...")

# Get tournament statistics
with session_scope() as session:
    # Get tournament statistics grouped by owner
    org_stats = session.query(
        Tournament.owner_name,
        func.count(Tournament.id).label('tournament_count'),
        func.sum(Tournament.num_attendees).label('total_attendance')
    ).filter(
        Tournament.owner_name.isnot(None)
    ).group_by(
        Tournament.owner_name
    ).order_by(
        func.sum(Tournament.num_attendees).desc()
    ).limit(150).all()
    
    total_tournaments = session.query(Tournament).count()
    total_attendance = session.query(func.sum(Tournament.num_attendees)).scalar() or 0
    unique_orgs = len(org_stats)

print(f"Found {len(org_stats)} organizations with data")

# Get the theme ID
themes_url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/themes.json"
response = requests.get(themes_url, headers=headers)
theme_id = None

if response.status_code == 200:
    themes = response.json().get('themes', [])
    for theme in themes:
        if theme.get('role') == 'main':
            theme_id = theme.get('id')
            print(f"Found active theme: {theme.get('name')} (ID: {theme_id})")
            break

if not theme_id:
    print("❌ Could not find active theme")
    exit(1)

# First, get the current template structure
print("\nFetching current template structure...")
template_key = "templates/page.attendance.json"
get_url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/themes/{theme_id}/assets.json?asset[key]={template_key}"
template_response = requests.get(get_url, headers=headers)

if template_response.status_code == 200:
    current_template = template_response.json().get('asset', {}).get('value', '')
    print("Current template retrieved")
    
    # Parse the JSON template
    try:
        template_data = json.loads(current_template)
        
        # Find the section that contains the content
        for section_key, section_data in template_data.get('sections', {}).items():
            if section_data.get('type') == 'rich-text':
                # Update the blocks with fresh data
                
                # Build new content HTML
                rows_html = ""
                for i, stat in enumerate(org_stats[:120], 1):  # Top 120 orgs
                    org_name = stat.owner_name
                    tournament_count = stat.tournament_count or 0
                    total_att = int(stat.total_attendance or 0)
                    
                    # Highlight BACKYARD TRY-HARDS
                    style = 'style="background-color: #ffffcc;"' if "BACKYARD" in org_name.upper() else ''
                    
                    rows_html += f"""
                    <tr {style}>
                        <td>{i}</td>
                        <td>{"<strong>" if "BACKYARD" in org_name.upper() else ""}{org_name}{"</strong>" if "BACKYARD" in org_name.upper() else ""}</td>
                        <td style="text-align: center;">{tournament_count}</td>
                        <td style="text-align: center;">{total_att:,}</td>
                    </tr>"""
                
                new_content = f"""
                <p style="text-align: center;">The following rankings are based on total tournament attendance from <a href="https://www.start.gg/" target="_blank">start.gg</a>.
                Data was last updated on <strong>{datetime.now().strftime('%B %d, %Y at %I:%M %p')} Pacific</strong>.
                The table below tracks <strong>{unique_orgs} organizations</strong> and <strong>{int(total_attendance):,} total tournament attendances</strong>.</p>
                
                <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                    <thead>
                        <tr style="background-color: #f0f0f0;">
                            <th style="padding: 8px; text-align: left;">Rank</th>
                            <th style="padding: 8px; text-align: left;">Organization</th>
                            <th style="padding: 8px; text-align: center;">Tournaments</th>
                            <th style="padding: 8px; text-align: center;">Total Attendance</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
                """
                
                # Update the text block
                for block_id, block_data in section_data.get('blocks', {}).items():
                    if block_data.get('type') == 'text':
                        block_data['settings']['text'] = new_content
                        print(f"Updated content block in section {section_key}")
                        break
                break
        
        # Convert back to JSON
        updated_template = json.dumps(template_data, indent=2)
        
        # Update the theme asset
        print("\nUpdating theme template...")
        update_url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/themes/{theme_id}/assets.json"
        update_payload = {
            'asset': {
                'key': template_key,
                'value': updated_template
            }
        }
        
        update_response = requests.put(update_url, headers=headers, json=update_payload)
        
        if update_response.status_code in [200, 201]:
            print("✅ Theme template updated successfully!")
            print(f"\nView at: https://backyardtryhards.com/pages/attendance")
            print("Note: May take 30-60 seconds for changes to appear")
        else:
            print(f"❌ Failed to update template: {update_response.status_code}")
            print(update_response.text)
            
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse template JSON: {e}")
else:
    print(f"❌ Could not fetch template: {template_response.status_code}")