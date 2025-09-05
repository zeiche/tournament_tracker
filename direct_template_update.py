#!/usr/bin/env python3
"""Direct template update - find and replace the exact content"""
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

# Get the template
template_key = "templates/page.attendance.json"
get_url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/themes/{theme_id}/assets.json"
params = {'asset[key]': template_key}

print(f"\nFetching template: {template_key}")
template_response = requests.get(get_url, headers=headers, params=params)

if template_response.status_code == 200:
    asset = template_response.json().get('asset', {})
    content = asset.get('value', '')
    
    print(f"Template size: {len(content)} bytes")
    
    # Parse and examine the structure
    try:
        data = json.loads(content)
        print("\nTemplate structure:")
        print(f"- Sections: {list(data.get('sections', {}).keys())}")
        
        # Look for the content
        for section_id, section in data.get('sections', {}).items():
            print(f"\nSection: {section_id}")
            print(f"  Type: {section.get('type')}")
            
            if section.get('blocks'):
                for block_id, block in section.get('blocks', {}).items():
                    print(f"  Block {block_id}: {block.get('type')}")
                    
                    # Check settings for content
                    settings = block.get('settings', {})
                    for key, value in settings.items():
                        if isinstance(value, str) and len(value) > 100:
                            print(f"    {key}: {value[:100]}...")
                            
                            # Check if this contains the old data
                            if 'OneMustFall' in value or 'August 26' in value:
                                print(f"    ⚠️  FOUND OLD DATA in {section_id}/{block_id}/{key}")
                                
                                # Replace with new content
                                new_html = f"""<div style="background: #00ff00; padding: 20px; text-align: center;">
<h2>🔄 UPDATED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 🔄</h2>
</div>
<p style="text-align: center;">Tournament attendance rankings from <a href="https://www.start.gg/">start.gg</a>.<br>
<strong>Last updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')} Pacific</strong></p>

<table style="width: 100%; border-collapse: collapse;">
<thead>
<tr style="background: #333; color: white;">
<th style="padding: 10px;">Rank</th>
<th style="padding: 10px;">Organization</th>
<th style="padding: 10px;">Tournaments</th>
<th style="padding: 10px;">Attendance</th>
</tr>
</thead>
<tbody>
<tr style="background: #ffffcc;">
<td style="padding: 8px;">1</td>
<td style="padding: 8px;"><strong>FRESH DATA TEST</strong></td>
<td style="padding: 8px; text-align: center;">999</td>
<td style="padding: 8px; text-align: center;">99,999</td>
</tr>
<tr>
<td style="padding: 8px;">2</td>
<td style="padding: 8px;">Updated Organization</td>
<td style="padding: 8px; text-align: center;">50</td>
<td style="padding: 8px; text-align: center;">5,000</td>
</tr>
</tbody>
</table>

<p style="margin-top: 20px; padding: 20px; background: #f0f0f0;">
<strong>Note:</strong> This data was updated via API at {datetime.now().strftime('%H:%M:%S')}.
If you see this, the update worked!
</p>"""
                                
                                # Update the content
                                block['settings'][key] = new_html
                                print(f"    ✅ REPLACED with new content")
        
        # Save the updated template
        updated_json = json.dumps(data, indent=2)
        
        print("\n" + "="*60)
        print("UPDATING TEMPLATE...")
        print("="*60)
        
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
            print("✅ Template updated successfully!")
            
            # Verify the update
            print("\nVerifying update...")
            verify_response = requests.get(get_url, headers=headers, params=params)
            if verify_response.status_code == 200:
                verify_content = verify_response.json().get('asset', {}).get('value', '')
                if 'FRESH DATA TEST' in verify_content:
                    print("✅ Verification: New content is in template")
                else:
                    print("❌ Verification: New content not found")
            
            print("\n" + "="*60)
            print("IMPORTANT:")
            print("="*60)
            print("1. Check: https://backyardtryhards.com/pages/attendance")
            print("2. You should see a GREEN box with 'UPDATED' text")
            print("3. If not visible:")
            print("   - Clear browser cache (Ctrl+Shift+R)")
            print("   - Try incognito mode")
            print("   - Check in Shopify admin theme editor")
        else:
            print(f"❌ Update failed: {update_response.status_code}")
            print(update_response.text)
            
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse JSON: {e}")
else:
    print(f"❌ Could not fetch template: {template_response.status_code}")
    print(template_response.text)