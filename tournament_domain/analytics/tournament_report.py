"""
tournament_report.py - Tournament Reporting and Publishing
Handles HTML generation, console reports, and Shopify publishing
"""
import os
import json
import httpx
import datetime
import time
from collections import defaultdict
from utils.database_service import database_service
from log_manager import LogManager
from polymorphic_core import announcer

# Initialize logger for this module
logger = LogManager().get_logger('tournament_report')
from visualizer import UnifiedVisualizer
from tournament_stylesheet import get_inline_styles, format_rank_badge

# Announce tournament reporting service via mDNS
announcer.announce(
    "Tournament Report Service",
    [
        "Generate HTML tournament reports and rankings",
        "Create console reports for terminal display",
        "Publish attendance data to Shopify",
        "Format player rankings with styling",
        "Export data to various formats",
        "Tournament data visualization and reporting"
    ],
    [
        "main() - Generate complete tournament report",
        "generate_html_report() - Create HTML output",
        "publish_to_shopify() - Update Shopify pages"
    ]
)

def get_display_name(primary_contact, data, org_names):
    """Get the best display name for a contact group"""
    contacts = data.get("contacts", [primary_contact])
    
    # Check if any contact has a mapped organization name
    if org_names:
        for contact in contacts:
            for org_data in org_names.values():
                mapped_contacts = [c.lower() for c in org_data["contacts"]]
                if contact.lower() in mapped_contacts:
                    return org_data["display_name"]
    
    # Prefer organization names over email/discord
    for contact in contacts:
        if '@' not in contact and 'discord' not in contact.lower():
            return contact
    
    # For discord entries, return the first contact (original Discord URL)
    if primary_contact.startswith('discord:'):
        return contacts[0] if contacts else primary_contact
    
    # Otherwise return the primary contact
    return primary_contact


def format_html_table(attendance_tracker, org_names):
    """Generate complete HTML table from attendance data using templates"""
    logger.debug(f"Formatting HTML table with {len(attendance_tracker)} entries")
    
    if not attendance_tracker:
        logger.error("No attendance data for HTML table")
        return "<p>No tournament data available.</p>"
    
    # Use unified visualizer for HTML generation
    visualizer = UnifiedVisualizer()
    
    # Sort by attendance
    sorted_orgs = sorted(attendance_tracker.items(), key=lambda x: x[1]["total_attendance"], reverse=True)
    
    total_orgs = len(sorted_orgs)
    grand_total_attendance = sum(org[1]["total_attendance"] for org in sorted_orgs)
    total_tournaments = sum(len(org[1]["tournaments"]) for org in sorted_orgs)
    
    # Get timestamp
    from datetime import datetime, timezone, timedelta
    pacific_offset = timedelta(hours=-7)  # PDT
    pacific_tz = timezone(pacific_offset)
    utc_now = datetime.now(timezone.utc)
    pacific_time = utc_now.astimezone(pacific_tz)
    last_updated = pacific_time.strftime("%B %d, %Y at %I:%M %p Pacific")
    
    # Try to load template
    html_template = None
    try:
        with open("tournament_table.html", "r") as f:
            html_template = f.read()
    except FileNotFoundError:
        pass
    
    table_rows = ""
    for rank, (primary_contact, data) in enumerate(sorted_orgs, 1):
        num_tournaments = len(data["tournaments"])
        total_attendance = data["total_attendance"]
        
        # Get display name (handles the contact mapping logic)
        org_name = get_display_name(primary_contact, data, org_names)
        
        table_rows += f"""
            <tr>
                <td class="rank">{rank}</td>
                <td class="organization">{org_name}</td>
                <td class="tournaments-count">{num_tournaments}</td>
                <td class="attendance-count">{total_attendance:,}</td>
            </tr>
        """
    
    if html_template:
        logger.debug("Using HTML template file")
        html = html_template.replace("{{title}}", "SoCal FGC Tournament Attendance")
        html = html.replace("{{total_orgs}}", f"{total_orgs:,}")
        html = html.replace("{{total_tournaments}}", f"{total_tournaments:,}")
        html = html.replace("{{grand_total_attendance}}", f"{grand_total_attendance:,}")
        html = html.replace("{{table_rows}}", table_rows)
        html = html.replace("{{last_updated}}", last_updated)
        
        return html
    else:
        logger.debug("Using visualizer for HTML generation")
        # Prepare data for visualizer
        table_data = []
        headers = ["#", "Organization", "Tournaments", "Attendance"]
        
        for rank, (primary_contact, data) in enumerate(sorted_orgs, 1):
            org_name = get_display_name(primary_contact, data, org_names)
            table_data.append([
                rank,
                org_name,
                len(data["tournaments"]),
                f"{data['total_attendance']:,}"
            ])
        
        # Use visualizer to create HTML table
        return visualizer.table(
            {'headers': headers, 'rows': table_data},
            title="SoCal FGC Tournament Attendance",
            subtitle=f"Last updated: {last_updated}"
        )

