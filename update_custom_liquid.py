#!/usr/bin/env python3
"""Update the custom-liquid section in the template"""
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

SHOPIFY_DOMAIN = os.getenv('SHOPIFY_DOMAIN')
SHOPIFY_ACCESS_TOKEN = os.getenv('SHOPIFY_ACCESS_TOKEN')

headers = {
    'X-Shopify-Access-Token': SHOPIFY_ACCESS_TOKEN,
    'Content-Type': 'application/json'
}

# Get theme ID
themes_url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/themes.json"
response = requests.get(themes_url, headers=headers)
theme_id = None

if response.status_code == 200:
    themes = response.json().get('themes', [])
    for theme in themes:
        if theme.get('role') == 'main':
            theme_id = theme.get('id')
            print(f"Active theme ID: {theme_id}")
            break

# Check if there's a custom-liquid section file
section_key = "sections/custom-liquid.liquid"
get_url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/themes/{theme_id}/assets.json"
params = {'asset[key]': section_key}

print(f"\nChecking for custom-liquid section...")
section_response = requests.get(get_url, headers=headers, params=params)

if section_response.status_code == 200:
    print("Found custom-liquid.liquid section file")

# Now get the attendance template
template_key = "templates/page.attendance.json"
params = {'asset[key]': template_key}

print(f"\nFetching template: {template_key}")
template_response = requests.get(get_url, headers=headers, params=params)

if template_response.status_code == 200:
    asset = template_response.json().get('asset', {})
    content = asset.get('value', '')
    
    try:
        data = json.loads(content)
        
        # Find and update the custom-liquid section
        for section_id, section in data.get('sections', {}).items():
            if section.get('type') == 'custom-liquid':
                print(f"\nFound custom-liquid section: {section_id}")
                
                # Get current settings
                settings = section.get('settings', {})
                
                # Look for the custom_liquid field
                if 'custom_liquid' in settings:
                    old_content = settings['custom_liquid']
                    print(f"Current content length: {len(old_content)} chars")
                    
                    if 'OneMustFall' in old_content or 'August' in old_content:
                        print("⚠️  Contains old data - replacing...")
                    
                    # Create new liquid content with fresh data
                    new_liquid = f"""
<div style="background: linear-gradient(45deg, #00ff00, #00cc00); padding: 30px; text-align: center; border-radius: 10px; margin-bottom: 30px;">
    <h1 style="color: white; margin: 0;">🎮 TOURNAMENT RANKINGS UPDATED 🎮</h1>
    <p style="color: white; font-size: 18px; margin: 10px 0;">Live data from Tournament Tracker</p>
    <p style="color: white; font-size: 16px; margin: 0;">Last sync: {datetime.now().strftime('%B %d, %Y at %I:%M %p')} Pacific</p>
</div>

<p style="text-align: center; font-size: 16px; margin: 20px 0;">
    Tournament attendance rankings from <a href="https://www.start.gg/" style="color: #0066cc;">start.gg</a>
</p>

<style>
    .rankings-table {{
        width: 100%;
        border-collapse: collapse;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    .rankings-table th {{
        background: #333;
        color: white;
        padding: 12px;
        text-align: left;
        font-weight: 500;
    }}
    .rankings-table td {{
        padding: 10px 12px;
        border-bottom: 1px solid #ddd;
    }}
    .rankings-table tr:nth-child(even) {{
        background: #f9f9f9;
    }}
    .highlight-row {{
        background: #ffffcc !important;
        font-weight: bold;
    }}
</style>

<table class="rankings-table">
    <thead>
        <tr>
            <th>Rank</th>
            <th>Organization</th>
            <th style="text-align: center;">Tournaments</th>
            <th style="text-align: center;">Total Attendance</th>
        </tr>
    </thead>
    <tbody>
        <tr class="highlight-row">
            <td>1</td>
            <td>UPDATED DATA - {datetime.now().strftime('%H:%M:%S')}</td>
            <td style="text-align: center;">100</td>
            <td style="text-align: center;">10,000</td>
        </tr>
        <tr>
            <td>2</td>
            <td>Fresh Organization</td>
            <td style="text-align: center;">80</td>
            <td style="text-align: center;">8,000</td>
        </tr>
        <tr>
            <td>3</td>
            <td>New Tournament Group</td>
            <td style="text-align: center;">75</td>
            <td style="text-align: center;">7,500</td>
        </tr>
        <tr class="highlight-row">
            <td>6</td>
            <td>BACKYARD TRY-HARDS</td>
            <td style="text-align: center;">45</td>
            <td style="text-align: center;">4,500</td>
        </tr>
    </tbody>
</table>

<div style="margin-top: 40px; padding: 20px; background: #e8f4f8; border-left: 4px solid #0066cc;">
    <p style="margin: 0; color: #333;">
        <strong>About this data:</strong> Rankings based on total attendance from all Fighting Game Community tournaments 
        in Southern California. Data is automatically synchronized from start.gg via the Tournament Tracker system.
    </p>
</div>
"""
                    
                    # Update the section
                    section['settings']['custom_liquid'] = new_liquid
                    print("✅ Replaced custom_liquid content")
                    
                    # Save the updated template
                    updated_json = json.dumps(data, indent=2)
                    
                    print("\nSaving updated template...")
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
                        print("✅ Template saved successfully!")
                        
                        # Force cache clear by updating page timestamp
                        page_url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/pages/108546031752.json"
                        touch_payload = {
                            'page': {
                                'id': 108546031752,
                                'title': f'Tournament Attendance Rankings'
                            }
                        }
                        touch_response = requests.put(page_url, headers=headers, json=touch_payload)
                        if touch_response.status_code in [200, 201]:
                            print("✅ Page touched to clear cache")
                        
                        print("\n" + "="*60)
                        print("SUCCESS!")
                        print("="*60)
                        print("The attendance page has been updated with:")
                        print("- GREEN gradient header box")
                        print("- Current timestamp")
                        print("- Fresh test data")
                        print("\nCheck: https://backyardtryhards.com/pages/attendance")
                        print("\nIf you still see old content:")
                        print("1. The page might be cached by Cloudflare")
                        print("2. Try adding ?v=2 to the URL")
                        print("3. Check Cloudflare cache settings")
                    else:
                        print(f"❌ Failed to save: {update_response.status_code}")
                        print(update_response.text)
                else:
                    print("❌ No custom_liquid field found in settings")
                    print(f"Available settings: {list(settings.keys())}")
                    
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error: {e}")
else:
    print(f"❌ Could not fetch template: {template_response.status_code}")