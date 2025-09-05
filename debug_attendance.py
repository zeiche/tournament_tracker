#!/usr/bin/env python3
"""Debug why attendance page isn't updating"""
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
print("ATTENDANCE PAGE DEBUG")
print("=" * 60)

# 1. Get the attendance page details
attendance_page_id = "108546031752"
url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/pages/{attendance_page_id}.json"

print(f"\n1. FETCHING ATTENDANCE PAGE (ID: {attendance_page_id}):")
print("-" * 40)

response = requests.get(url, headers=headers)

if response.status_code == 200:
    data = response.json()
    page = data.get('page', {})
    
    print(f"Title: {page.get('title')}")
    print(f"Handle: {page.get('handle')}")
    print(f"Updated at: {page.get('updated_at')}")
    print(f"Published at: {page.get('published_at')}")
    
    body = page.get('body_html', '')
    print(f"\nContent length: {len(body)} characters")
    
    # Check for update timestamp in content
    if 'September 5, 2025' in body:
        print("✅ Content CONTAINS 'September 5, 2025' - Update successful!")
    elif 'August 26, 2025' in body:
        print("❌ Content still shows 'August 26, 2025' - Not updated!")
    else:
        print("⚠️  No recognizable date found in content")
    
    # Show first 500 chars
    print(f"\nFirst 500 characters of content:")
    print("-" * 40)
    print(body[:500])
    
    # 2. Test immediate update with timestamp
    print(f"\n\n2. TESTING IMMEDIATE UPDATE:")
    print("-" * 40)
    
    test_content = f"""
    <div style="padding: 40px; background: yellow; text-align: center;">
        <h1>ATTENDANCE PAGE TEST UPDATE</h1>
        <h2>Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</h2>
        <p>If you see this yellow box, the update worked!</p>
    </div>
    {body}
    """
    
    update_payload = {
        'page': {
            'id': attendance_page_id,
            'body_html': test_content
        }
    }
    
    update_url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/pages/{attendance_page_id}.json"
    update_response = requests.put(update_url, headers=headers, json=update_payload)
    
    if update_response.status_code in [200, 201]:
        print("✅ Test update sent successfully!")
        updated_data = update_response.json()
        updated_page = updated_data.get('page', {})
        print(f"Updated at: {updated_page.get('updated_at')}")
        
        # 3. Verify the update
        print(f"\n3. VERIFYING UPDATE:")
        print("-" * 40)
        verify_response = requests.get(url, headers=headers)
        if verify_response.status_code == 200:
            verify_data = verify_response.json()
            verify_page = verify_data.get('page', {})
            verify_body = verify_page.get('body_html', '')
            
            if 'ATTENDANCE PAGE TEST UPDATE' in verify_body:
                print("✅ Test content is present in API response")
            else:
                print("❌ Test content NOT found in API response")
                
        print(f"\n4. CHECK THE LIVE PAGE:")
        print("-" * 40)
        print(f"Admin URL: https://{SHOPIFY_DOMAIN}/admin/online_store/pages/{attendance_page_id}")
        print(f"Live URL: https://backyardtryhards.com/pages/attendance")
        print("\nNOTE: There may be caching. Try:")
        print("  1. Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)")
        print("  2. Incognito/Private browsing")
        print("  3. Wait 1-2 minutes for CDN cache to clear")
    else:
        print(f"❌ Update failed: {update_response.status_code}")
        print(update_response.text)
else:
    print(f"❌ Failed to fetch page: {response.status_code}")
    print(response.text)

print("\n" + "=" * 60)