# Function removed - now using visualizer for all HTML generation

def find_store_and_theme():
    """Find Shopify store and theme configuration
    
    ⚠️ IMPORTANT: All configuration comes from .env file
    - SHOPIFY_ACCESS_TOKEN: The Shopify API token (starts with shpat_)
    - SHOPIFY_DOMAIN: The store domain (e.g., 8ccd49-4.myshopify.com)
    - ACCESS_TOKEN is NOT for Shopify - it's a legacy token
    
    See ENV_CONFIGURATION.md for details.
    """
    # Get from .env - NEVER hardcode these values!
    access_token = os.getenv("SHOPIFY_ACCESS_TOKEN")
    if not access_token:
        raise RuntimeError("SHOPIFY_ACCESS_TOKEN not set in .env file")
    
    store_url = os.getenv("SHOPIFY_DOMAIN", "8ccd49-4.myshopify.com")
    headers = {"X-Shopify-Access-Token": access_token, "Content-Type": "application/json"}
    
    with httpx.Client(timeout=10.0) as client:
        response = client.get(f"https://{store_url}/admin/api/2023-10/themes.json", headers=headers)
        if response.status_code == 200:
            themes = response.json()["themes"]
            main_theme = next((t for t in themes if t.get("role") == "main"), themes[0])
            return store_url, main_theme["id"], access_token
    raise RuntimeError("Could not connect to Shopify store")

def update_template(store_url, theme_id, access_token, html_content, attendance_tracker, org_names):
    """Update Shopify template with tournament data
    
    ⚠️ CRITICAL: This updates templates/page.attendance.json ONLY
    We NEVER create new pages! See IMPORTANT_SHOPIFY_RULES.md
    """
    template = "templates/page.attendance.json"
    headers = {"X-Shopify-Access-Token": access_token, "Content-Type": "application/json"}
    
    with httpx.Client(timeout=30.0) as client:
        asset_url = f"https://{store_url}/admin/api/2023-10/themes/{theme_id}/assets.json"
        
        try:
            response = client.get(asset_url, headers=headers, params={"asset[key]": template})
            if response.status_code == 200:
                current_data = json.loads(response.json()["asset"]["value"])
            else:
                current_data = {"sections": {"main": {"type": "page", "settings": {}}}, "order": ["main"]}
        except Exception as e:
            current_data = {"sections": {"main": {"type": "page", "settings": {}}}, "order": ["main"]}
        
        html_sections = []
        for section_id, section_data in current_data.get("sections", {}).items():
            section_type = section_data.get("type", "")
            if "custom-liquid" in section_type or "liquid" in section_type:
                html_sections.append((section_id, "custom_liquid"))
            elif "html" in section_type:
                html_sections.append((section_id, "html"))
        
        if html_sections:
            section_id, setting_name = html_sections[0]
            if "settings" not in current_data["sections"][section_id]:
                current_data["sections"][section_id]["settings"] = {}
            current_data["sections"][section_id]["settings"][setting_name] = format_html_table(attendance_tracker, org_names)
        else:
            new_section_id = f"tournament_html_{int(time.time())}"
            current_data["sections"][new_section_id] = {
                "type": "custom-liquid",
                "settings": {
                    "custom_liquid": format_html_table(attendance_tracker, org_names)
                }
            }
            
            if "order" in current_data:
                if new_section_id not in current_data["order"]:
                    current_data["order"].append(new_section_id)
            else:
                current_data["order"] = ["main", new_section_id]
        
        update_data = {"asset": {"key": template, "value": json.dumps(current_data, indent=2)}}
        response = client.put(asset_url, headers=headers, json=update_data)
        response.raise_for_status()
        return True

