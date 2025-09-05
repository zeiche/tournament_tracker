#!/usr/bin/env python3
"""Investigate why pages aren't publishing to live site"""
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

print("=" * 60)
print("INVESTIGATING PUBLISH ISSUE")
print("=" * 60)

# Check page visibility and publishing status
attendance_page_id = "108546031752"
url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/pages/{attendance_page_id}.json"

print(f"\n1. CHECKING PAGE VISIBILITY SETTINGS:")
print("-" * 40)

response = requests.get(url, headers=headers)
if response.status_code == 200:
    data = response.json()
    page = data.get('page', {})
    
    print(f"Page ID: {page.get('id')}")
    print(f"Title: {page.get('title')}")
    print(f"Handle: {page.get('handle')}")
    print(f"Created: {page.get('created_at')}")
    print(f"Updated: {page.get('updated_at')}")
    print(f"Published: {page.get('published_at')}")
    print(f"Published (bool): {page.get('published', 'NOT SET')}")
    print(f"Template suffix: {page.get('template_suffix', 'default')}")
    
    # Check if page is actually published
    if page.get('published_at'):
        pub_time = datetime.fromisoformat(page.get('published_at').replace('Z', '+00:00'))
        update_time = datetime.fromisoformat(page.get('updated_at').replace('Z', '+00:00'))
        
        if update_time > pub_time:
            print(f"\n⚠️  WARNING: Page was updated AFTER publishing!")
            print(f"   Published: {pub_time}")
            print(f"   Updated: {update_time}")
            print(f"   This might need republishing!")

print(f"\n2. TESTING ONLINE STORE API:")
print("-" * 40)

# Try the Online Store API (different from Admin API)
online_url = f"https://{SHOPIFY_DOMAIN}/pages/attendance"
print(f"Checking public URL: {online_url}")

public_response = requests.get(online_url)
if public_response.status_code == 200:
    content = public_response.text
    print(f"✅ Page is accessible (length: {len(content)} chars)")
    
    # Check what content is being served
    if "August 26, 2025" in content:
        print("❌ Still showing OLD content (August 26)")
    elif "September" in content:
        print("✅ Showing NEW content (September)")
    elif "ATTENDANCE PAGE TEST UPDATE" in content:
        print("✅ Showing TEST content")
    else:
        print("⚠️  Content unclear")
else:
    print(f"❌ Page not accessible: {public_response.status_code}")

print(f"\n3. FORCING REPUBLISH:")
print("-" * 40)

# Try to force republish by updating the published status
update_payload = {
    'page': {
        'id': attendance_page_id,
        'published': False  # First unpublish
    }
}

print("Step 1: Unpublishing page...")
unpublish_response = requests.put(url, headers=headers, json=update_payload)
if unpublish_response.status_code in [200, 201]:
    print("✅ Page unpublished")
else:
    print(f"❌ Failed to unpublish: {unpublish_response.status_code}")

# Now republish with fresh content
fresh_content = f"""
<div style="background: #00ff00; padding: 40px; text-align: center; font-size: 24px;">
    <h1>🚀 FRESH PUBLISH TEST 🚀</h1>
    <p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p>If you see this GREEN box, the republish worked!</p>
</div>

<div style="max-width: 1200px; margin: 40px auto; padding: 20px;">
    <h1>Tournament Attendance Rankings</h1>
    <p>Updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')} Pacific</p>
    
    <table style="width: 100%; border: 1px solid #ddd;">
        <tr style="background: #333; color: white;">
            <th style="padding: 10px;">Rank</th>
            <th style="padding: 10px;">Organization</th>
            <th style="padding: 10px;">Tournaments</th>
            <th style="padding: 10px;">Attendance</th>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #ddd;">1</td>
            <td style="padding: 10px; border: 1px solid #ddd;">TEST ORG</td>
            <td style="padding: 10px; border: 1px solid #ddd;">999</td>
            <td style="padding: 10px; border: 1px solid #ddd;">99,999</td>
        </tr>
    </table>
</div>
"""

republish_payload = {
    'page': {
        'id': attendance_page_id,
        'body_html': fresh_content,
        'published': True,  # Republish
        'published_at': datetime.now().isoformat()  # Set publish time to now
    }
}

print("Step 2: Republishing with fresh content...")
republish_response = requests.put(url, headers=headers, json=republish_payload)
if republish_response.status_code in [200, 201]:
    print("✅ Page republished with fresh content")
    result = republish_response.json()
    page_data = result.get('page', {})
    print(f"   Published at: {page_data.get('published_at')}")
    print(f"   Updated at: {page_data.get('updated_at')}")
else:
    print(f"❌ Failed to republish: {republish_response.status_code}")
    print(republish_response.text)

print(f"\n4. ALTERNATIVE: CREATE NEW PAGE")
print("-" * 40)
print("Creating a completely new test page...")

new_page_payload = {
    'page': {
        'title': f'Live Test {datetime.now().strftime("%H:%M")}',
        'handle': f'live-test-{datetime.now().strftime("%H%M")}',
        'body_html': f"""
        <div style="background: #ff00ff; padding: 60px; text-align: center;">
            <h1 style="font-size: 48px;">🎯 BRAND NEW PAGE TEST 🎯</h1>
            <p style="font-size: 24px;">Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p style="font-size: 20px;">This is a COMPLETELY NEW page!</p>
        </div>
        """,
        'published': True
    }
}

create_url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/pages.json"
create_response = requests.post(create_url, headers=headers, json=new_page_payload)

if create_response.status_code in [200, 201]:
    new_page = create_response.json().get('page', {})
    new_handle = new_page.get('handle')
    print(f"✅ New page created!")
    print(f"   ID: {new_page.get('id')}")
    print(f"   Handle: {new_handle}")
    print(f"   Test URL: https://backyardtryhards.com/pages/{new_handle}")
else:
    print(f"❌ Failed to create new page: {create_response.status_code}")

print("\n" + "=" * 60)
print("INVESTIGATION COMPLETE")
print("=" * 60)
print("\nCHECK THESE URLS:")
print(f"1. Attendance page: https://backyardtryhards.com/pages/attendance")
print(f"   - Should show GREEN box if republish worked")
print(f"2. New test page: Check URL shown above")
print(f"   - Should show PURPLE box")
print("\nIf neither works, there may be:")
print("- Theme override for page content")
print("- Liquid template issues")
print("- Store-level caching settings")
print("- DNS/CDN configuration issues")