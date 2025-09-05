#!/usr/bin/env python3
"""Debug Shopify pages to see what's happening"""
import os
import requests
import json
from datetime import datetime

# Load environment
from pathlib import Path
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
print("SHOPIFY PAGE DEBUGGER")
print("=" * 60)
print(f"Store: {SHOPIFY_DOMAIN}")
print()

# 1. List ALL pages
print("1. LISTING ALL PAGES:")
print("-" * 40)
url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/pages.json?limit=250"
response = requests.get(url, headers=headers)

if response.status_code == 200:
    data = response.json()
    pages = data.get('pages', [])
    print(f"Found {len(pages)} pages:\n")
    
    for page in pages:
        print(f"ID: {page['id']}")
        print(f"  Title: {page['title']}")
        print(f"  Handle: {page['handle']}")
        print(f"  Created: {page['created_at']}")
        print(f"  Updated: {page['updated_at']}")
        print(f"  Published: {page.get('published_at', 'Not published')}")
        print(f"  URL: https://{SHOPIFY_DOMAIN}/pages/{page['handle']}")
        print(f"  Admin: https://{SHOPIFY_DOMAIN}/admin/online_store/pages/{page['id']}")
        print()
else:
    print(f"Error listing pages: {response.status_code}")
    print(response.text)

# 2. Check specific Tournament Rankings pages
print("\n2. CHECKING TOURNAMENT RANKINGS PAGES:")
print("-" * 40)

# Search for any page with "tournament" in title
if response.status_code == 200:
    tournament_pages = [p for p in pages if 'tournament' in p['title'].lower()]
    
    if tournament_pages:
        print(f"Found {len(tournament_pages)} tournament-related pages:\n")
        for page in tournament_pages:
            print(f"Checking page ID {page['id']}: {page['title']}")
            
            # Get full page details
            detail_url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/pages/{page['id']}.json"
            detail_response = requests.get(detail_url, headers=headers)
            
            if detail_response.status_code == 200:
                detail_data = detail_response.json()
                page_detail = detail_data.get('page', {})
                
                # Check content preview
                body = page_detail.get('body_html', '')
                print(f"  Content length: {len(body)} characters")
                print(f"  First 200 chars: {body[:200]}...")
                print()
    else:
        print("No tournament pages found!")

# 3. Test updating an existing page
print("\n3. TESTING PAGE UPDATE:")
print("-" * 40)

# Let's try to update the most recent tournament page if it exists
if response.status_code == 200 and tournament_pages:
    test_page = tournament_pages[0]  # Get first tournament page
    page_id = test_page['id']
    
    print(f"Attempting to UPDATE page {page_id}: {test_page['title']}")
    
    update_url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/pages/{page_id}.json"
    
    update_content = f"""
    <h1>UPDATED: Tournament Rankings - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</h1>
    <p style="background: yellow; padding: 20px;">
        <strong>THIS PAGE WAS UPDATED BY DEBUG SCRIPT</strong><br>
        Time: {datetime.now().isoformat()}
    </p>
    <h2>If you see this, the update worked!</h2>
    """
    
    update_payload = {
        'page': {
            'id': page_id,
            'body_html': update_content
        }
    }
    
    print(f"Sending PUT request to update page...")
    update_response = requests.put(update_url, headers=headers, json=update_payload)
    
    if update_response.status_code in [200, 201]:
        print(f"✅ Page updated successfully!")
        updated_data = update_response.json()
        updated_page = updated_data.get('page', {})
        print(f"  Updated at: {updated_page.get('updated_at')}")
        print(f"  View at: https://{SHOPIFY_DOMAIN}/pages/{updated_page.get('handle')}")
    else:
        print(f"❌ Update failed: {update_response.status_code}")
        print(f"  Error: {update_response.text}")

# 4. Check if we're creating duplicates
print("\n4. CHECKING FOR DUPLICATE PAGES:")
print("-" * 40)

if response.status_code == 200:
    # Group pages by similar titles
    title_groups = {}
    for page in pages:
        base_title = page['title'].lower().replace('test', '').strip()
        if base_title not in title_groups:
            title_groups[base_title] = []
        title_groups[base_title].append(page)
    
    # Show any groups with multiple pages
    for title, group in title_groups.items():
        if len(group) > 1:
            print(f"Found {len(group)} pages with similar title '{title}':")
            for p in group:
                print(f"  - ID {p['id']}: {p['title']} (created {p['created_at']})")
            print()

print("\n" + "=" * 60)
print("DEBUG COMPLETE")
print("=" * 60)