def publish_table(attendance_tracker, org_names, console_only=False):
    """Publish tournament table to Shopify or console"""
    try:
        html_content = format_html_table(attendance_tracker, org_names)
        
        if console_only:
            logger.info("Console output mode - not publishing to Shopify")
            
            # Show rankings in console
            sorted_orgs = sorted(attendance_tracker.items(), key=lambda x: x[1]["total_attendance"], reverse=True)
            
            print(f"{'RANK':<6} {'ORGANIZATION':<50} {'TOURNAMENTS':<12} {'ATTENDANCE':<12}")
            print("-" * 80)
            
            for rank, (primary_contact, data) in enumerate(sorted_orgs[:20], 1):  # Show top 20
                org_name = get_display_name(primary_contact, data, org_names)
                tournaments = len(data["tournaments"])
                attendance = data["total_attendance"]
                
                print(f"{rank:<6} {org_name[:48]:<50} {tournaments:<12} {attendance:<12}")
            
            print("-" * 80)
            print(f"Total organizations: {len(sorted_orgs)}")
            print(f"Total tournaments: {sum(len(org[1]['tournaments']) for org in sorted_orgs)}")
            print(f"Total attendance: {sum(org[1]['total_attendance'] for org in sorted_orgs):,}")
            
            return True
        else:
            store_url, theme_id, access_token = find_store_and_theme()
            success = update_template(store_url, theme_id, access_token, html_content, attendance_tracker, org_names)
            
            if success:
                logger.info(f"Published to {store_url}")
            else:
                logger.error("Failed to update template")
            return success
            
    except Exception as e:
        logger.error(f"Publishing error: {e}")
        return False

def format_console_table(limit=20):
    """Generate console-friendly table for debugging"""
    print("Tournament Attendance Report")
    print("=" * 80)
    
    rankings = database_service.get_attendance_rankings(limit)
    stats = database_service.get_summary_stats()
    
    if not rankings:
        print("No attendance data available")
        return
    
    # Header
    print(f"{'Rank':<4} {'Organization':<40} {'Events':<8} {'Attendance':<12}")
    print("-" * 80)
    
    # Rows
    for rank, org_data in enumerate(rankings, 1):
        organization = org_data['display_name'][:38]  # Truncate long names
        tournament_count = org_data['tournament_count']
        total_attendance = org_data['total_attendance']
        
        medal = ""
        if rank == 1:
            medal = "1st"
        elif rank == 2:
            medal = "2nd"
        elif rank == 3:
            medal = "3rd"
        
        print(f"{medal}{rank:<3} {organization:<40} {tournament_count:<8} {total_attendance:<12,}")
    
    print("-" * 80)
    print(f"Summary: {stats['total_organizations']} orgs, "
          f"{stats['total_tournaments']} tournaments, "
          f"{stats['total_attendance']:,} total attendance")

def generate_html_report(limit=None, output_file=None):
    """Generate HTML attendance report"""
    logger.info("Generating HTML report")
    
    try:
        # Get data from database
        from shopify_service import shopify_service, get_legacy_attendance_data
        attendance_tracker, org_names = get_legacy_attendance_data()
        
        # Generate HTML
        html = format_html_table(attendance_tracker, org_names)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)
            logger.info(f"HTML report saved to {output_file}")
        else:
            print("HTML Report Generated:")
            print("-" * 80)
            print(html)
            print("-" * 80)
        
        return html
        
    except Exception as e:
        logger.error(f"HTML generation failed: {e}")
        return None

