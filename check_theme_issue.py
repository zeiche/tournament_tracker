#!/usr/bin/env python3
"""Check if theme is overriding page content"""
import os
import requests
import json
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
print("CHECKING THEME AND TEMPLATE ISSUES")
print("=" * 60)

# 1. Check active theme
print("\n1. CHECKING ACTIVE THEME:")
print("-" * 40)

themes_url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/themes.json"
response = requests.get(themes_url, headers=headers)

if response.status_code == 200:
    themes = response.json().get('themes', [])
    active_theme = None
    
    for theme in themes:
        if theme.get('role') == 'main':
            active_theme = theme
            print(f"Active theme: {theme.get('name')}")
            print(f"Theme ID: {theme.get('id')}")
            print(f"Updated: {theme.get('updated_at')}")
            break
    
    if active_theme:
        theme_id = active_theme.get('id')
        
        # Check if there's a custom page template
        print("\n2. CHECKING FOR CUSTOM PAGE TEMPLATES:")
        print("-" * 40)
        
        # Look for page templates
        assets_url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/themes/{theme_id}/assets.json"
        assets_response = requests.get(assets_url, headers=headers)
        
        if assets_response.status_code == 200:
            assets = assets_response.json().get('assets', [])
            
            # Look for attendance-related templates
            attendance_templates = []
            page_templates = []
            
            for asset in assets:
                key = asset.get('key', '')
                if 'attendance' in key.lower():
                    attendance_templates.append(key)
                elif 'templates/page' in key:
                    page_templates.append(key)
            
            if attendance_templates:
                print("⚠️  Found attendance-specific templates:")
                for template in attendance_templates:
                    print(f"   - {template}")
                    
                    # Get the template content
                    template_url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/themes/{theme_id}/assets.json?asset[key]={template}"
                    template_response = requests.get(template_url, headers=headers)
                    if template_response.status_code == 200:
                        asset_data = template_response.json().get('asset', {})
                        content = asset_data.get('value', '')
                        if 'August 26' in content or 'OneMustFall' in content:
                            print(f"   ❌ FOUND HARDCODED CONTENT IN {template}!")
                            print("      This template contains the old data!")
            
            if page_templates:
                print("\nPage templates found:")
                for template in page_templates[:5]:  # Show first 5
                    print(f"   - {template}")

# 2. Check metafields
print("\n3. CHECKING PAGE METAFIELDS:")
print("-" * 40)

attendance_page_id = "108546031752"
metafields_url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/pages/{attendance_page_id}/metafields.json"
meta_response = requests.get(metafields_url, headers=headers)

if meta_response.status_code == 200:
    metafields = meta_response.json().get('metafields', [])
    if metafields:
        print(f"Found {len(metafields)} metafields")
        for field in metafields:
            print(f"  - {field.get('namespace')}.{field.get('key')}: {field.get('value')[:50]}...")
    else:
        print("No metafields found")

# 3. Try GraphQL API to check content
print("\n4. CHECKING VIA GRAPHQL API:")
print("-" * 40)

graphql_url = f"https://{SHOPIFY_DOMAIN}/admin/api/2024-01/graphql.json"
graphql_query = {
    "query": """
    {
      page(id: "gid://shopify/OnlineStorePage/108546031752") {
        id
        title
        handle
        body
        bodySummary
        publishedAt
        updatedAt
      }
    }
    """
}

graphql_response = requests.post(graphql_url, headers=headers, json=graphql_query)
if graphql_response.status_code == 200:
    gql_data = graphql_response.json()
    page_data = gql_data.get('data', {}).get('page', {})
    if page_data:
        body = page_data.get('body', '')
        print(f"Page title: {page_data.get('title')}")
        print(f"Published: {page_data.get('publishedAt')}")
        print(f"Updated: {page_data.get('updatedAt')}")
        
        if 'GREEN' in body or 'FRESH PUBLISH TEST' in body:
            print("✅ GraphQL shows NEW content (GREEN box)")
        elif 'TEST UPDATE' in body:
            print("✅ GraphQL shows TEST content")
        else:
            print("❌ GraphQL shows different content")

# 4. Direct check of what the store is serving
print("\n5. CHECKING ACTUAL RENDERED CONTENT:")
print("-" * 40)

# Check both domains
domains = [
    f"https://{SHOPIFY_DOMAIN}/pages/attendance",
    "https://backyardtryhards.com/pages/attendance"
]

for domain_url in domains:
    print(f"\nChecking: {domain_url}")
    try:
        page_response = requests.get(domain_url, timeout=5)
        if page_response.status_code == 200:
            content = page_response.text
            
            # Check for specific markers
            if 'August 26, 2025' in content:
                print("  ❌ Shows OLD content (August 26)")
            elif 'GREEN' in content or 'FRESH PUBLISH' in content:
                print("  ✅ Shows NEW content (GREEN box)")
            elif 'September' in content:
                print("  ✅ Shows UPDATED content (September)")
            
            # Check if it's using a template
            if 'template-attendance' in content or 'page-attendance' in content:
                print("  ⚠️  Using custom attendance template")
            
            # Check for Liquid tags
            if '{{' in content or '{%' in content:
                print("  ⚠️  Contains unprocessed Liquid tags")
    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "=" * 60)
print("DIAGNOSIS:")
print("=" * 60)

print("""
If the API shows new content but the site shows old:
1. Theme has a HARDCODED template (templates/page.attendance.liquid)
2. Theme is using metafields or sections for content
3. There's an app injecting the old content
4. CDN/Proxy is serving cached content (Cloudflare, etc)

SOLUTION:
- Check theme files for 'page.attendance.liquid'
- Look in theme customizer for attendance page sections
- Check if any apps control page content
- Check DNS settings (is it using Cloudflare?)
""")