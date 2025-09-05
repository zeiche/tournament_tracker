#!/usr/bin/env python3
"""Update the attendance page on Shopify with fresh data"""
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
from tournament_models import Tournament, Organization
from sqlalchemy import func

SHOPIFY_DOMAIN = os.getenv('SHOPIFY_DOMAIN')
SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')

headers = {
    'X-Shopify-Access-Token': SHOPIFY_ACCESS_TOKEN,
    'Content-Type': 'application/json'
}

print("Gathering tournament data...")

# Get organization statistics
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
    
    # Get total statistics
    total_tournaments = session.query(Tournament).count()
    total_attendance = session.query(func.sum(Tournament.num_attendees)).scalar() or 0
    total_orgs = session.query(Organization).count()

print(f"Found {len(org_stats)} organizations with data")

# Generate HTML content for attendance page
html_content = f"""
<div style="max-width: 1200px; margin: 0 auto; padding: 20px;">
    <h1 style="text-align: center; margin-bottom: 10px;">Tournament Attendance Rankings</h1>
    <p style="text-align: center; color: #666; margin-bottom: 30px;">
        Data from start.gg • Updated {datetime.now().strftime('%B %d, %Y at %I:%M %p')} Pacific
    </p>
    
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 40px;">
        <div style="background: #f0f0f0; padding: 20px; border-radius: 8px; text-align: center;">
            <div style="font-size: 32px; font-weight: bold; color: #333;">{total_orgs:,}</div>
            <div style="color: #666; margin-top: 5px;">Organizations</div>
        </div>
        <div style="background: #f0f0f0; padding: 20px; border-radius: 8px; text-align: center;">
            <div style="font-size: 32px; font-weight: bold; color: #333;">{total_tournaments:,}</div>
            <div style="color: #666; margin-top: 5px;">Tournaments</div>
        </div>
        <div style="background: #f0f0f0; padding: 20px; border-radius: 8px; text-align: center;">
            <div style="font-size: 32px; font-weight: bold; color: #333;">{int(total_attendance):,}</div>
            <div style="color: #666; margin-top: 5px;">Total Attendances</div>
        </div>
    </div>
    
    <table style="width: 100%; border-collapse: collapse; background: white;">
        <thead>
            <tr style="background: #333; color: white;">
                <th style="padding: 12px; text-align: left; font-weight: 500;">Rank</th>
                <th style="padding: 12px; text-align: left; font-weight: 500;">Organization</th>
                <th style="padding: 12px; text-align: center; font-weight: 500;">Tournaments</th>
                <th style="padding: 12px; text-align: center; font-weight: 500;">Total Attendance</th>
            </tr>
        </thead>
        <tbody>
"""

# Add table rows
for i, stat in enumerate(org_stats, 1):
    org_name = stat.owner_name
    tournament_count = stat.tournament_count or 0
    total_att = int(stat.total_attendance or 0)
    
    # Highlight BACKYARD TRY-HARDS
    row_style = "background: #ffffcc;" if "BACKYARD" in org_name.upper() else "background: white;" if i % 2 == 0 else "background: #f9f9f9;"
    
    html_content += f"""
            <tr style="{row_style}">
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{i}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; font-weight: {'bold' if 'BACKYARD' in org_name.upper() else 'normal'};">
                    {org_name}
                </td>
                <td style="padding: 10px; text-align: center; border-bottom: 1px solid #ddd;">{tournament_count}</td>
                <td style="padding: 10px; text-align: center; border-bottom: 1px solid #ddd;">{total_att:,}</td>
            </tr>
"""

html_content += """
        </tbody>
    </table>
    
    <div style="margin-top: 40px; padding: 20px; background: #f0f0f0; border-radius: 8px;">
        <p style="margin: 0; font-size: 14px; color: #666;">
            <strong>About this data:</strong> Rankings are based on total tournament attendance from start.gg. 
            Data includes all Fighting Game Community tournaments in Southern California from 2024-2025.
            Updated automatically from the Tournament Tracker system.
        </p>
    </div>
</div>
"""

# Find and update the attendance page
print("Finding attendance page...")
list_url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/pages.json"
response = requests.get(list_url, headers=headers)

attendance_page_id = None
if response.status_code == 200:
    pages = response.json().get('pages', [])
    for page in pages:
        if page.get('handle') == 'attendance':
            attendance_page_id = page.get('id')
            print(f"Found attendance page: ID {attendance_page_id}")
            break

if attendance_page_id:
    # Update the existing attendance page
    update_url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/pages/{attendance_page_id}.json"
    
    payload = {
        'page': {
            'id': attendance_page_id,
            'title': 'Tournament Attendance Rankings',
            'body_html': html_content
        }
    }
    
    print("Updating attendance page...")
    update_response = requests.put(update_url, headers=headers, json=payload)
    
    if update_response.status_code in [200, 201]:
        print(f"✅ Attendance page updated successfully!")
        print(f"   View at: https://backyardtryhards.com/pages/attendance")
        print(f"   Admin: https://{SHOPIFY_DOMAIN}/admin/online_store/pages/{attendance_page_id}")
    else:
        print(f"❌ Failed to update: {update_response.status_code}")
        print(f"   Error: {update_response.text}")
else:
    print("❌ Attendance page not found!")