def get_legacy_attendance_data():
    """
    Convert SQLAlchemy data to legacy format for existing Shopify code
    Returns data in the format expected by existing publishing system
    """
    rankings = database_service.get_attendance_rankings()
    
    # Convert to old format (attendance_tracker, org_names)
    attendance_tracker = {}
    org_names = {}
    
    for rank, org_data in enumerate(rankings, 1):
        # Use display_name as key since normalized_key doesn't exist
        key = org_data['display_name']
        
        # Attendance tracker format
        # Use tournament_count from the rankings data
        tournament_count = org_data.get('tournament_count', 0)
        attendance_tracker[key] = {
            'tournaments': [''] * tournament_count,  # Create list with correct count
            'total_attendance': org_data.get('total_attendance', 0),
            'contacts': []  # No contacts in rankings anymore
        }
        
        # Organization names format - always include for now
        org_names[f"org_{rank}"] = {
            'display_name': org_data['display_name'],
            'contacts': []
        }
    
    return attendance_tracker, org_names

def publish_to_shopify():
    """Publish tournament data to Shopify"""
    logger.info("Publishing to Shopify")
    
    try:
        # Get data from database in legacy format
        from shopify_service import shopify_service, get_legacy_attendance_data
        attendance_tracker, org_names = get_legacy_attendance_data()
        
        # Publish using existing functionality
        success = publish_table(attendance_tracker, org_names)
        
        if success:
            logger.info("Successfully published to Shopify")
            return True
        else:
            logger.error("Shopify publishing failed")
            return False
            
    except Exception as e:
        logger.error(f"Shopify publishing failed: {e}")
        return False

def generate_geo_data(output_format='json'):
    """
    Generate geographic data for tournaments
    Returns GeoJSON for mapping or regular JSON for analysis
    """
    from collections import defaultdict
    import json
    
    geo_data = []
    city_stats = defaultdict(int)
    
    # Get all tournaments with geo data using DatabaseService
    tournaments = database_service.get_tournaments_with_location()
    
    for t in tournaments:
            try:
                lat = float(t.lat)
                lng = float(t.lng)
                
                geo_entry = {
                    'id': t.id,
                    'name': t.name,
                    'lat': lat,
                    'lng': lng,
                    'city': t.city,
                    'state': t.addr_state,
                    'venue': t.venue_name,
                    'address': t.venue_address,
                    'attendees': t.num_attendees or 0,
                    'date': t.start_at,
                    'slug': t.short_slug or t.slug
                }
                
                geo_data.append(geo_entry)
                
                # Track city statistics
                if t.city:
                    city_stats[t.city] += 1
                    
            except (ValueError, TypeError):
                continue
    
    if output_format == 'geojson':
        # Return GeoJSON format for mapping
        features = []
        for entry in geo_data:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [entry['lng'], entry['lat']]
                },
                "properties": {
                    "name": entry['name'],
                    "city": entry['city'],
                    "venue": entry['venue'],
                    "attendees": entry['attendees'],
                    "date": entry['date']
                }
            })
        
        return {
            "type": "FeatureCollection",
            "features": features
        }
    else:
        # Return regular JSON with stats
        return {
            'tournaments': geo_data,
            'city_stats': dict(city_stats),
            'total_with_geo': len(geo_data)
        }

if __name__ == "__main__":
    print("Testing tournament reporting...")
    
    # Test console report
    print("\nConsole Table Test:")
    format_console_table(10)
    
    # Test HTML generation
    print(f"\nHTML Report Test:")
    html = generate_html_report()
    if html:
        print(f"Generated {len(html)} characters of HTML")
    
    print("Tournament reporting tests completed!")

